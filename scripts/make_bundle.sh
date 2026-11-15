#!/usr/bin/env bash
# make_bundle.sh - zip everything a remote GPU machine needs (source, weights, MNIST test set).
# Output: build_bundle/cs259_bundle.zip  (upload it to Colab's Files panel or scp it to a cluster)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
python3 data/download_mnist.py --verify
mkdir -p build_bundle
rm -f build_bundle/cs259_bundle.zip
zip -r -q build_bundle/cs259_bundle.zip Makefile include src scripts benchmarks data/download_mnist.py data/SHA256SUMS \
    data/weights data/raw/t10k-images-idx3-ubyte data/raw/t10k-labels-idx1-ubyte data/raw/t10k-images-idx3-ubyte.gz \
    data/raw/t10k-labels-idx1-ubyte.gz data/raw/train-images-idx3-ubyte.gz data/raw/train-labels-idx1-ubyte.gz \
    -x "*.DS_Store"
ls -la build_bundle/cs259_bundle.zip
