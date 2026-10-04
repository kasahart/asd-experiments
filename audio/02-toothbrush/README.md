# ToothBrushの4条件を聞き比べる

Notebook第3節と同じ正常録音のB0・B1・W1・SSです。各WAVは全長6秒、16 kHz、モノラル、PCM16。Notebookの音声プレーヤーに埋め込んだWAVをそのまま保存し、条件ごとの正規化は追加していません。

| 条件 | 音声 |
|---|---|
| B0：近接マイク | [b0.wav](b0.wav) |
| B1：遠方マイク | [b1.wav](b1.wav) |
| W1：複素減算 | [w1.wav](w1.wav) |
| SS：スペクトル減算 | [ss.wav](ss.wav) |

## 出典と利用条件

出典：[DCASE 2026 Challenge Task 2 Additional Training Dataset v1](https://zenodo.org/records/20151556)、DOI: 10.5281/zenodo.20151556。作成者：Tomoya Nishida、Noboru Harada、Daiki Takeuchi、Daisuke Niizumi、Keisuke Imoto、Kota Dohi、Harsh Purohit、Takashi Endo、Yohei Kawaguchi。データ提供：Hitachi Ltd. / NTT Inc.

使用録音：`ToothBrush/train/section_00_source_train_normal_0000_noAttribute.wav`。加工：近接・遠方チャネルの選択、W1複素減算、SSスペクトル減算、PCM16音声化。音声はコードのMITとは別に[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)で提供します。再配布・改変には帰属表示・非商用・継承の条件が適用されます。[帰属と加工内容](../../notebooks/DATA_ATTRIBUTION.md)を参照してください。配布元による本実装の推奨を意味しません。
