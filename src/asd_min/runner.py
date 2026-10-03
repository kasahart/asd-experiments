# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
"""Small serial inference path. Every condition fits its own normal memory."""
from pathlib import Path
import csv
import hashlib
import json
import time
import numpy as np
import torch
from .waveform import load_audio, condition_audio
from .beam import BEAMVarianceMin
from .pooling import frequency_pooling, sequence_to_time_frequency

MACHINES = ('BlowerDustCollector', 'Sander', 'SewingMachine', 'ToothBrush', 'ToyDrone')
CHECKPOINT_SHA256 = '8d1b234032a9ccff353612dc6c20982346dc2968b205b79d97303eb5e77bfb34'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def plan(root, machines=MACHINES, limit=None):
    root = Path(root)
    selected = {}
    for machine in machines:
        if machine not in MACHINES: raise ValueError('Evaluation machines only')
        selected[machine] = {}
        for split, count in [('train',1000),('test',200)]:
            paths = sorted((root/machine/split).glob('*.wav'))
            if len(paths) != count: raise ValueError(f'{machine}/{split}: expected {count}, got {len(paths)}')
            if split == 'train':
                if any('_train_normal_' not in p.name for p in paths):
                    raise ValueError('Normal training filenames required')
                if sum('_source_train_normal_' in p.name for p in paths) != 990 or sum('_target_train_normal_' in p.name for p in paths) != 10:
                    raise ValueError('Expected 990 source and 10 target normal training clips')
            if split == 'test' and {p.name for p in paths} != {f'section_00_{i:04d}.wav' for i in range(200)}:
                raise ValueError('Keep original anonymous Evaluation filenames')
            selected[machine][split] = paths[:limit] if limit else paths
    return selected


class Encoder:
    def __init__(self, checkpoint, device='cpu'):
        from .beats.BEATs import BEATs, BEATsConfig
        if digest(checkpoint) != CHECKPOINT_SHA256:
            raise ValueError('Expected article BEATs_iter3 checkpoint SHA-256')
        # Official checkpoint contains config dictionaries and tensors only.
        payload = torch.load(checkpoint, map_location='cpu', weights_only=True)
        self.model = BEATs(BEATsConfig(payload['cfg']))
        self.model.load_state_dict(payload['model'], strict=True)
        if self.model.predictor is not None: raise ValueError('Frozen sequence BEATs required')
        self.model.to(device).eval().requires_grad_(False)
        self.device = device

    @torch.inference_mode()
    def extract(self, audio):
        x = torch.from_numpy(np.ascontiguousarray(audio))[None].to(self.device)
        sequence, mask, grid = self.model.extract_features_with_grid(x)
        tf = sequence_to_time_frequency(sequence, grid)
        valid = None if mask is None else ~mask.reshape(1,*grid)
        return frequency_pooling(tf, mode='rdp', gamma=4, valid_time_mask=valid)[0].cpu().numpy()


def run(root, checkpoint, output, conditions=('b0','b1','w1','ss'), device='cpu', machines=MACHINES, limit=None):
    if limit is not None and limit < 5: raise ValueError('Smoke mode requires at least 5 references')
    selected = plan(root, machines, limit)
    output = Path(output)
    if output.exists(): raise ValueError('Refusing to overwrite output')
    torch.set_num_threads(2)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    encoder = Encoder(checkpoint, device)
    if str(device).startswith('cuda'): torch.cuda.reset_peak_memory_stats(device)
    output.mkdir(parents=True)
    receipt = {'status':'running','mode':'smoke_not_article_score' if limit else 'full',
               'conditions':list(conditions),'checkpoint_sha256':CHECKPOINT_SHA256,
               'torch':torch.__version__,'device':device,'input_sha256':{},'timings_seconds':{}}
    start = time.perf_counter()
    try:
        for condition in conditions:
            if condition not in ('b0','b1','w1','ss'): raise ValueError(condition)
            begin = time.perf_counter()
            for machine, splits in selected.items():
                print(f'{condition}/{machine}: extracting normal and test audio', flush=True)
                features = {}
                for split, paths in splits.items():
                    vectors = []
                    for path in paths:
                        receipt['input_sha256'][f'{machine}/{split}/{path.name}'] = digest(path)
                        vectors.append(encoder.extract(condition_audio(load_audio(path),condition)))
                    features[split] = {'embed_freq':np.stack(vectors),'path':np.array([p.name for p in paths])}
                # No sharing of memory across B0/B1/W1, no test labels.
                backend = BEAMVarianceMin(rescale_k=4,rescale_validation='train_all',rescale_scope='per_band')
                backend.fit(features['train'])
                train = backend.anomaly_score(features['train'])['main']
                test = backend.anomaly_score(features['test'])['main']
                threshold = float(np.quantile(train,.9,method='linear'))
                folder = output/condition; folder.mkdir(exist_ok=True)
                for prefix, values in [('anomaly_score',test),('decision_result',(test > threshold).astype(int))]:
                    with (folder/f'{prefix}_{machine}_section_00_test.csv').open('w',newline='') as f:
                        csv.writer(f).writerows(zip(features['test']['path'],values.tolist()))
                with (folder/f'{machine}_train_score.csv').open('w',newline='') as f:
                    writer=csv.writer(f);writer.writerow(['filename','score']);writer.writerows(zip(features['train']['path'],train.tolist()))
                (folder/f'{machine}_threshold.json').write_text(json.dumps({'q90':threshold})+'\n')
            receipt['timings_seconds'][condition] = time.perf_counter()-begin
        receipt['status'] = 'succeeded'
    except Exception:
        receipt['status']='failed'
        raise
    finally:
        receipt['elapsed_seconds']=time.perf_counter()-start
        if str(device).startswith('cuda'):
            receipt['peak_cuda_allocated_bytes']=torch.cuda.max_memory_allocated(device)
        (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt
