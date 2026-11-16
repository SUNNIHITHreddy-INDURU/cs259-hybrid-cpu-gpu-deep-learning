# Possible professor questions and answers

All numbers are measured (Spartan node: Tesla K40m, 2× Xeon E5-2680 v4, 24 threads, CUDA 11.7; mean of 20 passes over
10,000 images; times in milliseconds per pass). "CUDA pipeline" = CUDA with single-threaded CPU preprocessing and a fixed
16×16 block. Where something was not measured, the answer says so.

**1. Why MNIST?**
It is small, fully specified (784 inputs, 10 classes) and reproducible on any machine, so the study is about parallel
performance, not about accuracy. The weights were trained once (97.97 % test accuracy) so that "correct" is meaningful.

**2. Why inference instead of training?**
Inference is the deployment workload and has a clean, repeatable structure (preprocess, two layers, argmax). Training adds
backpropagation and an optimiser, which would need different kernels and a much larger scope. Training was done once offline
in NumPy only to obtain meaningful weights.

**3. Why C++ and CUDA instead of only Python?**
OpenMP and CUDA are C/C++ interfaces, and the study depends on explicit control of threads, memory and copies. A Python
layer would add overhead that hides exactly the effects being measured. Python is used only for the data download, the
one-time training and the analysis.

**4. Why is the serial implementation necessary?**
It is the correctness reference (every other implementation is compared with it) and the baseline of every speedup,
S = T_serial / T_implementation, and of the Amdahl fit.

**5. Why can CUDA kernel time differ from end-to-end time?**
Kernel-only time excludes preprocessing, copies and launch overhead. At batch 4096 the three GPU kernels take 23.0 ms, but
the whole CUDA pipeline takes 46.7 ms: 52.8× against serial compute-only, 26.4× end-to-end. 43.3 % of the pipeline is the
single-threaded CPU preprocessing and 7.3 % is copies.

**6. What exactly makes your implementation hybrid?**
OpenMP threads preprocess batch i+1 into pinned memory while CUDA streams copy and compute batch i. Both have a real role:
the hybrid-sequential control (OpenMP preprocessing, no overlap) gives 1.62× over the CUDA pipeline; overlapping adds 1.16×;
total 1.89× (24.7 ms against 46.7 ms). Streams overlap different batches only. The layers of one batch depend on each other
and run in order on one stream.

**7. Why does speedup stop increasing with more OpenMP threads?**
It depends on the machine and batch size. On the Xeon it does not stop for batches of 32 or more: 21.6× with 24 threads
(efficiency 0.90). On the Apple M4 the speedup follows the ideal up to its 4 performance cores (3.85×) and flattens at 5.56×
with 10 threads; the Karp–Flatt metric jumps from 0.013 to 0.101 when the efficiency cores join. With one image per batch,
synchronisation costs more than the work (M4: 0.13× with 10 threads). (The M4 is not compared with the GPU.)

**8. Why might CUDA be slower for small batches?**
With one image per batch the program runs 10,000 batches, each with 3 kernel launches, 2 copies and a synchronisation. The
kernels take 109.1 µs per batch; a batch of one image leaves only 256 of the 4,096 launched threads with useful work, so the
kernels are latency-bound (my interpretation; the kernel was not profiled separately). Launch/API/sync overhead is 9.7 µs per batch. End-to-end it is 0.82× (slower than serial).

**9. How did you verify correctness?**
Eighty comparisons per build against the serial reference on all 10,000 images, over batch sizes (including 37, which leaves
a partial batch), thread counts, block sizes and stream counts. The tolerance (max logit difference 1×10⁻⁴, agreement
≥ 99.9 %) was fixed before measuring. Results: OpenMP bit-identical; CUDA and hybrid differ by at most 7.6×10⁻⁶ with 100 %
identical predictions; accuracy 97.97 % everywhere; float32 against an independent float64 NumPy computation: 9.3×10⁻⁵.

**10. What are the limitations?**
One old GPU (Tesla K40m, compute capability 3.5), one CPU node plus a laptop, untuned kernels (3.3 GFLOP/s serial,
70.9 OpenMP, 176.5 CUDA kernels alone), a small network that fits in cache, shared machines (median variation 0.2 %, one
slow pass kept), and a comparison of CUDA with a fixed block against OpenMP with tuned thread count.

**11. Why not PyTorch?**
The goal is to study OpenMP and CUDA directly. A framework would hide the kernels, transfers and threading that this study
measures.

**12. Why not cuBLAS?**
It would replace the kernel under study with an opaque, tuned routine and shift the conclusions to library quality. It is
listed as future work. Our kernels are untuned, so a library would very likely be faster; that was not measured.

**13. What would change with a larger CNN?**
Not measured. Hypotheses only: more arithmetic per byte copied could shrink the relative cost of transfers, but weights that
no longer fit in cache could make memory bandwidth the limit. This needs its own experiment.

**14. How does Amdahl's law apply?**
I fitted the serial fraction f to the measured speedups. On the Xeon, f = 0.006–0.007 for batches of 64 or more (a ceiling
above 130×, so 21.6× at 24 threads is not limited by it) and f = 0.088 for one image per batch (ceiling 11.4×). The batch
size therefore changes the effective serial fraction. On the M4 the efficiency cores break the equal-processor assumption.

**15. Which implementation is best and under what conditions?**
End-to-end: OpenMP for batches of 1 and 8 (162.8 ms and 75.5 ms); the pipelined hybrid from batch 32 on (33.3 ms down to
24.7 ms, about twice as fast as the runner-up); the CUDA pipeline with single-threaded preprocessing is never the fastest.
Compute-only, the GPU kernels are the fastest from batch 32 on (1.27× over the best OpenMP, 2.44× at batch 4096).

**16. What part of the workload is the bottleneck?**
CUDA pipeline at batch 4096: kernels 49.3 %, CPU preprocessing 43.3 %, copies 7.3 %. In the hybrid the pass (24.7 ms) is
within 1.07× of the kernel-only time (23.0 ms), so the GPU computation becomes the bottleneck. At batch 1 launch overhead
and under-filled GPU dominate.

**17. How reproducible are your results?**
Every pass is a row in a raw CSV with the hardware and compiler recorded; scripts, Slurm job files and commands are in the
repository and the Overleaf project; MNIST is checksum-verified and the weights are fixed. 20 passes per configuration,
median coefficient of variation 0.2 % (Spartan). The one slow pass (hybrid, batch 256, 4 threads: median 26.89 ms, maximum
54.18 ms) is kept in the data.

**18. What would you improve with more time?**
Tiled and cuBLAS-based kernels, a newer GPU, GPU-side preprocessing, a block-size tuned hybrid (best-versus-best), larger and
convolutional networks, and energy measurements.

## Extra questions that may come up

**Did you give any implementation an advantage?**
Some asymmetries are disclosed in the paper. In favour of OpenMP and hybrid: they use the best of seven thread counts, CUDA a
fixed block (the best block would change CUDA end-to-end by at most 2.8 %). In favour of the GPU: one-time initialisation
(110.7 ms) is excluded from steady-state times. Against the GPU: the CUDA pipeline preprocesses with one thread, and the K40m
is an older GPU. Everything else (data, weights, operations, precision, source-level reduction order) is the same.

**How many cores did you use?**
Spartan node: 2 sockets × 14 cores × 1 thread per core = 28 physical cores = 28 logical CPUs (lscpu); my jobs were allocated
24, so at most 24 OpenMP threads. Apple M4: 10 cores (4 performance + 6 efficiency), 10 logical CPUs.

**What does the GPU start-up cost?**
Cold start, 10 fresh processes: CUDA context creation 106.8 ms on average, weight upload 0.40 ms, buffer allocation 2.97 ms,
110.7 ms in total (about 2× one steady-state pass). The first CUDA pass shows no extra penalty; the first 24-thread OpenMP
pass is 27.9 % slower. Steady-state numbers exclude these one-time costs.

**Why is hybrid-sequential not a fifth implementation?**
It is a diagnostic control: it keeps OpenMP preprocessing but removes the overlap, so the effect of parallel preprocessing can
be separated from the effect of overlapping.

**Why did the M4 not take part in the CPU-versus-GPU comparison?**
It has no NVIDIA GPU, and mixing machines would break the same-machine fairness rule. Its results are used only for the
OpenMP study.
