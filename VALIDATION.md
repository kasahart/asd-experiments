# 検証記録 — 2026-10-03

公開準備コピーをML-PCの分離ディレクトリで検証。元privateの履歴やvisibilityは変更していません。

## 確認済み

- pytest 6件: 無音、far=0、scale復元、長さ、B0/B1 channel、BEAM自身除外・参照再構築、保存CSV全5機種×200匿名名、未取得入力/未確認採点条件の拒否。
- W1の元選択関数と比較: 合成信号・無音・far=0・実音2件、計5ケースのfloat32出力がarray_equal（最大絶対差0）。Torch periodic Hann、全録音LS、reflect端処理を保持。
- BEAM/base/RDP poolingとBEATs必要3コードファイルは選択snapshotからbyte-identicalで移植。初期SHA-256をdocs/import-manifest.jsonに記録。
- CPU smoke: ToothBrush train5/test5×3条件。正常参照は条件ごとに構築。Python3.12 / torch2.7.1+cpu、CPU i7-13700KF、torch threads2。抽出・採点約6.90秒（checkpoint初期化・SHA計算を除く）。少数参照のスコアは記事成績ではない。
- GPU smoke: 同じ30処理、Python3.11 / torch2.7.1+cu128、RTX PRO6000 Blackwell Max-Q、約0.80秒（同じく初期化を除く）。cold-startを含む条件別時間を速度比較に使わない。
- Wandas0.8.0 / Python3.12 Notebookの既定セルをheadlessで上から実行。保存結果の表とpAUC図、B0/B1/W1/SS合成波形・表示STFTの計5図を保存し、文字・軸・スケール・表示を目視確認。実音・再採点・推論cellは既定でskip。
- Wandas `describe(normalize=False)` が手動HTML Audioを生成し、autoplay=Falseを検証。音を実機再生した主観評価ではない。配布Notebook出力に音声を埋め込んでいない。
- editable package installとCLI保存結果閲覧を確認。
- allowlist切り出し点検: evaluator/正解/音声/重み/履歴/実行log/私的path/credentialsなし。保存submissionは研究側の異常度と判定のみ。残ったコードは独立license/NOTICE付きの必要部分。

## 全件GPU再推論と既存保存異常度との比較

RTX PRO6000 Blackwell Max-Q / Python3.11 / torch2.7.1+cu128。各条件で5機種×train1000/test200を新規特徴抽出し、正常参照を再構築。全6000ファイルのSHA-256は既存報告の入力inventoryと一致しました。checkpoint SHAも固定値と一致。

- 3条件計18000音の抽出・採点時間: B0 73.73秒、B1 70.88秒、W1 84.28秒、合計228.89秒。checkpoint初期化・ハッシュ確認は合計時間の外。条件間の小差を速度ベンチマークとは扱いません。
- PyTorch peak CUDA allocated: 528886272 bytes（約0.493 GiB）。CUDA contextや外部プロセスなど全GPU使用量を含まず、必要VRAM最小値の保証ではありません。開始時GPU使用596 MiB/97887 MiB、GPU利用0%。他プロセスを停止していません。
- 保存異常度15CSVとの最大絶対差は **4.8487236030097104e-08**。事前のfloat32比較基準1e-6以内。byte-identicalではありません。全15機種条件のテスト音の順位は一致、判定15CSVはbyte-identical。
- 初期段階では公式evaluator未実行でした。下記の最新追加検証で、固定公式版による主要指標の再採点一致を確認しました。元数値の出典は既存報告です。

機種条件別の比較は[full-inference-comparison.json](docs/full-inference-comparison.json)。新規全件出力はローカル検証先に保持し、保存報告CSVを上書きしていません。

## 未実施・利用条件

主観的試聴、他機器での全件時間と最低RAM/VRAM要件、未知機種への汎化は未検証。将来回、Dis-BEATs/DNN/ensemble/UIは配布・検証対象外。[権利文書](docs/rights.md)は著者自身の継続するローカル利用と読者用途・資産再配布を分けています。

## 公開用コピー

2026-10-03の所有者の明示指示に基づき、必要ファイルだけを新規publicリポジトリへ移す構成です。private原本の履歴は移さず、既存privateのvisibilityも変更しません。データ・重み・公式evaluator・正解は同梱しません。

## 新規部分のMIT選択反映

所有者の明示選択により、2026-10-03に新規CLI・Notebook・説明文をMITに設定。root LICENSEのCopyrightは既存所有者表記`kasahart`。README、pyprojectのPEP639宣言、第三者通知、権利文書を整合し、第三者MIT/NOTICEは変更していません。音声・checkpoint・evaluator・正解にはroot MITを適用しません。公開用コピーでも第三者資産の条件は個別に保持します。

## SS追加と公式採点（最新状態）

PR9 headは`de12a5825e6974c10934c72556bb6787f05c5a83`。ユーザーのSS確認後、正常参照をSSで再構築し、同じ6000入力の全件GPU推論を実施。94.9367秒、peak Torch CUDA allocated528886272bytes。SS smoke10音は0.513秒。詳細は[SS検証記録](docs/ss-validation.md)、[機械可読記録](docs/ss-experiment.json)。

既存利用記録・LICENSE全文・fixed clean checkoutを点検し、著者自身の内部非商用DCASE研究として既存公式evaluatorを無改変で実行。新たな許諾取得・契約同意操作や第三者配布は行っていません。元保存3条件からの公式出力は元報告とすべてbyte-identical。新規GPU推論の機種別AUC/pAUC・総合値も一致。W1のみ補助 `official score ci95` に約4.66e-11差があり、全出力byte一致ではありません。

SS総合値は**62.325**（B0比**−0.516ポイント**、W1比−4.510）。pAUCは2機種増・3機種減で、総合改善はありません。元記事にSS成績がないため既存SS報告との一致検証ではなく、新規実験です。自作submissionと集計事実を配布し、公式evaluator出力CSV・正解・PDFはローカルにのみ保持。

pytest6件、W1元関数との5ケースarray_equal、第三者コードと元保存CSVのhash保持を確認。SS合成CPU/GPU差2.38e-7、式分岐・位相・scale・長さ・有限値を検証。Wandas0.8.0 Notebookをheadlessで実行し、4条件表とpAUC・合成4条件の計5図を保存。音声controlのautoplay=Falseを確認し、配布Notebook出力に音声は埋め込みません。
