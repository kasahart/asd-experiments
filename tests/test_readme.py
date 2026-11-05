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


def test_each_comparison_renders_its_canonical_scores_and_no_empty_app_link():
    rendered = renderer.render(ROOT)
    scores = rendered.split('## スコア', 1)[1]
    sections = {part.splitlines()[0]: part for part in scores.split('\n### ')[1:]}
    expected = {
        'DCASE 2026 Evaluation / BEATs_iter3': [66.835, 62.841, 62.325, 58.362, 59.803, 70.241],
        'DCASE 2026 Development / 固定BEATs（第3回）': [67.480, 61.325],
        'DCASE 2026 Development / BEATs追加学習（第3回）': [69.528, 63.048],
        'DCASE 2026 Evaluation / 固定BEATs（第3回）': [66.835, 62.841],
        'DCASE 2026 Evaluation / BEATs追加学習（第3回）': [70.659, 67.916],
    }
    assert set(sections) == set(expected)
    for name, values in expected.items():
        text = re.search(r'\n    bar \[([^]]+)\]', sections[name]).group(1)
        assert [float(x) for x in text.split(', ')] == values
    assert '[marimoアプリ]()' not in rendered
    assert rendered.count('| B0 |') == 5 and rendered.count('| W1 |') == 5


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
