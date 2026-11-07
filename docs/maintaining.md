# 保守手順

## READMEの結果の要点・手法表・スコア・グラフを更新する

READMEの`<!-- summary:start -->`〜`<!-- summary:end -->`と`<!-- experiments:start -->`〜`<!-- experiments:end -->`、グラフ`results/readme/*.svg`は`scripts/update_readme.py`が生成します。手で編集しません。

1. [手法一覧](../configs/readme-methods.csv)に行を追加します。実験（`experiment`）・データ（`dataset`）・グラフの軸に出す短い組名（`chart_prefix`、例：`追加学習`。同じデータの中で重ならないもの）・特徴抽出モデル・モデルの追加学習・保存結果CSV・固定条件・入力取得を指定します。同じ記号の手法は、どの実験でも同じ特徴と参考文献にします。データ・特徴抽出・スコアが既存の比較と同じ行は、表とグラフで1行・1本にまとめられます。
2. 結果の要点で比べる組（基準→処理後）は[要点の設定](../configs/readme-summary.json)に`[chart_prefix, 記号]`で指定します。
3. 新しい実験やmarimoアプリは、READMEの「実験」表と「目的別の入口」表へ手で行を追加します。
4. 同じ比較範囲では同じ結果CSV・固定条件・入力取得を指定し、結果CSVにもスコア行を追加します。異なる比較条件には別の`comparison`を付けます。
5. `python scripts/update_readme.py`を実行します。`--check`で更新漏れを確認できます（CIでも実行します）。

## 手法のコードと解説を追加する

手法のコードと解説は同じ階層に置き、[実装案内](../src/asd_min/README.md)へ行を追加します。各実験の設定・結果・marimoアプリはその実験の資料として保持します。
