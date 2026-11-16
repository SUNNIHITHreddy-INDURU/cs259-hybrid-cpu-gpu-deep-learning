# Slide content

1. **Title** — Performance Evaluation of Hybrid CPU-GPU Parallelism for Deep Learning Using OpenMP and CUDA — Sunnihith Reddy Induru, CS 259, SJSU
2. **A fast GPU kernel is not a fast application** — Kernels only 52.8× | end-to-end 26.4× | batch 1 0.82×
3. **Six questions about CPU, GPU and hybrid execution** — RQ1: How much speedup does OpenMP give over serial?
RQ2: How does CUDA compare with serial and OpenMP – compute-only and end-to-end?
RQ3: How does the batch size change CPU and GPU performance?
RQ4: How much GPU time is data transfer, not computation?
RQ5: Does a hybrid OpenMP–CUDA pipeline improve end-to-end time?
RQ6: How do results relate to Amdahl's law, overhead and bandwidth?
4. **Two kinds of parallelism, two kinds of overhead** — OpenMP: shared memory, fork-join, barrier per loop. CUDA: thousands of threads, separate memory, PCIe copies, launch cost. Hybrid: overlap CPU and GPU work.
5. **Workload: MNIST digits through a 784→256→10 network** — 10,000 MNIST test images | 784→256→ReLU→10, float32 | 203,530 parameters | batches 1–4096 | stages: preprocess, hidden, output, argmax
6. **Four implementations of the same computation** — Serial | OpenMP | CUDA (1-thread preprocessing) | Hybrid pipeline. Hybrid-sequential = diagnostic control only.
7. **Streams overlap different batches, never the layers of one batch** — Schematic: sequential vs pipelined. Overlap between batches only; layers of one batch stay in order on one stream.
8. **Setup: one GPU node, steady-state timing, 20 passes** — Spartan node: 2× Xeon E5-2680 v4 (28 cores / 28 logical, 24 allocated), Tesla K40m, CUDA 11.7. Mac M4 (10/10) CPU only. 3 warm-up + 20 passes. Steady state.
9. **All implementations produce the same predictions** — 80/80 comparisons pass | max logit difference 7.6×10⁻⁶ | 100 % identical predictions | 97.97 % accuracy
10. **OpenMP scales with the fast cores – and loses at batch 1 on the M4** — Xeon 21.6× (24 threads) | M4 5.6× (10 threads) | M4 batch 1: 0.13×
11. **Compute-only versus end-to-end: the GPU's lead shrinks** — Compute-only: OpenMP 21.6×, GPU kernels 52.8×. End-to-end: OpenMP 21.6×, CUDA 26.4×, hybrid 50.0×
12. **Where the CUDA pipeline's time goes** — Batch 4096: kernels 49.3 %, preprocessing 43.3 %, copies 7.3 % | batch 1: kernels 72.4 %, copies 19.8 %
13. **The hybrid hides CPU work behind the GPU** — Hybrid 24.7 ms: 1.89× vs CUDA pipeline, 2.32× vs best OpenMP | parallel preprocessing 1.62× + overlap 1.16×
14. **Amdahl's law: the batch size changes the serial fraction** — Xeon f = 0.006–0.007 (batch ≥64), f = 0.088 (batch 1) | M4 Karp–Flatt 0.013 → 0.101
15. **Which implementation should you use?** — Batch 1–8: OpenMP | batch ≥32: hybrid pipeline | CUDA (1-thread preprocessing) never fastest end-to-end
16. **Conclusions, limitations and future work** — Conclusions | Limitations | Future work
17. **Backup: all end-to-end times (Spartan node)** — Table of all times
18. **Backup: CUDA block size and what tuning would change** — Block-size figure and sensitivity
19. **Backup: compiler settings and flag sensitivity** — Compiler table and flag sensitivity
20. **Backup: cold start and one-time GPU costs** — Cold-start table
21. **Backup: run-to-run variation and the slow pass** — Slow-pass statistics
22. **Backup: measured platform limits** — Micro-benchmarks
