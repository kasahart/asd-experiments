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
             '        width: 640', f'        height: {80 + 50 * len(labels)}',
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


def single(entries, key, group):
    values = {m.get(key, '') for m in entries}
    if len(values) != 1:
        raise ValueError(f'{group}: use one {key} per comparison')
    return values.pop()


def comparisons(root, methods):
    groups = {}
    for method in methods:
        groups.setdefault(method['comparison'], []).append(method)
    result = []
    for group, entries in groups.items():
        models = {(m['feature_model'], m['model_training']) for m in entries}
        if len(models) != 1:
            raise ValueError(f'{group}: use separate comparison groups for different feature models or model training')
        sources = {(m['summary_path'], m['protocol_path'], m['inputs_path'], m.get('references_path', ''),
                    m.get('split', ''), m.get('detector', ''), m.get('score_multiplier') or '100') for m in entries}
        if len(sources) != 1:
            raise ValueError(f'{group}: use one result source, protocol and input guide per comparison')
        summary_path, protocol_path, inputs_path, references_path, split, detector, multiplier = sources.pop()
        selected = [row for row in rows(root / summary_path)
                    if (not split or row.get('split') == split) and (not detector or row.get('detector') == detector)]
        if len({row['condition'] for row in selected}) != len(selected):
            raise ValueError(f'{group}: ambiguous summary rows; specify split and detector')
        scale = Decimal(multiplier)
        if scale not in {Decimal(1), Decimal(100)}:
            raise ValueError(f'{group}: score_multiplier must be 1 or 100')
        by_condition = {row['condition']: Decimal(row['official_score']) * scale for row in selected}
        conditions = [m['condition'] for m in entries]
        if len(set(conditions)) != len(conditions):
            raise ValueError(f'{group}: duplicate method')
        symbols = {m['condition']: m.get('symbol') or m['condition'].upper() for m in entries}
        if len(set(symbols.values())) != len(conditions):
            raise ValueError(f'{group}: duplicate method symbol')
        scores = {symbols[c]: by_condition[c] for c in conditions}
        if any(not value.is_finite() or not 0 <= value <= 100 for value in scores.values()):
            raise ValueError(f'{group}: expected finite 0–100 scores')
        result.append({'name': group, 'entries': entries, 'scores': scores,
                       'references': references_for(root, entries), 'references_path': references_path,
                       'summary_path': summary_path, 'protocol_path': protocol_path, 'inputs_path': inputs_path,
                       'round': single(entries, 'round', group), 'dataset': single(entries, 'dataset', group),
                       'chart_prefix': single(entries, 'chart_prefix', group)})
    prefixes = [(c['dataset'], c['chart_prefix']) for c in result]
    if len(set(prefixes)) != len(prefixes) or not all(p for _, p in prefixes):
        raise ValueError('Each comparison needs its own chart_prefix within a dataset')
    return result


def method_table(groups):
    symbols = {}
    for group in groups:
        for method in group['entries']:
            symbol = method.get('symbol') or method['condition'].upper()
            info = symbols.setdefault(symbol, {'descriptions': set(), 'references': set(), 'rounds': []})
            info['descriptions'].add(method['description'])
            if method.get('reference_url'):
                reference = f"[{method['reference_name']}]({method['reference_url']})"
                if method.get('reference_note'):
                    reference += f"（{method['reference_note']}）"
                info['references'].add(reference)
            if group['round'] not in info['rounds']:
                info['rounds'].append(group['round'])
    lines = ['| 手法 | 特徴 | 参考文献 | 使った回 |', '|---|---|---|---|']
    for symbol, info in symbols.items():
        if len(info['descriptions']) != 1 or len(info['references']) > 1:
            raise ValueError(f'{symbol}: use one description and one reference for the same method symbol')
        feature = info['descriptions'].pop().replace('|', r'\|')
        reference = info['references'].pop() if info['references'] else '—'
        lines.append(f"| {symbol} | {feature} | {reference} | {'・'.join(info['rounds'])} |")
    return lines, list(symbols)


def render(root):
    groups = comparisons(root, rows(root / 'configs/readme-methods.csv'))
    table, symbols = method_table(groups)
    lines = ['## 手法', '', *table]
    with_references = [g for g in groups if g['references']]
    if len({g['references_path'] for g in with_references}) > 1:
        raise ValueError('Use one challenge reference source')
    references = with_references[0]['references'] if with_references else {}
    systems = references.get('systems', [])
    if references:
        lines += ['', '#### ' + references['group_label'], '',
                  '| 記号 | 役割 | システム | 参考文献 |', '|---|---|---|---|']
        for system in systems:
            reference = (f"[{system['method_source_name']}]({system['method_source_url']})"
                         if system.get('method_source_url') else '—')
            lines.append(f"| {system['symbol']} | {system['role_label']} | {system['label']} | {reference} |")
        lines += ['', references['note']]
    reference_symbols = [system['symbol'] for system in systems]
    if len(set(reference_symbols)) != len(reference_symbols) or set(reference_symbols) & set(symbols):
        raise ValueError('duplicate chart symbol')

    lines += ['', '## スコア', '', '公式評価器の総合スコア（0–100、高いほど良い）です。回・データ・特徴抽出の組み合わせごとに1行です。', '',
              '| 回 | データ | 特徴抽出モデル | モデルの追加学習 | ' + ' | '.join(symbols) + ' | 資料 |',
              '|---|---|---|---|' + '---|' * len(symbols) + '---|']
    for group in groups:
        first = group['entries'][0]
        cells = [f"{group['scores'][s]:.3f}" if s in group['scores'] else '—' for s in symbols]
        links = (f"[条件]({group['protocol_path']}) · [入力]({group['inputs_path']}) · "
                 f"[CSV]({group['summary_path']})")
        lines.append(f"| {group['round']} | {group['dataset']} | {first['feature_model']} | "
                     f"{first['model_training']} | " + ' | '.join(cells) + f' | {links} |')
    for i, group in enumerate(groups):
        for earlier in groups[:i]:
            shared = [s for s in symbols if s in group['scores'] and s in earlier['scores']]
            same_setup = all(group['entries'][0][k] == earlier['entries'][0][k]
                             for k in ('dataset', 'feature_model', 'model_training'))
            if same_setup and shared and all(abs(group['scores'][s] - earlier['scores'][s]) < Decimal('1e-9') for s in shared):
                lines += ['', f"{group['dataset']}の{group['chart_prefix']}の{'・'.join(shared)}は、{earlier['chart_prefix']}と同じ処理・同じ結果です。"]
    if references:
        values = '、'.join(f"{s['symbol']}（{s['role_label']}）{Decimal(s['score']):.3f}" for s in systems)
        lines += ['', f"参考値（{references['split']}、本実験とは異なるモデル）：{values}。"
                      f"出典: [DCASE 2026 Task 2 Results]({references['source_url']}) · "
                      f"[システム名・参考値]({with_references[0]['references_path']})"]

    for dataset in dict.fromkeys(group['dataset'] for group in groups):
        bars = [(group['scores'][symbol], f"{group['chart_prefix']} {symbol}")
                for group in groups if group['dataset'] == dataset for symbol in group['scores']]
        bars.sort(key=lambda bar: (-bar[0], bar[1]))
        labels = [label for _, label in bars]
        values = [value for value, _ in bars]
        shown = systems if references and references['split'] == dataset else []
        labels += [system['symbol'] for system in shown]
        values += [Decimal(system['score']) for system in shown]
        lines += ['', f'### {dataset}', '',
                  '青：本実験（スコア順）' + ('／灰：公式・参考値（異なるモデル）。' if shown else '。'), '',
                  chart(labels, values, len(shown))]
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
