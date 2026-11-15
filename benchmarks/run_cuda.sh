#!/usr/bin/env bash
# CUDA-only benchmark with three block sizes. Needs nvcc. Usage: run_cuda.sh <platform>
set -euo pipefail; cd "$(dirname "$0")/.."; make gpu >/dev/null
build/gpu/nn_bench --platform "${1:-local}" --impls cuda --blocks 8,16,32 --out "results/raw/${1:-local}_$(date -u +%Y%m%dT%H%M%SZ)_cuda_bench.csv"
