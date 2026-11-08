# beam.py — 正常参照との比較とVarMin補正

BEAMで正常参照と比較し、VarMinでスコアを補正します。

## BEAM — 周波数ごとに、似た正常音を選ぶ

**入出力：** 正常録音の特徴`[N,F,D]`を参照として保持し、調べる録音の`[F,D]`と比較します。ここでの距離はL2正規化した特徴のscaled cosineです。

```math
\begin{aligned}
D(q_f, y_{i,f}) &= \tfrac{1}{2}\left(1 - \cos(q_f, y_{i,f})\right) \\
s^{\mathrm{raw}}_f &= \min_i D(q_f, y_{i,f}) \\
s^{\mathrm{raw}} &= \frac{1}{F}\sum_{f=1}^{F} s^{\mathrm{raw}}_f
\end{aligned}
```

| 式 | 関数 |
|---|---|
| $`D(q_f, y_{i,f})`$ | [`band_distance.py`](band_distance.py)の`cosine_distance()`（正規化済み特徴には`_cosine_distance_normalized()`） |
| $`s^{\mathrm{raw}}_f`$ | `band_distance.nearest_reference()`（最小値と、選んだ参照のindex） |
| $`s^{\mathrm{raw}}`$ | [`beam.py`](beam.py)の`band_mean()` |

**直感：** 低い帯域は正常録音A、高い帯域は正常録音Bと似ている場合があります。一つの正常録音に全帯域が同時に似ていることを要求せず、帯域ごとに参照を選びます。正常な成分の組み合わせが変わっただけで距離が大きくなる問題を抑える、という[BEAM論文](https://arxiv.org/html/2603.13749)の設計に基づきます。

CSVの異常度には、次節のVarMin補正後の $`s`$（`main`）を使います。

## VarMin — 正常音でも生じる距離の偏りを補正する

**入出力：** 正常参照間の距離から、各参照の近傍距離 $`b_{i,f}`$ と帯域ごとの補正係数 $`\alpha_f`$ を推定します。それをBEAMの参照比較へ加えます。

**直感：** 正常参照でも、密集した場所にある特徴と、周りに似た参照が少ない特徴があります。単純な距離だけでは、後者を参照する正常音のスコアが大きくなることがあります。近傍への距離を手掛かりに、その偏りを補正します。

```math
\begin{aligned}
b_{i,f} &= \frac{1}{4}\sum_{k \in \mathcal{N}_4(i,f)} D(y_{i,f}, y_{k,f}) \\
j(z,f) &= \mathop{\mathrm{arg\,min}}\limits_{i \neq z} D(y_{z,f}, y_{i,f}) \\
u_{z,f} &= D(y_{z,f}, y_{j(z,f),f}), \qquad v_{z,f} = b_{j(z,f),f} \\
\alpha_f &= \frac{\mathrm{Cov}_z(u_{z,f}, v_{z,f})}{\mathrm{Var}_z(v_{z,f})} \\
s_f &= \min_i \left\{ D(q_f, y_{i,f}) - \alpha_f\, b_{i,f} \right\} \\
s &= \frac{1}{F}\sum_{f=1}^{F} s_f
\end{aligned}
```

$`\mathcal{N}_4(i,f)`$ は帯域 $`f`$ で参照 $`i`$ に近い、自己を除く正常参照4件、$`j(z,f)`$ は正常train参照 $`y_z`$ の自己を除く最近傍です。

| 式 | 関数（[`varmin.py`](varmin.py)） |
|---|---|
| $`b_{i,f}`$ | `compute_local_density()` |
| $`j(z,f)`$、$`u_{z,f}`$ | `leave_one_out_nearest()` |
| $`v_{z,f}`$ と全体の手順 | `estimate_train_all_alpha()` |
| $`\alpha_f`$ | `variance_minimizing_alpha()` |
| $`D - \alpha_f b_{i,f}`$ | `rescaled_distance()` |
| $`s_f`$、$`s`$ | `band_distance.nearest_reference()`・`beam.band_mean()`（[`beam.py`](beam.py)の`BEAMVarianceMin`が両者をまとめます） |

`BEAMVarianceMin`は[ASDKit](https://github.com/TakuyaFujimura/dcase-asd-toolkit)のbackend形式（`fit()`・`anomaly_score()`）です。

$`\alpha_f`$ は正常train全件をleave-one-outで使い、帯域ごとに求めます。補正後のスコアは0以上にclipしないので、負になることもあります。

係数の分散最小化は[VarMin論文](https://dcase.community/documents/workshop2025/proceedings/DCASE2025Workshop_Matsumoto_12.pdf)に由来します。近傍4件は[NA-SSL論文](https://arxiv.org/html/2608.00447v1)に合わせています。
