# 出典と利用条件

| 対象 | 出典・条件 | このコピーの扱い |
|---|---|---|
| ASDKit基盤 `base.py` | [公開上流ASDKit](https://github.com/TakuyaFujimura/dcase-asd-toolkit)由来。研究repoのMIT原文は[上流LICENSE](https://github.com/TakuyaFujimura/dcase-asd-toolkit/blob/main/LICENSE)と一致 | licenses/research-MIT.txtのCopyright 2025 Takuya Fujimuraを原文のまま保持 |
| BEAM/VarMin `beam.py`・W1選択処理 | ASDKit基盤とMIT表示を継承する研究repoに、kasahartが追加した再現・比較実装 | BEAMは記事原本のhash固定snapshotと一致し、研究固定Git revisionへの詳細API拡張を含む。W1は研究コードから必要関数を移植。受領したresearch-MIT原文を保持。上流基盤作者の実装と一括帰属しない |
| RDP pooling | kasahart追加の論文手法実装から選択したhash固定snapshot | pooling.pyは選択元とbyte-identical。licenses/beam-tfattr-MIT.txtの受領原文を保持し、そのcopyright行をRDP個別実装者の表示とは扱わない |
| BEATs.py/backbone.py/modules.py | 上記研究snapshot内のMicrosoft unilm/beats由来、MIT、Microsoft/fairseq由来ヘッダー | 必要3ファイルのみ。研究のgrid抽出拡張を含む。LICENSEとNOTICE.md（Apache由来情報）を保持。Tokenizer/quantizer/LoRA等は除外 |
| BEATs重み | [Microsoft公式案内](https://github.com/microsoft/unilm/tree/master/beats)のPre-Trained Iter3 | 同梱なし。公式READMEはimplementationとpretrained modelsを案内し、projectへ公式root MITを適用。独立したcheckpoint文言がないことだけをローカル推論の禁止根拠にしない。checkpoint内部の固有文言・再配布時の追加確認は未実施 |
| 音声 | [Zenodo 20151556](https://zenodo.org/records/20151556)、[20437238](https://zenodo.org/records/20437238)、CC BY-NC-SA 4.0 | 同梱なし。非商用・表示・継承条件を確認。処理済み音声の第三者配布も本コピーでは行わない |
| evaluatorと正解CSV | [NTT公式 fixed LICENSEv2.1.pdf](https://github.com/nttcslab/dcase2026_task2_evaluator/blob/f6a94a2b5e614a9626c9d1ccff6df0705e6aaa75/LICENSEv2.1.pdf) | 同梱しない。Section1は内部非商用試験等の限定、Section4(c)は第三者配布・変更等の禁止。著者の既存利用・内部非商用DCASE研究という用途を点検し、ローカル再採点に使用。読者の用途適合は別途確認。正解付属物も配布権を仮定しない |
| 保存異常度/既存集計 | 所有者の既存3条件報告と今回のSS実験 | 同梱するsubmissionは研究側が作った異常度・判定CSV。生正解・公式コード・公式出力CSVは除外。集計は既存値と今回の実測数値の事実記録 |
| 新規CLI/Notebook/説明 | この切り出しで作成 | 所有者がMITを明示選択。root LICENSE、Copyright 2026 kasahart |

**利用と配布の境界**: 著者自身の既存内部非商用DCASE研究における公式ローカル採点を完了しました。読者の用途が利用条件に適合するか、取得リンクや`--terms-reviewed`だけで解決するとは言いません。許諾取得や契約同意操作を代行していません。checkpoint内部固有文言・第三者再配布の追加確認は未実施で、重みを配布しません。新規CLI・Notebook・説明文は所有者選択のMIT、第三者表示・個別条件は保持します。公開用コピーは所有者の明示指示に基づくものです。

公式evaluatorを使用できる条件を読者自身が確認・解決した場合のみ、公式案内から別ディレクトリへ取得し、固定revisionにcheckoutします。本コピーの`evaluate`はそのclean HEADを確認して無改変で呼ぶ境界です。公式の依存関係・使い方は[公式README](https://github.com/nttcslab/dcase2026_task2_evaluator)を参照してください。

詳細な原本との対応は[import-manifest.json](import-manifest.json)。
