# 保守手順

## 結果の要点・手法表・スコア・グラフを更新する

READMEの`<!-- summary:start -->`〜`<!-- summary:end -->`、[結果の詳細](results.md)の`<!-- experiments:start -->`〜`<!-- experiments:end -->`、グラフ`results/readme/*.svg`は`scripts/update_readme.py`が生成します。手で編集しません。

1. [手法一覧](../configs/readme-methods.csv)に行を追加します。
   - 列：実験（`experiment`）・データ（`dataset`）・グラフの軸に出す短い組名（`chart_prefix`、例：`追加学習`）・特徴抽出モデル・モデルの追加学習・保存結果CSV。
   - 同じ記号の手法は、どの実験でも同じ特徴と参考文献にします。
   - データ・特徴抽出・組名が既存の比較と同じ行は、スコアが一致すれば表とグラフで1行・1本にまとめられます。
2. 結果の要点で比べる組（基準→処理後）は[要点の設定](../configs/readme-summary.json)に`[chart_prefix, 記号]`で指定します。
3. 新しい実験やmarimoアプリは、READMEの「入口」表へ手で行を追加します。
4. 結果CSVにスコア行を追加します。異なる比較条件には別の`comparison`を付けます。
5. `python scripts/update_readme.py`を実行します。`--check`で更新漏れを確認できます（CIでも実行します）。

## 説明文の置き場所

| 内容 | 置き場所 |
|---|---|
| 問い・結果の要点・入口 | [README](../README.md) |
| 手法・全スコア・グラフ | [結果の詳細](results.md)（生成） |
| 環境の作り方 | [実行環境](setup.md) |
| データ・重み・評価器の取得先 | [入力の取得](02-inputs.md) |
| 実験ごとの固定条件と手順 | [実験1](02-protocol.md)・[実験2](../reproduction/asd03/README.md) |
| 処理の解説 | コード隣のMarkdown（[実装案内](../src/asd_min/README.md)） |
| 出典・ライセンス | [出典と利用条件](rights.md)がまとめ役。詳細は[第三者通知](../THIRD_PARTY_NOTICES.md)と[帰属情報](DATA_ATTRIBUTION.md) |

同じ内容を2か所に書かず、他の文書へはリンクで参照します。

## 手法のコードと解説を追加する

手法のコードと解説は同じ階層に置き、[実装案内](../src/asd_min/README.md)へ行を追加します。各実験の設定・結果・marimoアプリはその実験の資料として保持します。
