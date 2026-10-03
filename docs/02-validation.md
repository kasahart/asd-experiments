# 第2回の検証範囲

全件再推論・評価器での再採点で、B0/B1/W1の主要指標が既存報告と一致しました。SSは新規に測定した結果です。異常度の差や実測時間・機器は以下の記録を参照してください。

| 記録 | 内容 |
|---|---|
| [3条件の比較](full-inference-comparison.json) | 入力一致、異常度比較、実測時間・機器 |
| [SS実験](ss-experiment.json) | 入力・設定・実測時間・採点 |
| [import-manifest](import-manifest.json) | 選択元とファイルhash |

W1の選択元との出力一致、SSの式・位相・scale・長さを確認しました。NotebookはWandas 0.8.0で全セルを実行し、表と合成図を確認しています。
