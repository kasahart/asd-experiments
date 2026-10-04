# 第2回のmarimoアプリ

[ブラウザーで開く](https://kasahart.github.io/asd-experiments/)。保存結果・図・手動再生の音声を読むアプリです。生音声からの推論や保存異常度の再採点は[CLI](../src/asd_min/runner.md)で行います。

## ローカルで読む・編集する

リポジトリのルートで実行します。アプリ単体にはPython 3.10以上とmarimo 0.25.1だけが必要です。Torch・Wandas・データ取得は不要です。

```bash
python3 -m venv .venv-app
.venv-app/bin/python -m pip install marimo==0.25.1
.venv-app/bin/marimo run apps/02_b0_b1_w1_ss.py
# 編集する場合は run を edit に変更
```

## Pages用HTMLを更新する

```bash
mkdir -p outputs/site
.venv-app/bin/marimo export html --no-include-code apps/02_b0_b1_w1_ss.py -o outputs/site/index.html -f
```

[marimoの静的HTML export](https://docs.marimo.io/guides/exporting/static_html/)を使います。結果表は正本CSVから読み、PNGとPCM16音声はHTMLに埋め込みます。公開ページではPythonの再実行・UIからの再推論は行いません。音声はブラウザーの手動コントロールで再生します。表示用JavaScriptとCSSはmarimoのCDNから読み込むため、初回閲覧にはネット接続が必要です。WASM・Pyodideは使いません。

`assets/02`の図は、従来の第2回Notebookで実行済みの出力をバイト単位で保存したものです。実録音の図を再描画する手順は[波形処理](../src/asd_min/waveform.md)を参照してください。機種別図は[正本CSV](../results/02-by-machine.csv)に対応します。旧NotebookはGitの履歴から取得できます。

コード・説明文は[MIT](../LICENSE)、実録音由来の図・音声は[帰属情報](../docs/DATA_ATTRIBUTION.md)の条件に従います。第三者の元LICENSE・NOTICEは保持しています。
