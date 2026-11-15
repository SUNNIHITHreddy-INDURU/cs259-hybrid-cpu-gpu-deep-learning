# Methodology

## What is measured
A **pass** processes the 10,000 MNIST test images in consecutive batches of size B
(last batch is smaller when B does not divide 10,000). Every implementation performs the same stages:

| Stage | Work | Where it runs |
|---|---|---|
| 0 Preprocess | per-image standardisation of 784 raw pixels | serial: 1 CPU thread; OpenMP: T threads; CUDA: 1 CPU thread; hybrid: T OpenMP threads |
| 1 Hidden layer | h = ReLU(W1^T x + b1), 784 -> 256 | CPU loops / OpenMP loops / CUDA kernel |
| 2 Output layer | z = W2^T h + b2, 256 -> 10 | same |
| 3 Prediction | argmax of the 10 logits | same |

Accumulation order is identical in all implementations (k = 0..783 for the hidden layer, j = 0..255 for
the output layer), so differences between them come only from fused multiply-add contraction on the device.

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
