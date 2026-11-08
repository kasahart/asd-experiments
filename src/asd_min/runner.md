# runner.py / cli.py — 条件比較の実行

**入出力：** 音声のルートディレクトリ、固定チェックポイント、出力先、条件、機種を受け取り、条件別の異常度・判定CSVと実行記録を生成します。

`run()`は各条件・機種で、波形処理→特徴抽出→正常参照構築→異常度出力を同じ順序で行います。重みのSHA-256と件数を確認し、既存出力は上書きしません。判定CSVの閾値（正常trainスコアの90%点）はAUC/pAUCに影響しません。

| 手順 | 関数（[`runner.py`](runner.py)） |
|---|---|
| 件数・ファイル名の確認 | `plan()` |
| 波形処理→BEATs→RDP | `extract_features()`（1録音は`Encoder.extract()`） |
| 正常参照の構築・採点・90%点の閾値 | `score_machine()` |
| 異常度・判定CSVと正常trainスコアの書き出し | `write_machine_outputs()` |
| 条件・機種の順に上の手順を実行し、実行記録を残す | `run()` |
| Developmentの採点（Dev7・Dev5） | [`development.py`](development.py)の`score_development()` |

固定値は[`protocol.py`](protocol.py)にあります。CLI（[`cli.py`](cli.py)）のサブコマンドは`results`（保存表の閲覧）、`infer`（生音声からの推論）、`score-dev`（Developmentの採点）、`evaluate`（公式評価器による採点）です。実行例は[実験1の固定条件](../../docs/02-protocol.md#実行する)にあります。
