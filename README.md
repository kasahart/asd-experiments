# ASD experiments — Zenn連載の実験入口

[第1回](https://zenn.dev/kasahart/articles/kasahart-20260919-dcase2026-asd-01)の読者向けのコードとNotebookです。

まず[第2回Notebook](notebooks/02_b0_b1_w1_ss.ipynb)を開いてください。B0（近接）・B1（遠方）・W1（複素線形減算）・SS（スペクトル減算）の結果と合成図を、保存済みの表示で読めます。インストールやデータ取得は不要です。Wandas 0.8.0の手動試聴はローカル実行時に利用できます。

| 調べたいこと | 入口 |
|---|---|
| 計算の仕組み | [実装案内](src/asd_min/README.md) |
| CLIの実行・再採点 | [runner解説](src/asd_min/runner.md#cliを使う) |
| 実験の設定と採点法 | [固定条件](docs/protocol.md) |
| データ・重みの取得と容量 | [入力取得](docs/inputs.md) |
| コードの由来と利用条件 | [権利文書](docs/rights.md)・[第三者通知](THIRD_PARTY_NOTICES.md) |
| 確認した範囲 | [検証範囲](VALIDATION.md) |

結果は[総合値](results/summary-with-ss.csv)と[機種別](results/by_machine-with-ss.csv)が正本です。B0/B1/W1は記事の既存報告、SSは追加実験です。

データ・重み・公式評価器・正解CSVは同梱せず、読者が公式から取得してパスを指定します。ライセンスと出典は[利用条件](docs/rights.md)を参照してください。
