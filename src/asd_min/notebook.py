# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
"""Wandas presentation; all waveform processing uses the experiment implementation."""
import hashlib
from pathlib import Path
import wandas as wd
from .waveform import condition_audio, load_audio, synthetic


def frames(wave=None, path=None, excerpt_s=None):
    if wd.__version__ != '0.8.0':
        raise ValueError('This notebook is validated with Wandas 0.8.0')
    if path is not None:
        wave = load_audio(path)
    if wave is None:
        wave = synthetic()
    selection = slice(None) if excerpt_s is None else slice(*(int(t*16000) for t in excerpt_s))
    # Fit/process the entire recording BEFORE selecting the display interval.
    return {c: wd.from_numpy(condition_audio(wave, c)[selection], sampling_rate=16000,
                             ch_labels=[c.upper()], ch_units='amplitude')
            for c in ('b0', 'b1', 'w1', 'ss')}


def recording_frames(data_root, example):
    path = Path(data_root) / example['path']
    if hashlib.sha256(path.read_bytes()).hexdigest() != example['sha256']:
        raise ValueError('Recording checksum differs from the documented example')
    return frames(path=path)


def show(frame, audio=False):
    # is_close=False returns figures without creating audio output.
    figures = frame.describe(
        normalize=False, is_close=audio, xlim=(0, 6),
        fmax=8000, ylim=(0, 8000), vmin=-100, vmax=0,
        waveform={'ylim': (-.5, .5)}, spectral={'xlim': (-100, 0)})
    if audio:
        return None
    fig = figures[0]
    fig.text(.5, -.02, 'Nishida et al. · doi:10.5281/zenodo.20151556 · CC BY-NC-SA 4.0',
             ha='center', fontsize=8)
    return fig
