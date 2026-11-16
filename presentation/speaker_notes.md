# Speaker notes — exactly 18 slides, about 21.25 minutes

## Slide 1: Title

**Estimated speaking time:** 1 min

**Main purpose:** Introduce the project and state that four execution approaches are compared on one workload.

**Recommended visual:** Dark title slide, no diagram.

**Text on the slide:** Performance Evaluation of Hybrid CPU–GPU Parallelism for Deep Learning Using OpenMP and CUDA; Sunnihith Reddy Induru; CS 259 — Advanced Parallel Processing; San José State University; Presentation date: to be added

**What to say:**

Good morning, everyone. My project is called "Performance Evaluation of Hybrid CPU-GPU Parallelism for Deep Learning Using OpenMP and CUDA."

The project evaluates four execution approaches for exactly the same neural-network inference workload on MNIST digits: a serial CPU baseline, an OpenMP version that uses many CPU threads, a CUDA version that runs the network on the GPU, and a hybrid OpenMP-CUDA pipeline that uses the CPU and the GPU at the same time.

I measured all four on the same machine, and I will tell you when each one is the right choice. One note before we start: every number in these slides was measured by me and can be traced back to the raw measurement files in my repository. I also use one extra configuration, called hybrid-sequential, but only as a diagnostic control - I will explain it when we reach the hybrid design.

## Slide 2: Why Parallelism Matters for Deep Learning

**Estimated speaking time:** 1 min

**Main purpose:** Show why parallel execution is needed and plant the idea that a fast kernel is not a fast application.

**Recommended visual:** Four-box flow: workload → repeated operations → computation cost → CPU and GPU parallelism; callout with measured kernel-only vs end-to-end speedup.

**Text on the slide:** Workload → repeated operations → computation cost → CPU and GPU parallelism; fast kernel ≠ fast application.

**What to say:**

Neural-network inference is a large number of repeated mathematical operations - mostly matrix operations. My network does about two hundred thousand multiply-adds per image, and one pass does that for ten thousand images. As the workload grows, the computation cost grows with it, and on one CPU thread it becomes slow.

There are two standard remedies: OpenMP uses several CPU threads that share memory, and CUDA uses many thousands of GPU threads.

But a fast GPU kernel does not always mean a fast complete application. The application also pays for preprocessing, for copying data to and from the GPU, and for kernel-launch overhead. On my measurements the GPU kernels alone are 52.8 times faster than serial, but the complete CUDA pipeline is only 26.4 times faster. The rest of the talk explains why, and what a hybrid design can do about it.

## Slide 3: Performance Tradeoffs Across CPU, GPU, and Hybrid Execution

**Estimated speaking time:** 1 min

**Main purpose:** State the main question and the six research questions that organise the results.

**Recommended visual:** Highlighted question box and six numbered research questions.

**Text on the slide:** Main question + RQ1–RQ6.

**What to say:**

This is the question the whole project asks: how do serial CPU, OpenMP CPU, CUDA GPU, and hybrid OpenMP-CUDA implementations compare when they execute the same neural-network inference workload?

To answer it properly I broke it into six research questions. One: how much speedup does OpenMP provide over serial execution? Two: how does CUDA compare with CPU execution? Three: how does batch size affect performance? Four: how much GPU time is spent on memory transfer? Five: does hybrid execution improve end-to-end performance? And six: how do the results relate to Amdahl's law and parallel overhead?

The results slides answer these in order: slide 14 gives the end-to-end times, slide 15 speedup and throughput, slide 16 the CUDA overhead and the hybrid, and slide 17 connects everything to Amdahl's law.

## Slide 4: Project Objectives

**Estimated speaking time:** 1 min

**Main purpose:** List what was built and measured, and stress that all implementations compute the same workload.

**Recommended visual:** Six numbered objectives and a highlighted fairness statement.

**Text on the slide:** Six objectives; same data, weights, network, workload.

**What to say:**

Here is what I set out to do. One: implement a serial C++ baseline. Two: implement an OpenMP version for the CPU. Three: implement a CUDA version for the GPU. Four: implement a hybrid OpenMP-CUDA pipeline. Five: compare execution time, speedup, throughput, scalability, correctness and overhead across them. And six: determine which implementation is best for different batch sizes.

The point I want to stress at the bottom of the slide is fairness. All four implementations use the same input data, the same trained weights, the same network and the same mathematical workload. Only the execution model changes. That is what makes the comparison meaningful: any difference in time comes from how the work is executed, not from doing different work.

## Slide 5: CPU, OpenMP, GPU, and CUDA

**Estimated speaking time:** 1.25 min

**Main purpose:** Teach the four execution models (resource, memory model, parallelism) before any results.

**Recommended visual:** Four-row comparison table with a small 'workers' diagram per model.

**Text on the slide:** Table: model / main resource / memory model / parallelism + mini diagrams.

**What to say:**

Before the results, I want everyone to understand how these four models differ, because the results only make sense with that picture in mind.

Serial CPU: one CPU worker, one thread, doing the work strictly one piece after another, in shared CPU memory. OpenMP CPU: several CPU workers - threads - sharing the same CPU memory; the work is divided among them, with synchronization points between dependent steps. CUDA GPU: many, many GPU workers, but with a separate GPU memory, so data has to be copied there first; the parallelism is massive data parallelism - the same instructions on thousands of independent pieces of data. Hybrid: the CPU and the GPU working together, with coordinated parallelism - the CPU workers prepare the data while the GPU workers compute - and memory split between host and device.

The small pictures in the last column show the idea: one worker; several workers forked from a master and joined again; a big grid of tiny GPU workers; and a CPU worker feeding a GPU.

## Slide 6: MNIST Dataset and Neural-Network Workload

**Estimated speaking time:** 1 min

**Main purpose:** Define the workload: data, network architecture, precision, batch sizes and the fact that inference (not training) is measured.

**Recommended visual:** Image → pixels → features → network → digit flow, network architecture row, and fact list.

**Text on the slide:** MNIST image → 28×28 → 784 features → network → digit; 784→256→ReLU→10→argmax; 10,000 images, float32, batches 1–4096, accuracy 97.97 %.

**What to say:**

The workload is MNIST digit classification - inference only, no training. The image is the first real test image: 28 by 28 pixels, so 784 input features, and the network predicts seven, which is also its true label.

The architecture is small: 784 inputs, a hidden layer of 256 units, a ReLU, an output layer of 10 units, and an argmax that picks the digit. Everything is float32.

Every pass processes all ten thousand test images, in batches of 1, 8, 32, 64, 128, 256, 1,024 or 4,096. All implementations load the same trained weights, and the model classifies 97.97 percent correctly - confirmed by my training log and the correctness runs.

I chose MNIST because it is realistic but small enough to implement directly in C++ and CUDA, so I control every thread and every copy.

## Slide 7: Overall System Architecture

**Estimated speaking time:** 1 min

**Main purpose:** Show that the mathematical workload is identical while the execution model changes.

**Recommended visual:** Workload pipeline row with four aligned execution lanes (serial, OpenMP, CUDA, hybrid).

**Text on the slide:** Workload row; serial / OpenMP / CUDA / hybrid lanes aligned under the stages.

**What to say:**

This slide has the whole system on one page. The top row is the workload, and it is the same for everybody: MNIST input, preprocessing, hidden layer, ReLU, output layer, argmax, predicted digit.

Underneath, each lane shows who executes those stages. Serial, in gray: every stage runs on one CPU thread. OpenMP, in blue: every stage runs on multiple CPU threads. CUDA: the preprocessing still runs on a single CPU thread - which is why I call it the CUDA pipeline with single-threaded preprocessing and not a GPU-only version - and the neural-network layers run on the GPU, with a host-to-device copy before and a device-to-host copy after. Hybrid: OpenMP threads do the preprocessing, CUDA does the computation, and different batches overlap in time.

The message of the slide is at the bottom: the mathematical workload stays the same, only the execution model changes.

## Slide 8: Serial CPU Implementation

**Estimated speaking time:** 1 min

**Main purpose:** Explain the baseline that all speedups and the correctness checks refer to.

**Recommended visual:** Short pseudocode box and a one-thread timeline of sequential images.

**Text on the slide:** Pseudocode: per image → preprocess, hidden, ReLU, output, select digit; one thread; baseline and correctness reference.

**What to say:**

The serial implementation is the simplest. For each image: preprocess, compute the hidden layer, apply ReLU, compute the output layer, and select the predicted digit. One CPU thread does everything, in order.

It matters for two reasons. It is the baseline - every speedup in this talk is relative to the serial time on the same machine and batch size - and it is the reference for correctness: every other implementation is compared with its outputs.

On the Spartan node a serial pass takes 1235.4 milliseconds at batch 4096, and between 1234.6 and 1235.7 milliseconds across all batch sizes - essentially independent of batch size - about 8,094 images per second.

## Slide 9: OpenMP CPU Implementation

**Estimated speaking time:** 1.25 min

**Main purpose:** Explain fork-and-join execution, why synchronization is needed, and which thread counts were used.

**Recommended visual:** Fork-join diagram (main thread → threads → barrier → next stage) and thread-count chips.

**Text on the slide:** Fork-and-join; threads share memory; synchronization between stages; thread counts: Spartan 1,2,4,8,12,16,24; M4 1,2,4,6,8,10.

**What to say:**

OpenMP uses a fork-and-join model. The main CPU thread forks a team of threads. Each thread processes a separate portion of the work - different images or groups of hidden units - and these calculations are independent. The threads share CPU memory, so nothing is copied. At the end of each parallel loop all threads meet at a barrier before the next stage starts, because the next stage needs the previous results.

Thread counts: on the Spartan node 1, 2, 4, 8, 12, 16 and 24, because my job was allocated 24 CPUs; on the Apple M4 laptop 1, 2, 4, 6, 8 and 10 - a separate platform, never part of the GPU comparison.

Typical limits are thread overhead, synchronization and memory bandwidth. In my data the synchronization cost is visible at tiny batches: one image per batch saturates at 7.6 times, while large batches reach 21.6 times with 24 threads, an efficiency of 0.90. I did not isolate memory bandwidth.

## Slide 10: CUDA GPU Implementation

**Estimated speaking time:** 1.25 min

**Main purpose:** Explain the host–device model and the grid → block → thread hierarchy, and that kernel time and end-to-end time are different measurements.

**Recommended visual:** Host/device data-path flow plus grid, block and thread diagram with block-size options.

**Text on the slide:** Host memory → H2D → GPU memory → kernel launch → grid/blocks/threads → computation → D2H → predictions; kernel time ≠ end-to-end time.

**What to say:**

On the left is the data path. The CPU is the host, the GPU is the device, and they have separate memories. The batch starts in CPU memory, is copied over PCIe into GPU memory, the host launches a kernel, the kernel computes, and the predictions are copied back.

On the right is how the GPU organizes threads. A launch creates a grid; the grid is made of blocks; each block is made of threads. In my hidden-layer kernel a block is d by d threads, and thread tx, ty of block bx, by computes exactly one output: hidden unit j equals bx times d plus tx, for image b equals by times d plus ty. Threads compute independent outputs. I used 16 by 16 blocks - 256 threads - and also measured 8 by 8 and 32 by 32.

One distinction matters for the whole talk: kernel time and end-to-end time are different measurements. Kernel time is only the GPU computation; end-to-end includes preprocessing, both copies, launches and synchronization. I never treat kernel-only speed as the speed of the application.

## Slide 11: Hybrid OpenMP–CUDA Pipeline

**Estimated speaking time:** 1.25 min

**Main purpose:** Explain how OpenMP preprocessing, pinned memory, asynchronous copies and three CUDA streams make different batches overlap, and what hybrid-sequential is.

**Recommended visual:** Six-box hybrid flow plus a CPU lane and three CUDA stream lanes showing batch overlap (schematic).

**Text on the slide:** OpenMP preprocessing → pinned memory → async transfer → CUDA streams → GPU computation → predictions; timeline; layers ordered within a batch; hybrid-sequential = control.

**What to say:**

This is the central idea. In the plain CUDA pipeline the GPU idles while the CPU preprocesses, and the CPU waits while the GPU works. The hybrid removes that waiting.

The flow at the top: OpenMP threads preprocess into pinned host memory; pinned memory allows asynchronous transfers; the transfers go into CUDA streams; the GPU computes; the predictions come back.

The timeline is a schematic, not measured data. The CPU preprocesses batch 1, then 2, then 3. As soon as batch 1 is ready, its copy, kernels and copy back go into stream 0; while the GPU works on it, the CPU is already preprocessing batch 2, which stream 1 handles, and batch 3 goes to stream 2. So OpenMP preprocesses future batches while CUDA processes earlier ones.

The purple box matters: inside one batch the hidden layer, output layer and argmax depend on each other, so they stay in order; only different batches overlap.

Hybrid-sequential - OpenMP preprocessing with no overlap - is only a diagnostic control. It separates the benefit of parallel preprocessing from the benefit of overlap.

## Slide 12: Experimental Setup and Measurement Protocol

**Estimated speaking time:** 1.25 min

**Main purpose:** Document exactly what was measured and why each important decision was made.

**Recommended visual:** Three-column table: item, configuration, reason.

**Text on the slide:** Setup table with reasons.

**What to say:**

Here is exactly how I measured, and why. The workload is the ten thousand MNIST test images in float32 through the 784-256-10 network, in batches from 1 to 4,096 - covering both latency-bound and throughput-bound behavior.

The main platform is a Spartan GPU node: two Xeon E5-2680 v4 CPUs - lscpu reports 28 physical cores and 28 logical CPUs, and my jobs were allocated 24, so OpenMP uses at most 24 threads - and a Tesla K40m with CUDA 11.7. Compilers are g++ 11.4.1 with O3 and march native, and nvcc 11.7. The Apple M4, with clang 21, is only a separate CPU study.

Protocol: three unrecorded warm-up passes to remove start-up effects, then twenty recorded passes, all kept and reported with mean, median, standard deviation, minimum, maximum and 95 percent confidence intervals. GPU stages use CUDA events; end-to-end time is wall clock. GPU initialization, allocation and weight upload are one-time costs, excluded from steady state and measured separately: 110.7 milliseconds. The CUDA block is fixed at 16 by 16, and CPU-versus-GPU comparisons use one node only.

## Slide 13: Correctness Validation Before Performance Comparison

**Estimated speaking time:** 1 min

**Main purpose:** Show that all implementations produce equivalent outputs before any timing is interpreted.

**Recommended visual:** Accuracy-vs-correctness definition boxes and a comparison table.

**Text on the slide:** Accuracy vs correctness; table: passed, max logit difference, agreement, accuracy.

**What to say:**

Before interpreting any timing I checked correctness - and I separate two ideas. Accuracy: how well the model classifies MNIST, 97.97 percent. Correctness: whether all implementations produce equivalent outputs.

The table compares each implementation with the serial reference on all ten thousand images, over several batch sizes, thread counts, block sizes and stream counts - eighty comparisons, all passing. OpenMP is bit-identical. CUDA and both hybrid variants differ by at most 7.6×10⁻⁶ in the logits and predict exactly the same digit for every image.

Small floating-point differences are possible - same operations and source-level order, but compilers may apply optimizations such as fused multiply-add - so I fixed a tolerance beforehand: maximum logit difference 1e-4, agreement at least 99.9 percent. A faster implementation is invalid if its output is incorrect.

## Slide 14: End-to-End Execution Time Across All Implementations

**Estimated speaking time:** 1.25 min

**Main purpose:** Compare all four implementations on one graph and locate the performance crossovers.

**Recommended visual:** One native line chart (log time axis) with serial, OpenMP, CUDA pipeline and hybrid pipeline versus batch size, with 95% error bars.

**Text on the slide:** Fastest at batch 1/8: OpenMP; from batch 32: hybrid; CUDA pipeline reaches OpenMP around batch 128–256.

**What to say:**

This is the main result: all four implementations on one graph - serial, OpenMP with its best thread count, the CUDA pipeline and the hybrid. The y-axis is the time of one pass over ten thousand images in milliseconds, log scale, with tiny 95 percent confidence intervals. Everything is the Spartan node.

Fastest for small batches: OpenMP. At batch 1 it needs 162.8 milliseconds, the hybrid 650.9, and the CUDA pipeline 1507.0 - slower than serial at 1234.8. At batch 8 OpenMP still leads, 75.5 against 87.5.

Fastest for large batches: the hybrid - 24.7 milliseconds at batch 4096, against 46.7 for the CUDA pipeline and 57.3 for OpenMP.

The crossover: the hybrid overtakes OpenMP at batch 32; the plain CUDA pipeline catches OpenMP only around batch 128 to 256.

Why is CUDA slower for small batches? Each batch pays for launches, two copies and a synchronization, and one image leaves most GPU threads idle. Why does the hybrid win for larger batches? The GPU gets enough work, the preprocessing is parallel, and it overlaps with GPU work on another batch.

## Slide 15: Speedup and Throughput Across All Implementations

**Estimated speaking time:** 1.5 min

**Main purpose:** Show relative performance (speedup) and absolute performance (throughput) of all four implementations side by side.

**Recommended visual:** Two native charts: speedup over serial (×) and throughput (images per second, log axis), each with all four implementations.

**Text on the slide:** Speedup = serial time / implementation time; throughput = 10,000 / time (s). Batch 4096: speedup OpenMP 21.6×, CUDA 26.4×, hybrid 50.0×.

**What to say:**

Same four implementations, two different views. On the left is speedup, defined as the serial time divided by the implementation time, so serial is the line at one. On the right is throughput, ten thousand images divided by the pass time in seconds - how many images per second each implementation processes.

Read the left chart first. At batch 4096 OpenMP is 21.6 times faster than serial, the CUDA pipeline 26.4 times, and the hybrid 50.0 times. At batch 1 the picture is different: OpenMP gives 7.6 times, the hybrid 1.9 times, and the CUDA pipeline 0.8 - below one, which means slower than serial.

The right chart says the same thing in images per second. Serial processes about 8,094 images per second. At batch 4096 OpenMP reaches 174,451, the CUDA pipeline 214,024, and the hybrid 404,844 images per second. Notice that serial and OpenMP throughput barely change with batch size, while the GPU-based implementations improve a lot, because larger batches amortize the fixed launch and copy costs.

So: the hybrid delivers the highest throughput from batch 32 on, OpenMP is best for the smallest batches, and the CUDA pipeline with single-threaded preprocessing is never the best.

## Slide 16: CUDA Overhead and Hybrid Performance

**Estimated speaking time:** 1.25 min

**Main purpose:** Explain why CUDA kernels are fast but the CUDA pipeline is slower, and quantify what OpenMP preprocessing and CPU–GPU overlap each contribute.

**Recommended visual:** Left: line chart of kernel-only, CUDA end-to-end, hybrid-sequential and hybrid-pipelined; right: stacked percentage chart of CUDA pipeline stages.

**Text on the slide:** Batch 4096: kernels 23.0 ms, CUDA end-to-end 46.7 ms, hybrid-sequential 28.8 ms, hybrid-pipelined 24.7 ms; shares: kernels 49.3 %, preprocessing 43.3 %, copies 7.3 %.

**What to say:**

This slide explains the gap between a fast kernel and a slower pipeline, and what the hybrid recovers. On the left are four things: CUDA kernels only, which exclude preprocessing and copies; CUDA end-to-end, the full pipeline; hybrid-sequential, the control with OpenMP preprocessing but no overlap; and the pipelined hybrid.

At batch 4096 the kernels take 23.0 milliseconds, but the complete CUDA pipeline takes 46.7. The stacked bar shows why: kernels are 49.3 percent, single-threaded CPU preprocessing 43.3 percent - 20.2 milliseconds at every batch size - and copies only 7.3 percent. At batch 1 copies are 19.8 percent and launch and synchronization 6.4 percent; that gray part is a residual, not directly timed.

OpenMP preprocessing alone takes the pass from 46.7 to 28.8 milliseconds, 1.62 times faster. The asynchronous overlap brings it to 24.7 - another 1.16 times, and only 1.07 times the kernel-only time.

It depends on batch size: at batch 1 the hybrid needs 650.9 milliseconds against 162.8 for OpenMP, so it is not best there; it overtakes OpenMP from batch 32.

## Slide 17: Amdahl’s Law and Performance Bottlenecks

**Estimated speaking time:** 1.25 min

**Main purpose:** Connect Amdahl's law to the measured results and explain which serial costs limit the speedup.

**Recommended visual:** Formula, native chart of measured speedup vs fitted Amdahl curves (batch 1 and 4096), and four connecting statements.

**Text on the slide:** S(N) = 1/((1−P)+P/N); Xeon f = 0.006 (batch 4096), 0.088 (batch 1).

**What to say:**

Amdahl's law: S of N equals one over one minus P plus P over N. P is the parallel portion and one minus P the serial portion; however many threads you add, speedup cannot exceed one over the serial fraction. Serial preprocessing, transfers, synchronization and kernel launches sit in that serial part.

I fitted it to my OpenMP data. For batch 4096 on the Xeon the serial fraction is only 0.006, a ceiling of 179.3 times, so the 21.6 times measured at 24 threads is not limited by it. For one image per batch it is 0.088, a ceiling of 11.4 times, and the measured curve flattens at 7.6 times: small batches carry more overhead relative to useful work. On the Apple M4, a separate platform, speedup flattens beyond its four performance cores, at 5.6 times with ten threads.

The same logic explains the GPU: kernels are 52.8 times faster than serial, but transfers and single-threaded preprocessing act like a serial part, so the pipeline reaches 26.4 times. The hybrid overlaps independent stages of different batches and reaches 50.0 times.

## Slide 18: Conclusions, Limitations, and Future Work

**Estimated speaking time:** 1.75 min

**Main purpose:** Summarise the verified conclusions, state the limitations honestly, list future work and end with the main message.

**Recommended visual:** Three-column text (conclusions, limitations, future work) and a closing statement.

**Text on the slide:** Five conclusions; six limitations; seven future-work items; closing statement.

**What to say:**

The conclusions, all backed by measurements. One: OpenMP improves CPU execution - 21.6 times with 24 threads on the Xeon at large batches - but reaches scaling limits at tiny batches and on the M4's efficiency cores. Two: CUDA kernels give strong computational speedup, 52.8 times over serial compute-only at batch 4096. Three: CUDA end-to-end performance is limited by preprocessing and transfers - the complete pipeline reaches 26.4 times. Four: hybrid execution can cut end-to-end time - 24.7 milliseconds against 46.7 for the CUDA pipeline at batch 4096. Five: the best implementation depends on batch size - OpenMP for batches of 1 and 8, the hybrid from batch 32.

Limitations: an older Tesla K40m, a small fully connected network, straightforward rather than fully tuned kernels, a shared environment, results that may differ on modern GPUs, and different CPU architectures on the Mac and Spartan. CUDA also used a fixed block size while OpenMP and the hybrid used their best thread count.

Future work: shared-memory tiling, GPU-side preprocessing, cuBLAS, a newer GPU, larger and convolutional networks, and energy measurements.

The main message: there is no universally fastest implementation. The best choice depends on workload size, parallel work, preprocessing cost, memory-transfer overhead, and the ability to overlap CPU and GPU stages. Thank you - I am happy to take questions.
