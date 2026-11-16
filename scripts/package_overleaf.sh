#!/usr/bin/env bash
# package_overleaf.sh - build report/cs259-overleaf.zip: the LaTeX project (root) plus the code (code/).
# Upload with Overleaf: New Project -> Upload Project. Compiler: pdfLaTeX; main document: main.tex.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 analysis/generate_numbers.py >/dev/null
python3 analysis/generate_paper_tables.py >/dev/null
# figures used by the paper: results/figures/paper -> report/overleaf/figures
for f in architecture hybrid_timeline network_architecture cold_start correctness_all omp_combined amdahl_combined \
         exec_time_spartan_k40_native speedup_spartan_k40_native throughput_spartan_k40_native \
         cuda_kernel_vs_e2e_spartan_k40_native transfer_breakdown_spartan_k40_native hybrid_compare_spartan_k40_native \
         cuda_block_size_spartan_k40_native; do
  cp "results/figures/paper/$f.pdf" "report/overleaf/figures/$f.pdf"
done
python3 scripts/check_units.py
STAGE="$(mktemp -d)"; trap 'rm -rf "$STAGE"' EXIT
O=report/overleaf
mkdir -p "$STAGE/code"
cp -R $O/main.tex $O/cs259.cls $O/cs259.bst $O/refs.bib $O/latexmkrc $O/numbers.tex $O/sections $O/tables $O/figures "$STAGE/"
cp $O/README_OVERLEAF.md "$STAGE/README_OVERLEAF.md"
# code, raw measurements and analysis (no build products, no downloaded MNIST files)
cp README.md LICENSE Makefile CMakeLists.txt "$STAGE/code/"
cp -R include src scripts benchmarks analysis colab requirements docs environment "$STAGE/code/"
mkdir -p "$STAGE/code/data/weights" "$STAGE/code/results"
cp data/download_mnist.py data/SHA256SUMS "$STAGE/code/data/"
cp data/weights/* "$STAGE/code/data/weights/"
cp -R results/raw results/processed results/tables "$STAGE/code/results/"
find "$STAGE" -name ".DS_Store" -delete -o -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
rm -f report/cs259-overleaf.zip
(cd "$STAGE" && zip -r -q "$OLDPWD/report/cs259-overleaf.zip" .)
ls -la report/cs259-overleaf.zip
