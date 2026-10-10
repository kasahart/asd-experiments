# runner.py / cli.py — 条件比較の実行

**入出力：** 音声のルートディレクトリ、固定チェックポイント、出力先、条件、機種を受け取り、条件別の異常度・判定CSVと実行記録を生成します。

## 共通runner — 条件の比較を同じ手順に保つ

`run()`は各条件・機種で、train/testの波形処理→特徴抽出→正常参照構築→異常度出力を同じ順序で行います。正常trainの再採点では同一pathの自己参照を除き、その異常度の90%点を閾値として、厳密に`score > threshold`なら異常判定を出します。閾値はAUC/pAUCの順位比較とは別の、判定CSVを作るための設定です。

BEATs重みのSHA-256、train/test件数と匿名テスト名を確認し、既存出力を上書きしません。時間・正常trainスコア・閾値をローカルに記録します。実録音の再描画も同じ`condition_audio()`を呼び、Wandasで図を作ります。


| 手順 | 関数（[`runner.py`](runner.py)） |
|---|---|
| 件数・ファイル名の確認 | `plan()` |
| 波形処理→BEATs→RDP | `extract_features()`（1録音は`Encoder.extract()`） |
| 正常参照の構築・採点・90%点の閾値 | `score_machine()` |
| 異常度・判定CSVと正常trainスコアの書き出し | `write_machine_outputs()` |
| 条件・機種の順に上の手順を実行し、実行記録を残す | `run()` |
| Developmentの採点（Dev7・Dev5） | [`development.py`](development.py)の`score_development()` |

条件名・機種・件数・RDPの`gamma`・VarMinの近傍数・閾値の分位点・重みのSHA-256は[`protocol.py`](protocol.py)にまとめています。CLIの`results`は保存表の閲覧、`infer`は生音声からの再推論、`evaluate`は指定した固定版の評価器による保存異常度の採点です。

[公開コード：runner.py](runner.py) / [cli.py](cli.py) / [README](../../README.md)

## CLIを使う

以下は第2回の実行例です。

リポジトリのルートで、Python 3.12の環境を準備します。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install torch==2.7.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e .
python -m asd_min.cli results
```

保存結果・実録音の比較・手動試聴は[marimoアプリ](../../apps/README.md)で提供します。実データの推論・再採点には、以下のCLIを使います。

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

構成の選択にはDevelopment 7機種を使います。`--dataset dev`で同じ手順を実行し、`score-dev`でDev7とDev5を求めます。Developmentの採点に評価器は使いません。

```bash
python -m asd_min.cli infer --dataset dev --input /path/to/dev_data/raw \
  --checkpoint /path/to/BEATs_iter3.pt --output outputs/part02-dev --conditions b0 b1 w1 ss --device cpu
python -m asd_min.cli score-dev --system outputs/part02-dev/b0 --output outputs/part02-dev/b0-scores.csv
```

`--limit`や`--machine`付きは動作確認用です。公式全5機種スコアの再採点には全件出力を使います。

```bash
# 配布元の利用条件を確認したら --terms-reviewed を指定します。
python -m asd_min.cli evaluate --system results/b0 \
  --evaluator /path/to/official-evaluator --output outputs/rescore-b0 --terms-reviewed
# b1、w1、ssも別の出力先で行う
```
