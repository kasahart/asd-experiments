# 実装案内

処理の解説は対応するコードと同じ階層に置いています。手法ごとの結果・固定条件・Notebookは[READMEの手法表](../../README.md#手法)を参照してください。

| 処理 | 解説 | コード |
|---|---|---|
| BEATs特徴抽出 | [BEATs.md](beats/BEATs.md) | [BEATs.py](beats/BEATs.py) |
| RDP時間集約 | [pooling.md](pooling.md) | [pooling.py](pooling.py) |
| BEAM＋VarMin採点 | [beam.md](beam.md) | [beam.py](beam.py) |
| 波形処理 | [waveform.md](waveform.md) | [waveform.py](waveform.py) |
| 条件比較の実行 | [runner.md](runner.md) | [runner.py](runner.py)・[cli.py](cli.py) |

出典は[第三者通知](../../THIRD_PARTY_NOTICES.md)、ファイルhashは[import-manifest](../../docs/import-manifest.json)を参照してください。
