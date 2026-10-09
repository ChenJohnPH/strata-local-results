#!/usr/bin/env bash
set -euo pipefail
task_root="$HOME/llama-rpc"
task_archive="$task_root/cmake.tar.gz"
task_tools="$task_root/tools"
mkdir -p "$task_tools"
echo 'e5bb807f7728cb60cd8b27ebc97a2edb469b68655f21e844a600c3575b76f5bb  '"$task_archive" | sha256sum --check
tar -xzf "$task_archive" -C "$task_tools"
task_cmake="$task_tools/cmake-4.4.4-linux-x86_64/bin/cmake"
export PATH="/usr/local/cuda-12.4/bin:$PATH"
"$task_cmake" --version
"$task_cmake" -S "$task_root/source" -B "$task_root/build" \
    -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON -DGGML_RPC=ON \
    -DCMAKE_CUDA_ARCHITECTURES=89 -DCUDAToolkit_ROOT=/usr/local/cuda-12.4 \
    -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF
"$task_cmake" --build "$task_root/build" --parallel 8 \
    --target llama-server llama-cli ggml-rpc-server
"$task_root/build/bin/llama-server" --version
"$task_root/build/bin/llama-server" --list-devices
echo DESKTOP_BUILD_COMPLETE
