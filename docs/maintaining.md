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
| 全実験で共通の採点方法 | [評価の共通条件](evaluation.md) |
| 実験ごとの固定条件と手順 | 各実験の資料（READMEの入口表が一覧） |
| 処理の解説 | コード隣のMarkdown（[実装案内](../src/asd_min/README.md)） |
| 出典・ライセンス | [出典と利用条件](rights.md)がまとめ役。詳細は[第三者通知](../THIRD_PARTY_NOTICES.md)と[帰属情報](DATA_ATTRIBUTION.md) |

同じ内容を2か所に書かず、他の文書へはリンクで参照します。

## 手法のコードと解説を追加する

手法のコードと解説は同じ階層に置き、[実装案内](../src/asd_min/README.md)へ行を追加します。各実験の設定・結果・marimoアプリはその実験の資料として保持します。

## 実験を追加する

1. 実験の固定条件・手順を1つの資料にまとめ、コードの隣（例：`reproduction/<名前>/README.md`）に置きます。共通の取得先・環境・採点方法は書き直さず、[入力の取得](02-inputs.md)・[実行環境](setup.md)・[評価の共通条件](evaluation.md)へリンクします。
2. READMEの問いの一覧と「入口」表に1行ずつ追加します。実験の一覧はこの表だけに置きます。
3. 結果CSVと手法一覧を「結果の要点・手法表・スコア・グラフを更新する」の手順で追加します。
4. 新しい外部コードや依存を使う場合は[第三者通知](../THIRD_PARTY_NOTICES.md)に、新しい実録音由来の図・音声は[帰属情報](DATA_ATTRIBUTION.md)に追記します。marimoアプリは[アプリの説明](../apps/README.md#アプリを追加する)のとおり追加します。
