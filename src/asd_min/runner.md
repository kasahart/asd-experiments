# runner.py / cli.py — 条件比較の実行

**入出力：** 音声のルートディレクトリ、固定チェックポイント、出力先、条件、機種を受け取り、条件別の異常度・判定CSVと実行記録を生成します。

## 共通runner — 条件の比較を同じ手順に保つ

`run()`は各条件・機種で、train/testの波形処理→特徴抽出→正常参照構築→異常度出力を同じ順序で行います。判定CSVの閾値（正常trainスコアの90%点）は[固定条件](../../docs/02-protocol.md)のとおりで、AUC/pAUCには影響しません。

BEATs重みのSHA-256、train/test件数と匿名テスト名を確認し、既存出力を上書きしません。時間・正常trainスコア・閾値をローカルに記録します。

| 手順 | 関数（[`runner.py`](runner.py)） |
|---|---|
| 件数・ファイル名の確認 | `plan()` |
| 波形処理→BEATs→RDP | `extract_features()`（1録音は`Encoder.extract()`） |
| 正常参照の構築・採点・90%点の閾値 | `score_machine()` |
| 異常度・判定CSVと正常trainスコアの書き出し | `write_machine_outputs()` |
| 条件・機種の順に上の手順を実行し、実行記録を残す | `run()` |
| Developmentの採点（Dev7・Dev5） | [`development.py`](development.py)の`score_development()` |

条件名・機種・件数・RDPの`gamma`・VarMinの近傍数・閾値の分位点・重みのSHA-256は[`protocol.py`](protocol.py)にまとめています。

[公開コード：runner.py](runner.py) / [cli.py](cli.py) / [固定条件](../../docs/02-protocol.md)

## CLIを使う

以下は実験1の実行例です。環境は[実行環境](../../docs/setup.md)のとおり作り（推論だけなら`pip install -e .`で足ります）、入力は[入力の取得](../../docs/02-inputs.md)のとおり取得・配置します。サブコマンドは`results`（保存表の閲覧）、`infer`（生音声からの再推論）、`score-dev`（Developmentの採点）、`evaluate`（公式評価器による採点）です。保存結果の閲覧と試聴は[marimoアプリ](../../apps/README.md)でもできます。

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
