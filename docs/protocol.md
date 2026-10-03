# 第2回の固定条件

Evaluationの5機種。正常参照はAdditional Trainingの各1000正常音（source990/target10）。匿名Evaluationの各200テスト音を採点。Developmentへの流用やtest正解による学習・閾値選択はしません。

- ch0=near、ch1=far、16 kHzの同期2chを維持。B0=ch0/B1=ch1/W1=同じ2chからの残差。
- frozen **BEATs_iter3**、FP32、AMPなし、TF32なし。音声全体をbatch1で特徴抽出。周波数パッチを保持し、時間方向のRDP gamma=4、eps=1e-8。
- BEAM VarMin4、scaled cosine `0.5*(1-cos)`、正常train_all参照、密度は自身を除く近傍4件、alphaはtrain_allのleave-one-outで周波数別に推定。補正後に参照最小値、周波数の一様平均。条件ごとに参照を新規構築。
- 正常train再採点でも自身を除外。条件・機種ごとの正常trainスコア90%点（linear）、判定は厳密な `score > threshold`。
- W1: 共同peakを0.9へ正規化（peak<=1e-12ならscale1）、float32。TorchHann periodic、STFT1024/window1024/hop512、center=True、reflect、normalized=False、onesided=True。録音の端も含めた全フレームで `H=sum(C*conj(F))/(sum(abs(F)^2)+1e-12)`、`Y=C-HF`。同じ窓でISTFT、元の長さ・共同scaleを復元。
- 公式evaluator fixed `f6a94a2b5e614a9626c9d1ccff6df0705e6aaa75` は読者取得、無改変。5機種のsource AUC/target AUC/pAUCの15指標の調和平均×100。故障検出率ではない。

BEAM per_bandは研究再実装で明示した仮定であり、元論文による完全保証の主張ではありません。

NotebookのWandas STFTは表示・説明用です。Wandasによる端処理や正規化はTorchの実測W1と同じと仮定しません。このNotebookのW1音声は共通計算核を使い、Wandasは可視化と手動試聴に使います。合成音はDCASE成績や実音の改善の証拠ではありません。

## 追加条件SS

近接/遠方の**大きさ**をbeta1で減算し、`near_abs > far_abs`なら差、それ以外はgamma0.1×near_absを使い、近接位相で復元します。Hann512/hop256。periodic Hann・center=True・reflect・入力正規化なしは、報告が未指定の詳細を固定したローカル選択です。[SS config](../configs/02_ss.json)。正常参照はSS処理した音から再構築します。

## 公式指標の対象

固定evaluatorのsource AUCはsourceの正常音と**両domainすべての異常音**で計算し、target AUCはtargetの正常音と両domainすべての異常音で計算します。domain内だけの異常音に限定したAUCではありません。pAUCは機種ごとの全200テスト音、max_fpr=0.1の標準化pAUCです。公式総合値は5機種のsource AUC・target AUC・pAUCの15値（epsilon clamp）の調和平均。再採点は独自の二重実装でなく、読者取得の固定公式版を使います。
