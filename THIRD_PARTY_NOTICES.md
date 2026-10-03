# Third-party notices

Selected source snapshots and modifications are listed in [出典と利用条件](docs/rights.md) and [import-manifest](docs/import-manifest.json).

The code combines the ASDKit foundation with implementations of BEAM/VarMin, RDP, and W1.

- **ASDKit foundation (`base.py`)**: derived from [ASDKit](https://github.com/TakuyaFujimura/dcase-asd-toolkit). [licenses/research-MIT.txt](licenses/research-MIT.txt) is byte-identical to the [ASDKit LICENSE](https://github.com/TakuyaFujimura/dcase-asd-toolkit/blob/main/LICENSE), including Copyright (c) 2025 Takuya Fujimura.
- **BEAM/VarMin (`beam.py`)**: a reproduction implementation on the ASDKit foundation.  The research MIT notice is retained.
- **RDP (`pooling.py`)**: an implementation of the pooling method in [NA-SSL論文](https://arxiv.org/html/2608.00447v1). The received [licenses/beam-tfattr-MIT.txt](licenses/beam-tfattr-MIT.txt), including Copyright (c) 2025 Takuya Fujimura, is retained unchanged.
- BEATs, backbone and modules: Microsoft MIT headers and an extension for grid extraction. Retained [BEATs LICENSE](src/asd_min/beats/LICENSE), [NOTICE](src/asd_min/beats/NOTICE.md), and research MIT notice. Three Python files are copied byte-for-byte from the selected research snapshot; package-only `__init__.py` is new and intentionally omits optional training/tokenizer imports.
- **W1**: waveform.py uses joint normalization, Torch STFT/ISTFT and full-recording complex least-squares. The received research MIT notice is retained. Additional validation/loading helpers are companion code.

New companion CLI, notebook and documentation are licensed under the root MIT LICENSE, Copyright (c) 2026 kasahart. Third-party LICENSE/NOTICE texts are retained.

SS implements the magnitude equation in [Chu・Qian技術報告](https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Qian_65_t2.pdf), Section 2.1.

## 参考文献

本文の短名と正式タイトルは次の対応です。

| 短名 | 正式タイトル |
|---|---|
| [BEATs論文](https://proceedings.mlr.press/v202/chen23ag.html) | BEATs: Audio Pre-Training with Acoustic Tokenizers |
| [BEAM論文](https://arxiv.org/html/2603.13749) | Sub-Band Spectral Matching with Localized Score Aggregation for Robust Anomalous Sound Detection |
| [VarMin論文](https://dcase.community/documents/workshop2025/proceedings/DCASE2025Workshop_Matsumoto_12.pdf) | Adjusting Bias in Anomaly Scores via Variance Minimization for Domain-Generalized Discriminative Anomalous Sound Detection |
| [NA-SSL論文](https://arxiv.org/html/2608.00447v1) | Anomalous Sound Detection Meets Noise-Aware Self-Supervised Learning |
| [MERL技術報告](https://www.merl.com/publications/docs/TR2026-100.pdf) | The MERL Systems for DCASE 2026 Challenge Task 2 |
| [Ozeki技術報告](https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Ozeki_101_t2.pdf) | Anomalous Sound Detection Method with Simple Noise Reduction |
| [Chu・Qian技術報告](https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Qian_65_t2.pdf) | Anomalous Sound Detection System for DCASE 2026 Task 2 Using Dual-Channel Spectral Subtraction and Efficient Audio Transformer |
