# Speaker notes (20-minute talk; slides 1-16 about 19 minutes, backups for questions)

## Slide 1: Title

**Time:** 0.5 min

**On the slide:** Performance Evaluation of Hybrid CPU-GPU Parallelism for Deep Learning Using OpenMP and CUDA — Sunnihith Reddy Induru, CS 259, SJSU

**What to say:** Greet the audience. One sentence: I compared four ways of running the same neural-network inference – serial, OpenMP on the CPU, CUDA on the GPU, and a hybrid that uses both – and measured when each one wins. Everything I show was measured by me and is in the paper.

## Slide 2: A fast GPU kernel is not a fast application

**Time:** 1.25 min

**On the slide:** Kernels only 52.8× | end-to-end 26.4× | batch 1 0.82×

**What to say:** Start with the punchline. At batch size 4096 the GPU kernels alone are 52.8 times faster than serial code. But the pipeline an application actually runs - preprocessing, copies, kernels - is only 26.4 times faster. And with one image per batch the same GPU pipeline is 0.82 times: slower than serial. Same GPU, same data. The rest of the talk explains why, and what to do about it. All numbers: Tesla K40m node, mean of 20 runs.

## Slide 3: Six questions about CPU, GPU and hybrid execution

**Time:** 1 min

**On the slide:** RQ1: How much speedup does OpenMP give over serial?
RQ2: How does CUDA compare with serial and OpenMP – compute-only and end-to-end?
RQ3: How does the batch size change CPU and GPU performance?
RQ4: How much GPU time is data transfer, not computation?
RQ5: Does a hybrid OpenMP–CUDA pipeline improve end-to-end time?
RQ6: How do results relate to Amdahl's law, overhead and bandwidth?

**What to say:** Read the six questions briefly. RQ1-RQ3 are about scaling and batch size, RQ4 about transfers, RQ5 is the hybrid, RQ6 connects to theory. I will show the answer to each with measured numbers.

## Slide 4: Two kinds of parallelism, two kinds of overhead

**Time:** 1 min

**On the slide:** OpenMP: shared memory, fork-join, barrier per loop. CUDA: thousands of threads, separate memory, PCIe copies, launch cost. Hybrid: overlap CPU and GPU work.

**What to say:** OpenMP: a team of CPU threads sharing memory; every parallel loop ends in a barrier, so the work per loop must be larger than the synchronisation cost. CUDA: thousands of GPU threads, but separate memory - data must cross PCIe, and each kernel launch has a fixed cost. The hybrid idea: let the CPU prepare the next batch while the GPU computes the current one.

## Slide 5: Workload: MNIST digits through a 784→256→10 network

**Time:** 1 min

**On the slide:** 10,000 MNIST test images | 784→256→ReLU→10, float32 | 203,530 parameters | batches 1–4096 | stages: preprocess, hidden, output, argmax

**What to say:** The workload is deliberately small and fully specified. Ten thousand MNIST test images, a fully connected network 784 to 256 with ReLU to 10, float32. 203,530 parameters; I trained the weights once with NumPy and every implementation loads the same file. Each pass has four stages: preprocessing - per-image standardisation, the hidden layer, the output layer, and argmax. I process the images in batches of 1 to 4096.

## Slide 6: Four implementations of the same computation

**Time:** 1.5 min

**On the slide:** Serial | OpenMP | CUDA (1-thread preprocessing) | Hybrid pipeline. Hybrid-sequential = diagnostic control only.

**What to say:** Four primary implementations. Serial: one CPU thread. OpenMP: the CPU stages run on T threads. CUDA: preprocessing on ONE CPU thread, then copies, three GPU kernels, copy back - note this is not GPU-only because the preprocessing is on the CPU, so I call it CUDA with single-threaded preprocessing. Hybrid: OpenMP threads preprocess into pinned memory, copies are asynchronous, kernels run on streams. I also measured one diagnostic control, hybrid-sequential, to separate parallel preprocessing from overlapping. All use the same operations, data, weights, precision and source-level reduction order.

## Slide 7: Streams overlap different batches, never the layers of one batch

**Time:** 1.5 min

**On the slide:** Schematic: sequential vs pipelined. Overlap between batches only; layers of one batch stay in order on one stream.

**What to say:** This is a schematic, not measured data. Top: the CUDA pipeline does preprocessing, copy, kernels, copy back for batch 1, and only then starts batch 2 - the GPU waits during preprocessing. Bottom: the hybrid preprocesses batch 2 on the CPU while the GPU is still working on batch 1. Important: the hidden layer, output layer and argmax of ONE batch depend on each other, so they run in order on one stream. The overlap is only between different batches, using three streams and pinned buffers.

## Slide 8: Setup: one GPU node, steady-state timing, 20 passes

**Time:** 1 min

**On the slide:** Spartan node: 2× Xeon E5-2680 v4 (28 cores / 28 logical, 24 allocated), Tesla K40m, CUDA 11.7. Mac M4 (10/10) CPU only. 3 warm-up + 20 passes. Steady state.

**What to say:** The reference platform is a Spartan GPU node: two Xeon E5-2680 v4 CPUs - lscpu reports 2 sockets times 14 cores times 1 thread, so 28 physical cores and 28 logical CPUs; my job was allocated 24 - and a Tesla K40m with CUDA 11.7. The CPU-versus-GPU comparison uses only this node. The Mac M4 is used for the OpenMP study only and never mixed with GPU numbers. Each configuration: 3 warm-up passes and 20 recorded passes. All times are steady-state: GPU initialisation, allocation and weight upload are excluded - I measured them separately, 110.7 ms in total. Compile flags are in the paper.

## Slide 9: All implementations produce the same predictions

**Time:** 1 min

**On the slide:** 80/80 comparisons pass | max logit difference 7.6×10⁻⁶ | 100 % identical predictions | 97.97 % accuracy

**What to say:** Before timing anything I verified correctness. Every implementation is compared with the serial reference on all 10,000 images: eighty comparisons per build over batch sizes, thread counts, block sizes and stream counts, all within the tolerance I fixed in advance. OpenMP is bit-identical to serial. CUDA and hybrid differ by at most 7.6×10⁻⁶ in the logits, and predict exactly the same digit for every image. Accuracy is 97.97 percent everywhere. Small differences can come from compiler floating-point optimisations such as fused multiply-add.

## Slide 10: OpenMP scales with the fast cores – and loses at batch 1 on the M4

**Time:** 1.5 min

**On the slide:** Xeon 21.6× (24 threads) | M4 5.6× (10 threads) | M4 batch 1: 0.13×

**What to say:** RQ1. On the Xeon the speedup is almost linear: 21.6 times with 24 threads at batch 4096, efficiency 0.90. On the Apple M4 it follows the ideal line up to its four performance cores - 3.85 times with four threads - then flattens at 5.6 times with ten. With one image per batch, OpenMP on the M4 is slower than serial: 0.13 times with ten threads, because the synchronisation cost per batch is larger than the work. On the Xeon one image takes 123.5 microseconds, on the M4 only 14.1. The Mac is not compared with the GPU.

## Slide 11: Compute-only versus end-to-end: the GPU's lead shrinks

**Time:** 1.5 min

**On the slide:** Compute-only: OpenMP 21.6×, GPU kernels 52.8×. End-to-end: OpenMP 21.6×, CUDA 26.4×, hybrid 50.0×

**What to say:** RQ2. Two different questions. Compute-only - just the hidden layer, output layer and argmax - the GPU kernels are 52.8 times faster than serial and 2.44 times faster than the best OpenMP at batch 4096. End-to-end, with single-threaded preprocessing and copies, the CUDA pipeline is 26.4 times faster than serial and only 1.23 times faster than OpenMP. The hybrid pipeline reaches 50.0 times. For the hybrid there is no compute-only number because its stages overlap. This CUDA result uses a fixed 16 by 16 block; OpenMP and the hybrid use their best thread count.

## Slide 12: Where the CUDA pipeline's time goes

**Time:** 1.5 min

**On the slide:** Batch 4096: kernels 49.3 %, preprocessing 43.3 %, copies 7.3 % | batch 1: kernels 72.4 %, copies 19.8 %

**What to say:** RQ4. At batch 4096 the pipeline spends 49.3 percent in GPU kernels, 43.3 percent in the single-threaded CPU preprocessing - 20.2 milliseconds, constant for every batch size - and only 7.3 percent in copies. The host-to-device copy of 31.4 megabytes takes 3.27 ms, 9.6 gigabytes per second, matching my separate PCIe measurement. At batch 1 the picture flips: kernels 72.4 percent, copies 19.8 percent, launch overhead 6.4 percent.

## Slide 13: The hybrid hides CPU work behind the GPU

**Time:** 1.5 min

**On the slide:** Hybrid 24.7 ms: 1.89× vs CUDA pipeline, 2.32× vs best OpenMP | parallel preprocessing 1.62× + overlap 1.16×

**What to say:** RQ5. The pipelined hybrid needs 24.7 ms at batch 4096: 1.89 times faster than the CUDA pipeline and 2.32 times faster than the best OpenMP. Two ingredients: parallel preprocessing alone - the hybrid-sequential control - gives 1.62 times, and overlapping batches adds another 1.16 times. The hybrid time is only 1.07 times the kernel-only time, so copies and preprocessing are almost completely hidden. The hybrid is fastest from batch 32; at batch 1 and 8 OpenMP alone wins. All differences are significant, p below 10 to the minus 32.

## Slide 14: Amdahl's law: the batch size changes the serial fraction

**Time:** 1.25 min

**On the slide:** Xeon f = 0.006–0.007 (batch ≥64), f = 0.088 (batch 1) | M4 Karp–Flatt 0.013 → 0.101

**What to say:** RQ6. I fitted Amdahl's law to the measured speedups. On the Xeon, for batches of 64 or more, the serial fraction is only 0.006 to 0.007, a ceiling above 130 times - so the 21.6 times at 24 threads is not limited by the serial fraction. With one image per batch it is 0.088, a ceiling of only 11.4 times. On the M4 the Karp-Flatt metric jumps from 0.013 to 0.101 when the efficiency cores join in - a heterogeneous chip breaks the equal-processor assumption. Synchronisation cost against work per batch explains the rest: 7.2 microseconds fork-join on the Xeon, 22.0 on the M4.

## Slide 15: Which implementation should you use?

**Time:** 1 min

**On the slide:** Batch 1–8: OpenMP | batch ≥32: hybrid pipeline | CUDA (1-thread preprocessing) never fastest end-to-end

**What to say:** The answer depends on the batch size. For single images or batches of 8, plain OpenMP on the multicore CPU is fastest. From batch 32 on, the pipelined hybrid is fastest, by about a factor of two over the runner-up. The CUDA pipeline with single-threaded preprocessing is never the fastest end-to-end. In a compute-only comparison the GPU kernels are the fastest from batch 32 on - so the GPU pays off only when preprocessing and copies are overlapped. Caveat: CUDA uses a fixed block size while OpenMP and hybrid use their best thread count.

## Slide 16: Conclusions, limitations and future work

**Time:** 1.25 min

**On the slide:** Conclusions | Limitations | Future work

**What to say:** Conclusions: OpenMP 21.6 times on 24 Xeon threads; the GPU's kernels are 52.8 times faster than serial but the end-to-end pipeline only 26.4 times; the hybrid reaches 24.7 ms per pass, 1.89 times better than the CUDA pipeline. Best choice depends on batch size. Limitations, honestly: one old GPU, the K40m; one CPU node plus a laptop; untuned kernels and a small network; shared machines, median variation 0.2 percent, one slow pass kept in the data. Future work: tiled kernels and cuBLAS, newer GPUs, larger and convolutional networks, GPU-side preprocessing. Thank you - questions?

## Slide 17: Backup: all end-to-end times (Spartan node)

**Time:** 0 min

**On the slide:** Table of all times

**What to say:** Backup slide for questions: end-to-end time per pass for every batch size. OpenMP and Hybrid show the best thread count in brackets. The kernel column is the compute-only GPU kernel time.

## Slide 18: Backup: CUDA block size and what tuning would change

**Time:** 0 min

**On the slide:** Block-size figure and sensitivity

**What to say:** Block size matters only at small batches: at batch 64 the kernel takes 37.3 ms with 8 by 8 blocks, 34.4 with 16 by 16 and 48.6 with 32 by 32. If the best block were used, the CUDA end-to-end time would improve by at most 2.8 percent, and the crossover with OpenMP would move from batch 256 to 128. The main comparison keeps the fixed block, so it is not best-versus-best.

## Slide 19: Backup: compiler settings and flag sensitivity

**Time:** 0 min

**On the slide:** Compiler table and flag sensitivity

**What to say:** Compiler settings. On Spartan one binary is built with g++ 11.4.1 through nvcc 11.7 for the K40's compute capability 3.5; the reference build adds -march=native, the sensitivity build does not. The Mac uses Apple clang with no architecture flag. No fast-math, and the floating-point contraction options were not set, so compiler defaults apply. Plain -O3 changes the serial time by only about five percent.

## Slide 20: Backup: cold start and one-time GPU costs

**Time:** 0 min

**On the slide:** Cold-start table

**What to say:** One-time costs excluded from steady-state times, measured in ten fresh processes: CUDA context creation 106.8 ms on average, weight upload 0.40 ms, buffer allocation 2.97 ms - 110.7 ms in total, about 2.01 times a steady-state CUDA pass. After set-up the first CUDA pass shows no penalty; the first 24-thread OpenMP pass is 27.9 percent slower.

## Slide 21: Backup: run-to-run variation and the slow pass

**Time:** 0 min

**On the slide:** Slow-pass statistics

**What to say:** Variation is small: median coefficient of variation 0.2 percent on Spartan. The largest is the hybrid-pipelined configuration at batch 256 with 4 threads: mean 28.25 ms, median 26.89, standard deviation 6.10, minimum 26.78, maximum 54.18. One pass is over 1.5 times the median. I did not remove it; it is in all statistics and in the raw data.

## Slide 22: Backup: measured platform limits

**Time:** 0 min

**On the slide:** Micro-benchmarks

**What to say:** Micro-benchmark results used in the analysis: PCIe bandwidth, device memory copy rate, kernel launch cost, CPU memory bandwidth and OpenMP fork-join cost. No hardware peak numbers are assumed - everything here was measured.
