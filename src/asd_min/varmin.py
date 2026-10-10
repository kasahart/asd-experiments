"""VarMin: per-band variance-minimum rescaling of BEAM distances.

Each equation in beam.md's VarMin section is one function here.
"""

import logging
from typing import Tuple

import numpy as np

from .band_distance import nearest_reference, self_excluded_distances

logger = logging.getLogger(__name__)


def compute_local_density(
    reference_normalized: np.ndarray,
    k: int = 4,
    chunk_size: int = 128,
) -> np.ndarray:
    """b[i,f] = mean distance from reference i to its K nearest *other* references.

    Inputs are checked once by ``BEAMVarianceMin``.

    Args:
        reference_normalized: ``[R, F, D]`` finite unit-norm normal references.
        k: Number of neighbours K. Reduced to ``R - 1`` with a warning when
            fewer references exist.
        chunk_size: Number of references processed at once.

    Returns:
        Local density ``b`` of shape ``[R, F]``.
    """
    reference_count, frequency_count, _ = reference_normalized.shape
    if reference_count < 2:
        raise ValueError("Variance-minimum rescaling needs at least 2 references")
    effective_k = min(k, reference_count - 1)
    if effective_k != k:
        logger.warning(
            "Only %d references are available; using effective_k=%d instead of K=%d.",
            reference_count,
            effective_k,
            k,
        )

    density = np.empty((reference_count, frequency_count), dtype=np.float32)
    for query_slice, distance in self_excluded_distances(
        reference_normalized, chunk_size
    ):
        nearest = np.partition(distance, effective_k - 1, axis=1)[:, :effective_k, :]
        density[query_slice] = nearest.mean(axis=1)
    return density


def leave_one_out_nearest(
    reference_normalized: np.ndarray, chunk_size: int = 128
) -> Tuple[np.ndarray, np.ndarray]:
    """Raw nearest other reference of each normal reference (TrainAll leave-one-out).

    j(z,f) = argmin_{i != z} D(y[z,f], y[i,f])
    u[z,f] = D(y[z,f], y[j(z,f),f])

    Args:
        reference_normalized: ``[R, F, D]`` unit-norm normal references.
        chunk_size: Number of references processed at once.

    Returns:
        ``(u, j)``: distances ``[R, F]`` (float32) and indices ``[R, F]``.
    """
    reference_count, frequency_count, _ = reference_normalized.shape
    u = np.empty((reference_count, frequency_count), dtype=np.float32)
    j = np.empty((reference_count, frequency_count), dtype=np.intp)
    for query_slice, distance in self_excluded_distances(
        reference_normalized, chunk_size
    ):
        j[query_slice], u[query_slice] = nearest_reference(distance)
    return u, j


def variance_minimizing_alpha(
    u: np.ndarray, v: np.ndarray, eps: float = 1e-12
) -> np.ndarray:
    """alpha[f] = Cov_z(u[z,f], v[z,f]) / Var_z(v[z,f]).

    This alpha minimizes the variance over z of ``u - alpha * v``, that is, of
    the rescaled normal scores. Bands whose ``Var_z(v)`` is at most ``eps`` get
    alpha = 0 with a warning. Alpha is not clipped and may be negative.

    Args:
        u: Raw leave-one-out distances ``[R, F]``.
        v: Local density of the selected neighbour, ``v[z,f] = b[j(z,f),f]``.
        eps: Variance threshold.

    Returns:
        Per-band alpha ``[F]`` (float32).
    """
    frequency_count = u.shape[1]
    u_centered = u.astype(np.float64) - u.mean(axis=0, dtype=np.float64)
    v_centered = v.astype(np.float64) - v.mean(axis=0, dtype=np.float64)
    numerator = np.mean(u_centered * v_centered, axis=0)
    denominator = np.mean(v_centered * v_centered, axis=0)
    alpha = np.zeros(frequency_count, dtype=np.float64)
    stable = denominator > eps
    alpha[stable] = numerator[stable] / denominator[stable]
    if not stable.all():
        logger.warning(
            "VarMin alpha denominator <= eps for bands %s; alpha is set to zero.",
            np.flatnonzero(~stable).tolist(),
        )
    if not np.isfinite(alpha).all():
        raise FloatingPointError("Alpha estimation produced NaN or Inf")
    return alpha.astype(np.float32)


def estimate_train_all_alpha(
    reference_normalized: np.ndarray,
    local_density: np.ndarray,
    chunk_size: int = 128,
    eps: float = 1e-12,
) -> np.ndarray:
    """Estimate per-band alpha with TrainAll leave-one-out validation.

    Runs ``leave_one_out_nearest`` (j, u), gathers v[z,f] = b[j(z,f),f], and
    returns ``variance_minimizing_alpha(u, v)``.

    Args:
        reference_normalized: ``[R, F, D]`` unit-norm normal references.
        local_density: ``b`` from ``compute_local_density``, shape ``[R, F]``.
        chunk_size: Number of references processed at once.
        eps: Variance threshold for alpha.

    Returns:
        Per-band alpha ``[F]``.
    """
    frequency_count = reference_normalized.shape[1]
    density = np.asarray(local_density, dtype=np.float32)
    u, j = leave_one_out_nearest(reference_normalized, chunk_size)
    v = density[j, np.arange(frequency_count)[None, :]]  # v[z,f] = b[j(z,f),f]
    return variance_minimizing_alpha(u, v, eps)


def rescaled_distance(
    distance: np.ndarray, alpha: np.ndarray, local_density: np.ndarray
) -> np.ndarray:
    """VarMin-rescaled distance D(q[f], y[i,f]) - alpha[f] b[i,f].

    Args:
        distance: Raw distances ``[Q, R, F]``.
        alpha: Per-band coefficients ``[F]``.
        local_density: ``b`` of the references, ``[R, F]``.

    Returns:
        Rescaled distances ``[Q, R, F]``; values may be negative.
    """
    return distance - alpha[None, None, :] * local_density[None, :, :]


class VarianceMinRescaler:
    """Fit the VarMin terms ``b`` and ``alpha`` from normal references.

    Only TrainAll validation and a separate alpha per band are implemented; the
    arguments keep the ASDKit configuration names.

    Args:
        k: Number of neighbours for the local density.
        validation: Must be ``"train_all"``.
        scope: Must be ``"per_band"``.
        chunk_size: Number of references processed at once.
        eps: Variance threshold for alpha.
    """

    def __init__(
        self,
        k: int = 4,
        validation: str = "train_all",
        scope: str = "per_band",
        chunk_size: int = 128,
        eps: float = 1e-12,
    ):
        if validation != "train_all":
            raise NotImplementedError(
                f"rescale_validation={validation!r} is not implemented"
            )
        if scope != "per_band":
            raise NotImplementedError(f"rescale_scope={scope!r} is not implemented")
        if isinstance(k, bool) or not isinstance(k, int) or k <= 0:
            raise ValueError(f"k must be a positive integer, got {k!r}")
        self.k = k
        self.validation = validation
        self.scope = scope
        self.chunk_size = chunk_size
        self.eps = eps

    def fit(self, reference_normalized: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Compute local density and alpha for one normal memory.

        Args:
            reference_normalized: ``[R, F, D]`` unit-norm normal references.

        Returns:
            ``(local_density, alpha)`` with shapes ``[R, F]`` and ``[F]``.
        """
        density = compute_local_density(
            reference_normalized, k=self.k, chunk_size=self.chunk_size
        )
        alpha = estimate_train_all_alpha(
            reference_normalized,
            density,
            chunk_size=self.chunk_size,
            eps=self.eps,
        )
        return density, alpha
