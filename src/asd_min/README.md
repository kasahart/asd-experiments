# 実装案内

処理の解説は対応するコードと同じ階層に置いています。各解説には、式とそれを計算する関数の対応表があります。手法ごとの結果・固定条件・marimoアプリは[READMEの手法表](../../README.md#手法)を参照してください。

| 処理 | 解説 | コード |
|---|---|---|
| BEATs特徴抽出 | [BEATs.md](beats/BEATs.md) | [BEATs.py](beats/BEATs.py) |
| RDP時間集約 | [pooling.md](pooling.md) | [pooling.py](pooling.py) |
| BEAM＋VarMin採点 | [beam.md](beam.md) | [beam.py](beam.py)・[varmin.py](varmin.py)・[band_distance.py](band_distance.py) |
| 波形処理 | [waveform.md](waveform.md) | [waveform.py](waveform.py) |
| 条件比較の実行 | [runner.md](runner.md) | [runner.py](runner.py)・[cli.py](cli.py) |
| 固定条件の値 | [02-protocol.md](../../docs/02-protocol.md) | [protocol.py](protocol.py) |

出典は[第三者通知](../../THIRD_PARTY_NOTICES.md)を参照してください。
