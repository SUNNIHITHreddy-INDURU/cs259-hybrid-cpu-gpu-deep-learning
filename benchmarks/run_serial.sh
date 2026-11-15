#!/usr/bin/env bash
# Serial-only benchmark (all batch sizes). Usage: run_serial.sh <platform>
set -euo pipefail; cd "$(dirname "$0")/.."; make cpu >/dev/null
build/cpu/nn_bench --platform "${1:-local}" --impls serial --out "results/raw/${1:-local}_$(date -u +%Y%m%dT%H%M%SZ)_serial_bench.csv"
