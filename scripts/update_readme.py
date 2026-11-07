# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
"""Render the README summary, docs/results.md tables and SVG score charts from method metadata and canonical result CSVs."""
import argparse
import csv
import html
import json
from decimal import Decimal
from pathlib import Path

START = '<!-- experiments:start -->'
END = '<!-- experiments:end -->'
SUMMARY_START = '<!-- summary:start -->'
SUMMARY_END = '<!-- summary:end -->'


def replace_block(text, start, end, body):
    before, rest = text.split(start)
    _, after = rest.split(end)
    return before + start + '\n\n' + body + '\n\n' + end + after


def rows(path):
    with path.open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


BLUE = '#2458a6'
GRAY = '#9099a5'
CHART_DIR = 'results/readme'


def text_width(text, size):
    """Rough rendered width: CJK glyphs are about one em, others about 0.6 em."""
    return sum(size if ord(char) > 0x2E80 else 0.6 * size for char in text)


def chart(labels, values, reference_count=0):
    """Horizontal bar chart as a self-contained SVG with a 10-point grid."""
    size, row, bar = 13, 34, 22
    label_width = int(max(text_width(label, size) for label in labels)) + 16
    plot_width, top = 440, 34
    left = label_width
    height = top + row * len(labels) + 40
    width = left + plot_width + 60
    scale = plot_width / 100
    font = "font-family=\"'Hiragino Sans','Noto Sans CJK JP','Yu Gothic',Meiryo,sans-serif\""
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}" {font} font-size="{size}">',
           f'<rect width="{width}" height="{height}" fill="#ffffff"/>']
    bottom = top + row * len(labels)
    for tick in range(0, 101, 10):
        x = left + tick * scale
        stroke = '#888888' if tick == 0 else '#d5d9de'
        out.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}" stroke="{stroke}" stroke-width="1"/>')
        out.append(f'<text x="{x:.1f}" y="{bottom + 16}" text-anchor="middle" fill="#333333">{tick}</text>')
    out.append(f'<text x="{left + plot_width / 2:.1f}" y="{bottom + 34}" text-anchor="middle" fill="#333333">'
               'Official score</text>')
    first_reference = len(labels) - reference_count
    for index, (label, value) in enumerate(zip(labels, values)):
        y = top + row * index + (row - bar) / 2
        length = float(value) * scale
        color = GRAY if index >= first_reference else BLUE
        out.append(f'<text x="{left - 8}" y="{y + bar / 2 + 4.5:.1f}" text-anchor="end" fill="#222222">'
                   f'{html.escape(label)}</text>')
        out.append(f'<rect x="{left}" y="{y:.1f}" width="{length:.1f}" height="{bar}" fill="{color}"/>')
        out.append(f'<text x="{left + length + 5:.1f}" y="{y + bar / 2 + 4.5:.1f}" fill="#222222">{value:.3f}</text>')
    out.append('</svg>')
    return '\n'.join(out) + '\n'


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
                       'experiments': [single(entries, 'experiment', group)], 'dataset': single(entries, 'dataset', group),
                       'chart_prefix': single(entries, 'chart_prefix', group)})
    return result


def method_table(groups):
    symbols = {}
    for group in groups:
        for method in group['entries']:
            symbol = method.get('symbol') or method['condition'].upper()
            info = symbols.setdefault(symbol, {'descriptions': set(), 'references': set(), 'experiments': []})
            info['descriptions'].add(method['description'])
            if method.get('reference_url'):
                reference = f"[{method['reference_name']}]({method['reference_url']})"
                if method.get('reference_note'):
                    reference += f"（{method['reference_note']}）"
                info['references'].add(reference)
            for experiment in group['experiments']:
                if experiment not in info['experiments']:
                    info['experiments'].append(experiment)
    lines = ['| 手法 | 特徴 | 参考文献 | 使った実験 |', '|---|---|---|---|']
    for symbol, info in symbols.items():
        if len(info['descriptions']) != 1 or len(info['references']) > 1:
            raise ValueError(f'{symbol}: use one description and one reference for the same method symbol')
        feature = info['descriptions'].pop().replace('|', r'\|')
        reference = info['references'].pop() if info['references'] else '—'
        lines.append(f"| {symbol} | {feature} | {reference} | {'・'.join(sorted(info['experiments']))} |")
    return lines, list(symbols)


DATASET_ORDER = ['Evaluation', 'Development']


def merge_identical(groups):
    """Fold a comparison into an earlier one with the same setup and identical scores."""
    merged = []
    for group in groups:
        for earlier in merged:
            same_setup = all(group['entries'][0][k] == earlier['entries'][0][k]
                             for k in ('dataset', 'feature_model', 'model_training'))
            shared = set(group['scores']) & set(earlier['scores'])
            if (same_setup and shared == set(group['scores'])
                    and all(abs(group['scores'][s] - earlier['scores'][s]) < Decimal('1e-9') for s in shared)):
                earlier['experiments'] += [e for e in group['experiments'] if e not in earlier['experiments']]
                earlier['sources'] += [s for s in [group['summary_path']] if s not in earlier['sources']]
                break
        else:
            merged.append({**group, 'experiments': list(group['experiments']), 'sources': [group['summary_path']]})
    keys = [(g['dataset'], g['chart_prefix']) for g in merged]
    if len(set(keys)) != len(keys) or not all(prefix for _, prefix in keys):
        raise ValueError('Each comparison needs its own chart_prefix within a dataset')
    rank = {name: i for i, name in enumerate(DATASET_ORDER)}
    return sorted(merged, key=lambda g: rank.get(g['dataset'], len(rank)))


def lookup(groups, dataset, prefix, symbol):
    for group in groups:
        if group['dataset'] == dataset and group['chart_prefix'] == prefix and symbol in group['scores']:
            return group['scores'][symbol]
    return None


def summary_chart(panels, dataset, systems):
    """Two-panel change chart: hollow baseline dot -> filled result dot, coloured by direction."""
    lo, hi, left, width, row = 55, 75, 250, 440, 42
    x = lambda value: left + (float(value) - lo) / (hi - lo) * width
    up, down, base, ink, muted, grid = '#1f4e99', '#b4532a', '#9aa3ad', '#222222', '#5b6470', '#e3e6ea'
    font = "font-family=\"'Hiragino Sans','Noto Sans CJK JP','Yu Gothic',Meiryo,sans-serif\""
    out, y0 = [], 20
    for panel in panels:
        out.append(f'<text x="16" y="{y0 + 14}" font-size="15" font-weight="bold" fill="{ink}">{html.escape(panel["title"])}</text>')
        out.append(f'<text x="16" y="{y0 + 34}" font-size="12" fill="{muted}">基準：{html.escape(panel["baseline"])}'
                   '　○ 基準 → ● 処理後（青：上がった／橙：下がった）</text>')
        top = y0 + 52
        bottom = top + row * len(panel['rows'])
        for tick in range(lo, hi + 1, 5):
            out.append(f'<line x1="{x(tick):.1f}" y1="{top}" x2="{x(tick):.1f}" y2="{bottom}" stroke="{grid}"/>')
            out.append(f'<text x="{x(tick):.1f}" y="{bottom + 16}" text-anchor="middle" font-size="12" fill="{muted}">{tick}</text>')
        for system in systems:
            value = Decimal(system['score'])
            out.append(f'<line x1="{x(value):.1f}" y1="{top}" x2="{x(value):.1f}" y2="{bottom}" stroke="#9099a5" stroke-dasharray="4 3"/>')
            out.append(f'<text x="{x(value) + 3:.1f}" y="{top + 10}" font-size="11" fill="{muted}">{system["symbol"]}</text>')
        for index, (label, note, start, end) in enumerate(panel['rows']):
            y = top + row * index + row / 2 + 4
            color = up if end > start else down
            note_text = f'<tspan fill="{muted}" font-size="12">（{html.escape(note)}）</tspan>' if note else ''
            out.append(f'<text x="{left - 12}" y="{y + 4.5}" text-anchor="end" fill="{ink}">{html.escape(label)}{note_text}</text>')
            out.append(f'<line x1="{x(start):.1f}" y1="{y}" x2="{x(end):.1f}" y2="{y}" stroke="{color}" stroke-width="2.5"/>')
            out.append(f'<circle cx="{x(start):.1f}" cy="{y}" r="5.5" fill="#ffffff" stroke="{base}" stroke-width="2"/>')
            out.append(f'<circle cx="{x(end):.1f}" cy="{y}" r="5.5" fill="{color}" stroke="#ffffff" stroke-width="1.5"/>')
            text_x = max(x(start), x(end)) + 12
            out.append(f'<text x="{text_x:.1f}" y="{y + 4.5}" fill="{color}" font-weight="bold">{end - start:+.2f}</text>')
            out.append(f'<text x="{text_x + 46:.1f}" y="{y + 4.5}" fill="{muted}" font-size="12">{start:.1f} → {end:.1f}</text>')
        y0 = bottom + 40
    caption = f'{dataset} 総合スコア' + ('（破線は公式ベースライン・参考システム）' if systems else '')
    out.append(f'<text x="{left + width / 2}" y="{y0 - 6}" text-anchor="middle" font-size="12" fill="{muted}">{caption}</text>')
    height, total = y0 + 6, left + width + 150
    return '\n'.join([f'<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="{height}" '
                      f'viewBox="0 0 {total} {height}" {font} font-size="13">',
                      f'<rect width="{total}" height="{height}" fill="#ffffff"/>', *out, '</svg>']) + '\n'


def summary(root, groups, references):
    config = json.loads((root / 'configs/readme-summary.json').read_text(encoding='utf-8'))
    datasets = config['datasets']
    lines = ['| 観点 | 比較 | ' + ' | '.join(datasets) + ' |', '|---|---|' + '---|' * len(datasets)]
    panels = []
    for panel in config['panels']:
        rows_ = []
        for i, pair in enumerate(panel['pairs']):
            deltas = []
            for dataset in datasets:
                start, end = lookup(groups, dataset, *pair['from']), lookup(groups, dataset, *pair['to'])
                deltas.append(None if start is None or end is None else (start, end))
            if deltas[0] is None:
                raise ValueError(f"summary: {pair['label']} has no {datasets[0]} score")
            rows_.append((pair['label'], pair['note'], *deltas[0]))
            title = panel['title'] if i == 0 else ''
            compared = f"{pair['from'][1]}（{pair['from'][0]}）→ {pair['to'][1]}（{pair['to'][0]}）"
            cells = [f'{d[1] - d[0]:+.2f}'.replace('-', '−') if d else '—' for d in deltas]
            lines.append(f'| {title} | {compared} | ' + ' | '.join(cells) + ' |')
        panels.append({**panel, 'rows': rows_})
    shown = [s for s in references.get('systems', []) if references.get('split') == datasets[0]]
    path = f'{CHART_DIR}/summary.svg'
    headline = []
    for panel in panels:
        parts = []
        for label, note, start, end in panel['rows']:
            symbol = label.split(' ', 1)[0]
            parts.append(f"{symbol}{'（' + note + '）' if note else ''} {end - start:+.2f}".replace('-', '−'))
        headline.append(f"- **{panel['title']}**（基準：{panel['baseline']}）：{'、'.join(parts)}")
    readme = [f'![明示的なノイズ除去の効果と、BEATs追加学習の効果（{datasets[0]}）]({path})', '', *headline, '',
              f'値は {datasets[0]} の総合スコアの差（処理後 − 基準）で、各条件1回分の結果です。'
              + ('破線は公式ベースライン（BASE）と参考システム（REF）で、モデルが異なります。' if shown else '')
              + f'{"・".join(datasets[1:])}の差と全スコアは[結果の詳細](docs/results.md)にあります。']
    results = ['## 結果の要点', '', f'![明示的なノイズ除去の効果と、BEATs追加学習の効果（{datasets[0]}）](../{path})', '', *lines, '',
               '値は総合スコアの差（処理後 − 基準）で、各条件1回分の結果です。'
               + ('図の破線は公式ベースライン（BASE）と参考システム（REF）で、モデルが異なります。' if shown else '')
               + '各値は下の[スコア](#スコア)の表から計算しています。']
    return '\n'.join(readme), '\n'.join(results), {path: summary_chart(panels, datasets[0], shown)}


def build(root):
    files = {}
    raw = comparisons(root, rows(root / 'configs/readme-methods.csv'))
    table, symbols = method_table(raw)
    groups = merge_identical(raw)
    lines = ['## 手法', '', *table]
    with_references = [g for g in raw if g['references']]
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

    lines += ['', '## スコア', '', '公式評価器の総合スコア（0–100、高いほど良い）です。データ・特徴抽出の組み合わせごとに1行です。', '',
              '| データ | 特徴抽出 | ' + ' | '.join(symbols) + ' | 実験 |',
              '|---|---|' + '---|' * len(symbols) + '---|']
    for group in groups:
        first = group['entries'][0]
        cells = [f"{group['scores'][s]:.3f}" if s in group['scores'] else '—' for s in symbols]
        lines.append(f"| {group['dataset']} | {first['feature_model']}（{first['model_training']}） | "
                     + ' | '.join(cells) + f" | {'・'.join(sorted(group['experiments']))} |")
    sources = list(dict.fromkeys(path for g in groups for path in g['sources']))
    lines += ['', '数値の正本：' + '・'.join(f'[{path}](../{path})' for path in sources)]
    if references:
        values = '、'.join(f"{s['symbol']}（{s['role_label']}）{Decimal(s['score']):.3f}" for s in systems)
        lines += ['', f"参考値（{references['split']}、本実験とは異なるモデル）：{values}。"
                      f"出典: [DCASE 2026 Task 2 Results]({references['source_url']}) · "
                      f"[システム名・参考値](../{with_references[0]['references_path']})"]

    for dataset in dict.fromkeys(group['dataset'] for group in groups):
        bars = [(group['scores'][symbol], f"{group['chart_prefix']} {symbol}")
                for group in groups if group['dataset'] == dataset for symbol in group['scores']]
        bars.sort(key=lambda bar: (-bar[0], bar[1]))
        labels = [label for _, label in bars]
        values = [value for value, _ in bars]
        shown = systems if references and references['split'] == dataset else []
        labels += [system['symbol'] for system in shown]
        values += [Decimal(system['score']) for system in shown]
        path = f'{CHART_DIR}/score-{dataset.lower()}.svg'
        lines += ['', f'### {dataset}', '',
                  '青：本実験（スコア順）' + ('／灰：公式・参考値（異なるモデル）。' if shown else '。'), '',
                  f'![{dataset}の総合スコア（スコア順）](../{path})']
        files[path] = chart(labels, values, len(shown))
    readme_summary, results_summary, summary_files = summary(root, groups, references)
    files.update(summary_files)
    return results_summary + '\n\n' + '\n'.join(lines), files, readme_summary


def render(root):
    return build(root)[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check README, docs/results.md and charts without editing them')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    readme = root / 'README.md'
    results_doc = root / 'docs/results.md'
    text, files, summary_text = build(root)
    updated_readme = replace_block(readme.read_text(encoding='utf-8'), SUMMARY_START, SUMMARY_END, summary_text)
    updated_results = replace_block(results_doc.read_text(encoding='utf-8'), START, END, text)
    outputs = {readme: updated_readme, results_doc: updated_results,
               **{root / name: content for name, content in files.items()}}
    stale = [p for p, content in outputs.items() if not p.exists() or p.read_text(encoding='utf-8') != content]
    if args.check:
        if stale:
            parser.exit(1, 'README, docs/results.md or charts are stale; run python scripts/update_readme.py\n')
    else:
        for p, content in outputs.items():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding='utf-8')

if __name__ == '__main__':
    main()
