#!/usr/bin/env bash
# build.sh - build CPU targets, and GPU targets when nvcc is available.
set -euo pipefail
cd "$(dirname "$0")/.."
make cpu
if command -v nvcc >/dev/null 2>&1; then make gpu; else echo "nvcc not found: skipping GPU targets"; fi
