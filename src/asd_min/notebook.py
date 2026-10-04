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
    # Fit/process the entire recording BEFORE selecting the display/listening interval.
    return {c: wd.from_numpy(condition_audio(wave, c)[selection], sampling_rate=16000,
                             ch_labels=[c.upper()], ch_units='amplitude')
            for c in ('b0', 'b1', 'w1', 'ss')}


def recording_frames(data_root, example):
    path = Path(data_root) / example['path']
    if hashlib.sha256(path.read_bytes()).hexdigest() != example['sha256']:
        raise ValueError('Recording checksum differs from the documented example')
    return frames(path=path, excerpt_s=example['excerpt_s'])


def show(frame, audio=False):
    # Manual controls only; preserve the recording level, without individual normalization.
    if audio:
        return frame.describe(normalize=False, is_close=True, fmax=8000)
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.5), layout='constrained')
    frame.plot(ax=axes[0], title=frame.labels[0] + ' waveform',
               xlim=(.45, .47), ylim=(-.5, .5), color='#2458a6')
    frame.stft(n_fft=1024, hop_length=512).plot(
        ax=axes[1], title='Wandas display STFT', fmax=8000, vmin=-100, vmax=0)
    fig.supxlabel('Excerpt: 2–3 s; waveform zoom: 2.45–2.47 s. Same scales for all conditions.')
    fig.suptitle('ToothBrush / section_00_source_train_normal_0000_noAttribute.wav', fontsize=10)
    fig.text(.5, -.04, 'Nishida et al. · doi:10.5281/zenodo.20151556 · CC BY-NC-SA 4.0',
             ha='center', fontsize=8)
    return fig
