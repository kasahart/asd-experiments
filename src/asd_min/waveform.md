# waveform.py — W1複素減算とSSスペクトル減算

## W1 — 2本の録音の大きさと位相を合わせる

**入出力：** 同期した近接・遠方の2ch波形から、近接側に残る1ch波形を作ります。STFTで得た複素成分を`C[f,t]`、`F[f,t]`とすると、周波数ごとの係数を録音全体で求めます。

```text
H[f] = sum_t C[f,t] conj(F[f,t]) / (sum_t |F[f,t]|^2 + 1e-12)
Y[f,t] = C[f,t] - H[f] F[f,t]
```

| 式・手順 | 関数（[`waveform.py`](waveform.py)） |
|---|---|
| 共同peakを0.9へ正規化 | `peak_normalize()` |
| `H[f]` | `w1_transfer()` |
| `Y[f,t]` | `w1_residual()` |
| STFT→`H`→`Y`→ISTFT→scale復元 | `w1()` |

**直感：** `H`は複素数なので、大きさの倍率と位相のずれを同時に調整します。調整後の遠方成分を近接から引いた二乗残差が小さくなるよう、各周波数に一つの係数を求めます。学習済みの分離モデルを追加せずに、入力の変更だけを比較できる処理として使っています。

式は既存の複素最小二乗に基づき、同じ形の減算は[Ozeki技術報告](https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Ozeki_101_t2.pdf)にもあります。

STFTの窓・長さなどの固定値は[実験1の固定条件](../../docs/02-protocol.md)にまとめています。

## SS — 調整係数を求めず、成分の大きさを引く

**入出力：** 2ch波形から、近接位相を使った1ch波形を作ります。`a=|C|`、`b=|F|`として、各時間・周波数位置で次を計算します。

```text
a > beta×b なら、出力の大きさは a - beta×b
それ以外なら、出力の大きさは gamma×a
beta=1、gamma=0.1。位相は近接側。
```

| 式・手順 | 関数（[`waveform.py`](waveform.py)） |
|---|---|
| 上の大きさと近接位相 | `ss_spectrum()` |
| STFT→`ss_spectrum()`→ISTFT | `ss()` |

条件名から処理への対応は`CONDITION_AUDIO`（B0=`near_channel`、B1=`far_channel`、W1=`w1`、SS=`ss`）です。W1・SSのSTFT設定は`W1_PARAMETERS`・`SS_PARAMETERS`にまとめています。

**直感と役割：** W1のように複素係数を合わせる処理と、大きさだけを引く処理を、同じ検知器で比較します。式は[Chu・Qian技術報告](https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Qian_65_t2.pdf) Section 2.1由来で、`0 < a-b < 0.1a`の小さな正の差も切り上げず、その差を使います。`a <= b`（等しい、または遠方の方が大きい）なら0.1倍を残します。

SSの固定値も[実験1の固定条件](../../docs/02-protocol.md#追加条件ss)と[SS config](../../configs/02_ss.json)にあります。


## 実録音の表示

[marimoアプリ](../../apps/README.md)の図はWandas 0.8.0で作成し、全条件で軸と色範囲を揃えています。機械音だけの正解波形はないため、保持率は算出しません。

元データから再描画するには、[公式データと録音checksum](../../docs/02-inputs.md)を確認し、`ASD_DATA_ROOT`を`ToothBrush`があるディレクトリに設定します。重みは不要です。

```bash
python -m pip install -e '.[visualization]'
ASD_DATA_ROOT=/path/to/eval_data/raw python scripts/render_recording.py
```

図は`outputs/recording-figures`へ保存します。保存先は`ASD_FIGURE_OUTPUT`で変更できます。スクリプトは2ch波形に共通の`condition_audio()`を適用してから近接側を取り出し、波形・STFT・Welchスペクトルを描きます（W1の係数は全6秒で推定）。


`tests/synthetic.py`の`synthetic()`は波形処理の単体テスト用入力です。

[前：BEAM＋VarMin](beam.md) / [公開コード](waveform.py) / [次：共通runner](runner.md)
