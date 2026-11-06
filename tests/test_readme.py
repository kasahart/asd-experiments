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


def test_score_table_and_single_chart_use_canonical_scores():
    rendered = renderer.render(ROOT)
    scores = rendered.split('## スコア', 1)[1]
    rows = [line for line in scores.splitlines() if line.startswith('| 第')]
    expected = [
        ['第2回', 'Evaluation', '62.841', '58.362', '66.835', '62.325'],
        ['第3回', 'Development', '61.325', '—', '67.480', '—'],
        ['第3回', 'Development', '63.048', '—', '69.528', '—'],
        ['第3回', 'Evaluation', '62.841', '—', '66.835', '—'],
        ['第3回', 'Evaluation', '67.916', '—', '70.659', '—'],
    ]
    cells = [[c.strip() for c in row.strip('|').split('|')] for row in rows]
    assert [c[:2] + c[4:8] for c in cells] == expected
    text, files = renderer.build(ROOT)
    assert '```mermaid' not in text
    charts = {name: [float(v) for v in re.findall(r'>(\d+\.\d{3})</text>', files[f'results/readme/score-{name}.svg'])]
              for name in ('evaluation', 'development')}
    assert charts['evaluation'] == [
        70.659, 67.916, 66.835, 66.835, 62.841, 62.841, 62.325, 58.362, 59.803, 70.241]
    assert charts['development'] == [69.528, 67.480, 63.048, 61.325]
    for name in charts:
        assert f'](results/readme/score-{name}.svg)' in scores
        assert (ROOT / f'results/readme/score-{name}.svg').read_text(encoding='utf-8') == files[f'results/readme/score-{name}.svg']
    assert 'Evaluationの第3回 固定のB0・W1は、第2回 固定と同じ処理・同じ結果です。' in scores


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
    entries = [dict(m) for m in methods if m['comparison'] == 'DCASE 2026 Development / 固定BEATs（第3回）']
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
