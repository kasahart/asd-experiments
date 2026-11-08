# 第三者通知

第三者のコード・ライブラリの出典と改変の有無です。リポジトリ全体の利用条件は[出典と利用条件](docs/rights.md)にあります。第三者のLICENSE・NOTICEは原文のまま保持しています。

| 対象 | 出典と改変 | ライセンス |
|---|---|---|
| BEAM/VarMin（`beam.py`・`varmin.py`・`band_distance.py`）、W1（`waveform.py`） | 研究コード由来の再現実装。W1の検証・読み込み補助は新規 | 研究コードのMIT通知（[licenses/research-MIT.txt](licenses/research-MIT.txt)、[ASDKitのLICENSE](https://github.com/TakuyaFujimura/dcase-asd-toolkit/blob/7601d673ef2ed5a2424965cac755365cf7112c5f/LICENSE)とバイト単位で同一、Copyright (c) 2025 Takuya Fujimura） |
| RDP（`pooling.py`） | [Temporal Pooling Strategies論文](https://arxiv.org/html/2603.04605v3) Section III-Eの実装。`gamma=4`とbackend構成は[NA-SSL論文](https://arxiv.org/html/2608.00447v1)に従う | 研究コードのMIT通知 |
| SS（`waveform.py`） | [Chu・Qian技術報告](https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Qian_65_t2.pdf) Section 2.1の大きさの式の実装 | W1と同じ（`waveform.py`の通知） |
| BEATs（`src/asd_min/beats/`） | 研究スナップショットのPython 3ファイルを無改変でコピー。グリッド抽出の拡張と、学習・tokenizer用importを省いた`__init__.py`は新規 | Microsoft MIT（[LICENSE](src/asd_min/beats/LICENSE)・[NOTICE](src/asd_min/beats/NOTICE.md)）と研究コードのMIT通知 |
| ASDKit（追加学習） | commit `7601d673ef2ed5a2424965cac755365cf7112c5f`の公式archiveを[upstream.lock.json](reproduction/asd03/upstream.lock.json)に従い仮想環境内へ取得。同梱・改変しない | 研究コードのMIT通知（archive内の原LICENSE） |
| marimo 0.25.1 | ブラウザーアプリのexportに使用。静的HTMLはmarimoのCDNからフロントエンドを読み込む | [Apache-2.0](licenses/marimo-Apache-2.0.txt) |
| [DCASE2026 Task 2公式評価器](https://github.com/nttcslab/dcase2026_task2_evaluator) | 利用者が別途設置し、共通の接続から無改変で実行。コード・正解は同梱しない | 配布元の`LICENSE`と`LICENSEv2.1.pdf` |

上記以外のコードと説明文はroot MIT（[LICENSE](LICENSE)）です。実録音由来の図・音声は[帰属情報](docs/DATA_ATTRIBUTION.md)の条件に従います。

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
