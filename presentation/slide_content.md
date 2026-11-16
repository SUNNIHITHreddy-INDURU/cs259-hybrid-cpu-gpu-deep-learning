# Slide content

1. [Introduction] **Title** — Title; Sunnihith Reddy Induru; CS 259 — Advanced Parallel Processing; San José State University; Presentation date: to be added
2. [Introduction] **Why Parallelism Matters for Deep Learning** — Workload → repeated matrix operations → many arithmetic operations → need for CPU and GPU parallelism; GPU kernels fast, application slower (preprocessing, transfers, launch overhead).
3. [Introduction] **Performance Tradeoffs Across CPU, GPU, and Hybrid Execution** — Main question + RQ1–RQ6.
4. [Introduction] **Serial, OpenMP, CUDA, and Hybrid Execution Models** — Table: model / main resource / memory model / main parallelism + mini diagrams.
5. [Method] **MNIST Inference Workload** — 10,000 test images; batches 1–4096; float32; same weights; accuracy 97.97 %.
6. [Method] **Neural-Network Computation** — 784 → FC 784→256 → ReLU → FC 256→10 → argmax; four stages; independent output elements.
7. [Method] **Four Implementations of the Same Computation** — Serial | OpenMP | CUDA (1-thread preprocessing) | Hybrid; hybrid-sequential = diagnostic control.
8. [Method] **CUDA Host–Device Execution** — Host memory → H2D copy → device memory → kernel launch → grid → blocks → threads → D2H copy → predictions; 8×8, 16×16, 32×32.
9. [Method] **Hybrid CPU–GPU Pipeline** — OpenMP preprocesses batch i+1 while CUDA copies/computes batch i; three streams; layers within a batch stay ordered; overlap between batches.
10. [Method] **Experimental Setup and Measurement Protocol** — Setup table; Spartan node for CPU-vs-GPU; M4 separate.
11. [Results] **Correctness Across Implementations** — Correctness table: comparisons passed, max logit difference, prediction agreement, accuracy.
12. [Results] **OpenMP Scalability** — Spartan: time, speedup, efficiency vs threads; 21.6× at 24 threads (batch 4096); batch 1 saturates; M4 in backup.
13. [Results] **CUDA Computation and End-to-End Performance** — End-to-end: serial, OpenMP, CUDA pipeline. Compute-only: serial, OpenMP, CUDA kernels. Kernels 52.8× vs pipeline 26.4× (batch 4096); batch 1 CUDA 0.82×.
14. [Results] **Where the CUDA Pipeline Time Goes** — Batch 1: kernels 72.4 %, copies 19.8 %; batch 4096: kernels 49.3 %, preprocessing 43.3 %, copies 7.3 %.
15. [Results] **Hybrid Execution Reduces End-to-End Time** — Hybrid 24.7 ms vs CUDA pipeline 46.7 ms (batch 4096); effects: 1.62× preprocessing, 1.16× overlap; hybrid faster than OpenMP from batch 32.
16. [Results] **The Best Implementation Depends on Batch Size** — Fastest / runner-up per batch size (end-to-end, Spartan).
17. [Results] **Why Speedup Eventually Stops Increasing** — S(N) = 1/((1−P)+P/N); Xeon f = 0.006 (batch 4096), 0.088 (batch 1); limitations list.
18. [Conclusions] **Conclusions and Future Work** — Four conclusions; future work; final statement.
19. [Backup] **Backup: Full end-to-end timing table (Spartan)** — Full timing table.
20. [Backup] **Backup: Compute-only comparison (stages 1–3)** — Compute-only table.
21. [Backup] **Backup: OpenMP on the Apple M4 (separate platform)** — M4 OpenMP charts.
22. [Backup] **Backup: CUDA block-size comparison** — Block-size chart.
23. [Backup] **Backup: Compiler settings and flag sensitivity** — Compiler table.
24. [Backup] **Backup: Cold-start timing** — Cold-start table.
25. [Backup] **Backup: Run-to-run variation** — Variation table.
26. [Backup] **Backup: Measured hardware limits (Spartan)** — Micro-benchmarks.
27. [Backup] **Backup: Detailed correctness results (Spartan, reference build)** — Detailed correctness.
28. [Backup] **Backup: Kernel and OpenMP code details** — Code excerpts.
