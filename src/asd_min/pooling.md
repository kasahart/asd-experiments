# pooling.py — 周波数を残すRDP集約

RDPの原論文は[Temporal Pooling Strategies論文](https://arxiv.org/html/2603.04605v3)（Section III-E）です。採用した`gamma=4`とbackendの組み合わせは[NA-SSL論文](https://arxiv.org/html/2608.00447v1)を参照しています。

## RDP — 平均から離れた短い区間を重くする

**入出力：** 関数は`[B,T,F,D]`を受け取り、時間方向へ集約した`[B,F,D]`を返します。runnerは録音1件を`B=1`で処理し、`[0]`を取り出して`[F,D]`を保持します。下の式は録音1件の特徴を表します。

周波数`f`の時点`t`の特徴を`x[t,f]`とすると、計算の中心は次の重み付き平均です。

```text
mu[f] = 時間方向の平均特徴
r[t,f] = ||x[t,f] - mu[f]|| / max_t ||x[t,f] - mu[f]||
w[t,f] = (1 + r[t,f])^gamma / sum_t (1 + r[t,f])^gamma
q[f] = sum_t w[t,f] x[t,f]
```

| 式 | 関数（[`pooling.py`](pooling.py)） |
|---|---|
| `mu[f]` | `time_mean()` |
| `r[t,f]` | `relative_deviation()` |
| `w[t,f]` | `deviation_weights()` |
| `q[f]` | `weighted_time_sum()` |
| 全体 | `relative_deviation_pooling()`（`frequency_pooling(mode="rdp")`から呼ばれます） |

**直感：** ずっと似た音が続く中で、短い区間だけ特徴が変わると、普通の平均では薄まります。RDPは平均から離れた区間を重くし、その変化を集約後にも残しやすくします。

`gamma=4`は[NA-SSL論文](https://arxiv.org/html/2608.00447v1)に沿った固定値で、最大偏差が`eps=1e-8`以下なら均等な時間平均になります。公開実装は、任意の有効時間mask、有限値検査、数値overflowを避ける内部scaleとlog/softmaxによる重み計算も備えます。これらは基本式を安定に計算する実装上の工夫です。

論文ではbackendの集約として扱う処理を、この実装では特徴抽出時に行います。runnerは`[F,D]`だけを保持し、全パッチ列を全録音分保存しません。


[公開コード](pooling.py) / [次：BEAM＋VarMin](beam.md)
