#!/usr/bin/env bash
# Same steps as README.md "実行環境" and .github/workflows/asd03.yml, in .venv.
set -euo pipefail

# The volume mounted at .venv is created by root.
sudo chown "$(id -u):$(id -g)" .venv
[ -x .venv/bin/python ] || python3.11 -m venv .venv
PY=.venv/bin/python

"$PY" -m pip install torch==2.7.1 torchaudio==2.7.1 torchvision==0.22.1 \
    --index-url "${TORCH_INDEX_URL:?}"
"$PY" -m pip install -e '.[training,app,visualization,evaluation,test]'
"$PY" reproduction/asd03/runtime.py install
"$PY" -m pip check

"$PY" - <<'PY'
import os
import torch
import asdkit, asd_min  # noqa: F401
print("torch", torch.__version__, "cuda", torch.cuda.is_available())
if os.environ.get("ASD_REQUIRE_CUDA") == "1":
    assert torch.cuda.is_available(), "CUDA is not available; use .devcontainer/cpu"
    print("GPU:", torch.cuda.get_device_name(0))
PY
