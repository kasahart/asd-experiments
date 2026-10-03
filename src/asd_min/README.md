# 今回の自前実装と、既存手法の対応

Notebookで見た4条件は、波形を選ぶ・加工する部分だけを変え、その後の検知器をそろえています。ここでは公開コードで実際に呼ばれる処理を説明します。**自前で実装したことと、手法そのものを新しく提案したことは分けます。** BEATsはMicrosoftの既存モデル、RDP・BEAM・VarMinは論文由来の手法です。公開コードは、それらの研究再実装・抽出拡張と、記事の比較に必要なDSP・実行処理を選んだものです。

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

`T`は時間パッチ数、`F`は周波数パッチ数、`D`は特徴ベクトルの次元です。`F`はSTFTの1 Hzごとの成分ではなく、BEATsの入力の周波数方向のパッチ位置です。最終特徴はTransformerで文脈化されているため、特定の位置の特徴を、その位置の音だけに反応する値とは扱いません。

| 処理 | 由来・今回の実装 | 公開コード |
|---|---|---|
| BEATs | Microsoftの既存モデル。研究側がグリッド形状の返却を追加 | [BEATs.py](beats/BEATs.py)、[runner.py](runner.py) |
| RDP | 論文手法の研究実装。beam-tf-attributionのpoolingを選択移植 | [pooling.py](pooling.py) |
| BEAM＋VarMin | 論文手法の研究再実装。参照・補正係数などを返す詳細APIも含む | [beam.py](beam.py) |
| W1 | 既存の複素最小二乗に基づく研究実装から、必要関数を移植 | [waveform.py](waveform.py)の`w1()` |
| SS | Qian技術報告の式1を、この公開用コピーで実装 | [waveform.py](waveform.py)の`ss_spectrum()`と`ss()` |
| 条件比較の実行 | 記事用の新規companion。参照再構築・出力・入力確認を共通化 | [runner.py](runner.py)、[cli.py](cli.py) |

## モジュールの隣にある解説

| 解説 | 対応するコード | 読む内容 |
|---|---|---|
| [BEATs.md](beats/BEATs.md) | [BEATs.py](beats/BEATs.py) | 既存モデルとグリッド抽出API拡張の区別 |
| [pooling.md](pooling.md) | [pooling.py](pooling.py) | RDPの時間集約、重み式、γ=4 |
| [beam.md](beam.md) | [beam.py](beam.py) | 帯域別参照、VarMin、train_all/per_band |
| [waveform.md](waveform.md) | [waveform.py](waveform.py) | W1複素LS、SS式1、端処理とscale |
| [runner.md](runner.md) | [runner.py](runner.py)・[cli.py](cli.py) | 各条件の参照再構築、入出力と判定 |

## 出典をどこまで確認したか

2026-10-03にユーザー指定の[dcase-asd-toolkit-research](https://github.com/kasahart/dcase-asd-toolkit-research)と[beam-tf-attribution](https://github.com/kasahart/beam-tf-attribution)のREADME・使用部分の実装・MIT表示を認証readで確認しました。両repoはその時点でprivateです。読者がアクセスできなくても、上の説明とこのrepoの公開コードで計算を確認できます。無関係な研究資料・実験結果は転載していません。

- 研究側の説明：[beam_rdp_varmin.md（固定revision）](https://github.com/kasahart/dcase-asd-toolkit-research/blob/122e56afbf4a21f3803b223e13d0b8bff4de55ea/docs/methods/beam_rdp_varmin.md)。最新mainでも当該説明を確認しました。
- RDP：[pooling.py（確認時revision）](https://github.com/kasahart/beam-tf-attribution/blob/cc5e941a3cc3c8fed01d50b85e0b925c69b14499/src/beam_tfattr/pooling.py)。公開コピーとbyte-identicalでした。この一致は寄与マップの利用を意味しません。
- BEATsのgrid拡張とW1の選択元は研究固定revisionと一致。BEAMの公開コピーは記事原本に保存されたhash固定snapshotと一致しますが、研究の固定Git revisionそのものとはbyte-identicalではなく、参照index・参照embedding・係数などを返す詳細APIの拡張があります。今回runnerは`anomaly_score()`の`main`を使い、寄与マップは生成しません。

各ファイルのhashは[import-manifest.json](../../docs/import-manifest.json)、権利の区分は[rights.md](../../docs/rights.md)と[第三者通知](../../THIRD_PARTY_NOTICES.md)を参照してください。手法の由来、実装の著作権、重みやデータの条件は別々です。今回の説明追加で、コード・固定条件・保存成績は変更していません。
