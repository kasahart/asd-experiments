# 実録音由来の図と音声の帰属

対象は、リポジトリに含まれる音声データ（アプリ内の埋め込み音声を含む）と、実録音由来の図です。これらは[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)で提供します。コード・説明文はMITです。

## 第2回：ToothBrushの実録音

出典：[DCASE 2026 Challenge Task 2 Additional Training Dataset v1](https://zenodo.org/records/20151556)、DOI: 10.5281/zenodo.20151556。作成者：Tomoya Nishida、Noboru Harada、Daiki Takeuchi、Daisuke Niizumi、Keisuke Imoto、Kota Dohi、Harsh Purohit、Takashi Endo、Yohei Kawaguchi。データ提供：Hitachi Ltd. / NTT Inc. 元データの利用条件：CC BY-NC-SA 4.0。

使用録音：`ToothBrush/train/section_00_source_train_normal_0000_noAttribute.wav`。加工：近接・遠方チャンネルの選択、W1複素減算、SSスペクトル減算、全録音6秒の波形・STFT・周波数スペクトル描画、PCM16音声化。原録音チャンネルB0・B1と加工音W1・SSの計4件（各6秒）を、アプリに手動再生コントロール付きで埋め込み、同じPCM16音声を独立WAVでも保存しています。条件ごとの正規化は追加していません。図・音声の再配布・改変は帰属表示、非商用、継承の条件に従ってください。配布元による本実装の推奨を意味しません。保証については元ライセンスの免責条件に従います。
