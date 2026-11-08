# 入力の取得（DCASE 2026 Task 2）

全実験で使うデータ・重み・評価器の取得先と配置です。

1. [DCASE 2026 Challenge Task 2 Additional Training Dataset](https://zenodo.org/records/20151556)の5機種train ZIPと[DCASE 2026 Challenge Task 2 Evaluation Dataset](https://zenodo.org/records/20437238)の5機種test ZIPを取得し、同じ `eval_data/raw` に展開します。
2. [BEATs README](https://github.com/microsoft/unilm/blob/master/beats/README.md)の **Pre-Trained Model / Iter3** を取得します。
3. 採点には[dcase2026_task2_evaluator](https://github.com/nttcslab/dcase2026_task2_evaluator/blob/f6a94a2b5e614a9626c9d1ccff6df0705e6aaa75/README.md)（`f6a94a2`版）と付属正解を使います。

```text
<INPUT>/BlowerDustCollector/{train,test}/*.wav
<INPUT>/Sander/{train,test}/*.wav
<INPUT>/SewingMachine/{train,test}/*.wav
<INPUT>/ToothBrush/{train,test}/*.wav
<INPUT>/ToyDrone/{train,test}/*.wav
```

ch0近接/ch1遠方、16 kHz stereo。各機種train1000/test200。

## Development（構成の選択用）

[DCASE 2026 Challenge Task 2 Development Dataset](https://zenodo.org/records/19336329)の7機種ZIP（`dev_ToyCar_r2.zip`、`dev_ToyCarEmu.zip`、`dev_bearingEmu.zip`、`dev_fan.zip`、`dev_gearboxEmu.zip`、`dev_sliderEmu.zip`、`dev_valveEmu.zip`）を同じ `dev_data/raw` に展開します。`dev_ToyCar_r2.zip`は`ToyCar`として展開されます。

```text
<INPUT>/{ToyCar,ToyCarEmu,bearingEmu,fan,gearboxEmu,sliderEmu,valveEmu}/{train,test}/*.wav
```

録音形式と件数はEvaluationと同じです（train1000はsource990/target10）。ToyCarは4月8日修正版`dev_ToyCar_r2.zip`（MD5 `353201db217e25377a7e7eccf9c1c8a7`）を使います。

## Checksum

2026-10-03にZenodoで確認したZIPのMD5です（`md5sum`で確認）。

| zip | MD5 |
|---|---|
| eval_data_BlowerDustCollector_train.zip | e79342948772cf51e50ff601cd9621f3 |
| eval_data_Sander_train.zip | 6cbcfbc65a09c4f3d00b9a55c50502ec |
| eval_data_SewingMachine_train.zip | 74d08cacba3da88753badd69d19e577b |
| eval_data_ToothBrush_train.zip | 6fa5f81796b5d37b3ed24bb8eff2ea25 |
| eval_data_ToyDrone_train.zip | af3e4040ef7c67d7ee920608d0c38d82 |
| eval_data_BlowerDustCollector_test.zip | ec90d56f189e84e6430fb2878c59cb84 |
| eval_data_Sander_test.zip | 05f81c9a80e91c7b3cea15f8e8559b44 |
| eval_data_SewingMachine_test.zip | f0a1a96b48006c301e8cec25e9214046 |
| eval_data_ToothBrush_test.zip | 987395506fbb48c570d5d26babcab05e |
| eval_data_ToyDrone_test.zip | b36102371c188b630d201d443a00bab2 |

BEATs_iter3.pt（約345 MiB）のSHA-256は`8d1b234032a9ccff353612dc6c20982346dc2968b205b79d97303eb5e77bfb34`です。Evaluation用データはZIPで約3.4 GB、展開後に約4 GBです。
