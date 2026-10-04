# BEATs.py — 既存モデルとグリッド抽出拡張

## BEATsのグリッド抽出 — 周波数を残すための拡張

**入出力：** 1ch波形から、固定BEATs_iter3の最終Transformer特徴列と、パッチ畳み込みが作った`(T,F)`を得ます。[pooling.py](../pooling.py)の`sequence_to_time_frequency()`は`L=T×F`を確認し、特徴列`[B,L,D]`を時間×周波数の並び`[B,T,F,D]`へ戻します。`B`はbatch数で、録音1件の抽出では`B=1`です。

**直感と役割：** すべてのパッチを一つに平均すると、低い音と高い音の違いが失われます。実際の畳み込み出力からグリッドを取り出すことで、その後に周波数ごとの集約・参照比較ができます。`F`を決め打ちせず、同じforwardで形状を返します。

モデルは[BEATs論文](https://proceedings.mlr.press/v202/chen23ag.html)に基づき、公開コードと重みは[BEATs](https://github.com/microsoft/unilm/tree/master/beats)を使います。`extract_features_with_grid()`は特徴列とパッチのグリッド形状を返す拡張です。固定した事前学習済みモデルから特徴を抽出します。

[公開コード](BEATs.py) / [抽出を呼ぶrunner](../runner.py) / [次：RDP](../pooling.md)
