"""Build a small index and one static marimo export per registered app."""
import argparse
from html import escape
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/kasahart/asd-experiments"
STYLE = """
:root{color-scheme:light;font-family:system-ui,-apple-system,sans-serif;color:#172b42;background:#f5f7fa}
body{margin:0;line-height:1.8}main{max-width:900px;margin:auto;padding:40px 24px 64px}
a{color:#1759a5;text-underline-offset:3px}a:focus-visible{outline:3px solid #e89e27;outline-offset:5px}
header nav{display:flex;gap:24px;flex-wrap:wrap}header h1{font-size:clamp(2rem,6vw,3rem);line-height:1.3;margin:32px 0 12px}
.lead{font-size:1.1rem;max-width:680px}.apps{display:grid;gap:24px;margin-top:32px}
article{background:white;border:1px solid #d9e1ea;border-radius:16px;padding:28px}
article h2{font-size:1.5rem;line-height:1.5;margin:0 0 12px}article p{margin:12px 0}
.open{display:inline-block;background:#1759a5;color:white;text-decoration:none;padding:10px 20px;border-radius:8px;font-weight:600;margin:8px 0}
.article-link{display:inline-block;margin:8px 0 8px 16px;font-weight:600}
.related{font-size:.95rem}.related a{display:inline-block}footer{border-top:1px solid #d9e1ea;margin-top:40px;padding-top:20px;font-size:.95rem}
@media(max-width:480px){.article-link{display:block;margin:8px 0}main{padding:24px 18px 40px}article{padding:20px}article h2{font-size:1.3rem}}
"""
NAV_STYLE = """
:root{--asd-nav-height:60px}
#root{position:relative;height:calc(100vh - var(--asd-nav-height))!important;height:calc(100dvh - var(--asd-nav-height))!important}
.site-nav{height:var(--asd-nav-height);box-sizing:border-box;max-width:1100px;margin:0 auto;padding:16px 24px;display:flex;gap:8px 24px;flex-wrap:wrap;align-content:center;align-items:center;border-bottom:1px solid #e1e5eb;font:16px/1.6 system-ui,sans-serif;background:white}
@media(max-width:380px){:root{--asd-nav-height:96px}.site-nav{padding:12px 18px}}
.site-nav a{color:#1759a5;text-underline-offset:3px}.site-nav a:focus-visible{outline:3px solid #e89e27;outline-offset:4px}
"""


def load_apps(path):
    apps = json.loads(path.read_text())
    if not isinstance(apps, list) or not apps:
        raise ValueError("Register at least one app")
    seen = set()
    for app in apps:
        slug = app["slug"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or slug in seen:
            raise ValueError(f"Invalid or duplicate slug: {slug}")
        seen.add(slug)
        source = ROOT / app["source"]
        if source.suffix != ".py" or not source.resolve().is_relative_to(ROOT / "apps") or not source.is_file():
            raise ValueError(f"Missing or invalid app source: {app['source']}")
        for key in ("title", "description"):
            if not isinstance(app[key], str) or not app[key].strip():
                raise ValueError(f"Missing {key}: {slug}")
        article_url = urlparse(app["article_url"])
        if article_url.scheme != "https" or not article_url.netloc:
            raise ValueError(f"Invalid article URL: {slug}")
        for article in app.get("related_articles", []):
            url = urlparse(article["url"])
            if url.scheme != "https" or not url.netloc or not article["label"].strip():
                raise ValueError(f"Invalid related article: {slug}")
    return apps


def render_index(apps):
    cards = []
    for app in apps:
        related = " · ".join(
            f'<a href="{escape(article["url"], quote=True)}">{escape(article["label"])}</a>'
            for article in app.get("related_articles", [])
        )
        cards.append(f'''<article>
<h2>{escape(app["title"])}</h2>
<p>{escape(app["description"])}</p>
<a class="open" href="apps/{app["slug"]}/">アプリを開く →</a>
<a class="article-link" href="{escape(app["article_url"], quote=True)}">記事を読む（Zenn）</a>
{f'<p class="related">関連記事：{related}</p>' if related else ''}
</article>''')
    return f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ASD experiments — 連載の実験アプリ</title>
<meta name="description" content="Zennの異常音検知連載に対応する実験アプリ。保存結果・図・音声をブラウザーで確認できます。">
<style>{STYLE}</style></head><body><main>
<header><nav aria-label="関連リンク"><a href="{REPO}">GitHub：コード・実行手順</a></nav>
<h1>ASD experiments</h1>
<p class="lead">Zennの異常音検知連載に対応する実験アプリです。結果・図・音声を、ブラウザーで確認できます。</p>
<p>読む・聞くためのインストールやデータ取得は不要です。</p></header>
<section class="apps" aria-label="実験アプリ一覧">{''.join(cards)}</section>
<footer>再推論・再採点の手順はGitHubの各実験の説明を参照してください。図・音声の出典と利用条件は、各アプリに記載しています。</footer>
</main></body></html>'''


def add_navigation(html, app):
    if '<body>' not in html or '</head>' not in html:
        raise ValueError("Unexpected marimo HTML structure")
    html = html.replace('</head>', f'<style>{NAV_STYLE}</style></head>', 1)
    nav = f'<nav class="site-nav" aria-label="アプリの移動"><a href="../../">← アプリ一覧</a><a href="{escape(app["article_url"], quote=True)}">記事を読む（Zenn）</a><a href="{REPO}">GitHub</a></nav>'
    return html.replace('<body>', '<body>' + nav, 1)


def build(apps, output, source_ref):
    # Reuse committed source references in both the deployment record and notices.
    output.mkdir(parents=True, exist_ok=True)
    for app in apps:
        folder = output / "apps" / app["slug"]
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / "index.html"
        subprocess.run([sys.executable, "-m", "marimo", "export", "html", "--no-include-code",
                        str(ROOT / app["source"]), "-o", str(target), "-f"], check=True, cwd=ROOT)
        target.write_text(add_navigation(target.read_text(), app))
    (output / "index.html").write_text(render_index(apps))
    (output / ".nojekyll").write_text("")
    shutil.copyfile(ROOT / "LICENSE", output / "LICENSE")
    shutil.copyfile(ROOT / "docs/DATA_ATTRIBUTION.md", output / "DATA_ATTRIBUTION.md")
    base = REPO + "/blob/" + source_ref + "/"
    notice = (ROOT / "THIRD_PARTY_NOTICES.md").read_text()
    notice = re.sub(r'\]\((?!https?://)([^)]+)\)', lambda match: '](' + base + match[1] + ')', notice)
    (output / "THIRD_PARTY_NOTICES.md").write_text(notice)
    (output / "build-source.json").write_text(json.dumps({"repository": REPO, "source_commit": source_ref,
        "marimo": "0.25.1", "apps": [{"url": "apps/" + a["slug"] + "/", "source": a["source"]} for a in apps]}, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/site")
    parser.add_argument("--check", action="store_true", help="Check metadata and source paths without exporting")
    args = parser.parse_args()
    apps = load_apps(ROOT / "configs/apps.json")
    if args.check:
        print(f"Validated {len(apps)} app(s)")
        return
    ref = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    build(apps, args.output.resolve(), ref)


if __name__ == "__main__":
    main()
