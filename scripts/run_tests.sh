#!/usr/bin/env bash
# run_tests.sh - correctness gate: every implementation is compared with the serial reference.
set -euo pipefail
cd "$(dirname "$0")/.."
BIN=build/cpu; [ -x build/gpu/nn_validate ] && BIN=build/gpu
"$BIN/nn_validate"
