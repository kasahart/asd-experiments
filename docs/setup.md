# 実行環境

依存関係は[pyproject.toml](../pyproject.toml)で管理します。学習にはPython 3.11を使います。

## Dev Container（推奨）

[.devcontainer](../.devcontainer)の設定を使うと、VS Codeの「Dev Containers: Reopen in Container」などで開くだけで、下の手動導入と同じ環境（`.venv`の作成から`pip check`まで）を自動で作ります。`.venv`はコンテナ用のボリュームに置くため、手元の`.venv`とは混ざりません。

| 設定 | 用途 | 必要なもの |
|---|---|---|
| [.devcontainer/devcontainer.json](../.devcontainer/devcontainer.json) | 学習・推論（CUDA 12.8版のPyTorch） | NVIDIA GPU、ドライバー、NVIDIA Container Toolkit |
| [.devcontainer/cpu/devcontainer.json](../.devcontainer/cpu/devcontainer.json) | テスト・アプリ・CPUでの推論 | Docker |

GPU版はCUDAが使えないと作成時に止まるので、その場合はCPU版で開きます。データ・重み・評価器は、リポジトリ内の`inputs/`（Gitの管理外）に置くと、コンテナからも同じパスで使えます。

## 手動で導入する

| やりたいこと | 入れるもの |
|---|---|
| marimoアプリを読むだけ | marimoだけ（[アプリの説明](../apps/README.md#ローカルで読む編集する)） |
| 実験1の推論（CPUでも可） | 下の1〜2行目と`.venv/bin/python -m pip install -e .` |
| 実験2の学習・公式採点・テストまで | 下の全部 |

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install torch==2.7.1 torchaudio==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
.venv/bin/python -m pip install -e '.[training,app,visualization,evaluation,test]'
.venv/bin/python reproduction/asd03/runtime.py install
.venv/bin/python -m pip check
```

| extra | 用途 |
|---|---|
| （なし） | 推論だけ（`pip install -e .`） |
| `training` | 実験2の追加学習 |
| `app` | marimoアプリ |
| `visualization` | 図の表示 |
| `evaluation` | 公式評価器の実行 |
| `test` | テスト |

CPU環境では、PyTorchの配布先を`https://download.pytorch.org/whl/cpu`に変えます。Torch・TorchAudio・TorchVisionは[公式PyTorch 2.7.1構成](https://pytorch.org/get-started/previous-versions/)に合わせて同じ配布先から導入します。`runtime.py install`は実験2用の固定ASDKitを仮想環境内へ導入します（取得元は[upstream.lock.json](../reproduction/asd03/upstream.lock.json)）。

データセット・BEATs重み・公式評価器・正解CSVは同梱していません（[入力の取得](02-inputs.md)）。
