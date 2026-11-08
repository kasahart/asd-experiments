# 評価の共通条件

全実験で共通の採点方法です。実験ごとの条件と手順は、[README](../README.md#入口)の入口表から各実験の資料を参照してください。

## Development と Evaluation

構成の選択はDevelopment 7機種（ToyCar、ToyCarEmu、bearingEmu、fan、gearboxEmu、sliderEmu、valveEmu）で行い、Evaluation 5機種は報告だけに使います。Developmentのtest正解はファイル名から読み、採点だけに使います。

## 指標

スコアはDCASE 2026 Task 2の[公式評価器](https://github.com/nttcslab/dcase2026_task2_evaluator/blob/f6a94a2b5e614a9626c9d1ccff6df0705e6aaa75/README.md)の定義に従います。

- 機種ごと：AUC_source（source正常＋全異常）、AUC_target（target正常＋全異常）、pAUC（全件、FPR 0.1まで）。公式評価器のsource-mix AUC・target-mix AUC・mixed pAUCにあたります。
- **Dev7**：Development 7機種×3指標＝21値の調和平均。選択に使います。
- **Dev5**：ToyCar・ToyCarEmuを除いた5機種×3指標＝15値の調和平均。診断用です。
- **Evaluation**：5機種×3指標＝15値の調和平均。

総合値は100倍して表示します。
