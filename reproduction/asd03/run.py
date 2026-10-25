#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
"""B0/W1: normal-only LoRA training and independent RDP4/BEAM inference."""
import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'src'))
DEV = ('bearingEmu', 'fan', 'gearboxEmu', 'sliderEmu', 'ToyCar', 'ToyCarEmu', 'valveEmu')
EVAL = ('BlowerDustCollector', 'Sander', 'SewingMachine', 'ToothBrush', 'ToyDrone')
MACHINES = tuple(sorted(DEV + EVAL))
NO_ATTRIBUTE = {'SewingMachine', 'ToothBrush', 'ToyCar', 'bearingEmu', 'sliderEmu', 'valveEmu'}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def select_inputs(development, evaluation):
    selected = {}
    for machine in MACHINES:
        root = development if machine in DEV else evaluation
        selected[machine] = {}
        for split in ['train', 'test']:
            ps = sorted((root / machine / split).glob('*.wav'))
            if not ps: raise ValueError(f'{machine}/{split}: no WAV inputs')
            if split == 'train':
                if any('_train_normal_' not in p.name for p in ps): raise ValueError('Normal training files only')
            selected[machine][split] = ps
    return selected


def validate_labels(path, training_paths):
    if any(p.parent.name != 'train' or '_train_normal_' not in p.name for p in training_paths):
        raise ValueError('Only normal training paths belong in the label map')
    data = json.loads(path.read_text())
    expected = {'dcase2026/raw/' + '/'.join(p.parts[-3:]) for p in training_paths}
    count = data.get('num_class')
    values = list(data.get('path2idx_dict', {}).values())
    if not expected or set(data.get('path2idx_dict', {})) != expected:
        raise ValueError('Labels must cover exactly the selected normal training paths')
    if type(count) is not int or count <= 0 or any(type(x) is not int for x in values) or set(values) != set(range(count)):
        raise ValueError('Expected contiguous class indices and a positive class count')
    return data


def materialize_labels(args, selected):
    if not args.labels:
        return
    validate_labels(args.labels, [p for m in MACHINES for p in selected[m]['train']])
    dest = args.output / 'train_labels.json'
    if dest.exists() and dest.read_bytes() != args.labels.read_bytes():
        raise ValueError('Existing output labels differ from --labels')
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        dest.write_bytes(args.labels.read_bytes())


def stage_command(module, overrides, log, config_dir=None):
    env = dict(os.environ)
    paths = [str(HERE), str(HERE.parents[1] / 'src')]
    if env.get('PYTHONPATH'):
        paths.append(env['PYTHONPATH'])
    env['PYTHONPATH'] = os.pathsep.join(paths)
    env.setdefault('MPLCONFIGDIR', str(log.parent / '.mpl'))
    log.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, '-m', 'runtime', module, '--config-dir', str(config_dir or HERE / 'config/train'), *overrides]
    print(module, log.name, flush=True)
    with log.open('w') as f:
        subprocess.run(command, cwd=HERE, env=env, stdout=f, stderr=subprocess.STDOUT, check=True)


def data_root(output, condition):
    return output / 'audio' / condition


def prepare(args, selected):
    import soundfile as sf
    from asd_min.waveform import load_audio, condition_audio
    if args.output.exists(): raise FileExistsError('Use a new output directory')
    for root in [args.development, args.evaluation]:
        if args.output.is_relative_to(root): raise ValueError('Output must be outside input trees')
    train = [p for item in selected.values() for p in item['train']]
    if args.labels: validate_labels(args.labels, train)
    args.output.mkdir(parents=True)
    receipt = {'mode': 'smoke_not_article_score' if args.smoke else 'full', 'status': 'preparing',
               'checkpoint': str(args.checkpoint), 'input_clips': 0}
    write_json(args.output / 'inputs.json', receipt)
    try:
        for c in args.conditions:
            for m in MACHINES:
                for split, ps in selected[m].items():
                    if args.smoke:
                        # Sorted train filenames: first 8 source, last 8 target.
                        ps = (ps[:8] + ps[-8:] if len(ps) > 16 else ps) if split == 'train' else ps[:4]
                    for p in ps:
                        wave = condition_audio(load_audio(p), 'b0' if c == 'raw' else 'w1')
                        dest = data_root(args.output, c) / 'formatted/dcase2026/raw' / m / split / p.name
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        sf.write(dest, wave, 16000, subtype='FLOAT')
                        receipt['input_clips'] += 1
        if args.labels:
            (args.output / 'train_labels.json').write_bytes(args.labels.read_bytes())
        receipt['status'] = 'complete'
    finally:
        write_json(args.output / 'inputs.json', receipt)


def generate_attributes(args, selected):
    from asdkit.labelers.basicinfo import BasicInfoLabeler
    if not args.ground_truth_attributes:
        raise ValueError('Provide the official ground_truth_attributes directory')
    names = []
    for m in MACHINES:
        for split in ['train', 'test']:
            paths = selected[m][split]
            if m in EVAL and split == 'test':
                f = args.ground_truth_attributes / f'ground_truth_{m}_section_00_test.csv'
                with f.open() as stream: rows = list(csv.reader(stream))
                mapping = dict(rows)
                if len(mapping) != len(rows) or not {p.name for p in paths}.issubset(mapping):
                    raise ValueError(f'{m}: missing or duplicate official attribute filenames')
                names.extend(f'dcase2026/raw/{m}/test/{mapping[p.name]}.wav' for p in paths)
            else:
                names.extend('dcase2026/raw/' + '/'.join(p.parts[-3:]) for p in paths)
    org = BasicInfoLabeler('machine_section_attr_domain'); org.fit(names)
    dest = args.output / 'attribute_labels.json'
    if dest.exists(): raise FileExistsError(dest)
    write_json(dest, {'num_class': org.num_class, 'path2idx_dict': {p: org.trans(p) for p in sorted(names)}})



def frozen_model_config(args, condition):
    from omegaconf import OmegaConf
    cfg, _ = training_config(args, condition)
    model_cfg = {'ckpt_path': str(args.checkpoint)}
    update = cfg.frontend.model_cfg.extractor_cfg.model_cfg.get('update_cfg')
    if update is not None:
        model_cfg['update_cfg'] = OmegaConf.to_container(update, resolve=True)
    return model_cfg, cfg.frontend.get('rdp_gamma', 4)


def teacher(args):
    """W1 normal training clips with AP; inference uses RDP separately."""
    import numpy as np
    import torch
    from asdkit.datasets import PLDataModule
    from asdkit.utils.common import instantiate_tgt
    from asdkit.utils.asdkit_utils.extract import loader2dict
    from asdkit.utils.config_class import DMConfig
    from runtime import RECORDING_SECONDS
    model_cfg, _ = frozen_model_config(args, 'w1_global')
    model = instantiate_tgt({'tgt_class': 'runtime.BEATsFrequencyPoolingFrozenModel',
                             'pooling': 'mean', 'model_cfg': model_cfg})
    for m in MACHINES:
        dst = args.output / 'teacher' / m / 'train_extract.npz'
        if dst.exists(): raise FileExistsError(dst)
        cfg = DMConfig(**{'dataloader': {'batch_size': 32, 'num_workers': 0, 'pin_memory': False, 'shuffle': False},
            'dataset': {'tgt_class': 'asdkit.datasets.WaveDataset',
                        'path_selector_list': [str(data_root(args.output, 'w1_global') / 'formatted/dcase2026/raw' / m / 'train/*.wav')]},
            'collator': {'tgt_class': 'runtime.DCASEWaveCollator', 'label_dict_path': {}, 'sr': 16000,
                         'sec': RECORDING_SECONDS[m], 'shuffle': False}, 'batch_sampler': None})
        loader = PLDataModule.get_loader(dm_config=cfg)
        z = loader2dict(loader, model, args.device, ['path', 'embed'])
        dst.parent.mkdir(parents=True, exist_ok=True); np.savez(dst, **z)
        print('teacher', m, len(z['path']), flush=True)
    del model
    if torch.cuda.is_available(): torch.cuda.empty_cache()


def generate_labels(args, selected):
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import LabelEncoder
    from asdkit.labelers.basicinfo import BasicInfoLabeler
    # Preserve the attribute dictionary's global integer numbering. This consults
    # filename attributes, never test waveforms, embeddings or anomaly labels.
    org = BasicInfoLabeler('machine_section_attr_domain')
    if not args.attribute_labels:
        raise ValueError('Supply the --attribute-labels dictionary to preserve the article class numbering')
    attribute_map = json.loads(args.attribute_labels.read_text())['path2idx_dict']
    org.fit(list(attribute_map))
    codes, paths = [], []
    root = args.teacher_dir or args.output / 'teacher'
    for mi, m in enumerate(MACHINES):
        if m in NO_ATTRIBUTE:
            with np.load(root / m / 'train_extract.npz', allow_pickle=False) as z:
                emb, ps = z['embed'], z['path'].tolist()
            expected = {p.name for p in selected[m]['train']}
            if len(ps) != len(expected) or {Path(p).name for p in ps} != expected:
                raise ValueError(f'{m}: teacher must cover exactly its selected normal training clips')
            domains = np.array([Path(p).name.split('_')[2] for p in ps])
            if not set(domains).issubset({'source', 'target'}) or not np.isfinite(emb).all(): raise ValueError('Invalid teacher')
            labels = np.full(len(ps), -1); offset = 0
            for d in np.unique(domains):
                use = domains == d; k = max(1, int(use.sum() * (.008 if d == 'source' else 0.0)))
                labels[use] = KMeans(n_clusters=k, random_state=42).fit_predict(emb[use]) + offset
                offset += len(np.unique(labels[use]))
        else:
            ps = [str(p) for p in selected[m]['train']]; labels = [org.trans(p) for p in ps]
        paths.extend(ps); codes.extend(f'{mi}_{int(i)}' for i in labels)
    indices = LabelEncoder().fit_transform(codes)
    data = {'num_class': len(set(indices)), 'path2idx_dict': {
        'dcase2026/raw/' + '/'.join(Path(p).parts[-3:]): int(i) for p, i in zip(paths, indices)}}
    dest = args.output / 'train_labels.json'
    if dest.exists(): raise FileExistsError(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Serialize the training label dictionary.
    dest.write_text(json.dumps(data, indent=4))
    validate_labels(dest, [p for m in MACHINES for p in selected[m]['train']])
    write_json(args.output / 'labels_receipt.json', {'classes': data['num_class'], 'normal_examples': len(indices),
               'test_waveforms_or_anomaly_labels_used': False, 'filename_attribute_numbering': True})


def validate_checkpoint_completion(payload, limits=None):
    limits = payload.get('training_limits', limits)
    if limits is None:
        # Older checkpoints contain loop counters but no trainer limits.
        from hydra import compose, initialize_config_dir
        with initialize_config_dir(config_dir=str(HERE / 'config/train'), version_base=None):
            limits = compose(config_name='main', overrides=['experiments=dis_beats_denoiser_comparison']).trainer
    completed = payload.get('loops', {}).get('fit_loop', {}).get('epoch_progress', {}).get('total', {}).get('completed', 0)
    max_steps, max_epochs = limits.get('max_steps', -1), limits.get('max_epochs')
    done = ((max_steps is not None and max_steps > 0 and payload.get('global_step', 0) >= max_steps)
            or (max_epochs is not None and max_epochs >= 0 and completed >= max_epochs))
    if payload.get('training_complete') is False or not done:
        raise ValueError(f"Incomplete checkpoint: steps={payload.get('global_step')}, completed_epochs={completed}")


def training_restart(ckpt, resume):
    if ckpt.exists():
        if not resume:
            raise FileExistsError('Existing checkpoint; explicitly use --resume-training')
        return [f'+resume_ckpt_path={json.dumps(str(ckpt))}']
    if ckpt.parent.exists():
        if not resume:
            raise FileExistsError('Incomplete training directory; explicitly use --resume-training')
        # Preserve interrupted files; upstream skips any existing checkpoint dir.
        index = 1
        backup = ckpt.parent.with_name(f'checkpoints.incomplete-{index}')
        while backup.exists():
            index += 1
            backup = ckpt.parent.with_name(f'checkpoints.incomplete-{index}')
        ckpt.parent.rename(backup)
    return []


def training_config(args, condition):
    from hydra import compose, initialize_config_dir
    overrides = ['experiments=dis_beats_denoiser_comparison', f'version={condition}',
        f'result_dir={json.dumps(str(args.output / "results"))}',
        f'data_dir={json.dumps(str(data_root(args.output, condition)))}',
        f'label_dict_path.main={json.dumps(str(args.output / "train_labels.json"))}',
        f'frontend.model_cfg.extractor_cfg.model_cfg.ckpt_path={json.dumps(str(args.checkpoint))}']
    if args.device == 'cpu':
        overrides += ['trainer.accelerator=cpu', 'trainer.devices=1']
    else:
        overrides += [f'trainer.devices=[{int(args.device.split(":")[-1])}]']
    if args.smoke:
        overrides += ['trainer.max_epochs=1', '+trainer.max_steps=2', 'datamodule.num_workers=0']
    overrides += getattr(args, 'set', [])
    directory = getattr(args, 'config_dir', HERE / 'config/train')
    with initialize_config_dir(config_dir=str(directory), version_base=None):
        cfg = compose(config_name='main', overrides=overrides)
    return cfg, overrides


def checkpoint_path(cfg, trained_root=None):
    root = Path(trained_root) if trained_root else Path(cfg.result_dir) / cfg.name / cfg.dcase
    return root / str(cfg.version) / str(cfg.seed) / 'model' / str(cfg.model_ver) / 'checkpoints/last.ckpt'


def train(args):
    import torch
    from omegaconf import OmegaConf
    for condition in args.conditions:
        cfg, overrides = training_config(args, condition)
        ckpt = checkpoint_path(cfg)
        overrides += training_restart(ckpt, args.resume_training)
        args.output.mkdir(parents=True, exist_ok=True)
        OmegaConf.save(cfg, args.output / f'{condition}_training_config.yaml', resolve=True)
        stage_command('asdkit.bin.train', overrides, args.output / f'{condition}_train.log',
                      getattr(args, 'config_dir', None))
        payload = torch.load(ckpt, map_location='cpu', weights_only=True)
        validate_checkpoint_completion(payload, cfg.trainer)
        write_json(args.output / f'{condition}_training.json', {'checkpoint': str(ckpt),
                   'steps': payload['global_step'], 'status': 'complete'})


def infer(args):
    import numpy as np
    import torch
    from runtime import FrequencyDisPLModel
    from asdkit.utils.common import instantiate_tgt
    from asdkit.utils.config_class import DMConfig
    from asdkit.datasets import PLDataModule
    from asdkit.utils.asdkit_utils.extract import loader2dict
    from hydra import compose, initialize_config_dir
    from omegaconf import OmegaConf
    for c in args.conditions:
        for detector in ['raw-BEATs', 'dis-BEATs']:
            if detector == 'raw-BEATs':
                model_cfg, gamma = frozen_model_config(args, c)
                model = instantiate_tgt({'tgt_class': 'runtime.BEATsFrequencyPoolingFrozenModel',
                   'pooling': 'rdp', 'gamma': gamma, 'model_cfg': model_cfg})
            else:
                cfg, _ = training_config(args, c)
                model_cfg = OmegaConf.to_container(cfg.frontend.model_cfg, resolve=True)
                model_cfg['extractor_cfg']['model_cfg']['ckpt_path'] = str(args.checkpoint)
                ckpt = checkpoint_path(cfg, args.trained_root)
                saved = torch.load(ckpt, map_location='cpu', weights_only=True)
                validate_checkpoint_completion(saved, cfg.trainer)
                model = FrequencyDisPLModel.load_from_checkpoint(ckpt, map_location='cpu', strict=False,
                    model_cfg=model_cfg, rdp_gamma=cfg.frontend.get('rdp_gamma', 4),
                    label_dict_path={'main': str(args.output / 'train_labels.json')})
                required = {n for n, p in model.named_parameters() if p.requires_grad}
                if not required.issubset(saved['state_dict']): raise ValueError('Missing trained parameters')
                model.eval().to(args.device)
            for m in args.machines:
                base = args.output / 'features' / detector / c / m; base.mkdir(parents=True, exist_ok=True)
                for split in ['train', 'test']:
                    dest = base / f'{split}_extract.npz'
                    if dest.exists(): raise FileExistsError(dest)
                    cfg = DMConfig(**{'dataloader': {'batch_size': 1, 'num_workers': 0, 'pin_memory': False, 'shuffle': False},
                        'dataset': {'tgt_class': 'asdkit.datasets.WaveDataset',
                            'path_selector_list': [str(data_root(args.output, c) / 'formatted/dcase2026/raw' / m / split / '*.wav')]},
                        'collator': {'tgt_class': 'runtime.DCASEWaveCollator', 'label_dict_path': {},
                                     'sr': 16000, 'sec': 'all', 'shuffle': False}, 'batch_sampler': None})
                    z = loader2dict(PLDataModule.get_loader(dm_config=cfg), model, args.device,
                                    ['path', 'section', 'is_normal', 'is_target', 'embed.*'])
                    if len(z['path']) == 0 or not np.isfinite(z['embed_freq']).all(): raise ValueError('Invalid extraction')
                    np.savez(dest, **z)
            del model
            if torch.cuda.is_available(): torch.cuda.empty_cache()


def score(args):
    import numpy as np
    from asd_min.beam import BEAMVarianceMin
    from asd_min.evaluation import decisions_from_normal, write_submission
    for c in args.conditions:
        for detector in ['raw-BEATs', 'dis-BEATs']:
            for m in args.machines:
                base = args.output / 'features' / detector / c / m
                dst = args.output / 'scores' / detector / c / f'{m}.csv'
                if dst.exists(): raise FileExistsError(dst)
                with np.load(base / 'train_extract.npz') as z: train_features = dict(z)
                with np.load(base / 'test_extract.npz') as z: test_features = dict(z)
                backend = BEAMVarianceMin(embed_key='embed_freq', sep_section=False, use_rescaling=True,
                          rescale_k=4, rescale_validation='train_all', rescale_scope='per_band', chunk_size=128)
                backend.fit(train_features)
                scores = backend.anomaly_score(test_features)['main']
                _, decisions = decisions_from_normal(backend.anomaly_score(train_features)['main'], scores)
                write_submission(args.output / 'submissions' / detector / c, m,
                                 [Path(p).name for p in test_features['path']], scores.tolist(), decisions.tolist())
                if not np.isfinite(scores).all(): raise ValueError('Non-finite scores')
                dst.parent.mkdir(parents=True, exist_ok=True)
                with dst.open('w') as f:
                    writer = csv.writer(f); writer.writerow(['filename', 'anomaly_score'])
                    writer.writerows((Path(p).name, float(s)) for p, s in zip(test_features['path'], scores))
                print('scored', detector, c, m, len(scores), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage', choices=['plan', 'prepare', 'attributes', 'teacher', 'labels', 'train', 'infer', 'score', 'all'], default='plan')
    p.add_argument('--development', type=Path, required=True, help='dev_data/raw/{machine}/{train,test}')
    p.add_argument('--evaluation', type=Path, required=True, help='eval_data/raw/{machine}/{train,test}')
    p.add_argument('--checkpoint', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--labels', type=Path, help='Optional normal-training label JSON')
    p.add_argument('--teacher-dir', type=Path, help='Existing normal-only AP teacher embeddings')
    p.add_argument('--ground-truth-attributes', type=Path, help='Official released filename-attribute mapping for exact class numbering')
    p.add_argument('--attribute-labels', type=Path, help='Attribute dictionary generated by ASDKit')
    p.add_argument('--trained-root', type=Path, help='Existing {condition}/1234/model/all/checkpoints/last.ckpt')
    p.add_argument('--config-dir', type=Path, default=HERE / 'config/train', help='Hydra YAML directory')
    p.add_argument('--set', action='append', default=[], metavar='KEY=VALUE', help='Override YAML values; may be repeated')
    p.add_argument('--device', default='cuda:0')
    p.add_argument('--conditions', nargs='+', choices=['raw', 'w1_global'], default=['raw', 'w1_global'])
    p.add_argument('--machines', nargs='+', choices=MACHINES, default=list(MACHINES))
    p.add_argument('--resume-training', action='store_true', help='Explicitly restore an existing training checkpoint, optimizer and loop state')
    p.add_argument('--smoke', action='store_true', help='16 normal + 4 test clips/machine, 2 training steps; NOT article scores')
    args = p.parse_args()
    for k in ['development', 'evaluation', 'checkpoint', 'output', 'labels', 'teacher_dir', 'trained_root', 'attribute_labels', 'ground_truth_attributes', 'config_dir']:
        if getattr(args, k) is not None: setattr(args, k, getattr(args, k).resolve())
    if len(set(args.conditions)) != len(args.conditions) or len(set(args.machines)) != len(args.machines): p.error('Duplicate selection')
    if args.stage in ['all', 'teacher'] and not args.labels and not args.teacher_dir and 'w1_global' not in args.conditions:
        p.error('Teacher label generation requires --conditions w1_global (or provide --labels/--teacher-dir)')
    if args.smoke and args.stage == 'all' and not args.labels:
        p.error('--smoke --stage all requires the previously generated --labels JSON')
    if args.stage == 'plan':
        from omegaconf import OmegaConf
        cfg, _ = training_config(args, args.conditions[0])
        print(OmegaConf.to_yaml(cfg, resolve=True)); return
    import torch
    import torchaudio
    from runtime import load
    torchaudio.load = load
    torch.set_num_threads(1); torch.set_float32_matmul_precision('highest')
    torch.backends.cuda.matmul.allow_tf32 = False; torch.backends.cudnn.allow_tf32 = False
    selected = select_inputs(args.development, args.evaluation)
    if args.stage in ['train', 'infer']:
        materialize_labels(args, selected)
        validate_labels(args.output / 'train_labels.json', [p for m in MACHINES for p in selected[m]['train']])
    if args.stage in ['prepare', 'all']: prepare(args, selected)
    if args.stage == 'attributes' or (args.stage == 'all' and not args.labels and not args.attribute_labels):
        generate_attributes(args, selected)
        args.attribute_labels = args.output / 'attribute_labels.json'
    if args.stage in ['teacher', 'all'] and not args.labels and not args.teacher_dir: teacher(args)
    if args.stage in ['labels', 'all'] and not args.labels: generate_labels(args, selected)
    if args.stage in ['train', 'all']: train(args)
    if args.stage in ['infer', 'all']: infer(args)
    if args.stage in ['score', 'all']:
        from threadpoolctl import threadpool_limits
        # Match verified score CSVs without changing training/label generation.
        with threadpool_limits(limits=1, user_api='blas'):
            score(args)
    write_json(args.output / f'stage_{args.stage}_receipt.json', {'status': 'complete', 'stage': args.stage,
               'mode': 'smoke_not_article_score' if args.smoke else 'full'})


if __name__ == '__main__': main()
