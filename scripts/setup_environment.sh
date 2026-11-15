#!/usr/bin/env bash
# setup_environment.sh - check/install what the project needs. Never touches system files silently.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
echo "== checking tools =="
for t in python3 make git; do command -v $t >/dev/null || { echo "missing: $t"; exit 1; }; done
if [ "$(uname -s)" = "Darwin" ]; then
  command -v brew >/dev/null || { echo "Homebrew is required on macOS"; exit 1; }
  brew list libomp >/dev/null 2>&1 || brew install libomp
else
  command -v g++ >/dev/null || { echo "missing: g++ (install build-essential)"; exit 1; }
fi
command -v nvcc >/dev/null && echo "nvcc: $(nvcc --version | tail -1)" || echo "nvcc not found: GPU targets cannot be built here (CPU targets only)"
python3 -m pip install --quiet --user numpy pandas matplotlib scipy
echo "== data =="
python3 data/download_mnist.py
[ -f data/weights/mlp_784_256_10.bin ] || python3 scripts/train_mnist_mlp.py
echo "setup complete"
