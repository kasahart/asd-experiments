# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
"""Public Wandas 0.8.0 presentation. Computation comes from waveform/runner."""
import numpy as np
import wandas as wd
from .waveform import condition_audio,synthetic,load_audio


def frames(wave=None,path=None):
    if wd.__version__!='0.8.0': raise ValueError('This notebook is validated with Wandas 0.8.0')
    if path is not None: wave=load_audio(path)
    if wave is None: wave=synthetic()
    return {c:wd.from_numpy(condition_audio(wave,c),sampling_rate=16000,
                            ch_labels=[c.upper()],ch_units='amplitude') for c in ('b0','b1','w1','ss')}


def show(frame,audio=False):
    # describe creates a manual HTML audio control, no autoplay. normalize=False
    # preserves the comparison level; the W1 computation restores original scale.
    if audio: return frame.describe(normalize=False,is_close=True,fmax=4000)
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(1,2,figsize=(11,3.5),layout='constrained')
    frame.plot(ax=axs[0],title='Waveform',xlim=(0,.04),ylim=(-1,1))
    frame.stft(n_fft=1024,hop_length=512).plot(ax=axs[1],title='Wandas display STFT',fmax=4000,vmin=-100,vmax=-20)
    return fig
