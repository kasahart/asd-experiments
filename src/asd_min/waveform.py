# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart (companion additions)
# Portions adapted from research code Copyright (c) 2025 Takuya Fujimura.
"""Waveform conditions B0/B1/W1/SS; each equation in waveform.md is one function.

W1 operations are adapted from the MIT research snapshot. See
licenses/research-MIT.txt and THIRD_PARTY_NOTICES.md. No Wandas DSP here.
"""

import numpy as np
import soundfile as sf
import torch


def load_audio(path):
    """Read a 16 kHz two-channel WAV as float32 ``[2, N]`` (row 0 near, row 1 far).

    Raises:
        ValueError: The rate, channel count, length (> 512 samples) or
            finiteness differs from the protocol.
    """
    frames, rate = sf.read(path, dtype="float32", always_2d=True)
    if rate != 16000 or frames.shape[1] != 2 or len(frames) <= 512:
        raise ValueError("Expected 16 kHz stereo [near, far], length >512")
    if not np.isfinite(frames).all():
        raise ValueError("Non-finite audio")
    return np.ascontiguousarray(frames.T)


def _validate_stereo(wave, min_length, name):
    """Return ``wave`` as float32 ``[2, N]`` after checking shape, length and finiteness."""
    array = np.asarray(wave, dtype=np.float32)
    if (
        array.ndim != 2
        or array.shape[0] != 2
        or array.shape[1] <= min_length
        or not np.isfinite(array).all()
    ):
        raise ValueError(
            f"{name} requires finite stereo audio longer than {min_length} samples"
        )
    return array


def _stft(tensor, p):
    """Torch periodic-Hann STFT of [near, far] with the method's fixed settings.

    Args:
        tensor: ``[2, N]`` waveform.
        p: ``W1_PARAMETERS`` or ``SS_PARAMETERS``.

    Returns:
        ``(spectra, window)``: complex ``[2, n_fft // 2 + 1, frames]`` and the
        window to reuse in ``_istft``.
    """
    window = torch.hann_window(p["win_length"], periodic=True, dtype=tensor.dtype)
    spectra = torch.stft(
        tensor,
        n_fft=p["n_fft"],
        hop_length=p["hop_length"],
        win_length=p["win_length"],
        window=window,
        center=p["center"],
        pad_mode=p["pad_mode"],
        normalized=p["normalized"],
        onesided=p["onesided"],
        return_complex=True,
    )
    return spectra, window


def _istft(spectrum, window, p, length):
    """Inverse of ``_stft`` for one channel, trimmed to ``length`` samples."""
    return torch.istft(
        spectrum,
        n_fft=p["n_fft"],
        hop_length=p["hop_length"],
        win_length=p["win_length"],
        window=window,
        center=p["center"],
        normalized=p["normalized"],
        onesided=p["onesided"],
        length=length,
        return_complex=False,
    )


# B0/B1: one microphone as recorded.


def near_channel(wave):
    """B0: the near microphone (row 0) as recorded."""
    return wave[0]


def far_channel(wave):
    """B1: the far microphone (row 1) as recorded."""
    return wave[1]


# W1: complex least-squares subtraction.

W1_PARAMETERS = {
    "n_fft": 1024, "win_length": 1024, "hop_length": 512,
    "center": True, "pad_mode": "reflect", "normalized": False, "onesided": True,
    "peak": 0.9, "eps": 1e-12,
}  # fmt: skip


def peak_normalize(array):
    """Scale both channels by one joint factor so the joint peak becomes 0.9.

    Args:
        array: float32 ``[2, N]`` waveform.

    Returns:
        ``(normalized, scale)``; multiply by ``scale`` to restore. ``scale`` is 1
        for (near) silence.
    """
    peak = float(np.max(np.abs(array)))
    scale = peak / W1_PARAMETERS["peak"] if peak > 1e-12 else 1.0
    normalized = np.empty_like(array)
    normalized[0] = array[0] / np.float32(scale)
    normalized[1] = array[1] / np.float32(scale)
    return normalized, scale


def w1_transfer(near, far):
    """H[f] = sum_t C[f,t] conj(F[f,t]) / (sum_t |F[f,t]|^2 + eps).

    The complex least-squares coefficient that best maps the far spectrum to the
    near spectrum, estimated once over the whole recording.

    Args:
        near: Complex near spectrum ``C`` of shape ``[F, T]``.
        far: Complex far spectrum ``F`` of shape ``[F, T]``.

    Returns:
        Complex ``[F]`` coefficients ``H``.
    """
    return (near * far.conj()).sum(-1) / (
        far.abs().square().sum(-1) + W1_PARAMETERS["eps"]
    )


def w1_residual(near, far, transfer):
    """Y[f,t] = C[f,t] - H[f] F[f,t].

    Args:
        near: Complex near spectrum ``C`` ``[F, T]``.
        far: Complex far spectrum ``F`` ``[F, T]``.
        transfer: ``H`` from ``w1_transfer``, shape ``[F]``.

    Returns:
        Complex residual spectrum ``Y`` ``[F, T]``.
    """
    return near - transfer[:, None] * far


def w1(wave):
    """W1: complex least-squares subtraction of the far channel from the near one.

    Steps: ``peak_normalize`` -> STFT -> ``w1_transfer`` (H) -> ``w1_residual``
    (Y) -> ISTFT -> restore the joint scale.

    Args:
        wave: Finite ``[2, N]`` waveform (near, far), N > 512.

    Returns:
        float32 ``[N]`` residual waveform.
    """
    array = _validate_stereo(wave, 512, "W1")
    normalized, scale = peak_normalize(array)
    tensor = torch.from_numpy(np.ascontiguousarray(normalized))
    (near, far), window = _stft(tensor, W1_PARAMETERS)
    residual = w1_residual(near, far, w1_transfer(near, far))
    output = _istft(residual, window, W1_PARAMETERS, array.shape[1])
    restored = output.numpy().astype(np.float32, copy=False) * np.float32(scale)
    if not np.isfinite(restored).all():
        raise ValueError("Non-finite W1 output")
    return restored.astype(np.float32, copy=False)


# SS: magnitude spectral subtraction (Chu/Qian report, Eq. 1).

SS_PARAMETERS = {
    "sample_rate": 16000, "n_fft": 512, "win_length": 512, "hop_length": 256,
    "window": "torch_hann_periodic", "center": True, "pad_mode": "reflect",
    "normalized": False, "onesided": True, "beta": 1.0, "gamma": 0.1,
    "phase": "near", "input_normalization": "none",
}  # fmt: skip


def ss_spectrum(near, far):
    """SS Eq. (1): |Y| = |C| - beta|F| if |C| > beta|F|, else gamma|C|; phase of C.

    Not power subtraction or max(diff, gamma*near). Strict > is important:
    equal magnitudes use gamma*near. No far phase alignment.

    Args:
        near: Complex near spectrum ``C``.
        far: Complex far spectrum ``F`` of the same shape.

    Returns:
        Complex spectrum with the subtracted magnitude and the near phase.
    """
    if near.shape != far.shape or not near.is_complex() or not far.is_complex():
        raise ValueError("Matching complex near/far spectra required")
    if not torch.isfinite(near).all() or not torch.isfinite(far).all():
        raise ValueError("Finite spectra required")
    a, b = near.abs(), SS_PARAMETERS["beta"] * far.abs()
    magnitude = torch.where(a > b, a - b, SS_PARAMETERS["gamma"] * a)
    return torch.polar(magnitude, near.angle())


def ss(wave):
    """SS: magnitude spectral subtraction with the near phase.

    The article/report specify Hann512/hop256, beta1/gamma0.1 and near phase.
    They do not specify periodic/center/padding. This local condition fixes
    Torch periodic Hann, center=True/reflect, raw physical channel scale.
    This is not a reproduction of the full Qian EAT/KNN system.

    Args:
        wave: Finite ``[2, N]`` waveform (near, far), N > 256.

    Returns:
        float32 ``[N]`` waveform.
    """
    array = _validate_stereo(wave, 256, "SS")
    tensor = torch.from_numpy(np.ascontiguousarray(array))
    (near, far), window = _stft(tensor, SS_PARAMETERS)
    output = _istft(ss_spectrum(near, far), window, SS_PARAMETERS, array.shape[1])
    result = output.numpy().astype(np.float32, copy=False)
    if not np.isfinite(result).all():
        raise ValueError("Non-finite SS output")
    return result


CONDITION_AUDIO = {"b0": near_channel, "b1": far_channel, "w1": w1, "ss": ss}


def condition_audio(wave, condition):
    """Return the 1-channel input the detector receives under ``condition``.

    Args:
        wave: ``[2, N]`` waveform (near, far).
        condition: One of ``CONDITION_AUDIO`` (``b0``, ``b1``, ``w1``, ``ss``).

    Returns:
        ``[N]`` waveform.
    """
    if condition not in CONDITION_AUDIO:
        raise ValueError(condition)
    return CONDITION_AUDIO[condition](wave)
