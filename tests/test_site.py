"""Catch catalog additions that would create broken or ambiguous app URLs."""

import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "build_site", Path(__file__).resolve().parents[1] / "scripts/build_site.py"
)
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)


def test_registered_routes_and_return_link():
    apps = site.load_apps(site.ROOT / "configs/apps.json")
    html = site.render_index(apps)
    for app in apps:
        assert f'href="apps/{app["slug"]}/"' in html
        assert f'href="{app["article_url"]}"' in html
    export = site.add_navigation(
        '<html><head></head><body><div id="root"></div></body></html>', apps[0]
    )
    assert 'href="../../"' in export
    assert f'href="{apps[0]["article_url"]}"' in export
    assert '<div id="root"></div>' in export


@pytest.mark.parametrize(
    "failure", ["duplicate", "traversal", "missing-source", "invalid-article"]
)
def test_invalid_catalog_addition_fails_before_export(tmp_path, failure):
    apps = json.loads((site.ROOT / "configs/apps.json").read_text())
    if failure == "duplicate":
        apps.append(dict(apps[0]))
    elif failure == "traversal":
        apps[0]["slug"] = "../other"
    elif failure == "invalid-article":
        apps[0]["article_url"] = "javascript:void(0)"
    else:
        apps[0]["source"] = "apps/missing.py"
    path = tmp_path / "apps.json"
    path.write_text(json.dumps(apps))
    with pytest.raises(ValueError):
        site.load_apps(path)
