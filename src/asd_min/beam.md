# beam.py — 正常参照との比較とVarMin補正

BEAMで正常参照と比較し、VarMinでスコアを補正します。

## BEAM — 周波数ごとに、似た正常音を選ぶ

**入出力：** 正常録音の特徴`[N,F,D]`を参照として保持し、調べる録音の`[F,D]`と比較します。ここでの距離はL2正規化した特徴のscaled cosineです。

```text
D(q[f], y[i,f]) = 0.5 × (1 - cosine(q[f], y[i,f]))
raw_band[f] = min_i D(q[f], y[i,f])
raw_score = 周波数方向の一様平均(raw_band)
```

| 式 | 関数 |
|---|---|
| `D(q[f], y[i,f])` | [`band_distance.py`](band_distance.py)の`cosine_distance()`（正規化済み特徴には`_cosine_distance_normalized()`） |
| `raw_band[f] = min_i D` | `band_distance.nearest_reference()`（最小値と、選んだ参照のindex） |
| `raw_score` | [`beam.py`](beam.py)の`band_mean()` |

**直感：** 低い帯域は正常録音A、高い帯域は正常録音Bと似ている場合があります。一つの正常録音に全帯域が同時に似ていることを要求せず、帯域ごとに参照を選びます。正常な成分の組み合わせが変わっただけで距離が大きくなる問題を抑える、という[BEAM論文](https://arxiv.org/html/2603.13749)の設計に基づきます。

正常メモリは、source990件とtarget10件を一緒に使います。domain別に二つのメモリを作る方法や、帯域の音量による重み付けは使いません。条件ごとにメモリを構築し、各条件で加工した正常音から構築します。

CSVの異常度には、次節のVarMin補正後の`main`を使います。

## VarMin — 正常音でも生じる距離の偏りを補正する

**入出力：** 正常参照間の距離から、各参照の近傍距離`b[i,f]`と帯域ごとの補正係数`alpha[f]`を推定します。それをBEAMの参照比較へ加えます。

**直感：** 正常参照でも、密集した場所にある特徴と、周りに似た参照が少ない特徴があります。単純な距離だけでは、後者を参照する正常音のスコアが大きくなることがあります。近傍への距離を手掛かりに、その偏りを補正します。

```text
b[i,f] = 参照iから、自己を除く近い正常参照4件への距離の平均
j(z,f) = 正常train参照y[z]の、自己を除くraw最近傍のindex
u[z,f] = D(y[z,f], y[j(z,f),f])
v[z,f] = b[j(z,f),f]
alpha[f] = Cov_z(u[z,f], v[z,f]) / Var_z(v[z,f])
main_band[f] = min_i { D(q[f], y[i,f]) - alpha[f] b[i,f] }
main_score = 周波数方向の一様平均(main_band)
```

| 式 | 関数（[`varmin.py`](varmin.py)） |
|---|---|
| `b[i,f]` | `compute_local_density()` |
| `j(z,f)`、`u[z,f]` | `leave_one_out_nearest()` |
| `v[z,f]`と全体の手順 | `estimate_train_all_alpha()` |
| `alpha[f]` | `variance_minimizing_alpha()` |
| `D - alpha[f] b[i,f]` | `rescaled_distance()` |
| `main_band`、`main_score` | `band_distance.nearest_reference()`・`beam.band_mean()`（[`beam.py`](beam.py)の`BEAMVarianceMin`が両者をまとめます） |

`BEAMVarianceMin`は[ASDKit](https://github.com/TakuyaFujimura/dcase-asd-toolkit)のbackend形式（`fit()`・`anomaly_score()`）を保ちます。`anomaly_score_details()`は帯域ごとのスコアと、選ばれた参照のindex・特徴・密度・`alpha`を返す診断出力です。

正常train全件を一つずつ仮の検証音にするのが`train_all`、自己を比較相手から外すのがleave-one-out、帯域ごとに係数を求めるのが`per_band`です。`alpha`の分母が`eps=1e-12`以下なら0とし、係数や最終スコアを0以上にclipしません。したがって異常度は負になることもあります。補正後に全参照から最小値を選び直します。

係数の分散最小化は[VarMin論文](https://dcase.community/documents/workshop2025/proceedings/DCASE2025Workshop_Matsumoto_12.pdf)に由来します。近傍4件は[NA-SSL論文](https://arxiv.org/html/2608.00447v1)に合わせています。この実装では、共有正常メモリ・train_all・per_bandを使い、帯域平均の前に補正します。

条件比較では同じ検知器を使います。


[公開コード：beam.py](beam.py)・[varmin.py](varmin.py)・[band_distance.py](band_distance.py) / [前：RDP](pooling.md) / [次：波形処理（W1/SS）](waveform.md)
