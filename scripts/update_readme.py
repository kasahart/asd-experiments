# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
"""Render README methods and score graphs from method metadata and canonical result CSVs."""
import argparse
import csv
import json
from decimal import Decimal
from pathlib import Path

START = '<!-- experiments:start -->'
END = '<!-- experiments:end -->'


def rows(path):
    with path.open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def chart(labels, values, reference_count=0):
    categories = ', '.join(json.dumps(label, ensure_ascii=False) for label in labels)
    lines = ['```mermaid', '---', 'config:', '    xyChart:',
             '        width: 480', f'        height: {80 + 50 * len(labels)}',
             '        showDataLabel: true',
             '    themeVariables:', '        xyChart:',
             '            plotColorPalette: "#2458a6"']
    if reference_count:
        first_reference = len(labels) - reference_count + 1
        lines += [f'    themeCSS: ".bar-plot-0 rect:nth-child(n+{first_reference}) {{ fill: #9099a5; }}"']
    lines += ['---', 'xychart-beta horizontal',
              f'    x-axis [{categories}]',
              '    y-axis "Official score" 0 --> 100',
              '    bar [' + ', '.join(f'{value:.3f}' for value in values) + ']', '```']
    return '\n'.join(lines)


def references_for(root, entries):
    paths = {m.get('references_path', '') for m in entries}
    if len(paths) != 1:
        raise ValueError('Use one challenge reference source per comparison')
    path = paths.pop()
    references = json.loads((root / path).read_text()) if path else {}
    if references and references['comparison'] != entries[0]['comparison']:
        raise ValueError('Challenge references belong to another comparison')
    return references


def render(root):

    methods = rows(root / 'configs/readme-methods.csv')
    groups = {}
    for method in methods:
        groups.setdefault(method['comparison'], []).append(method)
    lines = ['## 手法']
    for group, entries in groups.items():
        models = {(m['feature_model'], m['model_training']) for m in entries}
        if len(models) != 1:
            raise ValueError(f'{group}: use separate comparison groups for different feature models or model training')
        notebooks = {m['notebook_path'] for m in entries}
        common_notebook = len(notebooks) == 1
        lines += ['', f'### {group}', '']
        if common_notebook:
            lines += [f'[Notebook]({next(iter(notebooks))})', '']
        lines += ['| 手法 | 特徴 | 特徴抽出モデル | モデルの追加学習 | 参考文献 |' + ('' if common_notebook else ' Notebook |'),
                  '|---|---|---|---|---|' + ('' if common_notebook else '---|')]
        for method in entries:
            feature = method['description'].replace('|', r'\|')
            reference = '—'
            if method.get('reference_url'):
                reference = f"[{method['reference_name']}]({method['reference_url']})"
                if method.get('reference_note'):
                    reference += f"（{method['reference_note']}）"
            row = f"| {method['condition'].upper()} | {feature} | {method['feature_model']} | {method['model_training']} | {reference} |"
            if not common_notebook:
                row += f" [Notebook]({method['notebook_path']}) |"
            lines.append(row)
        references = references_for(root, entries)
        if references:
            lines += ['', '#### ' + references['group_label'], '',
                      '| 記号 | 役割 | システム | 参考文献 |', '|---|---|---|---|']
            for system in references['systems']:
                reference = (f"[{system['method_source_name']}]({system['method_source_url']})"
                             if system.get('method_source_url') else '—')
                lines.append(f"| {system['symbol']} | {system['role_label']} | {system['label']} | {reference} |")
            lines += ['', references['note']]
    lines += ['', '## スコア', '', '総合スコアは高いほど良く、本実験の手法はスコア順に並べています。']
    for group, entries in groups.items():
        sources = {(m['summary_path'], m['protocol_path'], m['inputs_path'], m.get('references_path', '')) for m in entries}
        if len(sources) != 1:
            raise ValueError(f'{group}: use one result source, protocol and input guide per comparison')
        summary_path, protocol_path, inputs_path, references_path = sources.pop()
        scores = {row['condition']: Decimal(row['official_score']) * 100 for row in rows(root / summary_path)}
        conditions = [m['condition'] for m in entries]
        if len(set(conditions)) != len(conditions):
            raise ValueError(f'{group}: duplicate method')
        references = references_for(root, entries)
        ordered = sorted(conditions, key=lambda condition: (-scores[condition], condition))
        systems = references.get('systems', [])
        symbols = [system['symbol'] for system in systems]
        if len(set(symbols)) != len(symbols) or set(symbols) & {c.upper() for c in conditions}:
            raise ValueError(f'{group}: duplicate chart symbol')
        labels = [c.upper() for c in ordered] + symbols
        values = [scores[c] for c in ordered] + [Decimal(system['score']) for system in systems]
        lines += ['', f'### {group}', '',
                  f'[固定条件]({protocol_path}) · [入力取得]({inputs_path}) · [総合値]({summary_path})', '',
                  '青：本実験' + ('／灰：公式・参考値（異なるモデル）。' if systems else '。'), '',
                  chart(labels, values, len(systems))]
        if references:
            lines += ['', f"出典: [DCASE 2026 Task 2 Results]({references['source_url']}) · "
                      f'[システム名・参考値]({references_path})']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check README without editing it')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    path = root / 'README.md'
    current = path.read_text(encoding='utf-8')
    before, rest = current.split(START)
    _, after = rest.split(END)
    updated = before + START + '\n\n' + render(root) + '\n\n' + END + after
    if args.check:
        if updated != current:
            parser.exit(1, 'README is stale; run python scripts/update_readme.py\n')
    else:
        path.write_text(updated, encoding='utf-8')


if __name__ == '__main__':
    main()
