# waveform.py — W1複素減算とSSスペクトル減算

## W1 — 2本の録音の大きさと位相を合わせる

**入出力：** 同期した近接・遠方の2ch波形から、近接側に残る1ch波形を作ります。STFTで得た複素成分を $`C_{f,t}`$、$`F_{f,t}`$ とすると、周波数ごとの係数を録音全体で求めます。

```math
\begin{aligned}
H_f &= \frac{\sum_t C_{f,t}\, \overline{F_{f,t}}}{\sum_t \lvert F_{f,t} \rvert^2 + 10^{-12}} \\
Y_{f,t} &= C_{f,t} - H_f\, F_{f,t}
\end{aligned}
```

| 式・手順 | 関数（[`waveform.py`](waveform.py)） |
|---|---|
| 共同peakを0.9へ正規化 | `peak_normalize()` |
| $`H_f`$ | `w1_transfer()` |
| $`Y_{f,t}`$ | `w1_residual()` |
| STFT→$`H`$→$`Y`$→ISTFT→scale復元 | `w1()` |

**直感：** $`H_f`$ は複素数なので、大きさの倍率と位相のずれを同時に調整します。調整後の遠方成分を近接から引いた二乗残差が小さくなるよう、各周波数に一つの係数を求めます。学習済みの分離モデルを追加せずに、入力の変更だけを比較できる処理として使っています。

式は既存の複素最小二乗に基づき、同じ形の減算は[Ozeki技術報告](https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Ozeki_101_t2.pdf)にもあります。

STFTの窓・長さなどの固定値は[実験1の固定条件](../../docs/02-protocol.md)にまとめています。

## SS — 調整係数を求めず、成分の大きさを引く

**入出力：** 2ch波形から、近接位相を使った1ch波形を作ります。$`a = \lvert C_{f,t} \rvert`$、$`b = \lvert F_{f,t} \rvert`$ として、各時間・周波数位置で出力の大きさを次のように決め、位相は近接側を使います。

```math
\lvert Y_{f,t} \rvert =
\begin{cases}
a - \beta b & (a > \beta b) \\
\gamma a & (\text{otherwise})
\end{cases}
\qquad \beta = 1,\ \gamma = 0.1
```

| 式・手順 | 関数（[`waveform.py`](waveform.py)） |
|---|---|
| 上の大きさと近接位相 | `ss_spectrum()` |
| STFT→`ss_spectrum()`→ISTFT | `ss()` |

**直感と役割：** W1のように複素係数を合わせる処理と、大きさだけを引く処理を、同じ検知器で比較します。式は[Chu・Qian技術報告](https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Qian_65_t2.pdf) Section 2.1由来で、$`0 < a-b < 0.1a`$ の小さな正の差も切り上げず、その差を使います。$`a \le b`$（等しい、または遠方の方が大きい）なら0.1倍を残します。

SSの固定値も[実験1の固定条件](../../docs/02-protocol.md#追加条件ss)にあります。
