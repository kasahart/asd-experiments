# ASD experiments — Zenn連載の実験入口

Zennの異常音検知（ASD）連載に対応する実験コードとNotebookです。手法・結果・解説を以下の表から参照できます。

<!-- experiments:start -->

## 手法

### DCASE 2026 Evaluation / BEATs_iter3

[Notebook](notebooks/02_b0_b1_w1_ss.ipynb)

| 手法 | 特徴 | 参考文献 |
|---|---|---|
| B0 | 近接マイク | — |
| B1 | 遠方マイク | — |
| W1 | 振幅と位相を合わせて減算 | [Ozeki技術報告](https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Ozeki_101_t2.pdf)（同形の減算） |
| SS | 振幅スペクトル減算 | [Chu・Qian技術報告](https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Qian_65_t2.pdf)（式1） |

## スコア

総合スコアは高いほど良く、本実験の手法はスコア順に並べています。

### DCASE 2026 Evaluation / BEATs_iter3

[固定条件](docs/02-protocol.md) · [入力取得](docs/02-inputs.md) · [総合値](results/02-summary.csv)

![DCASE 2026 Evaluation / BEATs_iter3。本実験: W1（振幅と位相を合わせて減算）66.835、B0（近接マイク）62.841、SS（振幅スペクトル減算）62.325、B1（遠方マイク）58.362。公式ベースライン・参考システム: DCASE2026_baseline_task2_MSE（公式ベースライン）59.803、Fujimura_MERL_task2_3（一部処理の参考元）70.241。下段は大会で報告された公式ベースラインと参考システムの値です。Fujimura_MERL_task2_3はNA-BEATsを使います。本実験はBEATs_iter3を使い、同システムのRDPなど一部の処理を参考にしています（NA-BEATs未使用）。](figures/scores-ec7ab031e849.svg)

下段は大会で報告された公式ベースラインと参考システムの値です。Fujimura_MERL_task2_3はNA-BEATsを使います。本実験はBEATs_iter3を使い、同システムのRDPなど一部の処理を参考にしています（NA-BEATs未使用）。

出典: [DCASE 2026 Task 2 Results](https://dcase.community/challenge2026/task-first-shot-unsupervised-anomalous-sound-detection-for-machine-condition-monitoring-results) · [システム名・参考値](results/02-challenge-references.json)
手法の参考: [NA-SSL論文](https://arxiv.org/html/2608.00447v1)

<!-- experiments:end -->

## 使い方と資料

| 調べたいこと | 入口 |
|---|---|
| 計算の仕組み | [実装案内](src/asd_min/README.md) |
| CLIの実行・再採点 | [runner解説](src/asd_min/runner.md#cliを使う) |
| コードの由来と利用条件 | [出典と利用条件](docs/rights.md)・[第三者通知](THIRD_PARTY_NOTICES.md) |
| 確認した範囲 | [検証範囲](VALIDATION.md) |

データ・重み・評価器・正解CSVは同梱していません。配布元から取得し、そのパスを指定します。ライセンスと出典は[出典と利用条件](docs/rights.md)を参照してください。

一覧とグラフの更新: [手法一覧](configs/readme-methods.csv)に行を追加し、保存結果CSVと固定条件・入力取得・Notebookを指定して `python scripts/update_readme.py` を実行します（Matplotlibと日本語フォントが必要です）。同じ比較範囲では同じ結果CSV・固定条件・入力取得を指定し、結果CSVにもスコア行を追加します。異なる比較条件には別の `comparison` を付けます。
手法のコードと解説は同じ階層に置き、[実装案内](src/asd_min/README.md)へ行を追加します。各回の設定・結果・Notebookはその回の資料として保持し、検証記録は[検証範囲](VALIDATION.md)へ追加します。
