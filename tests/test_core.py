from pathlib import Path

import numpy as np
import pytest
from synthetic import synthetic

from asd_min.beam import BEAMVarianceMin
from asd_min.evaluation import evaluate, validate
from asd_min.runner import plan, run
from asd_min.waveform import condition_audio, w1


def test_w1_silence_far_zero_and_scale():
    x = np.random.default_rng(7).normal(0, 0.2, (2, 16000)).astype(np.float32)
    np.testing.assert_array_equal(
        w1(np.zeros_like(x)), np.zeros(x.shape[1], np.float32)
    )
    nofar = np.stack([x[0], np.zeros_like(x[0])])
    np.testing.assert_allclose(w1(nofar), x[0], atol=3e-7, rtol=2e-6)
    np.testing.assert_allclose(w1(x * 3), w1(x) * 3, atol=2e-6, rtol=2e-4)
    assert len(w1(x)) == x.shape[1]
    np.testing.assert_array_equal(condition_audio(x, "b0"), x[0])
    np.testing.assert_array_equal(condition_audio(x, "b1"), x[1])


def test_backend_excludes_self_and_rebuilds():
    rng = np.random.default_rng(11)
    x = rng.normal(size=(8, 2, 5)).astype("float32")
    ids = np.array([str(i) for i in range(8)])
    b = BEAMVarianceMin()
    b.fit({"embed_freq": x, "path": ids})
    score = b.anomaly_score({"embed_freq": x, "path": ids})["raw"]
    assert (score > 0).all()
    b.fit({"embed_freq": x[:5], "path": ids[:5]})
    assert len(b.memory[0].embeddings) == 5


def test_stored_csv_inventory():
    root = Path(__file__).resolve().parents[1]
    for condition in ("b0", "b1", "w1", "ss"):
        assert len(validate(root / "results" / condition)) == 10


def test_missing_assets_and_terms(tmp_path):
    with pytest.raises(ValueError):
        plan(tmp_path)
    with pytest.raises(ValueError, match="Review evaluator"):
        evaluate(tmp_path, tmp_path, tmp_path)
    with pytest.raises(ValueError):
        run(tmp_path, tmp_path, tmp_path, limit=1)


def test_ss_strict_floor_and_near_phase():
    import torch

    from asd_min.waveform import ss_spectrum

    phases = torch.tensor([0.2, -0.6, 0.4, 1.2, 0.0])
    a = torch.tensor([10.0, 4.0, 4.0, 4.0, 0.0])
    b = torch.tensor([4.0, 10.0, 4.0, 3.8, 0.0])
    near = torch.polar(a, phases)
    far = torch.polar(b, torch.zeros(5))
    out = ss_spectrum(near, far)
    # 4-3.8=0.2: Eq.(1) does NOT floor a positive result to gamma*4=0.4.
    torch.testing.assert_close(
        out.abs(), torch.tensor([6.0, 0.4, 0.4, 0.2, 0.0]), atol=3e-7, rtol=2e-6
    )
    torch.testing.assert_close(out[:4].angle(), phases[:4])
    changed_far = far * torch.exp(torch.tensor(1.7j))
    torch.testing.assert_close(ss_spectrum(near, changed_far), out)


def test_ss_waveform_contract():
    from asd_min.waveform import ss

    x = synthetic()
    identical = np.stack([x[0], x[0]])
    np.testing.assert_allclose(ss(identical), 0.1 * x[0], atol=3e-7, rtol=3e-6)
    nofar = np.stack([x[0], np.zeros_like(x[0])])
    np.testing.assert_allclose(ss(nofar), x[0], atol=5e-7, rtol=3e-6)
    np.testing.assert_array_equal(
        ss(np.zeros_like(x)), np.zeros(x.shape[1], np.float32)
    )
    assert len(ss(x)) == x.shape[1]
    np.testing.assert_allclose(ss(x * 2), ss(x) * 2, atol=5e-7, rtol=3e-6)
    assert np.isfinite(ss(x)).all()


def test_render_rejects_wrong_recording_before_read(tmp_path):
    import importlib.util
    import json

    script = Path(__file__).resolve().parents[1] / "scripts/render_recording.py"
    spec = importlib.util.spec_from_file_location("render_recording", script)
    render = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(render)
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs/02-recording-example.json").write_text(
        json.dumps({"path": "same-name.wav", "sha256": "0" * 64})
    )
    (tmp_path / "eval_data/raw").mkdir(parents=True)
    (tmp_path / "eval_data/raw/same-name.wav").write_bytes(b"wrong recording")
    with pytest.raises(ValueError, match="SHA-256"):
        render.example_path(tmp_path, tmp_path / "eval_data/raw")


def test_protocol_matches_conditions_and_exported_config():
    import json

    from asd_min.protocol import CONDITIONS
    from asd_min.waveform import CONDITION_AUDIO, SS_PARAMETERS

    assert tuple(CONDITION_AUDIO) == CONDITIONS
    config = Path(__file__).resolve().parents[1] / "configs/02_ss.json"
    assert json.loads(config.read_text())["parameters"] == SS_PARAMETERS


def _dev_test_names():
    names = []
    for i in range(200):
        domain = ("source", "target")[i % 2]
        label = ("normal", "anomaly")[(i // 2) % 2]
        names.append(f"section_00_{domain}_test_{label}_{i:04d}_noAttribute.wav")
    return names


def test_plan_development_inventory(tmp_path):
    train = tmp_path / "fan/train"
    test = tmp_path / "fan/test"
    train.mkdir(parents=True)
    test.mkdir(parents=True)
    for i in range(1000):
        domain = "source" if i < 990 else "target"
        (train / f"section_00_{domain}_train_normal_{i:04d}_x.wav").touch()
    for name in _dev_test_names():
        (test / name).touch()
    selected = plan(tmp_path, ("fan",), dataset="dev")
    assert len(selected["fan"]["test"]) == 200
    with pytest.raises(ValueError, match="not in the eval dataset"):
        plan(tmp_path, ("fan",))
    (test / _dev_test_names()[0]).rename(test / "section_00_0000.wav")
    with pytest.raises(ValueError, match="labeled Development"):
        plan(tmp_path, ("fan",), dataset="dev")


def test_development_scores(tmp_path):
    from asd_min.development import machine_metrics, score_development
    from asd_min.protocol import DEVELOPMENT_MACHINES

    names = _dev_test_names()
    anomalous = np.array(["_anomaly_" in n for n in names], float)
    perfect = machine_metrics(names, anomalous)
    assert perfect == {
        "auc_source": 1.0,
        "auc_target": 1.0,
        "pauc": 1.0,
        "official": 1.0,
    }
    rng = np.random.default_rng(3)
    for machine in DEVELOPMENT_MACHINES:
        scores = anomalous + rng.normal(0, 1, 200)
        with (tmp_path / f"anomaly_score_{machine}_section_00_test.csv").open("w") as f:
            f.writelines(f"{n},{s}\n" for n, s in zip(names, scores))
    rows, summary = score_development(tmp_path)
    assert [r["machine"] for r in rows] == list(DEVELOPMENT_MACHINES)
    assert 0.5 < summary["dev7"] < 1 and 0.5 < summary["dev5"] < 1
    _, partial = score_development(tmp_path, ("fan",))
    assert partial == {"dev7": None, "dev5": None}
