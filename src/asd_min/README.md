# 今回の自前実装と、既存手法の対応

Notebookで見た4条件は、波形を選ぶ・加工する部分だけを変え、その後の検知器をそろえています。ここでは公開コードで実際に呼ばれる処理を説明します。BEATsはMicrosoftの既存モデル、RDP・BEAM・VarMinは論文由来の手法です。公開コードは、ASDKit由来の基盤にkasahartが追加した再実装・抽出拡張と、記事の比較に必要なDSP・実行処理を選んだものです。

## 処理の全体像と由来

```text
16 kHz 2ch録音 [2, samples]
  → B0/B1の選択、またはW1/SSの減算
  → 1ch波形 [samples]
  → 固定BEATsの特徴列 [1, L, D] とグリッド (T, F)
  → 時間×周波数の特徴 [1, T, F, D]
  → 周波数ごとに時間をRDPで集約 [1, F, D]
  → 条件・機種ごとの正常参照 [N, F, D] とBEAM/VarMinで比較
  → 録音1件の異常度（実装の main）
```

`T`は時間パッチ数、`F`は周波数パッチ数、`D`は特徴ベクトルの次元です。`F`はSTFTの1 Hzごとの成分ではなく、BEATsの入力の周波数方向のパッチ位置です。最終特徴はTransformerで文脈化されています。

| 処理 | 由来・今回の実装 | 公開コード |
|---|---|---|
| BEATs | Microsoftの既存モデル。kasahartが研究側でグリッド形状の返却を追加 | [BEATs.py](beats/BEATs.py)、[runner.py](runner.py) |
| RDP | 論文手法のkasahart追加実装。hash固定poolingを選択移植 | [pooling.py](pooling.py) |
| BEAM＋VarMin | 論文手法のkasahart追加再実装。詳細APIも含む | [beam.py](beam.py) |
| W1 | kasahart追加の複素LS研究実装から、必要関数を移植 | [waveform.py](waveform.py)の`w1()` |
| SS | Qian技術報告の式1を、この公開用コピーで実装 | [waveform.py](waveform.py)の`ss_spectrum()`と`ss()` |
| 条件比較の実行 | 記事用の新規companion。参照再構築・出力・入力確認を共通化 | [runner.py](runner.py)、[cli.py](cli.py) |

## モジュールの隣にある解説

| 解説 | 対応するコード | 読む内容 |
|---|---|---|
| [BEATs.md](beats/BEATs.md) | [BEATs.py](beats/BEATs.py) | 既存モデルとグリッド抽出API拡張の関係 |
| [pooling.md](pooling.md) | [pooling.py](pooling.py) | RDPの時間集約、重み式、γ=4 |
| [beam.md](beam.md) | [beam.py](beam.py) | 帯域別参照、VarMin、train_all/per_band |
| [waveform.md](waveform.md) | [waveform.py](waveform.py) | W1複素LS、SS式1、端処理とscale |
| [runner.md](runner.md) | [runner.py](runner.py)・[cli.py](cli.py) | 各条件の参照再構築、入出力と判定 |

## 出典

選択元のhashは[import-manifest.json](../../docs/import-manifest.json)、著作権表示とライセンスは[第三者通知](../../THIRD_PARTY_NOTICES.md)と[権利文書](../../docs/rights.md)にまとめています。BEAMは選択snapshotの詳細API拡張を含み、runnerは`anomaly_score()`の`main`を使います。
