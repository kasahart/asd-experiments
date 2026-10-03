# 実装と既存手法の対応

Notebookで見た4条件は、波形を選ぶ・加工する部分だけを変え、その後の検知器をそろえています。ここでは公開コードで実際に呼ばれる処理を説明します。BEATsはMicrosoftの既存モデル、RDP・BEAM・VarMinは論文由来の手法です。公開コードは、ASDKit基盤と各手法の再実装・特徴抽出拡張、波形処理・実行処理で構成されています。

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

| 処理 | 由来・実装内容 | 公開コード |
|---|---|---|
| BEATs | 既存モデルの特徴列とグリッド形状を取得 | [BEATs.py](beats/BEATs.py)、[runner.py](runner.py) |
| RDP | [NA-SSL論文](https://arxiv.org/html/2608.00447v1)を参考にした時間集約 | [pooling.py](pooling.py) |
| BEAM＋VarMin | [BEAM論文](https://arxiv.org/html/2603.13749)・[VarMin論文](https://dcase.community/documents/workshop2025/proceedings/DCASE2025Workshop_Matsumoto_12.pdf)を参考にした参照比較と補正 | [beam.py](beam.py) |
| W1 | 録音全体の複素最小二乗で共通音を減算 | [waveform.py](waveform.py)の`w1()` |
| SS | Chu・Qian技術報告の式1による大きさの減算 | [waveform.py](waveform.py)の`ss_spectrum()`と`ss()` |
| 条件比較の実行 | 参照再構築・出力・入力確認を共通化 | [runner.py](runner.py)、[cli.py](cli.py) |

## モジュールの隣にある解説

| 解説 | 対応するコード | 読む内容 |
|---|---|---|
| [BEATs.md](beats/BEATs.md) | [BEATs.py](beats/BEATs.py) | 既存モデルとグリッド抽出API拡張の関係 |
| [pooling.md](pooling.md) | [pooling.py](pooling.py) | RDPの時間集約、重み式、γ=4 |
| [beam.md](beam.md) | [beam.py](beam.py) | 帯域別参照、VarMin、train_all/per_band |
| [waveform.md](waveform.md) | [waveform.py](waveform.py) | W1複素LS、SS式1、端処理とscale |
| [runner.md](runner.md) | [runner.py](runner.py)・[cli.py](cli.py) | 各条件の参照再構築、入出力と判定 |

## 出典

選択元のhashは[import-manifest](../../docs/import-manifest.json)、著作権表示とライセンスは[第三者通知](../../THIRD_PARTY_NOTICES.md)と[出典と利用条件](../../docs/rights.md)にまとめています。runnerは`anomaly_score()`の`main`を使います。
