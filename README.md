# ASD experiments — Zenn連載の実験入口

[第1回](https://zenn.dev/kasahart/articles/kasahart-20260919-dcase2026-asd-01)と[第2回草稿 PR #9](https://github.com/kasahart/zenn/pull/9)の読者向けの実験コードです。今回の対象は B0（近接）、B1（遠方）、W1（複素線形減算）、SS（式1のスペクトル減算）です。

| やりたいこと | 入口 | 必要なもの |
|---|---|---|
| 保存結果を読む | `python -m asd_min.cli results` / Notebookの表 | 音声・重み不要 |
| 合成音で可視化・手動試聴 | [Notebook](notebooks/02_b0_b1_w1_ss.ipynb) | Wandas 0.8.0、CPU |
| 保存異常度を公式再採点 | `evaluate`、[権利条件](docs/rights.md) | 読者取得のevaluator・正解、使用条件の確認が前提 |
| 生音声から再推論 | `infer`、[入力取得](docs/inputs.md) | 公式音声とBEATs_iter3を読者が取得 |

記事の既存報告は **B0 62.841 / B1 58.362 / W1 66.835**。これらは元の既存報告値です。このコピーの全件GPU再推論では保存異常度と最大差4.85e-8、順位・判定一致を確認し、固定公式evaluatorのローカル再採点でも主要指標が一致しました。今回新たに測定した **SSは62.325（B0比−0.516ポイント）** で、総合改善はありません。[4条件の保存表](results/summary-with-ss.csv)と[SS実験記録](docs/ss-validation.md)を参照してください。外部の独立追試とは主張しません。

## 環境と最初の実行

Linux / Python 3.12 CPUで小規模検証しました。以下をコピーのルートで実行します。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install torch==2.7.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e '.[notebook]'
python -m asd_min.cli results
# Jupyterで notebooks/02_b0_b1_w1_ss.ipynb を開く（自動再生なし）
```

Notebookの既定実行は保存表と合成デモだけです。音声再生ボタンは `ENABLE_AUDIO=True` で生成し、読者が手動で押します。実データ・推論・採点は別セルで明示的に有効化します。

```bash
# パスは読者の取得先へ置き換える。dry-runは件数確認で重みをロードしない。
python -m asd_min.cli infer --input /path/to/eval_data/raw \
  --checkpoint /path/to/BEATs_iter3.pt --output outputs/part02 --dry-run
# 1機種各5件のsmoke（記事スコアにはならない）
python -m asd_min.cli infer --input /path/to/eval_data/raw \
  --checkpoint /path/to/BEATs_iter3.pt --output outputs/smoke \
  --machine ToothBrush --limit 5 --device cpu
# 全5機種、各train1000/test200。4条件を明示。時間と資源を確認してから実行。
python -m asd_min.cli infer --input /path/to/eval_data/raw \
  --checkpoint /path/to/BEATs_iter3.pt --output outputs/part02 --conditions b0 b1 w1 ss --device cpu
```

`infer`は条件別に正常参照を再構築し、匿名テスト名を保持した公式形式CSVを作ります。生音声や処理済み音声を保存しません。正常trainスコアと90%点閾値、入力SHA-256、実測時間をローカル出力に保存します。既存出力は上書きしません。`--limit`や`--machine`付き出力は公式全5機種スコアとして再採点できません。

```bash
# 使用条件を自分で確認・解決した読者のみ。flagは許諾や契約同意を取得する機能ではない。
python -m asd_min.cli evaluate --system results/b0 \
  --evaluator /path/to/official-evaluator --output outputs/rescore-b0 --terms-reviewed
# b1、w1、ssも別の出力先で行う
```

[固定条件](docs/protocol.md)、[出典・権利](docs/rights.md)、[検証範囲](VALIDATION.md)を参照してください。採点ライブラリの独立環境依存はevaluator公式案内に従って確認してください。取得経路があることだけで利用条件が解決したとは扱いません。

```text
src/asd_min/        CLIとNotebookが共有する最小計算核
notebooks/         各回の入口（今回は02のみ）
results/           B0/B1/W1の既存報告、SS新規結果と保存異常度
licenses/          選択して移した第三者コードの条件
docs/             取得・固定条件・出典（研究原本や私的履歴なし）
```

新規CLI・Notebook・説明文は[MIT](LICENSE)（Copyright 2026 kasahart）です。第三者部分は元の著作権表示・MIT/NOTICEを保持しています。音声データ・checkpoint・evaluator・正解の利用条件はroot MITの対象に含めません。Dis-BEATs、DNN、ensemble、UI、全5回原本、公式evaluator、正解CSV、音声、重みは同梱しません。

SSの固定条件・検証範囲は[SS検証記録](docs/ss-validation.md)と[config](configs/02_ss.json)へ。SS全5機種6000音の抽出・採点はRTX PRO6000で94.94秒でした（checkpoint初期化・入力hash確認を除く）。読者環境の所要時間や最低機器要件を保証する値ではありません。BEATs公式project MITに沿ったローカル推論と、checkpoint再配布の確認は区別します。
