# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
"""Render README methods and score graphs from method metadata and canonical result CSVs."""
import argparse
import csv
import hashlib
import json
import textwrap
from html import escape
from io import BytesIO
from decimal import Decimal
from pathlib import Path

START = '<!-- experiments:start -->'
END = '<!-- experiments:end -->'


def rows(path):
    with path.open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def chart(group, ordered, scores, references, descriptions):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    plt.rcParams.update({'font.family': ['Noto Sans CJK JP', 'DejaVu Sans'], 'svg.hashsalt': 'asd-readme-score'})
    ref_rows = references.get('systems', [])
    count = len(ordered)
    positions = list(range(count))
    ref_positions = list(range(count + 1, count + 1 + len(ref_rows)))
    fig, ax = plt.subplots(figsize=(6.4, 2.1 + .95 * (count + len(ref_rows))))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    ax.barh(positions, [float(scores[c]) for c in ordered], height=.62, color='#2458a6')
    if ref_rows:
        ax.barh(ref_positions, [float(r['score']) for r in ref_rows], height=.62,
                color='#b8bec7', edgecolor='#5a6470', linewidth=.8)
        ax.axhline(count - .15, color='#b8bec7', linewidth=.8)
        ax.text(0, count + .36, '大会参考値（別構成）', fontsize=17,
                color='#475569', va='center')
    labels = []
    for condition in ordered:
        feature = descriptions[condition]
        if len(feature) > 9 and 'を' in feature:
            feature = feature.replace('を', 'を\n', 1)
        else:
            feature = textwrap.fill(feature, width=9)
        labels.append(condition.upper() + '\n' + feature)
    labels += [r['label'].replace('_baseline_', '_\nbaseline_')
               .replace('_task2_', '_\ntask2_') for r in ref_rows]
    ax.set_yticks(positions + ref_positions, labels, fontsize=18)
    for position, value in zip(positions + ref_positions,
                               [scores[c] for c in ordered] + [Decimal(r['score']) for r in ref_rows]):
        inside = value > 84
        color = 'white' if inside and position < count else '#111827'
        ax.text(float(value) - 1.3 if inside else float(value) + 1.3, position,
                f'{value:.3f}', fontsize=20, va='center',
                ha='right' if inside else 'left', color=color)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.tick_params(axis='x', labelsize=13)
    ax.tick_params(axis='y', length=0, pad=9)
    ax.set_xlabel('Official score (0–100)', fontsize=14, labelpad=12)
    fig.suptitle(f"DCASE {references['year']} Task {references['task']} · {references['split']}" if references else group,
                 fontsize=20, x=.04, y=.97, ha='left')
    fig.text(.04, .895, '本実験: ' + group.split(' / ')[-1], fontsize=16, color='#475569')
    ax.set_ylim((ref_positions or positions)[-1] + .6, -.65)
    ax.set_axisbelow(True)
    ax.grid(axis='x', color='#e2e8f0', linewidth=.7)
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_color('#94a3b8')
    fig.subplots_adjust(left=.42, right=.95, top=.82, bottom=.09)
    stream = BytesIO()
    fig.savefig(stream, format='svg', metadata={'Date': None})
    plt.close(fig)
    alt = group + '。本実験: ' + '、'.join(f'{c.upper()}（{descriptions[c]}）{scores[c]:.3f}' for c in ordered)
    if ref_rows:
        alt += '。大会参考値（異なるモデル構成）: ' + '、'.join(
            f"{r['label']} {Decimal(r['score']):.3f}" for r in ref_rows)
    svg = stream.getvalue().decode()
    svg = svg.replace('<svg ', '<svg role="img" ', 1)
    at = svg.index('>', svg.index('<svg ')) + 1
    svg = svg[:at] + '<title>' + escape(group) + '</title><desc>' + escape(alt) + '</desc>' + svg[at:]
    svg = "\n".join(line.rstrip() for line in svg.splitlines()) + "\n"
    return svg.encode(), alt


def render(root, charts=None):

    methods = rows(root / 'configs/readme-methods.csv')
    groups = {}
    for method in methods:
        groups.setdefault(method['comparison'], []).append(method)
    lines = ['## 手法']
    for group, entries in groups.items():
        notebooks = {m['notebook_path'] for m in entries}
        common_notebook = len(notebooks) == 1
        lines += ['', f'### {group}', '']
        if common_notebook:
            lines += [f'[Notebook]({next(iter(notebooks))})', '']
        lines += ['| 手法 | 特徴 | 参考文献 |' + ('' if common_notebook else ' Notebook |'),
                  '|---|---|---|' + ('' if common_notebook else '---|')]
        for method in entries:
            feature = method['description'].replace('|', r'\|')
            reference = '—'
            if method.get('reference_url'):
                reference = f"[{method['reference_name']}]({method['reference_url']})"
                if method.get('reference_note'):
                    reference += f"（{method['reference_note']}）"
            row = f"| {method['condition'].upper()} | {feature} | {reference} |"
            if not common_notebook:
                row += f" [Notebook]({method['notebook_path']}) |"
            lines.append(row)
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
        references = json.loads((root / references_path).read_text()) if references_path else {}
        if references and references['comparison'] != group:
            raise ValueError(f'{group}: challenge references belong to another comparison')
        ordered = sorted(conditions, key=lambda condition: (-scores[condition], condition))
        descriptions = {m['condition']: m['description'] for m in entries}
        svg, alt = chart(group, ordered, scores, references, descriptions)
        path = 'figures/scores-' + hashlib.sha256(group.encode()).hexdigest()[:12] + '.svg'
        if charts is not None:
            charts[path] = svg
        lines += ['', f'### {group}', '',
                  f'[固定条件]({protocol_path}) · [入力取得]({inputs_path}) · [総合値]({summary_path})', '',
                  f'![{alt}]({path})']
        if references:
            lines += ['', references['note'], '',
                      f"出典: [DCASE 2026 Task 2 Results]({references['source_url']}) · "
                      f'[システム名・参考値]({references_path})']
            for system in references['systems']:
                if system.get('method_source_url'):
                    lines += [f"手法の参考: [{system['method_source_name']}]({system['method_source_url']})"]
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
    charts = {}
    updated = before + START + '\n\n' + render(root, charts) + '\n\n' + END + after
    if args.check:
        if updated != current or any(not (root / p).exists() or (root / p).read_bytes() != data
                                    for p, data in charts.items()):
            parser.exit(1, 'README or score graphs are stale; run python scripts/update_readme.py\n')
    else:
        path.write_text(updated, encoding='utf-8')
        for relative, data in charts.items():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)


if __name__ == '__main__':
    main()
