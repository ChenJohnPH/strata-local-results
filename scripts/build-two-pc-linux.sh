#!/usr/bin/env bash
set -euo pipefail
task_root="$HOME/Strata-two-pc-source"
mkdir -p "$task_root"
tar -xzf "$HOME/llama-rpc/two-pc-prepared-source.tar.gz" -C "$task_root"
task_source="$task_root/NTRYourWaifu-Strata-7add08d"
task_cmake="$HOME/llama-rpc/tools/cmake-4.4.4-linux-x86_64/bin/cmake"
"$task_cmake" -G Ninja -S "$task_source" -B "$HOME/two-pc-build-linux" \
    -DCMAKE_BUILD_TYPE=Release -DSTRATA_ENABLE_CUDA=ON -DSTRATA_BUILD_TESTS=OFF \
    -DSTRATA_PORTABLE=ON -DCMAKE_CUDA_RUNTIME_LIBRARY=Shared -DCMAKE_CUDA_ARCHITECTURES=89 \
    -DCMAKE_CUDA_COMPILER=/usr/local/cuda-12.4/bin/nvcc \
    -DCMAKE_MAKE_PROGRAM="$HOME/Strata-speed/.venv/bin/ninja" \
    -DSTRATA_GGML_DIR="$task_source/third_party/llama.cpp"
"$task_cmake" --build "$HOME/two-pc-build-linux" --target strata --parallel 6
