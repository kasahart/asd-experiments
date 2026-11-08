# 実験2：BEATs追加学習の再現

B0（近接ch）とW1（全区間の複素線形減算）を入力に、BEATs_iter3固定と正常12,000音でのLoRA追加学習を比較します。W1・BEATs・pooling・BEAMは`src/asd_min/`を共用し、学習は`runtime.py`が公開ASDKit（ASP、LoRA、SCAdaCos、Mixup、学習ループ）を無改変で呼び出します。

## 処理の流れ

`run.py --stage all`が次の順に実行し、`metrics.py`が公式評価器で採点します。

| 段階 | 処理 | 出力（`$OUT/`以下） |
|---|---|---|
| `prepare` | 公式2ch WAV → B0/W1 mono FLOAT WAV | `audio/<条件>/formatted/dcase2026/raw/` |
| `attributes` | 公開属性 → クラス番号用辞書 | `attribute_labels.json` |
| `teacher` | W1正常train → AP特徴 | `teacher/<機種>/train_extract.npz` |
| `labels` | 属性とAP特徴 → 共通116クラス | `train_labels.json`、`labels_receipt.json` |
| `train` | 正常trainと共通ラベル → 追加学習 | `results/asd03/dcase2026/<条件>/1234/model/all/checkpoints/last.ckpt` |
| `infer` | 固定／追加学習BEATs → RDP特徴 | `features/<モデル>/<条件>/<機種>/` |
| `score` | RDP特徴 → BEAM異常スコア | `scores/<モデル>/<条件>/<機種>.csv` |
| `metrics.py` | 公式評価器の出力 → 指標・総合値 | `metrics/{machine_metrics,summary}.csv` |

## 固定条件

- Development正常7,000音＋Additional training正常5,000音。各機種train 1,000、test 200。CLI条件名はB0が`raw`、W1が`w1_global`。
- 共通116クラス。属性を持つ6機種は属性・domain、残る6機種はW1の凍結BEATs周波数保持AP特徴でKMeans。sourceは7、targetは1、seed42。
- LoRA r64・q/k/v、ASP＋256次元分類射影、SCAdaCos 16subclusters、Mixup確率0.5、AdamW lr1e-4、warmup5,000step。
- batch8、10秒クロップ、25epoch／37,500step、seed1234。条件ごとに同じ初期モデルから学習。
- 推論は分類射影前の周波数保持特徴、時間方向RDP gamma4、BEAM-VarMin4（per-band・TrainAllは採用した再現仮定）。各条件・各機種1,000正常音から正常参照を再構築。

`attributes`はクラス番号を揃えるためだけにtestの公開属性・domainを参照します。学習には正常trainだけを使います。

## 実行する

環境は[実行環境](../../docs/setup.md)、取得先は[入力の取得](../../docs/02-inputs.md)のとおりです。`DEV`・`EVAL`はそこでの`dev_data/raw`・`eval_data/raw`です。`ground_truth_attributes/`は公式評価器に同梱されています。repoルートから実行し、出力先は新しいディレクトリにします。

```bash
PY=.venv/bin/python
DEV=inputs/dcase2026/dev_data/raw
EVAL=inputs/dcase2026/eval_data/raw
BASE=inputs/models/BEATs_iter3.pt
EVALUATOR=inputs/dcase2026/evaluator
OUT=$PWD/outputs/asd03

$PY reproduction/asd03/run.py --stage all \
  --development "$DEV" --evaluation "$EVAL" --checkpoint "$BASE" --output "$OUT" \
  --ground-truth-attributes "$EVALUATOR/ground_truth_attributes" --device cuda:0
$PY reproduction/asd03/metrics.py --run "$OUT" --evaluator "$EVALUATOR" --output "$OUT/metrics" --terms-reviewed
```

`--terms-reviewed`は評価器の利用条件を確認してから指定します。指標は[評価の共通条件](../../docs/evaluation.md)のとおりです。

- `--stage plan`は件数と合成後の設定を表示します。各段階は`--stage <段階名>`で単独実行できます。
- 生成済みのラベル・teacherは`--labels`・`--teacher-dir`、保存済みモデルは`--trained-root`で再利用でき、`--stage train --resume-training`で学習を再開します。
- 設定は`config/train/experiments/dis_beats_denoiser_comparison.yaml`を編集するか、`--set trainer.max_epochs=5`のように上書きします。
- `--smoke`は各機種16正常音＋4test音・2stepで全段階を通す動作確認です（`--labels`が必要）。
- その他のオプションは`--help`を参照してください。

## 確認範囲

掲載値（[結果の詳細](../../docs/results.md)）は周波数保持BEATsの同等構成で25epoch学習したcheckpointによるものです。この接続で確認したのはcheckpoint復元・特徴とスコアの一致・2step学習までで、25epochの独立再学習は未検証です。出典とライセンスは[第三者通知](../../THIRD_PARTY_NOTICES.md)にあります。
