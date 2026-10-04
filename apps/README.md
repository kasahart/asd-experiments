# marimoアプリと公開ページ

[アプリ一覧](https://kasahart.github.io/asd-experiments/) / [第2回を開く](https://kasahart.github.io/asd-experiments/apps/02-b0-b1-w1-ss/)。保存結果・図・手動再生の音声を読むアプリです。生音声からの推論や保存異常度の再採点は[CLI](../src/asd_min/runner.md)で行います。波形図の再描画は[波形処理](../src/asd_min/waveform.md)を参照してください。

## ローカルで読む・編集する

リポジトリのルートで実行します。アプリ単体にはPython 3.10以上とmarimo 0.25.1だけが必要です。Torch・Wandas・データ取得は不要です。

```bash
python3 -m venv .venv-app
.venv-app/bin/python -m pip install marimo==0.25.1
.venv-app/bin/marimo run apps/02_b0_b1_w1_ss.py
# 編集する場合は run を edit に変更
```

## Pages用HTMLを更新する

トップページはアプリ一覧、各アプリは`apps/<slug>/`で配信します。トップの一覧から各アプリへ進めるほか、個別URLを直接共有できます。各アプリ上部の「アプリ一覧」から戻れます。

```bash
.venv-app/bin/python scripts/build_site.py --check
.venv-app/bin/python scripts/build_site.py --output outputs/site
```

[marimoの静的HTML export](https://docs.marimo.io/guides/exporting/static_html/)を使います。結果表は正本CSVから読み、PNGとPCM16音声はHTMLに埋め込みます。公開ページではPythonの再実行は行いません。音声はブラウザーの手動コントロールで再生します。表示用JavaScriptとCSSはmarimoのCDNから読み込むため、初回閲覧にはネット接続が必要です。WASM・Pyodideは使いません。

`assets/02`の図は、従来の第2回Notebookで実行済みの出力をバイト単位で保存したものです。機種別図は[正本CSV](../results/02-by-machine.csv)に対応します。旧NotebookはGitの履歴から取得できます。

コード・説明文は[MIT](../LICENSE)、実録音由来の図・音声は[帰属情報](../docs/DATA_ATTRIBUTION.md)の条件に従います。第三者の元LICENSE・NOTICEは保持しています。

## アプリを追加する

1. `apps/`にmarimoのPythonファイルを追加します。図・音声などの保存ファイルと必要な帰属情報も用意します。
2. [一覧設定](../configs/apps.json)に1件追加します。`slug`（公開URL）、`title`、`description`、`source`（Pythonファイル）、任意の`related_articles`（`label`と`url`）を指定します。関連記事は公開済みのものを登録します。公開後の`slug`は変えないでください。
3. 上のコマンドで一覧と全アプリを生成し、表示・リンク・手動再生を確認します。`--check`はslugの重複・不正な形式・アプリファイルの欠落を検出します。export中にセルエラーがあれば生成は失敗します。

公開は生成した`outputs/site`の内容を、既存の`gh-pages`ブランチのルートへ反映してpushします。Pythonソースやデータ取得先を配信用ブランチへ移す必要はありません。静的HTML export後に共通の戻るリンクを付けるため、アプリごとにサイト用ナビゲーションを実装する必要もありません。
