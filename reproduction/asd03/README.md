# 第3回：BEATs追加学習の再現

B0（近接ch）とW1（全区間の複素線形減算）を入力に、BEATs_iter3固定と正常12,000音でのLoRA追加学習を比較します。学習には公開ASDKitの固定commitを仮想環境内へ自動取得し、周波数保持frontendなどの小さな接続を`runtime.py`に置いています。W1・BEATs・pooling・BEAMは既存の`src/asd_min/`を共用します。runnerは入出力と検査を担当します。

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
- 16kHz、2ch、近接→遠方の順。B0/W1をmono FLOAT WAVに変換。
- 共通116クラス。属性を持つ6機種は属性・domain、残る6機種はW1の凍結BEATs周波数保持AP特徴でKMeans。sourceは7、targetは1、seed42。
- LoRA r64・q/k/v、ASP＋256次元分類射影、SCAdaCos 16subclusters、Mixup確率0.5、AdamW lr1e-4、warmup5,000step。
- batch8、10秒クロップ、25epoch／37,500step、seed1234。条件ごとに同じ初期モデルから学習。
- 推論は分類射影前の周波数保持特徴、時間方向RDP gamma4、BEAM-VarMin4（per-band・TrainAllは採用した再現仮定）。各条件・各機種1,000正常音から正常参照を再構築。

データは[公式DCASE Task 2](https://dcase.community/challenge2026/task-first-shot-unsupervised-anomalous-sound-detection-for-machine-condition-monitoring)から取得します。ToyCarは4月8日修正版`dev_ToyCar_r2.zip`（MD5 `353201db217e25377a7e7eccf9c1c8a7`）を使い、`DEV/ToyCar`に配置します。公開属性対応と正解の取得先は下の「入力の取得と配置」に示します。音声・重み・個票・属性辞書・疑似ラベルJSONは同梱しません。

クラス番号を一貫して振るため、`attributes`はDevelopmentのtestファイル名とEvaluationの公式test属性対応表から属性・domain情報も参照します。正常/異常欄は分類キーに含めません。学習・teacher・クラスタリングは正常trainの波形と特徴だけを使い、test波形・test特徴・正常/異常ラベルを学習目的に用いません。trainのみから別の番号を振るとクラスの列順が変わるため、この手順と同じ学習結果を前提にできません。

## 入力の取得と配置

[Development](https://zenodo.org/records/19336329)、[Additional training](https://zenodo.org/records/20151556)、[Evaluation](https://zenodo.org/records/20437238)を配布元から取得します。Developmentの各機種`train/test`を`DEV`配下に、Additionalの`train`とEvaluationの`test`を同じ`EVAL`配下に配置します。どちらも`<ROOT>/<machine>/{train,test}/*.wav`の構成です。

重みは[BEATsのPre-Trained Model / Iter3](https://github.com/microsoft/unilm/blob/master/beats/README.md)から取得し、`BASE`に指定します。公式評価器は利用者が[公式評価器の固定版ZIP](https://github.com/nttcslab/dcase2026_task2_evaluator/archive/f6a94a2b5e614a9626c9d1ccff6df0705e6aaa75.zip)を別途展開し、そのディレクトリを`EVALUATOR`に指定します。下の例に合わせる場合は、展開先を`inputs/dcase2026/evaluator`に改名します。配布元のデータ・重み・評価器の利用条件（評価器の`LICENSE`と`LICENSEv2.1.pdf`を含む）を確認してください。これらの取得物はリポジトリへ追加しません。[既存の入力取得手順](../../docs/02-inputs.md)も参照できます。teacher特徴と116クラスJSONは下の手順で正常trainから生成します。

## 実行環境

リポジトリ共通の[実行環境](../../README.md#実行環境)から`training` extraと固定ASDKitを導入します。公式採点には同じ環境の`evaluation` extraを使います。依存版はrootの`pyproject.toml`、ASDKitのcommit・archive URL・SHA-256は`upstream.lock.json`、取得時にarchiveのSHA-256を確認します。実行時にコード・YAML・入力のSHA一致は要求しません。

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

順に前処理、属性番号、正常trainのteacher AP特徴、116クラスラベル、B0/W1学習、固定／追加学習モデル×B0/W1の4条件の特徴・スコアを作ります。ラベルは、選択した正常trainのパスを過不足なく含み、クラス番号が連続していることを確認します。

学習subprocessはPyTorch 2.7.1の既定の精度設定を明示します（float32行列積は`highest`、行列積TF32は無効、cuDNN TF32は許可）。teacher・推論では行列積とcuDNNのTF32を両方無効にします。

`all`と`score`の入口は、スコア計算の間だけBLASを1スレッドに固定します（`OPENBLAS_NUM_THREADS=1`相当）。保存スコアとの完全一致を確認した設定で、学習・ラベル生成には適用しません。

各段階は`--stage prepare|attributes|teacher|labels|train|infer|score`でも実行できます。単独の`train`・`infer`には、同じ出力先で先に`prepare`を済ませておきます。`train`・`infer`へ`--labels`を指定すると、正常trainのパスとクラス番号を検査して出力先へ配置します。既存の出力ラベルと異なる場合は停止します。`labels`単独実行には`--attribute-labels "$OUT/attribute_labels.json"`を追加します。既存teacherには`--teacher-dir`、生成済みラベルには`--labels`を使えます。teacherのAPと推論のRDPは別の処理です。新規ラベル生成にはW1音声が必要なので、`--conditions raw`だけで実行する場合は生成済みの`--labels`または`--teacher-dir`を指定します。

保存済みモデルの推論は`--trained-root`で`{raw,w1_global}/1234/model/all/checkpoints/last.ckpt`の親を指定します。設定したepoch数または最大step数を完了し、必要な訓練パラメータが揃ったモデルだけを評価します。

中断後にcheckpointから再開するときは`--stage train --resume-training`を明示します。最初のcheckpoint保存前に中断した場合は、未完了の`checkpoints`を`checkpoints.incomplete-N`へ退避して最初から学習します。checkpointがあればoptimizerとloopも復元しますが、途中epochからのデータ順序まで無中断実行と同一とは保証しません。

## 公式評価器による採点

評価器のコード・正解CSVは利用者が別途設置します。第2回と共通の[呼び出し接続](../../src/asd_min/evaluation.py)が公式スクリプトを無改変で実行します。AUC・pAUC・総合値は公式出力から取得し、表示単位を100倍へ変換します。機種スコアも公式の単機種集計を使います。

`score`は正常参照スコアの90%点を閾値として、第2回と共通の処理で判定CSVも生成します。これは公式評価器への入力です。Developmentの正解は公開testファイル名から公式形式のCSVに変換し、Evaluationは設置した評価器の正解を使います。評価用の作業ファイルと公式出力は`$OUT/metrics`以下に置き、設置先は書き換えません。`--terms-reviewed`は評価器の利用条件を確認した後に指定します。

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

この出力は記事のスコアではありません。`metrics.py`は200test/機種に満たない出力を拒否します。Developmentは21指標、Evaluationは15指標（source-mix AUC、target-mix AUC、mixed pAUC maxFPR0.1）の調和平均×100です。

## 確認結果

[全件集計](../../results/03-beats/README.md)を参照してください。掲載集計は周波数保持BEATsの同等構成で25epoch学習したcheckpointによる結果です。この外部ASDKit接続で確認した範囲はcheckpoint復元・特徴とスコアの一致・2step学習で、25epochの独立再学習は未検証です。

## 出典とライセンス

[原ASDKitの固定版](https://github.com/TakuyaFujimura/dcase-asd-toolkit/tree/7601d673ef2ed5a2424965cac755365cf7112c5f)を外部依存として取得し、MITの著作権・許諾通知は共通の[research-MIT.txt](../../licenses/research-MIT.txt)に保持しています。BEATsは[Microsoft原実装](https://github.com/microsoft/unilm/tree/master/beats)、MITを[LICENSE](../../src/asd_min/beats/LICENSE)、改変説明を[NOTICE](../../src/asd_min/beats/NOTICE.md)に保持しています。runner・集計・テスト・接続コードはroot MITです。元データ・重みは各配布元の条件に従います。
