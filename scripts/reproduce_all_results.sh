#!/usr/bin/env bash
# reproduce_all_results.sh <platform-name> - correctness gate + full benchmark + analysis + figures.
set -euo pipefail
cd "$(dirname "$0")/.."
PLATFORM="${1:-$(hostname -s)}"
MODE=cpu; command -v nvcc >/dev/null 2>&1 && MODE=gpu
benchmarks/run_all.sh "$PLATFORM" "$MODE"
python3 analysis/analyze_results.py
python3 analysis/statistical_analysis.py
python3 analysis/generate_tables.py
python3 analysis/generate_figures.py
