# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
"""Render README tables from method metadata and canonical result CSVs."""
import argparse
import csv
from decimal import Decimal
from pathlib import Path

START = '<!-- experiments:start -->'
END = '<!-- experiments:end -->'


def rows(path):
    with path.open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def render(root):
    methods = rows(root / 'configs/readme-methods.csv')
    lines = ['## 手法', '', '| 比較範囲 | 手法 | 説明 | Notebook |', '|---|---|---|---|']
    groups = {}
    for method in methods:
        group = method['comparison']
        condition = method['condition']
        description = method['description'].replace('|', r'\|')
        lines.append(f"| {group} | {condition.upper()} | {description} | [Notebook]({method['notebook_path']}) |")
        groups.setdefault(group, []).append(method)
    lines += ['', '## スコア', '', '総合スコアは高いほど良く、順位は同じ比較範囲内で付けています。']
    for group, entries in groups.items():
        sources = {(m['summary_path'], m['protocol_path'], m['inputs_path']) for m in entries}
        if len(sources) != 1:
            raise ValueError(f'{group}: use one result source, protocol and input guide per comparison')
        summary_path, protocol_path, inputs_path = sources.pop()
        scores = {row['condition']: Decimal(row['official_score']) * 100 for row in rows(root / summary_path)}
        conditions = [m['condition'] for m in entries]
        if len(set(conditions)) != len(conditions):
            raise ValueError(f'{group}: duplicate method')
        lines += ['', f'### {group}', '', f'[固定条件]({protocol_path}) · [入力取得]({inputs_path}) · [総合値]({summary_path})', '',
                  '| 順位 | 手法 | 総合スコア |', '|---:|---|---:|']
        ordered = sorted(conditions, key=lambda condition: (-scores[condition], condition))
        for condition in ordered:
            score = scores[condition]
            rank = 1 + sum(scores[other] > score for other in conditions)
            lines.append(f'| {rank} | {condition.upper()} | {score:.3f} |')
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
            parser.exit(1, 'README tables are stale; run python scripts/update_readme.py\n')
    else:
        path.write_text(updated, encoding='utf-8')


if __name__ == '__main__':
    main()
