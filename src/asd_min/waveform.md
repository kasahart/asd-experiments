# waveform.py — W1複素減算とSSスペクトル減算

各モジュールの役割と由来は[実装案内](README.md)にまとめています。ここでは対応する公開コードだけを説明します。自前の実装と、手法の独自提案は区別します。

## W1 — 2本の録音の大きさと位相を合わせる

**入出力：** 同期した近接・遠方の2ch波形から、近接側に残る1ch波形を作ります。STFTで得た複素成分を`C[f,t]`、`F[f,t]`とすると、周波数ごとの係数を録音全体で求めます。

```text
H[f] = sum_t C[f,t] conj(F[f,t]) / (sum_t |F[f,t]|^2 + 1e-12)
Y[f,t] = C[f,t] - H[f] F[f,t]
```

**直感：** `H`は複素数なので、大きさの倍率と位相のずれを同時に調整します。調整後の遠方成分を近接から引いた二乗残差が小さくなるよう、各周波数に一つの係数を求めます。学習済みの分離モデルを追加せずに、入力の変更だけを比較できる処理として使っています。

式は既存の複素最小二乗に基づき、同じ形の減算は[Ozeki技術報告](https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Ozeki_101_t2.pdf)にもあります。そのシステム全体の再現ではありません。今回の実装はMIT研究snapshotの`complex_least_squares_cancel()`を必要範囲だけ移したものです。

共同peakを0.9へ正規化、Torch periodic Hann、STFT1,024/hop512、center=True/reflect、全フレームで係数推定、元長で逆変換してscaleを復元します。説明用合成図で端のフレームを除く処理は実測に持ち込みません。遠方にも機械音があるため、残したい異常の手掛かりを削る可能性があります。録音中に伝わり方が変わっても係数は更新しません。

## SS — 調整係数を求めず、成分の大きさを引く

**入出力：** 2ch波形から、近接位相を使った1ch波形を作ります。`a=|C|`、`b=|F|`として、各時間・周波数位置で次を計算します。

```text
a > beta×b なら、出力の大きさは a - beta×b
それ以外なら、出力の大きさは gamma×a
beta=1、gamma=0.1。位相は近接側。
```

**直感と役割：** W1のように複素係数を合わせる処理と、大きさだけを引く処理を、同じ検知器で比較します。式は[Qian技術報告Section2.1](https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Qian_65_t2.pdf)由来で、チームのソースコードをコピーしたものではありません。`0 < a-b < 0.1a`の小さな正の差も切り上げず、その差を使います。`a <= b`（等しい、または遠方の方が大きい）なら0.1倍を残します。常に`max(a-b,0.1a)`とする実装ではありません。

実験用はHann512/hop256。報告が未指定のperiodic Hann・center=True/reflect・入力正規化なしはローカル実装で固定しています。QianのEAT/KNNやloopingは使わず、その全システムの成績を再現する条件でもありません。[SS config](../../configs/02_ss.json)、[実験記録](../../docs/ss-validation.md)


[前：BEAM＋VarMin](beam.md) / [公開コード](waveform.py) / [次：共通runner](runner.md)
