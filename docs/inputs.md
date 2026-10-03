# 読者が取得する入力

1. [Additional Training](https://zenodo.org/records/20151556)の5機種train zipと、[Evaluation](https://zenodo.org/records/20437238)の5機種test zipを取得。配布条件CC BY-NC-SA 4.0を確認してください。ZIP展開後の`eval_data/raw`を`--input`へ指定します。全5機種のtrain/testを同じrootへ揃え、匿名test名を変更しません。
2. [Microsoft BEATs公式README](https://github.com/microsoft/unilm/tree/master/beats)の **Pre-Trained Model / Iter3** を取得。Fine-tuned、Iter3+、Tokenizerは対象外です。公式project MIT案内とcheckpoint再配布時の確認は[rights.md](rights.md)へ。
3. 採点は[公式evaluator](https://github.com/nttcslab/dcase2026_task2_evaluator)と付属正解を別途取得する必要があります。取得前にLICENSEv2.1.pdfの用途条件を確認し、必要な許諾を解決してください。本コピーには入りません。

```text
<INPUT>/BlowerDustCollector/{train,test}/*.wav
<INPUT>/Sander/{train,test}/*.wav
<INPUT>/SewingMachine/{train,test}/*.wav
<INPUT>/ToothBrush/{train,test}/*.wav
<INPUT>/ToyDrone/{train,test}/*.wav
```

ch0近接/ch1遠方、16 kHz stereo。各機種train1000/test200。正常参照はtrainのみです。音声・重みをrepoへ追加せず、外部取得先のpathを指定します。

## Checksum

以下は2026-10-03にZenodo各配布ページで確認した**ZIPのMD5**です。解凍後WAVのSHA-256とは異なります。配布元が更新された場合は配布元の値を確認してください。

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

例: `md5sum eval_data_ToothBrush_test.zip`。重みは`sha256sum BEATs_iter3.pt`で確認します。
記事で使われたファイルのSHA-256は `8d1b234032a9ccff353612dc6c20982346dc2968b205b79d97303eb5e77bfb34`（既存報告の記録。本コピーでもローカル実物で一致確認）。これはMicrosoftが発行したchecksumと主張していません。CLIはこの重みを固定し、別の重みを拒否します。

## 容量と計算資源

Zenodo表示のダウンロード容量はtrain約2.8 GB、test 558.7 MB。ZIPと展開音声を同時保持するなら両方の空き容量が必要です。元の報告のWAV header件数から、PCM16 stereoの音声payloadは合計約3.99 GB（3600×10秒、1200×6秒、1200×16秒、16kHz×2ch×2bytes）と算出できます。これは圧縮ZIPやPython環境、メモリ、生成物の容量を含む最小payloadの見積りであり、必要ディスク容量全体の保証ではありません。

ローカルのcheckpointは約345 MiB。CPU依存・Notebook環境にも別途容量が必要です。CLIは音声出力・全件中間特徴をディスク保存せず、機種・条件ごとの特徴をメモリ保持します。RAM/VRAMの必要最小値は未測定。GPUは必須ではありませんが、CUDA12.8/PyTorch2.7.1とRTX PRO6000で全件検証済みです。他のGPU構成は未検証です。GPU PyTorchを使う場合はPyTorch公式の機器対応手順で導入してください。

実測時間と機器は[検証記録](../VALIDATION.md)から参照できます。別機器・CPU全件の時間は未測定です。先に `--machine ToothBrush --limit 5` で自分の環境を確認してください。
