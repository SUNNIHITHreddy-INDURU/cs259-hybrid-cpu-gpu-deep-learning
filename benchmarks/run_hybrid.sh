#!/usr/bin/env bash
# Hybrid (sequential and pipelined) benchmark. Needs nvcc. Usage: run_hybrid.sh <platform> [threads-list]
set -euo pipefail; cd "$(dirname "$0")/.."; make gpu >/dev/null
build/gpu/nn_bench --platform "${1:-local}" --impls hybrid_seq,hybrid ${2:+--threads $2} --out "results/raw/${1:-local}_$(date -u +%Y%m%dT%H%M%SZ)_hybrid_bench.csv"
