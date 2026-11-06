# 保守手順

## READMEの手法表・スコア・グラフを更新する

READMEの`<!-- experiments:start -->`から`<!-- experiments:end -->`までと、スコアのグラフ`results/readme/*.svg`は`scripts/update_readme.py`が生成します。手で編集しません。

1. [手法一覧](../configs/readme-methods.csv)に行を追加します。回（`round`）・データ（`dataset`）・グラフの軸に出す短い組名（`chart_prefix`、例：`第3回 追加学習`。同じデータの中で重ならないもの）・特徴抽出モデル・モデルの追加学習・保存結果CSV・固定条件・入力取得を指定します。同じ記号の手法は、どの回でも同じ特徴と参考文献にします。
2. marimoアプリや新しい回は、READMEの「連載の回と実験」表へ手で行を追加します。
3. 同じ比較範囲では同じ結果CSV・固定条件・入力取得を指定し、結果CSVにもスコア行を追加します。異なる比較条件には別の`comparison`を付けます。
4. `python scripts/update_readme.py`を実行します。`--check`で更新漏れを確認できます（CIでも実行します）。

## 手法のコードと解説を追加する

手法のコードと解説は同じ階層に置き、[実装案内](../src/asd_min/README.md)へ行を追加します。各回の設定・結果・marimoアプリはその回の資料として保持します。
