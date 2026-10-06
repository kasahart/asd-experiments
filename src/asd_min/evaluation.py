# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
"""Format predictions and invoke a reader-provided, unmodified evaluator."""
from pathlib import Path
import csv
import json
import math
import os
import subprocess
import sys
from .runner import MACHINES
REVISION = 'f6a94a2b5e614a9626c9d1ccff6df0705e6aaa75'
TRUTH_DIRS = ('ground_truth_data', 'ground_truth_domain', 'ground_truth_attributes')


def decisions_from_normal(train, test):
    import numpy as np
    train, test = np.asarray(train), np.asarray(test)
    if train.ndim != 1 or test.ndim != 1 or not len(train) or not np.isfinite(train).all() or not np.isfinite(test).all():
        raise ValueError('Expected finite normal-reference and test scores')
    threshold = float(np.quantile(train, .9, method='linear'))
    return threshold, (test > threshold).astype(int)


def write_submission(system, machine, names, scores, decisions):
    system = Path(system); system.mkdir(parents=True, exist_ok=True)
    names, scores, decisions = list(names), list(scores), list(decisions)
    if len(names) != len(scores) or len(names) != len(decisions):
        raise ValueError('Prediction lengths differ')
    for prefix, values in [('anomaly_score', scores), ('decision_result', decisions)]:
        with (system / f'{prefix}_{machine}_section_00_test.csv').open('w', newline='') as stream:
            csv.writer(stream).writerows(zip(names, values))


def validate(system, machines=MACHINES, expected_names=None):
    system = Path(system); expected = set()
    for machine in machines:
        names = (expected_names[machine] if expected_names is not None
                 else {f'section_00_{i:04d}.wav' for i in range(200)})
        if len(names) != 200:
            raise ValueError('Official evaluation requires 200 unique test clips per machine')
        for prefix in ('anomaly_score', 'decision_result'):
            name = f'{prefix}_{machine}_section_00_test.csv'; expected.add(name)
            with (system / name).open() as stream: rows = list(csv.reader(stream))
            if len(rows) != 200 or any(len(row) != 2 for row in rows): raise ValueError(name)
            if len({row[0] for row in rows}) != 200 or {row[0] for row in rows} != set(names):
                raise ValueError('Filename mismatch')
            for _, value in rows:
                number = float(value)
                if not math.isfinite(number) or (prefix == 'decision_result' and number not in (0, 1)):
                    raise ValueError('Invalid score')
    actual = {p.name for p in system.glob('anomaly_score_*.csv')} | {p.name for p in system.glob('decision_result_*.csv')}
    if actual != expected: raise ValueError('Unexpected submission files')
    return expected


def evaluate_many(systems, evaluator, output, terms_reviewed=False, machines=MACHINES, truth=None):
    if not terms_reviewed:
        raise ValueError('Review evaluator conditions yourself first; see docs/rights.md')
    evaluator, output = Path(evaluator).resolve(), Path(output).resolve()
    truth = Path(truth).resolve() if truth is not None else evaluator
    script = evaluator / 'dcase2026_task2_evaluator.py'
    if not script.is_file(): raise ValueError('Provide the installed official evaluator directory')
    revision = None
    if (evaluator / '.git').exists():
        revision = subprocess.check_output(['git', '-C', str(evaluator), 'rev-parse', 'HEAD'], text=True).strip()
        for diff in (['diff', '--quiet'], ['diff', '--cached', '--quiet']):
            if subprocess.run(['git', '-C', str(evaluator), *diff], check=False).returncode:
                raise ValueError('Evaluator must be unmodified')
    if output.exists(): raise ValueError('Refusing to overwrite')
    names, files = {}, []
    for machine in machines:
        filename = f'ground_truth_{machine}_section_00_test.csv'
        for directory in TRUTH_DIRS:
            source = truth / directory / filename
            if not source.is_file(): raise ValueError(f'Missing official-format truth: {source}')
            files.append((directory, source))
        with (truth / 'ground_truth_data' / filename).open() as stream: rows = list(csv.reader(stream))
        if len(rows) != 200 or any(len(row) != 2 for row in rows) or len({row[0] for row in rows}) != 200:
            raise ValueError('Expected 200 unique truth filenames')
        names[machine] = {row[0] for row in rows}
    selected = {}
    for name, system in systems.items():
        if not name or Path(name).name != name or name in {'.', '..'}: raise ValueError('Invalid system name')
        system = Path(system).resolve()
        selected[name] = {f'{prefix}_{machine}_section_00_test.csv': system / f'{prefix}_{machine}_section_00_test.csv'
                          for machine in machines for prefix in ('anomaly_score', 'decision_result')}
        if any(not source.is_file() for source in selected[name].values()): raise ValueError('Missing predictions')
    output.mkdir(parents=True)
    receipt = {'evaluator_revision': revision, 'status': 'running', 'machines': list(machines)}
    try:
        for directory, source in files:
            dest = output / directory / source.name; dest.parent.mkdir(exist_ok=True)
            dest.symlink_to(source)
        for name, sources in selected.items():
            stage = output / 'teams' / 'reader' / name; stage.mkdir(parents=True)
            for filename, source in sources.items(): (stage / filename).symlink_to(source)
            validate(stage, machines, names)
        command = [sys.executable, str(script), '--teams_root_dir', str(output / 'teams'), '--dir_depth', '2',
                   '--result_dir', str(output / 'results'), '--out_all', 'False',
                   '--additional_result_dir', str(output / 'additional')]
        env = dict(os.environ); env.setdefault('MPLCONFIGDIR', str(output / '.mpl'))
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        with (output / 'evaluator.log').open('w') as log:
            subprocess.run(command, cwd=output, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        results = {name: output / 'results' / f'{name}_result.csv' for name in systems}
        if any(not path.is_file() for path in results.values()): raise ValueError('Official evaluator produced incomplete results')
        receipt['status'] = 'succeeded'
        return results
    except Exception:
        receipt['status'] = 'failed'; raise
    finally:
        (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')


def evaluate(system, evaluator, output, terms_reviewed=False):
    system = Path(system).resolve()
    return evaluate_many({system.name: system}, evaluator, output, terms_reviewed)[system.name]


def read_official_result(path, machines):
    with Path(path).open() as stream: rows = list(csv.reader(stream))
    metrics, machine, header, total = {}, None, None, None
    for row in rows:
        if len(row) == 1 and row[0] in machines:
            machine, header = row[0], None
        elif row and row[0] == 'section' and 'AUC (source)' in row:
            header = row
        elif machine is not None and header is not None and row and row[0] == '00':
            values = dict(zip(header, row))
            metrics[machine] = {key: float(values[column]) * 100 for key, column in
                               [('source_mix_auc', 'AUC (source)'), ('target_mix_auc', 'AUC (target)'), ('mix_pauc', 'pAUC')]}
        elif row and row[0] == 'official score':
            total = float(row[2]) * 100
    if set(metrics) != set(machines) or total is None:
        raise ValueError('Missing official section or aggregate metrics')
    if any(not math.isfinite(value) or not 0 <= value <= 100
           for value in [total, *(v for item in metrics.values() for v in item.values())]):
        raise ValueError('Invalid official metrics')
    return metrics, total
