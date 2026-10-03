# Third-party notices

Selected source snapshots and modifications are listed in [docs/rights.md](docs/rights.md) and [docs/import-manifest.json](docs/import-manifest.json).

The code combines the ASDKit foundation and kasahart implementations of BEAM/VarMin, RDP, and W1.

- **ASDKit foundation (`base.py`)**: derived from [TakuyaFujimura/dcase-asd-toolkit](https://github.com/TakuyaFujimura/dcase-asd-toolkit). [licenses/research-MIT.txt](licenses/research-MIT.txt) is byte-identical to the [public upstream LICENSE](https://github.com/TakuyaFujimura/dcase-asd-toolkit/blob/main/LICENSE), including Copyright (c) 2025 Takuya Fujimura.
- **BEAM/VarMin (`beam.py`)**: a reproduction implementation added by kasahart in the research repository, on that existing foundation.  The research MIT notice is retained.
- **RDP (`pooling.py`)**: a kasahart-added implementation of the published pooling method, selected from a hash-fixed snapshot. The received [licenses/beam-tfattr-MIT.txt](licenses/beam-tfattr-MIT.txt), including Copyright (c) 2025 Takuya Fujimura, is retained unchanged.
- BEATs, backbone and modules: Microsoft MIT headers plus research modifications for grid extraction. Retained [BEATs LICENSE](src/asd_min/beats/LICENSE), [NOTICE](src/asd_min/beats/NOTICE.md), and research MIT notice. Three Python files are copied byte-for-byte from the selected research snapshot; package-only `__init__.py` is new and intentionally omits optional training/tokenizer imports.
- **W1**: waveform.py selects/adapts kasahart-added research operations for joint normalization, Torch STFT/ISTFT and full-recording complex least-squares. The received research MIT notice is retained. Additional validation/loading helpers are companion code.

BEATs reference: Sanyuan Chen et al., *BEATs: Audio Pre-Training with Acoustic Tokenizers*, ICML 2023, https://proceedings.mlr.press/v202/chen23ag.html . BEAM method reference: Takuya Fujimura et al., *The MERL Systems for DCASE 2026 Challenge Task 2*, https://www.merl.com/publications/docs/TR2026-100.pdf .

New companion CLI, notebook and documentation are licensed under the root MIT LICENSE, Copyright (c) 2026 kasahart. Third-party LICENSE/NOTICE texts are retained.

SS is a new MIT companion implementation of the magnitude equation described by Fan Chu and Mengui Qian, *Anomalous Sound Detection System for DCASE 2026 Task 2 Using Dual-Channel Spectral Subtraction and Efficient Audio Transformer*, Section 2.1, https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Qian_65_t2.pdf .
