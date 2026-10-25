"""Encoder-independent pooling for time-frequency patch embeddings."""

from __future__ import annotations

import math
from typing import NamedTuple, Optional, Tuple, Union

import torch


def sequence_to_time_frequency(
    x_seq: torch.Tensor, grid_shape: Tuple[int, int]
) -> torch.Tensor:
    """Restore a row-major patch sequence to its time-frequency grid.

    Args:
        x_seq: Patch sequence ``[B, L, D]`` with ``L = T * F``.
        grid_shape: ``(T, F)`` patch counts.

    Returns:
        ``[B, T, F, D]`` tensor (a view of the input).
    """

    if x_seq.ndim != 3:
        raise ValueError(
            f"x_seq must have shape [B, L, D], but got {tuple(x_seq.shape)}"
        )
    if len(grid_shape) != 2:
        raise ValueError(f"grid_shape must be (T, F), but got {grid_shape}")
    time_patches, frequency_patches = grid_shape
    if time_patches <= 0 or frequency_patches <= 0:
        raise ValueError(f"grid dimensions must be positive, but got {grid_shape}")
    expected_length = time_patches * frequency_patches
    if x_seq.shape[1] != expected_length:
        raise ValueError(
            "Patch sequence length does not match its grid: "
            f"L={x_seq.shape[1]}, T_p={time_patches}, "
            f"F_p={frequency_patches}, "
            f"expected_length={expected_length}"
        )
    return x_seq.reshape(
        x_seq.shape[0], time_patches, frequency_patches, x_seq.shape[2]
    )


def _expand_valid_time_mask(
    valid_time_mask: Optional[torch.Tensor], x_tf: torch.Tensor
) -> torch.Tensor:
    """Expand an optional ``[B, T]`` or ``[B, T, F]`` mask to boolean ``[B, T, F]``.

    None means every patch is valid. Every sample and band must keep at least
    one valid time patch.
    """
    batch, time, frequency, _ = x_tf.shape
    if time == 0:
        raise ValueError("x_tf must contain at least one time patch")
    if valid_time_mask is None:
        return torch.ones(
            (batch, time, frequency), dtype=torch.bool, device=x_tf.device
        )
    if valid_time_mask.dtype != torch.bool:
        raise TypeError("valid_time_mask must have dtype torch.bool")
    if valid_time_mask.device != x_tf.device:
        raise ValueError("valid_time_mask and x_tf must be on the same device")
    if valid_time_mask.shape == (batch, time):
        mask = valid_time_mask.unsqueeze(-1).expand(-1, -1, frequency)
    elif valid_time_mask.shape == (batch, time, frequency):
        mask = valid_time_mask
    else:
        raise ValueError(
            "valid_time_mask must have shape [B, T] or [B, T, F], but got "
            f"{tuple(valid_time_mask.shape)}"
        )
    if not mask.any(dim=1).all():
        raise ValueError("Every sample and frequency band needs a valid time patch")
    return mask


def _validate_time_frequency(x_tf: torch.Tensor) -> None:
    """Check that ``x_tf`` is a finite floating tensor of shape ``[B, T, F, D]``."""
    if x_tf.ndim != 4:
        raise ValueError(f"x_tf must have shape [B, T, F, D], got {tuple(x_tf.shape)}")
    if not x_tf.is_floating_point():
        raise TypeError(f"x_tf must be floating point, got {x_tf.dtype}")
    if not torch.isfinite(x_tf).all():
        raise ValueError("x_tf contains NaN or Inf")


class _ScaledBands(NamedTuple):
    """Valid patches divided by one scale per sample and band.

    The scale prevents overflow for finite inputs near the dtype limit; it does
    not change the time weights, and ``restore_band_scale`` undoes it.
    """

    x: torch.Tensor  # [B, T, F, D], invalid patches set to zero
    mask: torch.Tensor  # [B, T, F]
    mean_weight: torch.Tensor  # [B, T, F, 1], 1 / valid count on valid patches
    scale: torch.Tensor  # [B, 1, F, 1]


def _scale_bands(
    x_tf: torch.Tensor, valid_time_mask: Optional[torch.Tensor]
) -> _ScaledBands:
    """Mask invalid patches and divide each sample and band by its maximum magnitude.

    float16 and bfloat16 inputs are computed in float32.

    Args:
        x_tf: ``[B, T, F, D]`` features.
        valid_time_mask: Optional ``[B, T]`` or ``[B, T, F]`` boolean mask.

    Returns:
        ``_ScaledBands`` holding the scaled features, mask, mean weights and scale.
    """
    mask = _expand_valid_time_mask(valid_time_mask, x_tf)
    compute_dtype = (
        torch.float32 if x_tf.dtype in {torch.float16, torch.bfloat16} else x_tf.dtype
    )
    x_compute = x_tf.to(dtype=compute_dtype)
    mask_value = mask.unsqueeze(-1).to(dtype=compute_dtype)
    valid_count = mask_value.sum(dim=1)
    mean_weight = mask_value / valid_count.unsqueeze(1)
    valid_x = x_compute.masked_fill(~mask.unsqueeze(-1), 0)
    band_scale = valid_x.abs().amax(dim=(1, 3), keepdim=True)
    safe_band_scale = torch.where(
        band_scale > 0, band_scale, torch.ones_like(band_scale)
    )
    return _ScaledBands(valid_x / safe_band_scale, mask, mean_weight, safe_band_scale)


def restore_band_scale(
    pooled_scaled: torch.Tensor, bands: _ScaledBands, dtype: torch.dtype
) -> torch.Tensor:
    """Undo ``_scale_bands`` on a pooled ``[B, F, D]`` result and cast to ``dtype``."""
    return (pooled_scaled.clamp(min=-1, max=1) * bands.scale.squeeze(1)).to(dtype)


def time_mean(bands: _ScaledBands) -> torch.Tensor:
    """mu[f] = mean over valid t of x[t,f].

    Args:
        bands: Scaled features from ``_scale_bands``.

    Returns:
        ``[B, F, D]`` time mean (in the scaled domain).
    """
    return (bands.x * bands.mean_weight).sum(dim=1)


def relative_deviation(
    bands: _ScaledBands, mu: torch.Tensor, eps: float
) -> torch.Tensor:
    """r[t,f] = ||x[t,f] - mu[f]|| / max_t ||x[t,f] - mu[f]||.

    ``r`` is zero for every t when the maximum deviation is at most ``eps``
    (measured before scaling), so the pooling falls back to the plain mean.

    Args:
        bands: Scaled features from ``_scale_bands``.
        mu: ``[B, F, D]`` output of ``time_mean``.
        eps: Deviation threshold.

    Returns:
        ``[B, T, F]`` relative deviations in ``[0, 1]``; zero on invalid patches.
    """
    distance = torch.linalg.vector_norm(bands.x - mu.unsqueeze(1), dim=-1)
    distance = distance.masked_fill(~bands.mask, 0)
    max_distance = distance.amax(dim=1, keepdim=True)
    scaled_eps = eps / bands.scale.squeeze(-1)
    has_deviation = max_distance > scaled_eps
    safe_max_distance = torch.where(
        has_deviation, max_distance, torch.ones_like(max_distance)
    )
    return torch.where(
        has_deviation,
        distance / safe_max_distance,
        torch.zeros_like(distance),
    )


def deviation_weights(
    r: torch.Tensor, gamma: float, mask: torch.Tensor, dtype: torch.dtype
) -> torch.Tensor:
    """w[t,f] = (1 + r[t,f])^gamma / sum_t (1 + r[t,f])^gamma.

    Computed as softmax_t(gamma * log1p(r)) so large gamma does not overflow.
    Invalid patches get zero weight.

    Args:
        r: ``[B, T, F]`` output of ``relative_deviation``.
        gamma: Non-negative emphasis exponent; 0 gives the plain mean.
        mask: ``[B, T, F]`` valid patches.
        dtype: Output dtype.

    Returns:
        ``[B, T, F]`` weights summing to one over t.
    """
    weight_dtype = torch.float64 if gamma > torch.finfo(torch.float32).max else dtype
    log_weight = torch.log1p(r.to(dtype=weight_dtype)) * gamma
    log_weight = log_weight.masked_fill(~mask, -torch.inf)
    return torch.softmax(log_weight, dim=1).to(dtype=dtype)


def weighted_time_sum(x: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
    """q[f] = sum_t w[t,f] x[t,f].

    Args:
        x: ``[B, T, F, D]`` features.
        weight: ``[B, T, F]`` time weights.

    Returns:
        ``[B, F, D]`` pooled features.
    """
    return (x * weight.unsqueeze(-1)).sum(dim=1)


def relative_deviation_pooling(
    x_tf: torch.Tensor,
    gamma: float = 4.0,
    eps: float = 1e-8,
    valid_time_mask: Optional[torch.Tensor] = None,
    return_weights: bool = False,
) -> Union[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
    """RDP: pool time independently per band, emphasizing relative deviations.

    Computes ``time_mean`` (mu), ``relative_deviation`` (r),
    ``deviation_weights`` (w) and ``weighted_time_sum`` (q) in that order.

    Args:
        x_tf: Floating-point tensor with shape ``[B, T, F, D]``.
        gamma: Non-negative deviation emphasis exponent.
        eps: Threshold below which the maximum deviation is treated as zero.
        valid_time_mask: Optional boolean ``[B, T]`` or ``[B, T, F]`` mask.
        return_weights: Also return normalized ``[B, T, F]`` weights.

    Returns:
        Pooled ``[B, F, D]`` features in the input dtype, and the weights when
        ``return_weights`` is True.
    """

    _validate_time_frequency(x_tf)
    if isinstance(gamma, bool) or not isinstance(gamma, (int, float)):
        raise TypeError("gamma must be a finite non-negative number")
    gamma = float(gamma)
    if not math.isfinite(gamma) or gamma < 0:
        raise ValueError(f"gamma must be finite and non-negative, got {gamma}")
    if not math.isfinite(eps) or eps <= 0:
        raise ValueError(f"eps must be finite and positive, got {eps}")

    bands = _scale_bands(x_tf, valid_time_mask)
    r = relative_deviation(bands, time_mean(bands), eps)
    weight_compute = deviation_weights(r, gamma, bands.mask, bands.x.dtype)
    pooled = restore_band_scale(
        weighted_time_sum(bands.x, weight_compute), bands, x_tf.dtype
    )
    weight = weight_compute.to(dtype=x_tf.dtype)

    if not torch.isfinite(pooled).all() or not torch.isfinite(weight).all():
        raise FloatingPointError("RDP produced a non-finite result")
    if return_weights:
        return pooled, weight
    return pooled


def frequency_pooling(
    x_tf: torch.Tensor,
    mode: str = "rdp",
    gamma: float = 4.0,
    eps: float = 1e-8,
    valid_time_mask: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    """Pool ``[B, T, F, D]`` over time while retaining frequency bands.

    Args:
        x_tf: ``[B, T, F, D]`` features.
        mode: ``"rdp"`` (``relative_deviation_pooling``) or ``"mean"``
            (``time_mean`` only).
        gamma: RDP emphasis exponent; ignored for ``"mean"``.
        eps: RDP deviation threshold; ignored for ``"mean"``.
        valid_time_mask: Optional boolean ``[B, T]`` or ``[B, T, F]`` mask.

    Returns:
        ``[B, F, D]`` pooled features in the input dtype.
    """

    if mode not in {"mean", "rdp"}:
        raise ValueError(f"pooling mode must be 'mean' or 'rdp', got {mode!r}")
    if mode == "rdp":
        pooled = relative_deviation_pooling(
            x_tf,
            gamma=gamma,
            eps=eps,
            valid_time_mask=valid_time_mask,
        )
        assert isinstance(pooled, torch.Tensor)
        return pooled

    _validate_time_frequency(x_tf)
    bands = _scale_bands(x_tf, valid_time_mask)
    return restore_band_scale(time_mean(bands), bands, x_tf.dtype)


__all__ = [
    "deviation_weights",
    "frequency_pooling",
    "relative_deviation",
    "relative_deviation_pooling",
    "sequence_to_time_frequency",
    "time_mean",
    "weighted_time_sum",
]
