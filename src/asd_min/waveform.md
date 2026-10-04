# waveform.py — W1複素減算とSSスペクトル減算

## W1 — 2本の録音の大きさと位相を合わせる

**入出力：** 同期した近接・遠方の2ch波形から、近接側に残る1ch波形を作ります。STFTで得た複素成分を`C[f,t]`、`F[f,t]`とすると、周波数ごとの係数を録音全体で求めます。

```text
H[f] = sum_t C[f,t] conj(F[f,t]) / (sum_t |F[f,t]|^2 + 1e-12)
Y[f,t] = C[f,t] - H[f] F[f,t]
```

**直感：** `H`は複素数なので、大きさの倍率と位相のずれを同時に調整します。調整後の遠方成分を近接から引いた二乗残差が小さくなるよう、各周波数に一つの係数を求めます。学習済みの分離モデルを追加せずに、入力の変更だけを比較できる処理として使っています。

式は既存の複素最小二乗に基づき、同じ形の減算は[Ozeki技術報告](https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Ozeki_101_t2.pdf)にもあります。

共同peakを0.9へ正規化、Torch periodic Hann、STFT1,024/hop512、center=True/reflect、全フレームで係数推定、元長で逆変換してscaleを復元します。

## SS — 調整係数を求めず、成分の大きさを引く

**入出力：** 2ch波形から、近接位相を使った1ch波形を作ります。`a=|C|`、`b=|F|`として、各時間・周波数位置で次を計算します。

```text
a > beta×b なら、出力の大きさは a - beta×b
それ以外なら、出力の大きさは gamma×a
beta=1、gamma=0.1。位相は近接側。
```

**直感と役割：** W1のように複素係数を合わせる処理と、大きさだけを引く処理を、同じ検知器で比較します。式は[Chu・Qian技術報告](https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Qian_65_t2.pdf) Section 2.1由来で、`0 < a-b < 0.1a`の小さな正の差も切り上げず、その差を使います。`a <= b`（等しい、または遠方の方が大きい）なら0.1倍を残します。

実験用はHann512/hop256。報告が未指定のperiodic Hann・center=True/reflect・入力正規化なしはローカル実装で固定しています。[SS config](../../configs/02_ss.json)、[第2回の検証範囲](../../docs/02-validation.md)


## 実録音の表示

NotebookはToothBrushの正常録音0000を全6秒処理し、可視化と手動試聴には全長6秒のデータを使います。Notebook内でSHA-256を確認し、`wd.read()`で読み込みます。B0・B1はチャンネルを選択し、W1・SSは`apply()`から実験と同じ`condition_audio()`を呼びます。`apply()`内では2chを保ち、処理後の近接側を取り出します。W1の係数を表示区間だけで推定し直しません。Wandasの`describe`で4条件の軸と色範囲を揃え、試聴用プレーヤーも個別正規化なしで表示します。機械音だけの正解波形はないため、保持率は算出しません。[図の出典・利用条件](../../notebooks/DATA_ATTRIBUTION.md)

`synthetic()`は波形処理の単体テスト用入力です。

[前：BEAM＋VarMin](beam.md) / [公開コード](waveform.py) / [次：共通runner](runner.md)
