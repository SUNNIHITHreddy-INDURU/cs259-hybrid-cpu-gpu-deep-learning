#!/usr/bin/env bash
# run_cold.sh <platform> [launches=10] - cold-start timing: each launch is a fresh process (genuine cold start).
# Output: results/raw/<platform>_<UTC timestamp>_cold.csv (one row per launch; -1 = not measured on this machine).
set -euo pipefail
cd "$(dirname "$0")/.."
PLATFORM="${1:?usage: run_cold.sh <platform> [launches]}"; N="${2:-10}"
BUILD_DIR="${BUILD_DIR:-build}"; THREADS="${THREADS:-24}"
if command -v nvcc >/dev/null 2>&1; then make gpu BUILD="$BUILD_DIR"; BIN="$BUILD_DIR/gpu"; else make cpu BUILD="$BUILD_DIR"; BIN="$BUILD_DIR/cpu"; fi
export OMP_PROC_BIND=close OMP_PLACES=cores
OUT="results/raw/${PLATFORM}_$(date -u +%Y%m%dT%H%M%SZ)_cold.csv"
for i in $(seq 1 "$N"); do
  "$BIN/nn_bench" --platform "$PLATFORM" --impls serial --cold --cold-batch 256 --threads "$THREADS" --out "$OUT"
done
echo "wrote $OUT"
