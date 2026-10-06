import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import pytest
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import run
from asd_min.evaluation import validate, read_official_result


def test_standard_training_config_and_user_overrides(tmp_path):
    from types import SimpleNamespace
    args = SimpleNamespace(output=tmp_path, checkpoint=tmp_path / 'base.pt', device='cpu', smoke=False,
                           config_dir=HERE / 'config/train', set=[])
    cfg, _ = run.training_config(args, 'raw')
    assert cfg.trainer.max_epochs == 25 and cfg.datamodule.batch_size == 8 and cfg.seed == 1234
    args.set = ['trainer.max_epochs=3', 'datamodule.batch_size=4', 'seed=5678',
                'frontend.model_cfg.extractor_cfg.lora_cfg.r=8']
    cfg, _ = run.training_config(args, 'raw')
    assert cfg.trainer.max_epochs == 3 and cfg.datamodule.batch_size == 4 and cfg.seed == 5678
    assert cfg.frontend.model_cfg.extractor_cfg.lora_cfg.r == 8
    assert '5678' in str(run.checkpoint_path(cfg))


def test_test_paths_rejected_from_training_labels(tmp_path):
    paths = [tmp_path / 'ToothBrush/test/section_00_source_test_normal_0000_noAttribute.wav']
    with pytest.raises(ValueError, match='normal training'):
        run.validate_labels(tmp_path / 'nonexistent.json', paths)


def test_missing_training_recordings_rejected(tmp_path):
    with pytest.raises(ValueError, match='no WAV inputs'):
        run.select_inputs(tmp_path, tmp_path)


def write_prediction_fixture(root, names, values):
    from asd_min.evaluation import write_submission
    write_submission(root, 'ToyDrone', names, values, [0] * len(names))


def test_smoke_is_not_a_benchmark(tmp_path):
    write_prediction_fixture(tmp_path, [f'section_00_{i:04d}.wav' for i in range(4)], [.1] * 4)
    with pytest.raises(ValueError): validate(tmp_path, ('ToyDrone',))


def test_nonfinite_scores_rejected(tmp_path):
    values = [float(i) for i in range(200)]; values[0] = float('nan')
    write_prediction_fixture(tmp_path, [f'section_00_{i:04d}.wav' for i in range(200)], values)
    with pytest.raises(ValueError, match='Invalid score'): validate(tmp_path, ('ToyDrone',))


def test_official_output_is_read_without_recalculating_its_aggregate(tmp_path):
    path = tmp_path / 'result.csv'
    path.write_text('ToyDrone\nsection,AUC (source),AUC (target),pAUC\n00,0.75,0.5,0.6\nofficial score,,0.61\n')
    values, total = read_official_result(path, ('ToyDrone',))
    assert values['ToyDrone'] == {'source_mix_auc': 75., 'target_mix_auc': 50., 'mix_pauc': 60.}
    assert total == 61.
    path.write_text(path.read_text().replace('0.61', 'nan'))
    with pytest.raises(ValueError, match='Invalid official'): read_official_result(path, ('ToyDrone',))


def test_incomplete_checkpoint_cannot_be_evaluated():
    payload = {'global_step': 37500, 'loops': {'fit_loop': {'epoch_progress': {'total': {'completed': 24}}}}}
    with pytest.raises(ValueError, match='Incomplete checkpoint'):
        run.validate_checkpoint_completion(payload)
    payload['loops']['fit_loop']['epoch_progress']['total']['completed'] = 25
    run.validate_checkpoint_completion(payload)
    payload['training_limits'] = {'max_epochs': 30, 'max_steps': -1}
    with pytest.raises(ValueError, match='Incomplete checkpoint'):
        run.validate_checkpoint_completion(payload)


def test_resume_requires_all_trainable_weights():
    import torch
    from runtime import validate_trainable_state
    model = torch.nn.Linear(2, 1)
    model.bias.requires_grad_(False)
    validate_trainable_state(model, {'weight': model.weight.detach()})
    with pytest.raises(ValueError, match='Missing trained parameters'):
        validate_trainable_state(model, {'bias': model.bias.detach()})


def test_standalone_labels_are_materialized_and_conflicts_rejected(tmp_path):
    from types import SimpleNamespace
    selected = {m: {'train': [tmp_path / m / 'train' / f'section_00_source_train_normal_{i:04d}_attr.wav' for i in range(1000)]} for m in run.MACHINES}
    names = ['dcase2026/raw/' + '/'.join(p.parts[-3:]) for m in run.MACHINES for p in selected[m]['train']]
    labels = tmp_path / 'supplied.json'
    labels.write_text(json.dumps({'num_class': 116, 'path2idx_dict': {p: i % 116 for i, p in enumerate(names)}}))
    args = SimpleNamespace(labels=labels, output=tmp_path / 'out')
    run.materialize_labels(args, selected)
    dest = args.output / 'train_labels.json'
    assert dest.read_bytes() == labels.read_bytes()
    run.materialize_labels(args, selected)
    dest.write_text('{}')
    with pytest.raises(ValueError, match='Existing output labels differ'):
        run.materialize_labels(args, selected)


def test_external_collator_preserves_anonymous_evaluation_metadata():
    import torch
    from runtime import DCASEWaveCollator
    collator = DCASEWaveCollator(label_dict_path={}, sec='all', sr=16000, shuffle=False)
    path = 'formatted/dcase2026/raw/ToyDrone/test/section_00_0001.wav'
    batch = collator([{'path': path, 'wave': torch.ones(80)}])
    assert batch['path'] == [path]
    assert batch['section'] == [0] and batch['is_normal'] == [-1] and batch['is_target'] == [-1]
    assert batch['wave'].shape == (1, 80)


def test_dcase2026_train_config_rejects_other_years():
    from runtime import ASDTrainConfig
    from pydantic import ValidationError
    cfg = dict(seed=1234, dcase='dcase2026', name='asd03', version='raw', result_dir='results', data_dir='data',
               frontend={}, trainer={}, callback={}, datamodule={'train': {'dataloader': {}, 'dataset': {}, 'collator': {}}}, model_ver='all')
    assert ASDTrainConfig(**cfg).dcase == 'dcase2026'
    cfg['dcase'] = 'dcase2025'
    with pytest.raises(ValidationError, match='requires dcase2026'):
        ASDTrainConfig(**cfg)


def test_normal_collation_matches_upstream_including_random_crop():
    import torch
    from runtime import DCASEWaveCollator, UpstreamWaveCollator
    samples = [{'path': f'formatted/dcase2026/raw/ToyCar/train/section_00_source_train_normal_{i:04d}_attr.wav',
                'wave': torch.arange(320, dtype=torch.float32) + i} for i in range(2)]
    cfg = dict(label_dict_path={}, sec=.01, sr=16000, shuffle=True)
    np.random.seed(19)
    original = UpstreamWaveCollator(**cfg)(samples)
    after_original = np.random.get_state()
    np.random.seed(19)
    actual = DCASEWaveCollator(**cfg)(samples)
    after_actual = np.random.get_state()
    assert list(actual) == list(original)
    for key in actual:
        if isinstance(actual[key], torch.Tensor):
            assert torch.equal(actual[key], original[key])
        else:
            assert actual[key] == original[key]
    assert after_original[0] == after_actual[0]
    assert np.array_equal(after_original[1], after_actual[1])
    assert after_original[2:] == after_actual[2:]


def test_mixed_named_and_anonymous_batch_keeps_paths_and_known_labels():
    import torch
    from runtime import DCASEWaveCollator
    paths = ['formatted/dcase2026/raw/ToyDrone/test/section_00_0001.wav',
             'formatted/dcase2026/raw/fan/test/section_00_target_test_anomaly_0002_attr.wav']
    batch = DCASEWaveCollator(label_dict_path={}, sec='all', sr=16000, shuffle=False)(
        [{'path': p, 'wave': torch.ones(80) * i} for i, p in enumerate(paths)])
    assert batch['path'] == paths
    assert batch['is_normal'] == [-1, 0] and batch['is_target'] == [-1, 1]
    assert batch['attr'] == ['', 'attr'] and batch['section'] == [0, 0]


def test_interruption_before_first_checkpoint_preserves_files_and_restarts(tmp_path):
    ckpt = tmp_path / 'checkpoints/last.ckpt'
    ckpt.parent.mkdir()
    (ckpt.parent / 'partial.tmp').write_text('interrupted')
    with pytest.raises(FileExistsError, match='Incomplete training directory'):
        run.training_restart(ckpt, False)
    (tmp_path / 'checkpoints.incomplete-1').mkdir()
    assert run.training_restart(ckpt, True) == []
    assert not ckpt.parent.exists()
    assert (tmp_path / 'checkpoints.incomplete-2/partial.tmp').read_text() == 'interrupted'


def test_existing_checkpoint_requires_explicit_resume(tmp_path):
    ckpt = tmp_path / 'checkpoints/last.ckpt'
    ckpt.parent.mkdir(); ckpt.write_bytes(b'checkpoint')
    with pytest.raises(FileExistsError, match='Existing checkpoint'):
        run.training_restart(ckpt, False)
    assert run.training_restart(ckpt, True) == [f'+resume_ckpt_path={json.dumps(str(ckpt))}']
    assert ckpt.read_bytes() == b'checkpoint'


def test_new_training_needs_no_resume_override(tmp_path):
    assert run.training_restart(tmp_path / 'checkpoints/last.ckpt', False) == []


def test_changed_normal_label_map_is_validated_by_content_not_sha(tmp_path):
    paths = [tmp_path / 'ToyCar/train' / f'section_00_source_train_normal_{i:04d}_attr.wav' for i in range(6)]
    mapping = {'dcase2026/raw/' + '/'.join(p.parts[-3:]): i % 2 for i, p in enumerate(paths)}
    labels = tmp_path / 'labels.json';labels.write_text(json.dumps({'num_class': 2, 'path2idx_dict': mapping}))
    assert run.validate_labels(labels, paths)['num_class'] == 2
    mapping[next(iter(mapping))] = 9
    labels.write_text(json.dumps({'num_class': 2, 'path2idx_dict': mapping}))
    with pytest.raises(ValueError, match='contiguous'):
        run.validate_labels(labels, paths)


def test_completion_uses_saved_training_limits_and_rejects_interruption():
    payload = {'global_step': 3, 'training_limits': {'max_epochs': 1, 'max_steps': 3},
               'training_complete': True, 'loops': {'fit_loop': {'epoch_progress': {'total': {'completed': 0}}}}}
    run.validate_checkpoint_completion(payload)
    payload['global_step'] = 2
    with pytest.raises(ValueError, match='Incomplete'):
        run.validate_checkpoint_completion(payload)
    payload['global_step'] = 3;payload['training_complete'] = False
    with pytest.raises(ValueError, match='Incomplete'):
        run.validate_checkpoint_completion(payload)


def test_edited_yaml_directory_controls_training_defaults(tmp_path):
    from types import SimpleNamespace
    import shutil
    directory = tmp_path / 'train'
    shutil.copytree(HERE / 'config/train', directory)
    experiment = directory / 'experiments/dis_beats_denoiser_comparison.yaml'
    experiment.write_text(experiment.read_text().replace('max_epochs: 25', 'max_epochs: 7'))
    main = directory / 'main.yaml';main.write_text(main.read_text().replace('seed: 1234', 'seed: 1111'))
    args = SimpleNamespace(output=tmp_path / 'out', checkpoint=tmp_path / 'base.pt', device='cpu', smoke=False,
                           config_dir=directory, set=[])
    cfg, _ = run.training_config(args, 'raw')
    assert cfg.trainer.max_epochs == 7 and cfg.seed == 1111


def test_frozen_and_tuned_config_share_backbone_update_and_rdp_gamma(tmp_path):
    from types import SimpleNamespace
    args = SimpleNamespace(output=tmp_path, checkpoint=tmp_path / 'other.pt', device='cpu', smoke=False,
        config_dir=HERE / 'config/train', set=['+frontend.model_cfg.extractor_cfg.model_cfg.update_cfg.dropout=0.0',
                                             'frontend.rdp_gamma=2'])
    model_cfg, gamma = run.frozen_model_config(args, 'w1_global')
    assert model_cfg == {'ckpt_path': str(args.checkpoint), 'update_cfg': {'dropout': 0.0}} and gamma == 2


def test_official_call_stages_selected_truth_and_preserves_user_install(tmp_path, monkeypatch):
    import csv
    import subprocess
    from asd_min.evaluation import evaluate_many
    source = tmp_path / 'official'; source.mkdir()
    (source / 'dcase2026_task2_evaluator.py').write_text('# fixture; no evaluator calculation copied\n')
    names = [f'section_00_{i:04d}.wav' for i in range(200)]
    for directory in ('ground_truth_data', 'ground_truth_domain', 'ground_truth_attributes'):
        path = source / directory / 'ground_truth_ToyDrone_section_00_test.csv';path.parent.mkdir()
        with path.open('w', newline='') as stream: csv.writer(stream).writerows((n, i % 2) for i, n in enumerate(names))
    before = {str(p.relative_to(source)): p.read_bytes() for p in source.rglob('*') if p.is_file()}
    predictions = tmp_path / 'predictions';write_prediction_fixture(predictions, names, [float(i) for i in range(200)])
    output = tmp_path / 'result'
    def fake_run(command, cwd, env, **kwargs):
        assert Path(cwd) == output and Path(command[1]) == source / 'dcase2026_task2_evaluator.py'
        assert (output / 'ground_truth_data/ground_truth_ToyDrone_section_00_test.csv').is_symlink()
        assert not (source / 'teams').exists()
        result = output / 'results/system_result.csv';result.parent.mkdir()
        result.write_text('fixture output')
        return subprocess.CompletedProcess(command, 0)
    monkeypatch.setattr('asd_min.evaluation.subprocess.run', fake_run)
    results = evaluate_many({'system': predictions}, source, output, True, ('ToyDrone',))
    assert results['system'].read_text() == 'fixture output'
    assert before == {str(p.relative_to(source)): p.read_bytes() for p in source.rglob('*') if p.is_file()}


def test_development_truth_converts_only_published_filename_labels(tmp_path):
    import csv
    from asd_min.evaluation import write_submission
    from metrics import development_truth
    systems = {'model': tmp_path / 'predictions'}
    names = [f'section_00_{"source" if i < 100 else "target"}_test_{"normal" if i % 2 == 0 else "anomaly"}_{i:04d}_attr.wav' for i in range(200)]
    for machine in run.DEV: write_submission(systems['model'], machine, names, range(200), [0] * 200)
    root = development_truth(systems, tmp_path / 'truth')
    rows = list(csv.reader((root / 'ground_truth_data/ground_truth_ToyCar_section_00_test.csv').open()))
    assert dict(rows)[names[0]] == '0' and dict(rows)[names[-1]] == '1'
    rows = list(csv.reader((root / 'ground_truth_domain/ground_truth_ToyCar_section_00_test.csv').open()))
    assert dict(rows)[names[0]] == '0' and dict(rows)[names[-1]] == '1'
    rows = list(csv.reader((root / 'ground_truth_attributes/ground_truth_ToyCar_section_00_test.csv').open()))
    assert dict(rows)[names[0]] == Path(names[0]).stem
