# 実験1の固定条件

Evaluationの5機種。正常参照はAdditional Trainingの各1000正常音（source990/target10）。匿名Evaluationの各200テスト音を採点（[評価の共通条件](evaluation.md)）。

- ch0=near、ch1=far、16 kHzの同期2chを維持。B0=ch0/B1=ch1/W1=同じ2chからの残差。
- frozen **BEATs_iter3**、FP32、AMPなし、TF32なし。音声全体をbatch1で特徴抽出。周波数パッチを保持し、時間方向のRDP gamma=4、eps=1e-8。
- BEAM VarMin4、scaled cosine $`\tfrac{1}{2}(1-\cos)`$、正常train_all参照、密度は自身を除く近傍4件、alphaはtrain_allのleave-one-outで周波数別に推定。補正後に参照最小値、周波数の一様平均。条件ごとに参照を新規構築。
- 正常train再採点でも自身を除外。条件・機種ごとの正常trainスコア90%点（linear）、判定は厳密な `score > threshold`。
- W1: 共同peakを0.9へ正規化（peak<=1e-12ならscale1）、float32。TorchHann periodic、STFT1024/window1024/hop512、center=True、reflect、normalized=False、onesided=True。係数は録音の端も含めた全フレームで推定（式は[W1の解説](../src/asd_min/waveform.md)）。同じ窓でISTFT、元の長さ・共同scaleを復元。

## 追加条件SS

beta1、gamma0.1、近接位相で復元（式は[SSの解説](../src/asd_min/waveform.md#ss--調整係数を求めず成分の大きさを引く)）。Hann512/hop256。periodic Hann・center=True・reflect・入力正規化なしは、報告が未指定の詳細を固定したローカル選択です。[SS config](../configs/02_ss.json)。

## 実行する

Developmentでも同じ手順で推論し、`score-dev`で採点します。環境は[実行環境](setup.md)（推論だけなら`pip install -e .`）、入力は[入力の取得](02-inputs.md)のとおりです。パスは取得先に置き換えます。

```bash
# 件数だけ確認（重みは読まない）。--machine ToothBrush --limit 5 で小規模に試せます
python -m asd_min.cli infer --input /path/to/eval_data/raw \
  --checkpoint /path/to/BEATs_iter3.pt --output outputs/part02 --dry-run
# Evaluation全件・4条件
python -m asd_min.cli infer --input /path/to/eval_data/raw \
  --checkpoint /path/to/BEATs_iter3.pt --output outputs/part02 --conditions b0 b1 w1 ss --device cpu
# Development（構成の選択）
python -m asd_min.cli infer --dataset dev --input /path/to/dev_data/raw \
  --checkpoint /path/to/BEATs_iter3.pt --output outputs/part02-dev --conditions b0 b1 w1 ss --device cpu
python -m asd_min.cli score-dev --system outputs/part02-dev/b0 --output outputs/part02-dev/b0-scores.csv
# 保存異常度を公式評価器で採点（利用条件を確認してから --terms-reviewed）
python -m asd_min.cli evaluate --system results/b0 \
  --evaluator /path/to/official-evaluator --output outputs/rescore-b0 --terms-reviewed
```
