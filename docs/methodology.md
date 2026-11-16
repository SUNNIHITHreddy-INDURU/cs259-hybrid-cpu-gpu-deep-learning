# Methodology

## What is measured
A **pass** processes the 10,000 MNIST test images in consecutive batches of size B
(last batch is smaller when B does not divide 10,000). Every implementation performs the same stages:

| Stage | Work | Where it runs |
|---|---|---|
| 0 Preprocess | per-image standardization of 784 raw pixels | serial: 1 CPU thread; OpenMP: T threads; CUDA: 1 CPU thread; hybrid: T OpenMP threads |
| 1 Hidden layer | h = ReLU(W1^T x + b1), 784 -> 256 | CPU loops / OpenMP loops / CUDA kernel |
| 2 Output layer | z = W2^T h + b2, 256 -> 10 | same |
| 3 Prediction | argmax of the 10 logits | same |

All implementations use the same mathematical operations, input data, weights, dimensions, precision, and
source-level reduction order (k = 0..783 for the hidden layer, j = 0..255 for the output layer). Small numerical
differences may result from compiler-specific floating-point optimizations (for example fused multiply-add
contraction); the contraction options (`-ffp-contract`, `--fmad`) were not set explicitly.

Naming: the four primary implementations are serial, OpenMP, **CUDA with single-threaded CPU preprocessing**
(its preprocessing runs on one CPU thread, so it is not GPU-only) and the **hybrid OpenMP-CUDA pipeline**.
*Hybrid-sequential* (OpenMP preprocessing, synchronous copies, no overlap) is a diagnostic control only.
CUDA streams overlap *different batches*; the stages of one batch are dependent and run in order on one stream.

## Steady state, compute-only and end-to-end
- All reported times are steady-state. One-time GPU costs (context creation, device/pinned buffer, stream and event
  allocation, weight upload) are excluded for every implementation; they are measured separately by
  `benchmarks/run_cold.sh` (10 fresh processes) and reported as cold-start results.
- *Compute-only* = stages 1-3 (hidden layer, output layer, argmax): CPU = sum of timed stage durations, GPU = CUDA-event
  time of the three kernels. *End-to-end* = stages 0-3 including copies = wall clock of the pass.
- Floating-point rates: 2 FLOP per multiply-add of the two layers = 406,528 FLOP per image, 4.07 GFLOP per pass;
  preprocessing, bias, ReLU and argmax are not counted. Rate = FLOP / end-to-end time unless labelled kernel-only.
- Tuning: OpenMP and hybrid use the best of the tested thread counts per batch size; CUDA uses a fixed 16x16 block
  (block sizes 8, 16, 32 were measured; see the block-size sensitivity in the paper). Comparisons are labelled
  "CUDA with fixed block vs OpenMP with tuned thread count".

## Compiler settings
| Build | Compiler | Flags |
|---|---|---|
| Apple M4 | Apple clang 21.0.0, libomp 23.1.2 | `-O3 -std=c++14 -Xpreprocessor -fopenmp` (no -march/-mcpu) |
| Spartan reference | host g++ 11.4.1 via nvcc 11.7.99 | host `-O3 -std=c++14 -fopenmp -march=native`; device `-O3 -arch=sm_35` |
| Spartan sensitivity | same | same, without `-march=native` |

## Timing
- **End-to-end** = wall clock of the whole pass (steady clock), measured after all host buffers have been
  allocated. One-time set-up (device buffers, weight upload) is excluded for every implementation and
  reported separately.
- **Stage times**: CPU stages timed with the steady clock; GPU stages (H2D copy, three kernels, D2H copy)
  with CUDA events recorded in the stream around each operation.
- Kernel-only time is reported *in addition to* end-to-end time and never substituted for it.
- In the pipelined hybrid, GPU-stage durations overlap with each other and with CPU work, so their sum may
  exceed the end-to-end time; the end-to-end time is the figure of merit.

## Protocol
- 3 unrecorded warm-up passes, then 20 recorded passes per configuration (every pass is a CSV row).
- Accuracy of every recorded pass is computed (outside the timers) and stored with the row.
- Raw CSV files are written to `results/raw/` with the platform name and a UTC timestamp and are never
  overwritten (the program refuses to open an existing file).
- Every row carries: timestamp, platform id, implementation, batch size, threads, block size, streams,
  stage times, accuracy, CPU model, logical threads, GPU model, compiler, CUDA runtime version.
- Thread placement: `OMP_PROC_BIND=close`, `OMP_PLACES=cores` on Linux (not honoured by macOS).

## Statistics (analysis/)
Mean, standard deviation, median, min, max and a 95 % Student-t confidence interval of the mean per
configuration. Speedup = T_serial / T_impl (same platform, same batch size). OpenMP efficiency = speedup /
threads. Throughput = 10,000 / T. Transfer share = (H2D + D2H) / end-to-end. Amdahl serial fraction is
fitted by least squares to the measured speedups; the Karp-Flatt metric is computed per thread count.
Welch t-tests and bootstrap confidence intervals of the ratio of means compare hybrid variants.

## Correctness gate (`nn_validate`)
Reference = serial implementation. Acceptance criterion fixed before any measurement:
max |logit difference| <= 1e-4 and prediction agreement >= 99.9 %. An independent anchor compares the
serial float32 logits of the first 100 images with a float64 NumPy computation.
