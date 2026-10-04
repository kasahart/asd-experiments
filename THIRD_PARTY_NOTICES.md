# Third-party notices

Selected source snapshots and modifications are listed in [出典と利用条件](https://github.com/kasahart/asd-experiments/blob/49f095937e21a48dde9f836e480e1208723487c7/docs/rights.md) and [import-manifest](https://github.com/kasahart/asd-experiments/blob/49f095937e21a48dde9f836e480e1208723487c7/docs/import-manifest.json).

The code combines the ASDKit foundation with implementations of BEAM/VarMin, RDP, and W1.

- **ASDKit foundation (`base.py`)**: derived from [ASDKit](https://github.com/TakuyaFujimura/dcase-asd-toolkit). [licenses/research-MIT.txt](https://github.com/kasahart/asd-experiments/blob/49f095937e21a48dde9f836e480e1208723487c7/licenses/research-MIT.txt) is byte-identical to the [ASDKit LICENSE](https://github.com/TakuyaFujimura/dcase-asd-toolkit/blob/main/LICENSE), including Copyright (c) 2025 Takuya Fujimura.
- **BEAM/VarMin (`beam.py`)**: a reproduction implementation on the ASDKit foundation.  The research MIT notice is retained.
- **RDP (`pooling.py`)**: an implementation of the RDP method proposed in [Temporal Pooling Strategies論文](https://arxiv.org/html/2603.04605v3), Section III-E. [NA-SSL論文](https://arxiv.org/html/2608.00447v1) is the reference for the adopted `gamma=4` and backend configuration. The received [licenses/beam-tfattr-MIT.txt](https://github.com/kasahart/asd-experiments/blob/49f095937e21a48dde9f836e480e1208723487c7/licenses/beam-tfattr-MIT.txt), including Copyright (c) 2025 Takuya Fujimura, is retained unchanged.
- BEATs, backbone and modules: Microsoft MIT headers and an extension for grid extraction. Retained [BEATs LICENSE](https://github.com/kasahart/asd-experiments/blob/49f095937e21a48dde9f836e480e1208723487c7/src/asd_min/beats/LICENSE), [NOTICE](https://github.com/kasahart/asd-experiments/blob/49f095937e21a48dde9f836e480e1208723487c7/src/asd_min/beats/NOTICE.md), and research MIT notice. Three Python files are copied byte-for-byte from the selected research snapshot; package-only `__init__.py` is new and intentionally omits optional training/tokenizer imports.
- **W1**: waveform.py uses joint normalization, Torch STFT/ISTFT and full-recording complex least-squares. The received research MIT notice is retained. Additional validation/loading helpers are companion code.

New companion CLI, marimo app code and explanatory text, and documentation are licensed under the root MIT LICENSE, Copyright (c) 2026 kasahart. The dataset-derived figures and embedded audio in app section 3 and the identical WAV listening examples in `audio/02-toothbrush` are excluded from MIT and distributed under CC BY-NC-SA 4.0; see [data attribution and modifications](https://github.com/kasahart/asd-experiments/blob/49f095937e21a48dde9f836e480e1208723487c7/docs/DATA_ATTRIBUTION.md). Third-party LICENSE/NOTICE texts are retained.

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

The browser app is exported with [marimo 0.25.1](https://github.com/marimo-team/marimo/tree/0.25.1), licensed under [Apache-2.0](https://github.com/kasahart/asd-experiments/blob/49f095937e21a48dde9f836e480e1208723487c7/licenses/marimo-Apache-2.0.txt). The static export loads marimo frontend assets from its CDN; the original marimo license is retained unchanged.
