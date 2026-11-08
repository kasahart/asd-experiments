# 実験2：BEATs追加学習の再現

B0（近接ch）とW1（全区間の複素線形減算）を入力に、BEATs_iter3固定と正常12,000音でのLoRA追加学習を比較します。W1・BEATs・pooling・BEAMは`src/asd_min/`を共用します。

## 処理の流れ

`run.py --stage all`が次の順に実行し、最後に`metrics.py`が利用者の設置した公式評価器を呼び出して評価します。

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

`runtime.py`は外部ASDKitの学習コードを呼び出し、DCASE2026・周波数保持特徴・FLOAT音声・checkpoint保存と復元を接続します。ASP、LoRA、SCAdaCos、Mixup、学習ループは公開ASDKitを使います。取得先のコードは書き換えません。

## 入力と固定条件

- Development正常7,000音＋Additional training正常5,000音。各機種train 1,000、test 200。
- CLI条件名はB0が`raw`、W1が`w1_global`です。
- 共通116クラス。属性を持つ6機種は属性・domain、残る6機種はW1の凍結BEATs周波数保持AP特徴でKMeans。sourceは7、targetは1、seed42。
- LoRA r64・q/k/v、ASP＋256次元分類射影、SCAdaCos 16subclusters、Mixup確率0.5、AdamW lr1e-4、warmup5,000step。
- batch8、10秒クロップ、25epoch／37,500step、seed1234。条件ごとに同じ初期モデルから学習。
- 推論は分類射影前の周波数保持特徴、時間方向RDP gamma4、BEAM-VarMin4（per-band・TrainAllは採用した再現仮定）。各条件・各機種1,000正常音から正常参照を再構築。

クラス番号を一貫して振るため、`attributes`はDevelopmentのtestファイル名とEvaluationの公式test属性対応表から属性・domain情報も参照します。正常/異常欄は分類キーに含めません。学習・teacher・クラスタリングは正常trainの波形と特徴だけを使い、test波形・test特徴・正常/異常ラベルを学習目的に用いません。

## 入力の取得と配置

取得先とchecksumは[入力の取得](../../docs/02-inputs.md)にあります。音声・重み・個票・ラベルJSONは同梱しません。配置は次のとおりです。

- Developmentの各機種`train/test`を`DEV`配下に、Additional trainingの`train`とEvaluationの`test`を同じ`EVAL`配下に置きます。どちらも`<ROOT>/<machine>/{train,test}/*.wav`の構成です。
- 重み（BEATs_iter3）を`BASE`に、展開した公式評価器のディレクトリを`EVALUATOR`に指定します。下の例に合わせる場合は、評価器の展開先を`inputs/dcase2026/evaluator`に改名します。
- Evaluationの公開属性対応（`ground_truth_attributes/`）と正解CSVは、公式評価器に同梱されています。別途の取得は不要です。

teacher特徴と116クラスJSONは下の手順で正常trainから生成します。

## 実行環境

環境の作り方は[実行環境](../../docs/setup.md)にあります。学習には`training` extraと固定ASDKit（`runtime.py install`）、公式採点には`evaluation` extraを使います。ASDKitのcommit・archive URL・SHA-256は`upstream.lock.json`で固定し、取得時にarchiveのSHA-256を確認します。実行時にコード・YAML・入力のSHA一致は要求しません。

repoルートから実行します。`inputs/...`は手元の取得先に置き換え、出力先は入力データの外にある新しいディレクトリにします。

```bash
PY=.venv/bin/python
DEV=inputs/dcase2026/dev_data/raw
EVAL=inputs/dcase2026/eval_data/raw
BASE=inputs/models/BEATs_iter3.pt
EVALUATOR=inputs/dcase2026/evaluator
OUT=$PWD/outputs/asd03
```

## ラベル生成から全件評価まで

```bash
$PY reproduction/asd03/run.py --stage plan --development "$DEV" --evaluation "$EVAL" --checkpoint "$BASE" --output "$OUT"
$PY reproduction/asd03/run.py --stage all \
  --development "$DEV" --evaluation "$EVAL" --checkpoint "$BASE" --output "$OUT" \
  --ground-truth-attributes "$EVALUATOR/ground_truth_attributes" --device cuda:0
$PY reproduction/asd03/metrics.py --run "$OUT" --evaluator "$EVALUATOR" --output "$OUT/metrics" --terms-reviewed
```

学習subprocessはPyTorch 2.7.1の既定の精度設定を明示します（float32行列積は`highest`、行列積TF32は無効、cuDNN TF32は許可）。teacher・推論では行列積とcuDNNのTF32を両方無効にします。

`all`と`score`の入口は、スコア計算の間だけBLASを1スレッドに固定します（`OPENBLAS_NUM_THREADS=1`相当）。保存スコアとの完全一致を確認した設定で、学習・ラベル生成には適用しません。

部分実行と再開：

- 各段階は`--stage <段階名>`で単独実行できます。`train`・`infer`の前には同じ出力先で`prepare`を済ませます。
- 生成済みのラベル・teacherは`--labels`・`--teacher-dir`で再利用できます（`--conditions raw`だけで実行する場合は必須）。
- 保存済みモデルの推論は`--trained-root`、中断した学習の再開は`--stage train --resume-training`です。その他は`--help`を参照してください。

`metrics.py`は[実験1と共通の接続](../../src/asd_min/evaluation.py)で公式評価器を無改変で実行し、公式出力を100倍して保存します。`--terms-reviewed`は評価器の利用条件を確認した後に指定します。指標の定義は[固定条件](../../docs/02-protocol.md#評価指標)を参照してください。

## 設定を変えて試す

学習設定の入口は`config/train/experiments/dis_beats_denoiser_comparison.yaml`です。YAMLを編集するか、`--set trainer.max_epochs=5 --set datamodule.batch_size=4 --set seed=5678`のように値を上書きします。`--set`は複数指定でき、学習と推論には同じ指定を使います。別の設定ディレクトリは`--config-dir`で選べます。`--stage plan`は合成後の設定を表示します。

重みは互換性のあるBEATs checkpoint、ラベルは選択した正常trainに対応するJSONを指定できます。入力件数やクラス数は固定しません。実際の学習設定は`<条件>_training_config.yaml`に保存し、checkpointに学習完了条件を記録します。出力先は実験ごとに新しく指定してください。標準設定と異なる実験は掲載値との同一条件比較にはなりません。`metrics.py`の全件集計には、引き続き公式200test/機種が必要です。

## 小規模の動作確認

先に`prepare`から`labels`まで実行して得た116クラスJSONを使い、各機種16正常音＋4test音、2step学習で保存・復元・推論・スコア算出を通します。学習入力は全12機種の192正常音で、2stepに消費するのは16音/条件です。`--machines ToothBrush`は推論・スコア算出の対象指定です。

```bash
$PY reproduction/asd03/run.py --stage all --smoke \
  --development "$DEV" --evaluation "$EVAL" --checkpoint "$BASE" \
  --labels "$OUT/train_labels.json" --output "$PWD/outputs/asd03-smoke" \
  --machines ToothBrush --device cuda:0
```

この出力は記事のスコアではありません。`metrics.py`は200test/機種に満たない出力を拒否します。

## 確認結果

集計値は[結果の詳細](../../docs/results.md)、CSVの説明は[実験2の結果CSV](../../results/03-beats/README.md)を参照してください。掲載集計は周波数保持BEATsの同等構成で25epoch学習したcheckpointによる結果です。この外部ASDKit接続で確認した範囲はcheckpoint復元・特徴とスコアの一致・2step学習で、25epochの独立再学習は未検証です。

## 出典とライセンス

ASDKit・BEATs・この再現コードの出典とライセンスは[第三者通知](../../THIRD_PARTY_NOTICES.md#実験2追加学習の再現)にまとめています。
