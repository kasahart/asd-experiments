from pathlib import Path
import numpy as np
import pytest
from asd_min.waveform import w1,synthetic,condition_audio
from asd_min.evaluation import validate,evaluate
from asd_min.runner import plan,run
from asd_min.beam import BEAMVarianceMin


def test_w1_silence_far_zero_and_scale():
    x=np.random.default_rng(7).normal(0,.2,(2,16000)).astype(np.float32)
    np.testing.assert_array_equal(w1(np.zeros_like(x)),np.zeros(x.shape[1],np.float32))
    nofar=np.stack([x[0],np.zeros_like(x[0])])
    np.testing.assert_allclose(w1(nofar),x[0],atol=3e-7,rtol=2e-6)
    np.testing.assert_allclose(w1(x*3),w1(x)*3,atol=2e-6,rtol=2e-4)
    assert len(w1(x))==x.shape[1]
    np.testing.assert_array_equal(condition_audio(x,'b0'),x[0])
    np.testing.assert_array_equal(condition_audio(x,'b1'),x[1])


def test_backend_excludes_self_and_rebuilds():
    rng=np.random.default_rng(11)
    x=rng.normal(size=(8,2,5)).astype('float32')
    ids=np.array([str(i) for i in range(8)])
    b=BEAMVarianceMin();b.fit({'embed_freq':x,'path':ids})
    score=b.anomaly_score({'embed_freq':x,'path':ids})['raw']
    assert (score>0).all()
    b.fit({'embed_freq':x[:5],'path':ids[:5]})
    assert len(b.memory[0].embeddings)==5


def test_stored_csv_inventory():
    root=Path(__file__).resolve().parents[1]
    for condition in ('b0','b1','w1','ss'): assert len(validate(root/'results'/condition))==10


def test_missing_assets_and_terms(tmp_path):
    with pytest.raises(ValueError):plan(tmp_path)
    with pytest.raises(ValueError,match='Review evaluator'):evaluate(tmp_path,tmp_path,tmp_path)
    with pytest.raises(ValueError,match='at least 5'):run(tmp_path,tmp_path,tmp_path,limit=1)


def test_ss_strict_floor_and_near_phase():
    import torch
    from asd_min.waveform import ss_spectrum
    phases=torch.tensor([.2,-.6,.4,1.2,0.])
    a=torch.tensor([10.,4.,4.,4.,0.])
    b=torch.tensor([4.,10.,4.,3.8,0.])
    near=torch.polar(a,phases);far=torch.polar(b,torch.zeros(5))
    out=ss_spectrum(near,far)
    # 4-3.8=0.2: Eq.(1) does NOT floor a positive result to gamma*4=0.4.
    torch.testing.assert_close(out.abs(),torch.tensor([6.,.4,.4,.2,0.]),atol=3e-7,rtol=2e-6)
    torch.testing.assert_close(out[:4].angle(),phases[:4])
    changed_far=far*torch.exp(torch.tensor(1.7j))
    torch.testing.assert_close(ss_spectrum(near,changed_far),out)


def test_ss_waveform_contract():
    from asd_min.waveform import ss
    x=synthetic()
    identical=np.stack([x[0],x[0]])
    np.testing.assert_allclose(ss(identical),.1*x[0],atol=3e-7,rtol=3e-6)
    nofar=np.stack([x[0],np.zeros_like(x[0])])
    np.testing.assert_allclose(ss(nofar),x[0],atol=5e-7,rtol=3e-6)
    np.testing.assert_array_equal(ss(np.zeros_like(x)),np.zeros(x.shape[1],np.float32))
    assert len(ss(x))==x.shape[1]
    np.testing.assert_allclose(ss(x*2),ss(x)*2,atol=5e-7,rtol=3e-6)
    assert np.isfinite(ss(x)).all()


def test_synthetic_crosstalk_and_machine_loss():
    from asd_min.waveform import synthetic_components
    parts = synthetic_components()
    wave = synthetic()
    # Independent tone projection verifies that both sources reach both microphones.
    t = np.arange(wave.shape[1]) / 16000
    basis = np.column_stack([np.sin(2*np.pi*f*t) for f in (1000,1900)] +
                            [np.cos(2*np.pi*f*t) for f in (1000,1900)])
    def amplitudes(signal, selection=slice(None)):
        coef = np.linalg.lstsq(basis[selection], signal[selection], rcond=None)[0]
        return np.hypot(coef[:2], coef[2:])
    np.testing.assert_allclose(amplitudes(wave[0]), [.15,.6], atol=1e-7)
    np.testing.assert_allclose(amplitudes(wave[1]), [.45,.18], atol=1e-7)
    coef = np.linalg.lstsq(basis, wave.T, rcond=None)[0]
    response = coef[:2] + 1j*coef[2:]
    np.testing.assert_allclose(response[1,1]/response[1,0], .3*np.exp(-2j*np.pi*1900*.0008), atol=2e-7)
    np.testing.assert_allclose(response[0,0]/response[0,1], (1/3)*np.exp(-2j*np.pi*1000*.0008), atol=2e-7)
    np.testing.assert_allclose(wave[0], parts['near_noise']+parts['near_machine'], atol=6e-8)
    np.testing.assert_allclose(wave[1], parts['far_noise']+parts['far_machine'], atol=6e-8)
    np.testing.assert_allclose(parts['near_machine'], parts['machine'], atol=1e-12)
    for condition in ('w1','ss'):
        residual = condition_audio(wave, condition)
        assert np.isfinite(residual).all() and residual.shape == wave[0].shape
        # This stationary crosstalk example attenuates desired machine sound as well as noise.
        assert (amplitudes(residual, slice(1600,-1600)) < amplitudes(wave[0])).all()


def test_demo_near_machine_far_noise_and_common_scale():
    import matplotlib.pyplot as plt
    from asd_min.notebook import frames, source_frames, microphone_components, show, demo_levels
    from asd_min.waveform import SYNTHETIC_PARAMETERS
    levels = demo_levels()
    assert levels[0]['machine_rms'] > levels[1]['machine_rms'] > 0
    assert levels[1]['noise_rms'] > levels[0]['noise_rms'] > 0
    assert levels[0]['machine_rms'] > levels[0]['noise_rms']
    assert levels[1]['noise_rms'] > levels[1]['machine_rms']
    assert SYNTHETIC_PARAMETERS['machine']['far_delay_ms'] > SYNTHETIC_PARAMETERS['machine']['near_delay_ms']
    assert SYNTHETIC_PARAMETERS['noise']['near_delay_ms'] > SYNTHETIC_PARAMETERS['noise']['far_delay_ms']
    components = microphone_components()
    for condition, frame in frames().items():
        fig = show(frame, target=source_frames()['machine'], components=components.get(condition))
        assert fig.axes[0].get_ylim() == (-1, 1)
        assert fig.axes[1].collections[0].get_clim() == (-100, 0)
        if condition in components:
            # The displayed machine contribution is the actual signal at THIS mic.
            np.testing.assert_allclose(fig.axes[0].lines[1].get_ydata(), components[condition]['machine'].data)
        plt.close(fig)
