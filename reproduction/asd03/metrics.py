# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
"""Convert predictions and read metrics from the installed official evaluator."""
import argparse
import csv
from pathlib import Path
import json
from asd_min.evaluation import evaluate_many, read_official_result
from run import DEV, EVAL, MACHINES, write_json


def development_truth(systems, destination):
    """Development discloses test labels in filenames instead of truth CSVs."""
    for machine in DEV:
        names = None
        for system in systems.values():
            with (system / f'anomaly_score_{machine}_section_00_test.csv').open() as stream:
                current = [row[0] for row in csv.reader(stream)]
            if len(current) != 200 or len(set(current)) != 200:
                raise ValueError('Official evaluation requires 200 unique test clips per machine')
            if names is None: names = sorted(current)
            elif set(current) != set(names): raise ValueError('Development systems have different test filenames')
        rows = {directory: [] for directory in ('ground_truth_data', 'ground_truth_domain', 'ground_truth_attributes')}
        for name in names:
            parts = name.split('_')
            if len(parts) < 6 or parts[:2] != ['section', '00'] or parts[3] != 'test' or parts[2] not in ('source', 'target') or parts[4] not in ('normal', 'anomaly'):
                raise ValueError('Expected disclosed Development test filenames')
            rows['ground_truth_data'].append((name, int(parts[4] == 'anomaly')))
            rows['ground_truth_domain'].append((name, int(parts[2] == 'target')))
            rows['ground_truth_attributes'].append((name, Path(name).stem))
        for directory, data in rows.items():
            path = destination / directory / f'ground_truth_{machine}_section_00_test.csv'
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('w', newline='') as stream: csv.writer(stream).writerows(data)
    return destination


def evaluate(root, evaluator, output, terms_reviewed=False):
    if not terms_reviewed: raise ValueError('Review evaluator conditions yourself first; see docs/rights.md')
    root, evaluator, output = map(lambda path: Path(path).resolve(), (root, evaluator, output))
    if output.exists(): raise FileExistsError('Use a new metric output directory')
    systems = {f'{detector}__{condition}': root / 'submissions' / detector / condition
               for detector in ('raw-BEATs', 'dis-BEATs') for condition in ('raw', 'w1_global')}
    if any(not system.is_dir() for system in systems.values()):
        raise ValueError('Run the score stage to generate official-format predictions')
    output.mkdir(parents=True)
    truth = development_truth(systems, output / 'development_truth')
    official, totals = {}, []
    for split, machines, labels in [('development', DEV, truth), ('evaluation', EVAL, evaluator)]:
        results = evaluate_many(systems, evaluator, output / 'official' / split, terms_reviewed, machines, labels)
        for name, path in results.items():
            _, score = read_official_result(path, machines)
            detector, condition = name.split('__')
            totals.append({'split': split, 'detector': detector, 'condition': condition, 'official_score': score})
        # Single-machine runs obtain its official aggregate without reimplementing hmean.
        for machine in machines:
            results = evaluate_many(systems, evaluator, output / 'official' / machine, terms_reviewed, (machine,), labels)
            for name, path in results.items():
                values, score = read_official_result(path, (machine,))
                official[name, machine] = {**values[machine], 'official_score': score}
    rows = [{'split': 'development' if machine in DEV else 'evaluation', 'detector': detector,
             'condition': condition, 'machine': machine, **official[f'{detector}__{condition}', machine]}
            for detector in ('raw-BEATs', 'dis-BEATs') for condition in ('raw', 'w1_global') for machine in MACHINES]
    order = {(row['split'], row['detector'], row['condition']): row for row in totals}
    totals = [order[split, detector, condition] for detector in ('raw-BEATs', 'dis-BEATs')
              for condition in ('raw', 'w1_global') for split in ('development', 'evaluation')]
    for name, data in [('machine_metrics.csv', rows), ('summary.csv', totals)]:
        with (output / name).open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(data[0]), lineterminator='\n'); writer.writeheader(); writer.writerows(data)
    write_json(output / 'receipt.json', {'status': 'complete', 'evaluator': str(evaluator),
        'test_clips_per_machine': 200, 'development_metrics': 21, 'evaluation_metrics': 15,
        'metrics_source': 'official evaluator outputs', 'mode': 'full'})
    return totals


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--evaluator', type=Path, required=True, help='Installed official evaluator directory')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--terms-reviewed', action='store_true')
    args = parser.parse_args()
    print(json.dumps(evaluate(args.run, args.evaluator, args.output, args.terms_reviewed), indent=2))
