# Project scope

**Title:** Performance Evaluation of Hybrid CPU-GPU Parallelism for Deep Learning Using OpenMP and CUDA

## Workload and data
- Dataset: MNIST, 10,000 test images (28 x 28 grayscale = 784 inputs, 10 classes).
- Network: fully connected 784 -> 256 -> ReLU -> 10, float32, inference only.
- Weights: trained once with NumPy (He initialisation, Adam, 10 epochs, seed 0; no PyTorch/TensorFlow);
  committed with a checksum. Inference is implemented from scratch in C++ and CUDA.
- One *pass* = preprocess (per-image standardisation) + hidden layer + output layer + argmax for all
  10,000 images, processed in batches of a given size.

## Implementations (same arithmetic, same data, same weights)
1. **Serial** C++ loops.
2. **OpenMP**: single parallel region, work-shared loops, 1-10 threads.
3. **CUDA**: preprocessing on one CPU thread, synchronous pageable transfers, three kernels.
4. **Hybrid OpenMP-CUDA**: OpenMP preprocessing into pinned buffers + asynchronous copies and kernels on
   several CUDA streams (software pipeline). Two variants separate the effects: *hybrid-sequential*
   (OpenMP preprocessing, no overlap) and *hybrid-pipelined* (OpenMP preprocessing + overlap).

## Research questions
See `docs/research_questions.md` (RQ1-RQ6).

## Variables
- Independent: implementation, batch size (1, 8, 32, 64, 128, 256, 1024, 4096), OpenMP thread count,
  CUDA thread-block size (8x8, 16x16, 32x32), number of streams (hybrid).
- Dependent: end-to-end time, stage times (preprocess, layers, H2D, kernel, D2H), speedup, efficiency,
  throughput, transfer share, accuracy, max/mean logit difference.
- Controlled: dataset, weights, precision (float32), compiler optimisation level (-O3), warm-up passes (3),
  measured passes (20), pass size (10,000 images), machine used for each comparison.

## Out of scope
Training on the GPU/CPU, convolutional networks, cuBLAS/cuDNN, mixed precision, multi-GPU, MPI,
energy measurements.

## Minimum successful project
All four implementations correct (tolerance 1e-4 on logits), OpenMP scaling and CPU-vs-GPU results with
repeated measurements, transfer breakdown, hybrid comparison, 20-run statistics, paper + slides.

## Not claimed
No result is stated unless it appears in `results/raw`. Hardware peak numbers are only used when they
were measured by the micro-benchmarks or reported by the device query.
