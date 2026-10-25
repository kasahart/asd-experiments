# 第3回：BEATs追加学習の結果

`summary.csv`（8総合値）、`machine_metrics.csv`（48機種条件）が数値の正本です。固定／追加学習モデル×B0/W1を比較し、Development7機種とEvaluation5機種を別集計します。各総合値はsource-mix AUC・target-mix AUC・mixed pAUCの調和平均×100です。指標と機種・集合の総合値は、[公式評価器の固定版](https://github.com/nttcslab/dcase2026_task2_evaluator/tree/f6a94a2b5e614a9626c9d1ccff6df0705e6aaa75)の出力を100倍して保存しています。

学習条件は正常12,000音、共通116クラス、25epoch・37,500step、seed1234です。詳細と入力取得手順は[再現コードの説明](../../reproduction/asd03/README.md)を参照してください。音声・重み・個票・疑似ラベルJSONは同梱していません。

| 集合 | 入力 | 固定BEATs | 追加学習BEATs |
|---|---|---:|---:|
| Development | B0 | 61.325 | 63.048 |
| Evaluation | B0 | 62.841 | 67.916 |
| Development | W1 | 67.480 | 69.528 |
| Evaluation | W1 | 66.835 | 70.659 |

表示は小数第3位に丸め、集計CSVには丸め前の値を保持します。

スコア計算はBLAS1スレッドに固定します。並列数を変えるとfloat32の微小差によって近接スコアの順位とAUCが変わる場合があります。正常trainだけを学習に使いますが、クラス番号の整列には公開testファイル名の属性・domain情報も参照します。
