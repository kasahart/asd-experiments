"""The experiment index must keep splits, models and score units distinct."""
import csv
import importlib.util
from pathlib import Path
import re
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('readme_renderer', ROOT / 'scripts/update_readme.py')
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


def test_score_table_and_charts_use_canonical_scores():
    text, files, _ = renderer.build(ROOT)
    scores = text.split('## スコア', 1)[1]
    rows = [line for line in scores.splitlines() if line.startswith(('| Evaluation', '| Development'))]
    cells = [[c.strip() for c in row.strip('|').split('|')] for row in rows]
    assert [[c[0]] + c[2:] for c in cells] == [
        ['Evaluation', '62.841', '58.362', '66.835', '62.325', '実験1・実験2'],
        ['Evaluation', '67.916', '—', '70.659', '—', '実験2'],
        ['Development', '61.325', '—', '67.480', '—', '実験2'],
        ['Development', '63.048', '—', '69.528', '—', '実験2'],
    ]
    assert '```mermaid' not in text
    charts = {name: [float(v) for v in re.findall(r'>(\d+\.\d{3})</text>', files[f'results/readme/score-{name}.svg'])]
              for name in ('evaluation', 'development')}
    assert charts['evaluation'] == [70.659, 67.916, 66.835, 62.841, 62.325, 58.362, 59.803, 70.241]
    assert charts['development'] == [69.528, 67.480, 63.048, 61.325]
    for name, content in files.items():
        assert (ROOT / name).read_text(encoding='utf-8') == content
    results_doc = (ROOT / 'docs/results.md').read_text(encoding='utf-8')
    assert text in results_doc
    assert '```mermaid' not in results_doc


def test_summary_shows_both_effects_as_differences():
    text, files, summary = renderer.build(ROOT)
    table = text.split('## 結果の要点', 1)[1].split('## スコア', 1)[0]
    rows = [[c.strip() for c in line.strip('|').split('|')] for line in table.splitlines() if line.startswith('|  ') or line.startswith('| ①') or line.startswith('| ②')]
    assert [r[2:] for r in rows] == [
        ['+3.99', '+6.16'], ['−0.52', '—'], ['+5.07', '+1.72'], ['+3.82', '+2.05']]
    svg = files['results/readme/summary.svg']
    assert re.findall(r'>([+−]\d+\.\d{2})</text>', svg) == ['+3.99', '−0.52', '+5.07', '+3.82']
    assert '](results/readme/summary.svg)' in summary
    assert 'W1 複素減算 +3.99、SS 振幅スペクトル減算 −0.52' in summary and 'B0 近接マイク +5.07、W1 複素減算 +3.82' in summary
    assert summary in (ROOT / 'README.md').read_text(encoding='utf-8')


def test_method_symbols_are_defined_once():
    methods = renderer.render(ROOT).split('## スコア', 1)[0]
    for symbol in ('B0', 'B1', 'W1', 'SS'):
        assert methods.count(f'| {symbol} |') == 1


def test_same_symbol_must_keep_one_description(tmp_path):
    (tmp_path / 'configs').mkdir()
    text = (ROOT / 'configs/readme-methods.csv').read_text(encoding='utf-8')
    (tmp_path / 'configs/readme-methods.csv').write_text(
        text.replace('w1_global,遠方マイクの大きさと位相を合わせて減算（全区間で推定）', 'w1_global,別の説明'), encoding='utf-8')
    for path in ('results/02-summary.csv', 'results/02-challenge-references.json', 'results/03-beats/summary.csv'):
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_bytes((ROOT / path).read_bytes())
    with pytest.raises(ValueError, match='one description'):
        renderer.render(tmp_path)


def test_ambiguous_split_or_detector_cannot_overwrite_scores(tmp_path):
    with (ROOT / 'configs/readme-methods.csv').open() as stream:
        methods = list(csv.DictReader(stream))
    entries = [dict(m) for m in methods if m['comparison'] == 'DCASE 2026 Development / 固定BEATs（実験2）']
    for method in entries:
        method['detector'] = ''
    (tmp_path / 'configs').mkdir()
    with (tmp_path / 'configs/readme-methods.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(entries[0]))
        writer.writeheader()
        writer.writerows(entries)
    summary = tmp_path / 'results/03-beats/summary.csv'
    summary.parent.mkdir(parents=True)
    summary.write_bytes((ROOT / 'results/03-beats/summary.csv').read_bytes())
    with pytest.raises(ValueError, match='ambiguous summary rows'):
        renderer.render(tmp_path)


def test_new_method_under_same_setup_merges_into_existing_row(tmp_path):
    text = (ROOT / 'configs/readme-methods.csv').read_text(encoding='utf-8')
    extra = ('DCASE 2026 Evaluation / 新手法（実験3）,実験3,Evaluation,重み固定,w2,別の減算,results/02-summary.csv,'
             ',,,,BEATs_iter3,重み固定,,,,W2\n')
    (tmp_path / 'configs').mkdir()
    (tmp_path / 'configs/readme-methods.csv').write_text(text + extra, encoding='utf-8')
    (tmp_path / 'configs/readme-summary.json').write_bytes((ROOT / 'configs/readme-summary.json').read_bytes())
    for path in ('results/02-summary.csv', 'results/02-challenge-references.json', 'results/03-beats/summary.csv'):
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_bytes((ROOT / path).read_bytes())
    summary = tmp_path / 'results/02-summary.csv'
    summary.write_text(summary.read_text(encoding='utf-8') + 'w2,0.6,0.6,0.6,0.6\n', encoding='utf-8')
    rendered, _, _ = renderer.build(tmp_path)
    rows = [line for line in rendered.splitlines() if line.startswith('| Evaluation | BEATs_iter3（重み固定）')]
    assert len(rows) == 1 and '60.000' in rows[0] and '実験1・実験2・実験3' in rows[0]


def test_summary_chart_axis_follows_data():
    assert renderer.axis_range([62.3, 70.7])[:2] == (61, 72)
    lo, hi, ticks = renderer.axis_range([40.2, 84.9])
    assert (lo, hi) == (39, 86) and ticks == [40, 45, 50, 55, 60, 65, 70, 75, 80, 85]
