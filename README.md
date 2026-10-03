# ASD experiments — Zenn連載の実験入口

Zennの異常音検知（ASD）連載に対応する実験コードとNotebookです。手法・結果・解説を以下の表から参照できます。

<!-- experiments:start -->

## 手法

| 比較範囲 | 手法 | 説明 | Notebook |
|---|---|---|---|
| DCASE 2026 Evaluation / BEATs_iter3 | B0 | 近接マイクをそのまま使用 | [Notebook](notebooks/02_b0_b1_w1_ss.ipynb) |
| DCASE 2026 Evaluation / BEATs_iter3 | B1 | 遠方マイクをそのまま使用 | [Notebook](notebooks/02_b0_b1_w1_ss.ipynb) |
| DCASE 2026 Evaluation / BEATs_iter3 | W1 | 大きさと位相を合わせて複素減算 | [Notebook](notebooks/02_b0_b1_w1_ss.ipynb) |
| DCASE 2026 Evaluation / BEATs_iter3 | SS | 大きさを減算し近接位相で復元 | [Notebook](notebooks/02_b0_b1_w1_ss.ipynb) |

## スコア

総合スコアは高いほど良く、順位は同じ比較範囲内で付けています。

### DCASE 2026 Evaluation / BEATs_iter3

[固定条件](docs/02-protocol.md) · [入力取得](docs/02-inputs.md) · [総合値](results/02-summary.csv)

| 順位 | 手法 | 総合スコア |
|---:|---|---:|
| 1 | W1 | 66.835 |
| 2 | B0 | 62.841 |
| 3 | SS | 62.325 |
| 4 | B1 | 58.362 |

<!-- experiments:end -->

## 使い方と資料

| 調べたいこと | 入口 |
|---|---|
| 計算の仕組み | [実装案内](src/asd_min/README.md) |
| CLIの実行・再採点 | [runner解説](src/asd_min/runner.md#cliを使う) |
| コードの由来と利用条件 | [出典と利用条件](docs/rights.md)・[第三者通知](THIRD_PARTY_NOTICES.md) |
| 確認した範囲 | [検証範囲](VALIDATION.md) |

データ・重み・評価器・正解CSVは同梱せず、読者が配布元から取得してパスを指定します。ライセンスと出典は[出典と利用条件](docs/rights.md)を参照してください。

表の更新: [手法一覧](configs/readme-methods.csv)に行を追加し、保存結果CSVと固定条件・入力取得・Notebookを指定して `python scripts/update_readme.py` を実行します。同じ比較範囲では同じ結果CSV・固定条件・入力取得を指定し、結果CSVにもスコア行を追加します。異なる比較条件には別の `comparison` を付けます。
手法のコードと解説は同じ階層に置き、[実装案内](src/asd_min/README.md)へ行を追加します。各回の設定・結果・Notebookはその回の資料として保持し、検証記録は[検証範囲](VALIDATION.md)へ追加します。
