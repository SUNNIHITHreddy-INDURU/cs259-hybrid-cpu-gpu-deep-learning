# Slide content (18 slides)

1. **Title** (1 min) — Introduce the project and state that four execution approaches are compared on one workload.
   - Visual: Dark title slide, no diagram.
   - Text: Performance Evaluation of Hybrid CPU–GPU Parallelism for Deep Learning Using OpenMP and CUDA; Sunnihith Reddy Induru; CS 259 — Advanced Parallel Processing; San José State University; Presentation date: to be added
2. **Why Parallelism Matters for Deep Learning** (1 min) — Show why parallel execution is needed and plant the idea that a fast kernel is not a fast application.
   - Visual: Four-box flow: workload → repeated operations → computation cost → CPU and GPU parallelism; callout with measured kernel-only vs end-to-end speedup.
   - Text: Workload → repeated operations → computation cost → CPU and GPU parallelism; fast kernel ≠ fast application.
3. **Performance Tradeoffs Across CPU, GPU, and Hybrid Execution** (1 min) — State the main question and the six research questions that organise the results.
   - Visual: Highlighted question box and six numbered research questions.
   - Text: Main question + RQ1–RQ6.
4. **Project Objectives** (1 min) — List what was built and measured, and stress that all implementations compute the same workload.
   - Visual: Six numbered objectives and a highlighted fairness statement.
   - Text: Six objectives; same data, weights, network, workload.
5. **CPU, OpenMP, GPU, and CUDA** (1.25 min) — Teach the four execution models (resource, memory model, parallelism) before any results.
   - Visual: Four-row comparison table with a small 'workers' diagram per model.
   - Text: Table: model / main resource / memory model / parallelism + mini diagrams.
6. **MNIST Dataset and Neural-Network Workload** (1 min) — Define the workload: data, network architecture, precision, batch sizes and the fact that inference (not training) is measured.
   - Visual: Image → pixels → features → network → digit flow, network architecture row, and fact list.
   - Text: MNIST image → 28×28 → 784 features → network → digit; 784→256→ReLU→10→argmax; 10,000 images, float32, batches 1–4096, accuracy 97.97 %.
7. **Overall System Architecture** (1 min) — Show that the mathematical workload is identical while the execution model changes.
   - Visual: Workload pipeline row with four aligned execution lanes (serial, OpenMP, CUDA, hybrid).
   - Text: Workload row; serial / OpenMP / CUDA / hybrid lanes aligned under the stages.
8. **Serial CPU Implementation** (1 min) — Explain the baseline that all speedups and the correctness checks refer to.
   - Visual: Short pseudocode box and a one-thread timeline of sequential images.
   - Text: Pseudocode: per image → preprocess, hidden, ReLU, output, select digit; one thread; baseline and correctness reference.
9. **OpenMP CPU Implementation** (1.25 min) — Explain fork-and-join execution, why synchronization is needed, and which thread counts were used.
   - Visual: Fork-join diagram (main thread → threads → barrier → next stage) and thread-count chips.
   - Text: Fork-and-join; threads share memory; synchronization between stages; thread counts: Spartan 1,2,4,8,12,16,24; M4 1,2,4,6,8,10.
10. **CUDA GPU Implementation** (1.25 min) — Explain the host–device model and the grid → block → thread hierarchy, and that kernel time and end-to-end time are different measurements.
   - Visual: Host/device data-path flow plus grid, block and thread diagram with block-size options.
   - Text: Host memory → H2D → GPU memory → kernel launch → grid/blocks/threads → computation → D2H → predictions; kernel time ≠ end-to-end time.
11. **Hybrid OpenMP–CUDA Pipeline** (1.25 min) — Explain how OpenMP preprocessing, pinned memory, asynchronous copies and three CUDA streams make different batches overlap, and what hybrid-sequential is.
   - Visual: Six-box hybrid flow plus a CPU lane and three CUDA stream lanes showing batch overlap (schematic).
   - Text: OpenMP preprocessing → pinned memory → async transfer → CUDA streams → GPU computation → predictions; timeline; layers ordered within a batch; hybrid-sequential = control.
12. **Experimental Setup and Measurement Protocol** (1.25 min) — Document exactly what was measured and why each important decision was made.
   - Visual: Three-column table: item, configuration, reason.
   - Text: Setup table with reasons.
13. **Correctness Validation Before Performance Comparison** (1 min) — Show that all implementations produce equivalent outputs before any timing is interpreted.
   - Visual: Accuracy-vs-correctness definition boxes and a comparison table.
   - Text: Accuracy vs correctness; table: passed, max logit difference, agreement, accuracy.
14. **End-to-End Execution Time Across All Implementations** (1.25 min) — Compare all four implementations on one graph and locate the performance crossovers.
   - Visual: One native line chart (log time axis) with serial, OpenMP, CUDA pipeline and hybrid pipeline versus batch size, with 95% error bars.
   - Text: Fastest at batch 1/8: OpenMP; from batch 32: hybrid; CUDA pipeline reaches OpenMP around batch 128–256.
15. **Speedup and Throughput Across All Implementations** (1.5 min) — Show relative performance (speedup) and absolute performance (throughput) of all four implementations side by side.
   - Visual: Two native charts: speedup over serial (×) and throughput (images per second, log axis), each with all four implementations.
   - Text: Speedup = serial time / implementation time; throughput = 10,000 / time (s). Batch 4096: speedup OpenMP 21.6×, CUDA 26.4×, hybrid 50.0×.
16. **CUDA Overhead and Hybrid Performance** (1.25 min) — Explain why CUDA kernels are fast but the CUDA pipeline is slower, and quantify what OpenMP preprocessing and CPU–GPU overlap each contribute.
   - Visual: Left: line chart of kernel-only, CUDA end-to-end, hybrid-sequential and hybrid-pipelined; right: stacked percentage chart of CUDA pipeline stages.
   - Text: Batch 4096: kernels 23.0 ms, CUDA end-to-end 46.7 ms, hybrid-sequential 28.8 ms, hybrid-pipelined 24.7 ms; shares: kernels 49.3 %, preprocessing 43.3 %, copies 7.3 %.
17. **Amdahl’s Law and Performance Bottlenecks** (1.25 min) — Connect Amdahl's law to the measured results and explain which serial costs limit the speedup.
   - Visual: Formula, native chart of measured speedup vs fitted Amdahl curves (batch 1 and 4096), and four connecting statements.
   - Text: S(N) = 1/((1−P)+P/N); Xeon f = 0.006 (batch 4096), 0.088 (batch 1).
18. **Conclusions, Limitations, and Future Work** (1.75 min) — Summarise the verified conclusions, state the limitations honestly, list future work and end with the main message.
   - Visual: Three-column text (conclusions, limitations, future work) and a closing statement.
   - Text: Five conclusions; six limitations; seven future-work items; closing statement.
