#!/usr/bin/env bash
# run_all.sh <platform-name> [cpu|gpu]
# Builds, runs the correctness gate, then the full benchmark grid and the micro-benchmarks.
# Each invocation writes NEW timestamped files into results/raw/ (existing data is never touched).
#   cpu : serial + OpenMP only (no CUDA needed)           gpu : serial, OpenMP, CUDA, hybrid_seq, hybrid
# Environment overrides: RUNS (default 20), WARMUP (3), THREADS ("1,2,4,..."), BATCHES, BLOCKS
set -euo pipefail
PLATFORM="${1:?usage: run_all.sh <platform-name> [cpu|gpu]}"
MODE="${2:-cpu}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
RAW="results/raw"; mkdir -p "$RAW"
RUNS="${RUNS:-20}"; WARMUP="${WARMUP:-3}"
BATCHES="${BATCHES:-1,8,32,64,128,256,1024,4096}"
export OMP_PROC_BIND="${OMP_PROC_BIND:-close}" OMP_PLACES="${OMP_PLACES:-cores}"   # honoured on Linux

[ -f data/raw/t10k-images-idx3-ubyte ] || python3 data/download_mnist.py
python3 data/download_mnist.py --verify
scripts/env_report.sh "$PLATFORM"

if [ "$MODE" = "gpu" ]; then
  make gpu; BIN=build/gpu; IMPLS="serial,openmp,cuda,hybrid_seq,hybrid"; BLOCKS="${BLOCKS:-8,16,32}"
else
  make cpu; BIN=build/cpu; IMPLS="serial,openmp"; BLOCKS="${BLOCKS:-16}"
fi
THREAD_ARG=(); [ -n "${THREADS:-}" ] && THREAD_ARG=(--threads "$THREADS")

echo "== correctness gate =="
"$BIN/nn_validate" --platform "$PLATFORM" --out "$RAW/${PLATFORM}_${TS}_validation.csv" | tee "$RAW/${PLATFORM}_${TS}_validation.log"

echo "== benchmarks =="
echo "system load before benchmarks: $(uptime)"
"$BIN/nn_bench" --platform "$PLATFORM" --impls "$IMPLS" --batches "$BATCHES" --blocks "$BLOCKS" \
  --runs "$RUNS" --warmup "$WARMUP" "${THREAD_ARG[@]}" --micro --out "$RAW/${PLATFORM}_${TS}_bench.csv" \
  | tee "$RAW/${PLATFORM}_${TS}_bench.log"
echo "system load after benchmarks: $(uptime)" | tee -a "$RAW/${PLATFORM}_${TS}_bench.log"
echo "done: $RAW/${PLATFORM}_${TS}_*"
