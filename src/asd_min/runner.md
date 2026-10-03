# runner.py / cli.py — 条件比較の実行

**入出力：** 音声のルートディレクトリ、固定チェックポイント、出力先、条件、機種を受け取り、条件別の異常度・判定CSVと実行記録を生成します。

## 共通runner — 条件の比較を同じ手順に保つ

`run()`は各条件・機種で、train/testの波形処理→特徴抽出→正常参照構築→異常度出力を同じ順序で行います。正常trainの再採点では同一pathの自己参照を除き、その異常度の90%点を閾値として、厳密に`score > threshold`なら異常判定を出します。閾値はAUC/pAUCの順位比較とは別の、判定CSVを作るための設定です。

BEATs重みのSHA-256、train/test件数と匿名テスト名を確認し、既存出力を上書きしません。入力hash・時間・正常trainスコア・閾値をローカルに記録します。Notebookの波形計算は同じ`condition_audio()`を呼び、Wandasは可視化と手動試聴を担います。


入力計画は`plan()`、特徴抽出は`Encoder.extract()`、全体実行は`run()`です。CLIの`results`は保存表の閲覧、`infer`は生音声からの再推論、`evaluate`は指定した固定版の評価器による保存異常度の採点です。

[公開コード：runner.py](runner.py) / [cli.py](cli.py) / [README](../../README.md)

## CLIを使う

以下は第2回の実行例です。

リポジトリのルートで、Python 3.12の環境を準備します。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install torch==2.7.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e '.[notebook]'
python -m asd_min.cli results
# Notebookを実行するには、別途JupyterLabまたはVS CodeのJupyter機能を使用。
# この.venvのPython kernelを選択する。
# Jupyterで notebooks/02_b0_b1_w1_ss.ipynb を開く（自動再生なし）
```

Notebookの既定実行は保存表と合成デモだけです。音声再生ボタンは `ENABLE_AUDIO=True` で生成し、手動で再生できます。実データの推論・再採点には、以下のCLIを使います。

```bash
# パスは取得先に置き換える。dry-runは件数確認で重みをロードしない。
python -m asd_min.cli infer --input /path/to/eval_data/raw \
  --checkpoint /path/to/BEATs_iter3.pt --output outputs/part02 --dry-run
# 1機種各5件のsmoke（記事スコアにはならない）
python -m asd_min.cli infer --input /path/to/eval_data/raw \
  --checkpoint /path/to/BEATs_iter3.pt --output outputs/smoke \
  --machine ToothBrush --limit 5 --device cpu
# 全5機種、各train1000/test200。4条件を明示。時間と資源を確認してから実行。
python -m asd_min.cli infer --input /path/to/eval_data/raw \
  --checkpoint /path/to/BEATs_iter3.pt --output outputs/part02 --conditions b0 b1 w1 ss --device cpu
```

`--limit`や`--machine`付きは動作確認用です。公式全5機種スコアの再採点には全件出力を使います。

```bash
# 配布元の利用条件を確認したら --terms-reviewed を指定します。
python -m asd_min.cli evaluate --system results/b0 \
  --evaluator /path/to/official-evaluator --output outputs/rescore-b0 --terms-reviewed
# b1、w1、ssも別の出力先で行う
```
