# pooling.py — 周波数を残すRDP集約

RDPの原論文は[Temporal Pooling Strategies論文](https://arxiv.org/html/2603.04605v3)（Section III-E）です。採用した`gamma=4`とbackendの組み合わせは[NA-SSL論文](https://arxiv.org/html/2608.00447v1)を参照しています。

## RDP — 平均から離れた短い区間を重くする

**入出力：** 時間×周波数パッチの特徴`[T,F,D]`を、時間方向へ集約して`[F,D]`にします。

周波数 $`f`$ の時点 $`t`$ の特徴を $`x_{t,f}`$ とすると、計算の中心は次の重み付き平均です。

```math
\begin{aligned}
\mu_f &= \frac{1}{T}\sum_{t=1}^{T} x_{t,f} \\
r_{t,f} &= \frac{\lVert x_{t,f} - \mu_f \rVert}{\max_{t'} \lVert x_{t',f} - \mu_f \rVert} \\
w_{t,f} &= \frac{(1 + r_{t,f})^{\gamma}}{\sum_{t'} (1 + r_{t',f})^{\gamma}} \\
q_f &= \sum_{t} w_{t,f}\, x_{t,f}
\end{aligned}
```

| 式 | 関数（[`pooling.py`](pooling.py)） |
|---|---|
| $`\mu_f`$ | `time_mean()` |
| $`r_{t,f}`$ | `relative_deviation()` |
| $`w_{t,f}`$ | `deviation_weights()` |
| $`q_f`$ | `weighted_time_sum()` |
| 全体 | `relative_deviation_pooling()`（`frequency_pooling(mode="rdp")`から呼ばれます） |

**直感：** ずっと似た音が続く中で、短い区間だけ特徴が変わると、普通の平均では薄まります。RDPは平均から離れた区間を重くし、その変化を集約後にも残しやすくします。

論文ではbackendの集約として扱う処理を、この実装では特徴抽出時に行います。
