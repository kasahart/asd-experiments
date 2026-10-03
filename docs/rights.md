# 出典と公開前の確認

| 対象 | 出典・条件 | このコピーの扱い |
|---|---|---|
| ASDKit基盤 `base.py` | [公開上流ASDKit](https://github.com/TakuyaFujimura/dcase-asd-toolkit)由来。研究repoのMIT原文は[上流LICENSE](https://github.com/TakuyaFujimura/dcase-asd-toolkit/blob/main/LICENSE)と一致 | licenses/research-MIT.txtのCopyright 2025 Takuya Fujimuraを原文のまま保持 |
| BEAM/VarMin `beam.py`・W1選択処理 | ASDKit基盤とMIT表示を継承する研究repoに、kasahartが追加した再現・比較実装 | BEAMは記事原本のhash固定snapshotと一致し、研究固定Git revisionへの詳細API拡張を含む。W1は固定revision `122e56afbf4a21f3803b223e13d0b8bff4de55ea`から必要関数を移植。受領したresearch-MIT原文を保持。上流基盤作者の実装と一括帰属しない |
| RDP pooling | kasahart追加の論文手法実装から選択したhash固定snapshot | pooling.pyは選択元とbyte-identical。licenses/beam-tfattr-MIT.txtの受領原文を保持し、そのcopyright行をRDP個別実装者の表示とは扱わない |
| BEATs.py/backbone.py/modules.py | 上記研究snapshot内のMicrosoft unilm/beats由来、MIT、Microsoft/fairseq由来ヘッダー | 必要3ファイルのみ。研究のgrid抽出拡張を含む。LICENSEとNOTICE.md（Apache由来情報）を保持。Tokenizer/quantizer/LoRA等は除外 |
| BEATs重み | [Microsoft公式案内](https://github.com/microsoft/unilm/tree/master/beats)のPre-Trained Iter3 | 同梱なし。公式READMEはimplementationとpretrained modelsを案内し、projectへ公式root MITを適用。独立したcheckpoint文言がないことだけをローカル推論の禁止根拠にしない。checkpoint内部の固有文言・再配布時の追加確認は未実施 |
| 音声 | [Zenodo 20151556](https://zenodo.org/records/20151556)、[20437238](https://zenodo.org/records/20437238)、CC BY-NC-SA 4.0 | 同梱なし。非商用・表示・継承条件を確認。処理済み音声の第三者配布も本コピーでは行わない |
| evaluatorと正解CSV | [NTT公式 fixed LICENSEv2.1.pdf](https://github.com/nttcslab/dcase2026_task2_evaluator/blob/f6a94a2b5e614a9626c9d1ccff6df0705e6aaa75/LICENSEv2.1.pdf) | 同梱しない。Section1は内部非商用試験等の限定、Section4(c)は第三者配布・変更等の禁止。著者の既存利用・内部非商用DCASE研究という用途を点検し、ローカル再採点に使用。読者の用途適合は別途確認。正解付属物も配布権を仮定しない |
| 保存異常度/既存集計 | 所有者の既存3条件報告と今回のSS実験 | 同梱するsubmissionは研究側が作った異常度・判定CSV。生正解・公式コード・公式出力CSVは除外。集計は既存値と今回の実測数値の事実記録 |
| 新規CLI/Notebook/説明 | この切り出しで作成 | 所有者がMITを明示選択。root LICENSE、Copyright 2026 kasahart |

**利用と配布の境界**: 著者自身の既存内部非商用DCASE研究における公式ローカル採点を完了しました。読者の用途が利用条件に適合するか、取得リンクや`--terms-reviewed`だけで解決するとは言いません。許諾取得や契約同意操作を代行していません。checkpoint内部固有文言・第三者再配布の追加確認は未実施で、重みを配布しません。新規CLI・Notebook・説明文は所有者選択のMIT、第三者表示・個別条件は保持します。公開用コピーは所有者の明示指示に基づくものです。

公式evaluatorを使用できる条件を読者自身が確認・解決した場合のみ、公式案内から別ディレクトリへ取得し、固定revisionにcheckoutします。本コピーの`evaluate`はそのclean HEADを確認して無改変で呼ぶ境界です。公式の依存関係・使い方は[公式README](https://github.com/nttcslab/dcase2026_task2_evaluator)を参照してください。

詳細な原本との対応は[import-manifest.json](import-manifest.json)。研究原本全部や私的ログのコピーは含みません。

## 公開と利用を分けた整理（2026-10-03再点検）

### 新規部分のライセンス

新規CLI・runner・Notebook・説明文は、自動的な継承ではなく、今回の所有者の明示回答「mitでいい。」によりMITを適用しました。root LICENSEの`kasahart`表記と所有者が選択したMITを保持しています。Git履歴は実装の出典を確認する記録であり、commit authorだけで法的権利を断定しません。既存privateの権利留保を一括MITと解釈したものではありません。

継承するのは選択元でMITと明記された範囲です。`base.py`/`beam.py`、`pooling.py`、BEATsの3ファイルは既存MIT許諾と保持した著作権表示・LICENSE/NOTICEが対象です。`waveform.py`のW1移植部分も選択元MITの表示を保持します。研究repoにはASDKit由来の基盤とkasahartの追加実装が混在します。受領したTakuya FujimuraのMIT表示を、追加実装すべての作者表示へ読み替えません。第三者の著作権表示は付け替えません。新規部分へのMIT選択は、checkpointやdataset/evaluatorへの許諾を与えるものではありません。

### 外部checkpointとevaluator

- **checkpoint**: [公式README](https://github.com/microsoft/unilm/blob/master/beats/README.md)はimplementationとpretrained modelsを両方案内し、BEATs_iter3へのリンクと推論例を掲載、License節でprojectへ[公式root MIT](https://github.com/microsoft/unilm/blob/master/LICENSE)を適用しています。確認した両一次資料にcheckpoint除外・research-only・別同意の記載は見当たりません。別のcheckpoint文言がないことだけでローカル推論を止める根拠にはしません。狭い未確認点はcheckpoint内部の固有文言と第三者再配布時の追加条件であり、本コピーでは重みを配布しません。ローカル実験は読者/著者自身が公式から取得したIter3を使います。README blob SHA `76c1ec344f4408683297ae48ff75fd7b9c85e9c1`、root LICENSE blob SHA `ae241a567f3de21656c00c7b341a6f8701e405b3`を2026-10-03に確認しました。
- **evaluator**: fixed revisionのLICENSEv2.1全文、既存の使用記録、clean checkoutを点検しました。Section1の内部非商用の試験・分析・評価という範囲に、著者自身の継続するDCASE手法比較が該当するとの限定的な整理に基づき、既存固定版を無改変でローカル実行しました。Section3は既存の受諾/アクセス/使用との関係を定めており、今回新たな契約同意や許諾取得操作はしていません。一般読者の別用途まで許可されたとは断定しません。Section4(c)・Section8およびExhibit Aの対象を踏まえ、evaluator本体・LICENSE PDF・付属正解・公式出力CSVを同梱しません。

本repoのMITは外部資産のライセンスを上書きしません。読者は公式条件を自分の用途に照らして確認し、必要な場合は権利者へ問い合わせてください。ここでは許諾取得や契約同意を代行しません。

### 検証範囲

既存3条件は同じ6000入力と固定checkpointで再推論し、異常度差は最大4.8487e-8、テスト順位・判定が一致しました。元保存異常度の公式再採点は3条件とも元公式出力CSVとbyte-identical。新規再推論も機種別AUC/pAUC・総合値が一致しました。ただしW1の補助CI欄に約4.66e-11差があり、全出力byte一致ではありません。既存値を今回得た独立した外部追試の成績とは呼びません。

SSは今回新規全件実験・公式ローカル採点で62.325を測定しました。原Qianシステム、主観的聞きやすさ、未知設備の汎化、大会勝者の完全再現について成功を主張しません。[SS検証記録](ss-validation.md)参照。

### 再点検で公開対象に残っているもの

- 必要なMITコード6ファイル（BEAM/base/RDP/BEATs3）、W1選択移植と新規companion、必要LICENSE/NOTICE。
- 所有者の保存異常度・判定・閾値と既存集計、入力を含まない比較検証記録。
- 合成図だけを保存したNotebook、公式取得先・固定条件・利用条件の文書。

公式evaluatorコード、公式出力CSV、付属正解CSV、LICENSE PDF、録音、処理済み音声、checkpoint、全研究原本、私的履歴、用途不明のvendorディレクトリは入っていません。移した第三者コードに対応するMIT/NOTICEがあることを確認し、権利根拠不明のコードが残っていることは確認されませんでした。新規CLI・Notebook・説明文には今回選択されたMITを明記しています。

2026-10-03に所有者から`kasahart/asd-experiments`のpublic作成・pushを明示指示されました。外部資産の利用条件はこの公開指示で変更されません。
