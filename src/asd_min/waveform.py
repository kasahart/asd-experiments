# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart (companion additions)
# Portions adapted from research code Copyright (c) 2025 Takuya Fujimura.
"""Selected canonical W1 operations, adapted from the MIT research snapshot.
See licenses/research-MIT.txt and docs/import-manifest.json. No Wandas DSP here.
"""
import numpy as np
import torch
import soundfile as sf


def load_audio(path):
    frames, rate = sf.read(path, dtype='float32', always_2d=True)
    if rate != 16000 or frames.shape[1] != 2 or len(frames) <= 512:
        raise ValueError('Expected 16 kHz stereo [near, far], length >512')
    if not np.isfinite(frames).all():
        raise ValueError('Non-finite audio')
    return np.ascontiguousarray(frames.T)


def w1(wave):
    array = np.asarray(wave, dtype=np.float32)
    if array.ndim != 2 or array.shape[0] != 2 or array.shape[1] <= 512 or not np.isfinite(array).all():
        raise ValueError('W1 requires finite stereo audio longer than 512 samples')
    peak = float(np.max(np.abs(array)))
    scale = peak / 0.9 if peak > 1e-12 else 1.0
    normalized = np.empty_like(array)
    normalized[0] = array[0] / np.float32(scale)
    normalized[1] = array[1] / np.float32(scale)
    tensor = torch.from_numpy(np.ascontiguousarray(normalized))
    window = torch.hann_window(1024, periodic=True, dtype=tensor.dtype)
    spectra = torch.stft(tensor, n_fft=1024, hop_length=512, win_length=1024,
                         window=window, center=True, pad_mode='reflect',
                         normalized=False, onesided=True, return_complex=True)
    near, far = spectra
    h = (near * far.conj()).sum(-1) / (far.abs().square().sum(-1) + 1e-12)
    residual = near - h[:, None] * far
    output = torch.istft(residual, n_fft=1024, hop_length=512, win_length=1024,
                         window=window, center=True, normalized=False, onesided=True,
                         length=array.shape[1], return_complex=False)
    restored = output.numpy().astype(np.float32, copy=False) * np.float32(scale)
    if not np.isfinite(restored).all():
        raise ValueError('Non-finite W1 output')
    return restored.astype(np.float32, copy=False)


def condition_audio(wave, condition):
    if condition == 'b0': return wave[0]
    if condition == 'b1': return wave[1]
    if condition == 'w1': return w1(wave)
    if condition == 'ss': return ss(wave)
    raise ValueError(condition)


def synthetic_components():
    """Original common tone and its two microphone components (before mixing)."""
    t = np.arange(16000, dtype=np.float64) / 16000
    return {
        'common': np.sin(2*np.pi*1000*t),
        'near_common': .8*np.sin(2*np.pi*1000*t+.65),
        'near_only': .12*np.sin(2*np.pi*1900*t),
    }


def synthetic():
    parts = synthetic_components()
    return np.stack([parts['near_common']+parts['near_only'],
                     .4*parts['common']]).astype(np.float32)


SS_PARAMETERS = {
    'sample_rate': 16000, 'n_fft': 512, 'win_length': 512, 'hop_length': 256,
    'window': 'torch_hann_periodic', 'center': True, 'pad_mode': 'reflect',
    'normalized': False, 'onesided': True, 'beta': 1.0, 'gamma': 0.1,
    'phase': 'near', 'input_normalization': 'none',
}


def ss_spectrum(near, far):
    """Article Eq.(1), not power subtraction or max(diff, gamma*near).

    Strict > is important: equal magnitudes use gamma*near.
    Reconstruction retains the original near phase; no far phase alignment.
    """
    if near.shape != far.shape or not near.is_complex() or not far.is_complex():
        raise ValueError('Matching complex near/far spectra required')
    if not torch.isfinite(near).all() or not torch.isfinite(far).all():
        raise ValueError('Finite spectra required')
    a, b = near.abs(), SS_PARAMETERS['beta'] * far.abs()
    magnitude = torch.where(a > b, a-b, SS_PARAMETERS['gamma']*a)
    return torch.polar(magnitude, near.angle())


def ss(wave):
    """Selected Qian equation with explicit local STFT boundary choices.

    The article/report specify Hann512/hop256, beta1/gamma0.1 and near phase.
    They do not specify periodic/center/padding. This local condition fixes
    Torch periodic Hann, center=True/reflect, raw physical channel scale.
    This is not a reproduction of the full Qian EAT/KNN system.
    """
    array = np.asarray(wave, dtype=np.float32)
    if array.ndim != 2 or array.shape[0] != 2 or array.shape[1] <= 256 or not np.isfinite(array).all():
        raise ValueError('SS requires finite stereo audio longer than 256 samples')
    tensor = torch.from_numpy(np.ascontiguousarray(array))
    p = SS_PARAMETERS
    window = torch.hann_window(p['win_length'],periodic=True,dtype=tensor.dtype)
    spectra = torch.stft(tensor,n_fft=p['n_fft'],hop_length=p['hop_length'],
                        win_length=p['win_length'],window=window,center=p['center'],
                        pad_mode=p['pad_mode'],normalized=p['normalized'],
                        onesided=p['onesided'],return_complex=True)
    residual = ss_spectrum(spectra[0],spectra[1])
    output = torch.istft(residual,n_fft=p['n_fft'],hop_length=p['hop_length'],
                         win_length=p['win_length'],window=window,center=p['center'],
                         normalized=p['normalized'],onesided=p['onesided'],
                         length=array.shape[1],return_complex=False)
    result = output.numpy().astype(np.float32,copy=False)
    if not np.isfinite(result).all(): raise ValueError('Non-finite SS output')
    return result
