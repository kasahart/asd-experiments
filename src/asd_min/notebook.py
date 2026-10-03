# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
"""Public Wandas 0.8.0 presentation. Computation comes from waveform/runner."""
import numpy as np
import wandas as wd
from .waveform import condition_audio,synthetic,synthetic_components,load_audio,SYNTHETIC_PARAMETERS


def frames(wave=None,path=None):
    if wd.__version__!='0.8.0': raise ValueError('This notebook is validated with Wandas 0.8.0')
    if path is not None: wave=load_audio(path)
    if wave is None: wave=synthetic()
    return {c:wd.from_numpy(condition_audio(wave,c),sampling_rate=16000,
                            ch_labels=[c.upper()],ch_units='amplitude') for c in ('b0','b1','w1','ss')}


NOISE_COLOR = '#b16a14'
MACHINE_COLOR = '#2458a6'
MIXTURE_COLOR = '#475569'


def source_frames():
    parts = synthetic_components()
    return {role: wd.from_numpy(parts[role].astype(np.float32), sampling_rate=16000,
                               ch_labels=[role.capitalize()], ch_units='amplitude')
            for role in ('noise', 'machine')}


def common_frame():
    """The environmental noise shared by both microphones, before mixing."""
    return source_frames()['noise']


def _plot(frame, axes, title, color):
    frame.plot(ax=axes[0], title=title, xlim=(.45, .46), ylim=(-1, 1), color=color)
    frame.stft(n_fft=1024, hop_length=512).plot(
        ax=axes[1], title='Wandas display STFT', fmax=4000, vmin=-100, vmax=0)


def show_sources():
    """Source roles and their levels before the microphone mixtures."""
    import matplotlib.pyplot as plt
    sources = source_frames()
    fig, axes = plt.subplots(2, 2, figsize=(11, 6), layout='constrained')
    _plot(sources['noise'], axes[0], 'Environment noise: reduce (1 kHz)', NOISE_COLOR)
    _plot(sources['machine'], axes[1], 'Machine sound: keep (1.9 kHz)', MACHINE_COLOR)
    for role, row, color in [('noise', 0, NOISE_COLOR), ('machine', 1, MACHINE_COLOR)]:
        axes[row, 1].axhline(SYNTHETIC_PARAMETERS[role]['frequency'], color=color,
                            linestyle='--', linewidth=1)
    return fig


def show(frame, audio=False, target=None):
    # Wandas describe creates manual controls; normalize=False preserves levels.
    if audio: return frame.describe(normalize=False, is_close=True, fmax=4000)
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.5), layout='constrained')
    _plot(frame, axes, 'Waveform', MIXTURE_COLOR)
    if target is not None:
        axes[0].lines[0].set_label(frame.labels[0])
        target.plot(ax=axes[0], color=MACHINE_COLOR, linestyle='--',
                    title='Output and clean machine reference', xlim=(.45, .46), ylim=(-1, 1))
        axes[0].lines[-1].set_label('Machine sound to keep')
        axes[0].legend(loc='upper right', fontsize=9)
        for role, color in [('noise', NOISE_COLOR), ('machine', MACHINE_COLOR)]:
            axes[1].axhline(SYNTHETIC_PARAMETERS[role]['frequency'], color=color,
                            linestyle='--', linewidth=1, label=role.capitalize())
        axes[1].legend(loc='upper right', fontsize=9)
    return fig
