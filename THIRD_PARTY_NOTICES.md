# Third-party notices

Source attribution and modifications are listed below; see [出典と利用条件](docs/rights.md) for usage terms.

The code implements BEAM/VarMin, RDP, and W1 with a shared BEATs backbone.

- **Research code attribution**: the original MIT notice is retained for the research-derived implementations below. [licenses/research-MIT.txt](licenses/research-MIT.txt) is byte-identical to the [ASDKit LICENSE](https://github.com/TakuyaFujimura/dcase-asd-toolkit/blob/7601d673ef2ed5a2424965cac755365cf7112c5f/LICENSE), including Copyright (c) 2025 Takuya Fujimura.
- **BEAM/VarMin (`beam.py`)**: a reproduction implementation. The research MIT notice is retained.
- **RDP (`pooling.py`)**: an implementation of the RDP method proposed in [Temporal Pooling Strategies論文](https://arxiv.org/html/2603.04605v3), Section III-E. [NA-SSL論文](https://arxiv.org/html/2608.00447v1) is the reference for the adopted `gamma=4` and backend configuration.
- BEATs, backbone and modules: Microsoft MIT headers and an extension for grid extraction. Retained [BEATs LICENSE](src/asd_min/beats/LICENSE), [NOTICE](src/asd_min/beats/NOTICE.md), and research MIT notice. Three Python files are copied byte-for-byte from the selected research snapshot; package-only `__init__.py` is new and intentionally omits optional training/tokenizer imports.
- **W1**: waveform.py uses joint normalization, Torch STFT/ISTFT and full-recording complex least-squares. The received research MIT notice is retained. Additional validation/loading helpers are companion code.

New companion CLI, marimo app code and explanatory text, and documentation are licensed under the root MIT LICENSE, Copyright (c) 2026 kasahart. The dataset-derived figures and embedded audio in app section 3 and the identical WAV listening examples in `audio/02-toothbrush` are excluded from MIT and distributed under CC BY-NC-SA 4.0; see [data attribution and modifications](docs/DATA_ATTRIBUTION.md). Third-party LICENSE/NOTICE texts are retained.

SS implements the magnitude equation in [Chu・Qian技術報告](https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Qian_65_t2.pdf), Section 2.1.

## 参考文献

本文の短名と正式タイトルは次の対応です。

| 短名 | 正式タイトル |
|---|---|
| [BEATs論文](https://proceedings.mlr.press/v202/chen23ag.html) | BEATs: Audio Pre-Training with Acoustic Tokenizers |
| [BEAM論文](https://arxiv.org/html/2603.13749) | Sub-Band Spectral Matching with Localized Score Aggregation for Robust Anomalous Sound Detection |
| [VarMin論文](https://dcase.community/documents/workshop2025/proceedings/DCASE2025Workshop_Matsumoto_12.pdf) | Adjusting Bias in Anomaly Scores via Variance Minimization for Domain-Generalized Discriminative Anomalous Sound Detection |
| [Temporal Pooling Strategies論文](https://arxiv.org/html/2603.04605v3) | Temporal Pooling Strategies for Training-Free Anomalous Sound Detection with Self-Supervised Audio Embeddings |
| [NA-SSL論文](https://arxiv.org/html/2608.00447v1) | Anomalous Sound Detection Meets Noise-Aware Self-Supervised Learning |
| [MERL技術報告](https://www.merl.com/publications/docs/TR2026-100.pdf) | The MERL Systems for DCASE 2026 Challenge Task 2 |
| [Ozeki技術報告](https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Ozeki_101_t2.pdf) | Anomalous Sound Detection Method with Simple Noise Reduction |
| [Chu・Qian技術報告](https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Qian_65_t2.pdf) | Anomalous Sound Detection System for DCASE 2026 Task 2 Using Dual-Channel Spectral Subtraction and Efficient Audio Transformer |

The browser app is exported with [marimo 0.25.1](https://github.com/marimo-team/marimo/tree/0.25.1), licensed under [Apache-2.0](licenses/marimo-Apache-2.0.txt). The static export loads marimo frontend assets from its CDN; the original marimo license is retained unchanged.

## 第3回：追加学習の再現

公開ASDKit commit `7601d673ef2ed5a2424965cac755365cf7112c5f`を `upstream.lock.json` に定義した公式archiveから仮想環境内へ取得し、editable依存として利用します。リポジトリにASDKit本体を同梱せず、原LICENSEを含むarchiveを仮想環境内に展開します。取得先のsourceは書き換えません。ASDKitと研究由来部分の原MIT通知は共通の [licenses/research-MIT.txt](licenses/research-MIT.txt) に保持しています。`runtime.py`のfrontend・学習設定は外部ASDKitを継承し、通常名のcollationも親実装に委譲します。匿名Evaluation名だけを接続側で補い、BEATsの復元は既存Encoderを共用します。BEATs・pooling・BEAM・W1は既存の `src/asd_min/` を共用し、Microsoft MIT/NOTICEと帰属は上の節を参照してください。外部依存の取得先・既定版・archive整合確認は `upstream.lock.json` にまとめています。新しいrunner・集計・テスト・説明文はroot MITです。データ・学習済み重み・ラベル個票は同梱しません。

## 公式DCASE評価器

[DCASE2026 Task 2の公式評価器](https://github.com/nttcslab/dcase2026_task2_evaluator)は利用者が別途設置し、第2回・第3回で共通の接続から無改変で実行します。評価器のコード・正解は同梱しません。利用条件は配布元の`LICENSE`と`LICENSEv2.1.pdf`を参照してください。こちらには予測の形式変換・Developmentの公開ファイル名からの正解CSV生成・公式出力の読み取りだけを置き、公式の指標計算を再実装しません。
