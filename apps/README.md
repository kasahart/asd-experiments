# marimoアプリと公開ページ

[アプリ一覧](https://kasahart.github.io/asd-experiments/)。保存結果・図・音声を読むアプリで、推論や再採点はしません。

## ローカルで読む・編集する

リポジトリのルートで実行します。必要なのはPython 3.10以上とmarimo 0.25.1だけです。

```bash
python3 -m venv .venv-app
.venv-app/bin/python -m pip install marimo==0.25.1
.venv-app/bin/marimo run apps/02_b0_b1_w1_ss.py
# 編集する場合は run を edit に変更
```

## 図を再描画する

実録音の図はWandas 0.8.0で作成し、全条件で軸と色範囲を揃えています。元データから再描画するには、`ASD_DATA_ROOT`を`ToothBrush`があるディレクトリに設定します（重みは不要）。

```bash
python -m pip install -e '.[visualization]'
ASD_DATA_ROOT=/path/to/eval_data/raw python scripts/render_recording.py
```

図は`outputs/recording-figures`（`ASD_FIGURE_OUTPUT`で変更可）へ保存します。

## Pages用HTMLを更新する

トップページはアプリ一覧、各アプリは`apps/<slug>/`で配信します。

```bash
.venv-app/bin/python scripts/build_site.py --check
.venv-app/bin/python scripts/build_site.py --output outputs/site
```

[marimoの静的HTML export](https://docs.marimo.io/guides/exporting/static_html/)で、結果表・図・音声をHTMLに埋め込みます。表示にはmarimoのCDNを使うため、閲覧にはネット接続が必要です。

## アプリを追加する

1. `apps/`にmarimoのPythonファイルを追加します。図・音声などの保存ファイルと必要な帰属情報も用意します。
2. [一覧設定](../configs/apps.json)に1件追加します。`slug`（公開URL）、`title`、`description`、`source`（Pythonファイル）、`article_url`（対応するZenn記事のURL）、任意の`related_articles`（`label`と`url`）を指定します。一覧へ戻るリンクと記事リンクは自動で付きます。公開後の`slug`は変えないでください。
3. 上のコマンドで生成して表示を確認し、`outputs/site`の内容を`gh-pages`ブランチのルートへ反映してpushします。
