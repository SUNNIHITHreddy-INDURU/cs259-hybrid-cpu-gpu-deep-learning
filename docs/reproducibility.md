# Reproducibility

## Exact commands used for the reported results

**Apple M4 (CPU only)**
```bash
THREADS=1,2,4,6,8,10 RUNS=20 WARMUP=3 benchmarks/run_all.sh mac_m4 cpu
```
macOS 26.6.2, Apple clang 21.0.0, libomp 23.1.2 (Homebrew), `-O3`.

**Spartan GPU node (Tesla K40m + dual Xeon E5-2680 v4), two Slurm jobs**
```bash
module load gcc/11.4.1 cuda/11.7
# reference runs: strong CPU baseline
sbatch --job-name=cs259_native --export=ALL,PLATFORM=spartan_k40_native,ARCH_FLAGS=-march=native,BUILD_DIR=build_native scripts/spartan_job.sbatch
# sensitivity runs: plain -O3
sbatch --job-name=cs259_o3 --export=ALL,PLATFORM=spartan_k40_o3,BUILD_DIR=build_o3 scripts/spartan_job.sbatch
```
Each job requests one K40 and 24 CPUs, sets `CUDA_ARCH=35` and `THREADS=1,2,4,8,12,16,24`, runs the
correctness gate, then the benchmark grid and the micro-benchmarks.

**Cold start (Spartan, 10 fresh processes, run after the main benchmarks)**
```bash
sbatch --job-name=cs259_cold --export=ALL,PLATFORM=spartan_k40_native,ARCH_FLAGS=-march=native,BUILD_DIR=build_native scripts/spartan_cold.sbatch
```
The main benchmark results were produced before the cold-start mode and the extra initialisation timers were added to
`nn_bench` / `CudaRunner`; those additions do not touch the timed code paths (they time the constructor and add a `--cold`
mode), and the validation gate was not re-run on the final binary of the cold-start job except through its own output.

**Analysis (any machine with Python 3, NumPy, pandas, SciPy, Matplotlib)**
```bash
python3 analysis/analyze_results.py
python3 analysis/statistical_analysis.py
python3 analysis/generate_tables.py
python3 analysis/generate_figures.py
python3 analysis/generate_numbers.py      # numbers quoted in the paper (report/overleaf/numbers.tex)
```

## From a clean clone
```bash
./scripts/setup_environment.sh && ./scripts/build.sh && ./scripts/run_tests.sh
./scripts/reproduce_all_results.sh my_machine
```
`data/download_mnist.py` downloads MNIST and verifies MD5 and SHA-256 checksums; the trained weights are
committed (`data/weights`, checksum in `data/weights/SHA256SUMS`) and can be regenerated with
`scripts/train_mnist_mlp.py` (NumPy only, fixed seed).

## Raw data
Every measured pass is one row in `results/raw/<platform>_<UTC timestamp>_bench.csv`, with the hardware and
compiler description repeated in each row. Files are never overwritten (the benchmark program refuses to
open an existing result file). Correctness-gate output is stored next to them (`*_validation.csv/log`),
together with micro-benchmark results (`*_bench_micro.csv`) and the run logs, which include the system load
at the start and end of each benchmark.

## Known sources of run-to-run variation
Other jobs and background services on shared machines, CPU frequency and thermal behaviour, and (on macOS)
thread placement chosen by the scheduler. The coefficient of variation of each configuration is reported in
the processed summary (`results/processed/summary_<platform>.csv`).
