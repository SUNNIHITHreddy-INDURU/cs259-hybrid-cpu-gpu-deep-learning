# Hybrid CPU-GPU parallelism for deep-learning inference: OpenMP and CUDA

CS 259 (Advanced Parallel Processing) course project by Sunnihith Reddy Induru.

Compares four implementations of the same MNIST inference workload (784 -> 256 -> ReLU -> 10, float32):
**serial C++**, **OpenMP**, **CUDA** and a **hybrid OpenMP + CUDA software pipeline**, on identical data and
weights, and reports execution time, speedup, scalability and where the time goes.

Every number in the paper comes from the raw CSV files in `results/raw/`; nothing is typed in by hand.

## Quick start
```bash
git clone <repository-url> && cd cs259-hybrid-cpu-gpu-deep-learning
./scripts/setup_environment.sh        # tools, MNIST download + checksum, python packages
./scripts/build.sh                    # CPU targets; GPU targets too when nvcc exists
./scripts/run_tests.sh                # correctness gate (all implementations vs serial)
./scripts/reproduce_all_results.sh my_machine   # benchmarks + analysis + figures + tables
```
CUDA targets need an NVIDIA GPU and `nvcc` (`make gpu`). For a machine without one (e.g. a Mac), only the
serial and OpenMP targets are built. `colab/run_benchmarks.ipynb` runs the full study on a Colab GPU runtime.

## Layout
| Path | Content |
|---|---|
| `include/`, `src/` | the four implementations and shared code (`src/serial`, `src/openmp`, `src/cuda`, `src/hybrid`, `src/common`, `src/app`) |
| `data/` | MNIST download + checksum script, trained weights (`data/weights`) |
| `scripts/`, `benchmarks/` | build, test, benchmark and reproduction scripts |
| `analysis/` | aggregation, statistics, tables, figures |
| `results/` | `raw/` (CSV), `processed/`, `tables/`, `figures/` |
| `report/overleaf/` | LaTeX source of the paper in the course template |
| `requirements/`, `docs/` | requirements, scope, research questions, methodology |
| `presentation/` | slide material |

## Method in one paragraph
A *pass* processes the 10,000 MNIST test images in batches of 1 to 4096. Serial and OpenMP run all stages on
the CPU; CUDA uploads preprocessed batches, runs three kernels and downloads the logits; the hybrid
preprocesses with OpenMP threads into pinned buffers while earlier batches are copied and computed on the GPU
through several CUDA streams. See `docs/methodology.md`.
