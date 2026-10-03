# SS追加検証 — 2026-10-03

## 条件の特定

GitHub APIでPR9現在headを確認: `de12a5825e6974c10934c72556bb6787f05c5a83`（前回確認と同じhead、updated_at 2026-10-03T02:21:33Z）。記事の比較表で、既存コピーのB0/B1/W1に加えて明記される条件は**SS: スペクトル減算（式1）**です。別の未公開変更を推測していません。このheadにはSS公式集計・機種別成績がなく、空欄です。ユーザーの「SSであってる。未検証なので、空欄になっているのはただしい。空欄を埋める実験をして。」という確認後、今回新たに全件実験しました。

[Qian技術報告 Section2.1](https://dcase.community/documents/challenge2026/technical_reports/DCASE2026_Qian_65_t2.pdf)でも16kHz、Hann512/hop256、beta=1/gamma=0.1、近接位相での復元を確認しました。W2のpower subtractionではありません。QianのEAT/KNN・looping全システムを再現する条件でもありません。

## 計算・config

`waveform.ss_spectrum()`が式を一度だけ実装し、`waveform.ss()`でSTFT/ISTFTします。CLIとNotebookは共通`condition_audio()`を呼びます。新規コードはMIT。原報告のコードやPDFは配布しません。

- `a=abs(near), b=abs(far)`。`a>b`なら`a-b`、それ以外は`0.1*a`。近接位相を保持。
- 等しい場合も0.1倍。正の差に常に0.1倍の下限を課す`max(a-b,0.1*a)`ではない。
- frame512/hop256、入力16kHz stereo、float32、元の長さで逆変換。
- 記事・報告で未指定の詳細は、このローカル実装がTorch periodic Hann、center=True、reflect、normalized=False、onesided=True、入力正規化なしと選択して固定。[02_ss.json](../configs/02_ss.json)は固定protocolの出力であり、runtime overrideではありません。原チームの端処理と完全同等とは主張しません。
- 推論のsplit、BEATs_iter3/RDP4/BEAM VarMin4 train_all/per_bandは既存と共通。SSも正常train参照を新規構築する経路です。他条件の正常参照を再利用しません。
- Wandas表示STFTは全条件1024/hop512で揃えた説明用の別解析。SSの実測STFT512/hop256と混同しません。

## 全件実験と公式ローカル採点

SSのToothBrush train5/test5 GPU smokeは0.513秒で成功。その後、5機種×train1000/test200の6000音を直列で処理し、SS専用の正常参照を再構築しました。6000入力のSHA-256は既存3条件のinventoryとすべて一致し、BEATs_iter3のchecksumも固定値と一致しました。FP32、AMP/TF32なし、Python3.11 / torch2.7.1+cu128です。

RTX PRO6000 Blackwell Max-Qで抽出・採点94.9367秒（checkpoint初期化・hash確認を除く）、PyTorch peak CUDA allocated 528886272 bytes（約0.493 GiB）。これはGPU全使用量や必要最低VRAMではありません。開始時utilization0%、596/97887MiBを確認し、他ジョブを停止していません。

既存利用記録とLICENSE全文を点検し、著者自身の継続する内部非商用DCASE研究という用途で、既存のclean固定evaluatorを無改変で実行しました。新たな許諾取得・契約同意操作はしていません。読者一般への無条件な使用許諾とは区別します（[権利整理](rights.md)）。evaluator・付属正解・公式出力CSVは配布しません。

| 条件 | 公式総合値×100 | B0との差（ポイント） |
|---|---:|---:|
| B0 | 62.841 | 0.000 |
| B1 | 58.362 | −4.479 |
| W1 | 66.835 | +3.994 |
| SS（今回新規測定） | **62.325** | **−0.516** |

SSはW1比−4.510ポイント。SS既存報告がないので追試一致の比較対象はありません。記事PRの空欄を埋める新規結果です。原Qianシステムの成績や完全再現ではありません。

| 機種 | SS pAUC×100 | B0との差（ポイント） |
|---|---:|---:|
| BlowerDustCollector | 73.474 | +1.474 |
| Sander | 52.368 | +0.421 |
| SewingMachine | 64.684 | −1.316 |
| ToothBrush | 49.632 | −0.526 |
| ToyDrone | 57.579 | −0.263 |

pAUCは2機種で上がり3機種で下がりました。総合改善や聞きやすさの改善は主張しません。詳細・入力とコードのhash・実測条件は[ss-experiment.json](ss-experiment.json)、[4条件集計](../results/summary-with-ss.csv)、[機種別集計](../results/by_machine-with-ss.csv)。元3条件の保存CSVは変更していません。

## 既存3条件の再採点と小規模検証

元の保存異常度からの再採点は、3条件すべて元公式出力CSVとbyte-identical。新規GPU再推論からの再採点も機種別AUC/pAUCと総合値はすべて一致しました。B0/B1公式出力CSVはbyte-identicalですが、W1の補助欄 `official score ci95` のみ2.9783502969025203e-05→2.978354952087245e-05（差約4.66e-11）。異常度の微小な数値差を含むため全出力の完全一致とは書きません。

合成テストは厳密な分岐（10/4→6、4/10→0.4、4/4→0.4、4/3.8→0.2）、近接位相、遠方位相への非依存、無音、far0、同一2ch、scale、長さ、有限値を確認。pytest6件合格。SS合成スペクトルのCPU/GPU最大絶対差2.38e-7。W1元関数との5ケースarray_equalも保持。

Notebook既定実行は保存結果と合成図だけです。音声自動再生や外部資産アクセスはありません。実音の主観的試聴、他GPU/CPUでの全件再現、未知機種への汎化は未検証です。公開用コピーには外部資産を同梱しません。
