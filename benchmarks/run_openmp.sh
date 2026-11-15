#!/usr/bin/env bash
# OpenMP thread sweep. Usage: run_openmp.sh <platform> [threads-list]
set -euo pipefail; cd "$(dirname "$0")/.."; make cpu >/dev/null
build/cpu/nn_bench --platform "${1:-local}" --impls openmp ${2:+--threads $2} --out "results/raw/${1:-local}_$(date -u +%Y%m%dT%H%M%SZ)_openmp_bench.csv"
