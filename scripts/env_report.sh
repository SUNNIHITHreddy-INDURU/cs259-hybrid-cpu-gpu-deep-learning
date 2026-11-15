#!/usr/bin/env bash
# env_report.sh <platform-name> - record hardware/software versions of THIS machine.
# Writes environment/environment_report_<platform>.md (never overwrites an existing report).
set -u
PLATFORM="${1:-local}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/environment/environment_report_${PLATFORM}.md"
[ -e "$OUT" ] && OUT="$ROOT/environment/environment_report_${PLATFORM}_$(date +%Y%m%d_%H%M%S).md"
have() { command -v "$1" >/dev/null 2>&1; }
run()  { echo; echo "\$ $*"; echo '```'; "$@" 2>&1 | head -${LINES_MAX:-40}; echo '```'; }
{
  echo "# Environment report - ${PLATFORM}"
  echo; echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ) by scripts/env_report.sh"
  echo; echo "## Operating system and CPU"
  run uname -a
  if [ "$(uname -s)" = "Darwin" ]; then
    run sw_vers
    run sysctl -n machdep.cpu.brand_string
    run sysctl hw.physicalcpu hw.logicalcpu hw.perflevel0.physicalcpu hw.perflevel1.physicalcpu hw.memsize hw.perflevel0.l2cachesize hw.perflevel1.l2cachesize
  else
    have lscpu && run lscpu
    run grep -m1 "model name" /proc/cpuinfo
    run nproc
    run free -h
  fi
  echo; echo "## Compilers and build tools"
  for c in c++ g++ clang++ cmake make; do have $c && { LINES_MAX=2 run $c --version; }; done
  echo; echo "## OpenMP"
  if [ "$(uname -s)" = "Darwin" ]; then run brew list --versions libomp; else have gcc && run bash -c "echo | gcc -fopenmp -dM -E - | grep _OPENMP"; fi
  echo; echo "## GPU and CUDA"
  if have nvidia-smi; then
    run nvidia-smi
    run nvidia-smi --query-gpu=name,compute_cap,memory.total,driver_version,clocks.max.sm,clocks.max.mem,pcie.link.gen.max,pcie.link.width.max --format=csv
  else echo; echo "nvidia-smi: not found (no NVIDIA GPU / driver on this machine)"; fi
  if have nvcc; then run nvcc --version; else echo; echo "nvcc: not found (CUDA cannot be compiled on this machine)"; fi
  echo; echo "## Python"
  have python3 && run python3 -c "import sys,numpy,pandas,matplotlib,scipy;print(sys.version.split()[0],'numpy',numpy.__version__,'pandas',pandas.__version__,'matplotlib',matplotlib.__version__,'scipy',scipy.__version__)"
  echo; echo "## Tools and storage"
  have git && LINES_MAX=1 run git --version
  run df -h "$ROOT"
} > "$OUT"
echo "wrote $OUT"
