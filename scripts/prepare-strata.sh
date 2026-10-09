#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/Strata-speed"
export PATH="$HOME/llama-rpc/tools/cmake-4.4.4-linux-x86_64/bin:/usr/local/cuda-12.4/bin:$PATH"
export STRATA_NVCC=/usr/local/cuda-12.4/bin/nvcc
if [ ! -x .venv/bin/python ]; then
    python3 -m venv --without-pip .venv
fi
if ! .venv/bin/python -m pip --version >/dev/null 2>&1; then
    python3 - <<'PY'
import urllib.request
urllib.request.urlretrieve('https://bootstrap.pypa.io/get-pip.py', 'get-pip.py')
PY
    .venv/bin/python get-pip.py
fi
exec .venv/bin/python setup.py --yes --family qwen --model Q2_0 \
    --cuda 12 --gpu 0 --context 16384 --vision no --low-ram auto \
    --gguf-dir "$HOME/llama-rpc/models/Q2_0" --data-dir "$HOME/Strata-speed-data" \
    --port 8080 --host 127.0.0.1 --no-start
