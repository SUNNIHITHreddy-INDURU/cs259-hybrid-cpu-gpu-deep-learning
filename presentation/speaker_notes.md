# Speaker notes — 18 main slides (about 23.25 minutes) + backup slides

## Slide 1: Title

**Estimated speaking time:** 0.5 min

**On the slide:** Title; Sunnihith Reddy Induru; CS 259 — Advanced Parallel Processing; San José State University; Presentation date: to be added

**What to say:**

Good morning, everyone. My project is called "Performance Evaluation of Hybrid CPU-GPU Parallelism for Deep Learning Using OpenMP and CUDA."

In one sentence: I took one small neural-network inference workload and ran it four ways - serial on one CPU thread, in parallel on many CPU threads with OpenMP, on the GPU with CUDA, and as a hybrid that uses OpenMP and CUDA together - and I measured when each one is the right choice.

Everything I will show was measured by me on the same machine, and every number in the slides can be traced back to the raw measurement files in my repository.

## Slide 2: Why Parallelism Matters for Deep Learning

**Estimated speaking time:** 1 min

**On the slide:** Workload → repeated matrix operations → many arithmetic operations → need for CPU and GPU parallelism; GPU kernels fast, application slower (preprocessing, transfers, launch overhead).

**What to say:**

Neural-network inference looks complicated, but underneath it is a large number of repeated arithmetic operations - mostly matrix operations that multiply inputs by weights. My network performs about two hundred thousand multiply-adds for every single image, and a pass over the MNIST test set does that ten thousand times.

Run one after another on a single CPU thread, that work becomes slow. There are two standard ways to speed it up. OpenMP splits the work across several CPU threads that share memory. CUDA launches thousands of lightweight threads on a GPU.

But there is a trap, and it is the theme of this talk: a GPU can compute very quickly while the complete application is much slower, because the application also has to preprocess the data, copy it across to the GPU, launch the kernels and synchronize. On my measurements the GPU kernels alone are 52.8 times faster than serial code, but the complete CUDA pipeline is only 26.4 times faster. The rest of the talk explains why, and what a hybrid design can do about it.

## Slide 3: Performance Tradeoffs Across CPU, GPU, and Hybrid Execution

**Estimated speaking time:** 1 min

**On the slide:** Main question + RQ1–RQ6.

**What to say:**

This is the question the whole project asks: how do serial CPU, OpenMP CPU, CUDA GPU and hybrid OpenMP-CUDA implementations compare when they execute the same neural-network inference workload?

To answer it properly I broke it into six research questions. One: how much speedup does OpenMP give over serial execution? Two: how does CUDA compare with serial and OpenMP? Three: how does batch size change CPU and GPU performance? Four: how much of the GPU's time is data transfer? Five: does hybrid CPU-GPU execution improve end-to-end performance? And six: how do the results relate to Amdahl's law and parallel overhead?

I will come back to each of these - the results slides are organised around them.

## Slide 4: Serial, OpenMP, CUDA, and Hybrid Execution Models

**Estimated speaking time:** 1.5 min

**On the slide:** Table: model / main resource / memory model / main parallelism + mini diagrams.

**What to say:**

Before the results, I want everyone to understand how these four models differ, because the results only make sense with that picture in mind.

Serial execution uses one CPU thread and processes the work strictly one piece after another. OpenMP uses several CPU threads, but they all share the same CPU memory; the work is divided among the threads, and there is a synchronization point at the end of each parallel loop. CUDA runs on the GPU, which has its own separate device memory, so data must be copied there first; the GPU then runs thousands of threads on independent pieces of data. The hybrid model gives different stages to different processors - the CPU threads prepare data while the GPU computes - and the memory is split between host and device.

The small diagrams in the last column show the idea: one thread, a fork into several threads and a join, a grid of GPU threads, and CPU plus GPU working together.

## Slide 5: MNIST Inference Workload

**Estimated speaking time:** 1 min

**On the slide:** 10,000 test images; batches 1–4096; float32; same weights; accuracy 97.97 %.

**What to say:**

The workload is MNIST handwritten-digit classification, and I measure inference, not training. Each image is 28 by 28 pixels - 784 numbers - and the network turns those 784 features into a predicted digit from zero to nine. The image on the slide is the first real image of the MNIST test set; the weights I use predict a seven for it, which is also its true label.

Every pass processes all ten thousand MNIST test images, in batches of 1, 8, 32, 64, 128, 256, 1,024 or 4,096 images. The computation is float32, and every implementation loads exactly the same trained weight file. The network classifies 97.97 percent of the test images correctly - that number comes from my training log and from the correctness runs.

I chose MNIST because it is a realistic but manageable deep-learning workload: small enough that I could implement it directly in C++ and CUDA, so I control every thread and every copy, without a deep-learning framework hiding them.

## Slide 6: Neural-Network Computation

**Estimated speaking time:** 1 min

**On the slide:** 784 → FC 784→256 → ReLU → FC 256→10 → argmax; four stages; independent output elements.

**What to say:**

This is the entire network. 784 input features go through a fully connected layer from 784 to 256 units, a ReLU activation, a second fully connected layer from 256 to 10 outputs, and an argmax that picks the predicted digit. That is two hundred and three thousand multiply-adds per image.

In the program the work is split into four measured stages: preprocessing, which standardizes each image; the hidden layer; the output layer; and the argmax.

The key point for parallelism is at the bottom: each output element - for example hidden unit j of image b - is a dot product that does not depend on any other output element in the same layer. So all of them can be computed at the same time. That independence is exactly what OpenMP threads and CUDA threads exploit. What is not independent is the order of the layers: the output layer needs the hidden layer first.

## Slide 7: Four Implementations of the Same Computation

**Estimated speaking time:** 1.5 min

**On the slide:** Serial | OpenMP | CUDA (1-thread preprocessing) | Hybrid; hybrid-sequential = diagnostic control.

**What to say:**

Here are the four implementations side by side, colour-coded by the resource that executes each stage.

Serial, in gray: one CPU thread does the preprocessing, the hidden layer and the output layer with argmax. OpenMP, in blue: the same stages, but each one is split across T CPU threads. CUDA: the preprocessing still runs on a single CPU thread - which is why I call it "CUDA with single-threaded preprocessing", not "GPU-only" - then the batch is copied to the GPU, three kernels run, and the results are copied back. Hybrid: OpenMP threads do the preprocessing into pinned memory, the copies are asynchronous, the kernels run on three CUDA streams, so different batches overlap.

One more thing, at the bottom of the slide: hybrid-sequential is a diagnostic control, not a fifth implementation. It uses OpenMP preprocessing and CUDA computation, but without overlapping batches. I use it later to separate two effects: the benefit of parallel preprocessing and the benefit of overlap.

## Slide 8: CUDA Host–Device Execution

**Estimated speaking time:** 1.5 min

**On the slide:** Host memory → H2D copy → device memory → kernel launch → grid → blocks → threads → D2H copy → predictions; 8×8, 16×16, 32×32.

**What to say:**

This slide shows how a CUDA program works. On the left is the data path. The CPU is the host and the GPU is the device, and they have separate memories. The input batch starts in CPU memory, is copied across the PCIe connection into GPU global memory, and then the host launches a kernel. When the kernel finishes, the predictions are copied back.

On the right is how the GPU organizes its threads. A kernel launch creates a grid. The grid is made of thread blocks, and each block is made of threads. In my hidden-layer kernel a block is a square of d by d threads, and thread tx, ty of block bx, by computes exactly one output element: hidden unit j equals bx times d plus tx, for image b equals by times d plus ty. I tested three block sizes: 8 by 8, which is 64 threads, 16 by 16, which is 256 threads and my default, and 32 by 32, which is 1,024 threads.

Two consequences matter for the results. First, every copy and every launch costs time that has nothing to do with computation. Second, for a batch of just one image the grid has very few useful threads, so the GPU is badly under-used.

## Slide 9: Hybrid CPU–GPU Pipeline

**Estimated speaking time:** 2 min

**On the slide:** OpenMP preprocesses batch i+1 while CUDA copies/computes batch i; three streams; layers within a batch stay ordered; overlap between batches.

**What to say:**

This is the central idea of the hybrid implementation. In the CUDA pipeline, the GPU sits idle while the CPU preprocesses, and the CPU waits while the GPU works. The hybrid removes that waiting.

The diagram is a schematic, not measured data. The top lane is the CPU: OpenMP threads preprocess batch 1, then batch 2, then batch 3. Below are three CUDA streams. As soon as batch 1 is preprocessed, its host-to-device copy, its kernels and its device-to-host copy go into stream 0. While the GPU works on batch 1, the CPU is already preprocessing batch 2, which is then handled by stream 1, and batch 3 goes to stream 2. Batches are assigned round-robin, and each stream has its own device buffers and its own pinned host buffers. Pinned memory is what allows copies to be asynchronous.

The important statement is on the slide: within one batch, the hidden layer, the output layer and the argmax depend on each other, so they stay in order. The overlap happens only between different batches.

Finally, the hybrid-sequential control: it uses OpenMP preprocessing but waits for each batch to finish before starting the next. Comparing the CUDA pipeline, the control and the full hybrid lets me say how much of the gain comes from parallel preprocessing, and how much comes from overlap.

## Slide 10: Experimental Setup and Measurement Protocol

**Estimated speaking time:** 1.25 min

**On the slide:** Setup table; Spartan node for CPU-vs-GPU; M4 separate.

**What to say:**

Here is exactly how I measured. The dataset is the ten thousand MNIST test images in float32. Each configuration gets three warm-up passes that are not recorded, followed by twenty recorded passes - and every recorded pass is kept as a row in a raw CSV file; nothing is removed.

GPU stages are timed with CUDA events; the end-to-end time is the wall-clock time of the whole pass. One-time costs - creating the CUDA context, allocating buffers, uploading the weights - are excluded from the steady-state timing, and I measured them separately: about 110.7 milliseconds in total.

The main platform is a Spartan GPU node with a Tesla K40m and two Xeon E5-2680 v4 CPUs. The node has 28 physical cores and 28 logical CPUs according to lscpu, and my jobs were allocated 24, so OpenMP uses at most 24 threads.

Two rules matter. All CPU-versus-GPU comparisons use the Spartan node only. The Apple M4 laptop is used only as a separate CPU scalability platform, and its numbers are never mixed with the Spartan GPU comparisons.

## Slide 11: Correctness Across Implementations

**Estimated speaking time:** 0.75 min

**On the slide:** Correctness table: comparisons passed, max logit difference, prediction agreement, accuracy.

**What to say:**

Before I trust any timing, I checked that every implementation computes the same thing. Every implementation is compared with the serial reference on all ten thousand images, over several batch sizes, thread counts, block sizes and stream counts - eighty comparisons in the reference build, and all of them pass.

OpenMP is bit-identical to serial. CUDA and both hybrid variants differ by at most 7.6×10⁻⁶ in the logits - which is tiny - and they predict exactly the same digit as serial for every image. Accuracy is 97.97 percent everywhere.

The small differences are expected: the operations and the source-level order of the sums are the same, but compilers can apply floating-point optimizations such as fused multiply-add. The correctness checks run outside the timed region, and I would not accept a performance result from an implementation that failed them.

## Slide 12: OpenMP Scalability

**Estimated speaking time:** 1.5 min

**On the slide:** Spartan: time, speedup, efficiency vs threads; 21.6× at 24 threads (batch 4096); batch 1 saturates; M4 in backup.

**What to say:**

RQ1: how much speedup does OpenMP give? These three charts are all from the Spartan node, for three batch sizes - 1, 256 and 4096 images - against the number of OpenMP threads.

Left: execution time per pass on a log scale. For batches of 256 and 4096 it falls from about twelve hundred milliseconds with one thread to about 57.3 milliseconds with 24 threads. Middle: the speedup over serial. For large batches it follows the ideal line closely - 21.6 times with 24 threads at batch 4096. Right: parallel efficiency, 0.90 at 24 threads for batch 4096.

Batch size 1 behaves differently: the speedup saturates at about 7.6 times and efficiency drops to 0.31, because one image offers only 16 work items per stage and every stage ends in a barrier - there is too little work per synchronization.

The Apple M4 is a different story and is shown separately in the backup: its speedup follows the ideal up to its 4 performance cores - 3.85 times with 4 threads - then flattens at 5.6 times with 10 threads. The two machines are different architectures, so they must be read separately. I did not isolate memory bandwidth as a cause of any flattening; what I can say is what the data shows.

## Slide 13: CUDA Computation and End-to-End Performance

**Estimated speaking time:** 1.75 min

**On the slide:** End-to-end: serial, OpenMP, CUDA pipeline. Compute-only: serial, OpenMP, CUDA kernels. Kernels 52.8× vs pipeline 26.4× (batch 4096); batch 1 CUDA 0.82×.

**What to say:**

RQ2 and RQ3: how does CUDA compare, and how does batch size matter? I split this slide into two charts on purpose, because they answer different questions.

The left chart is end-to-end: the time of the whole pass, including preprocessing, copies, launches and synchronization. It shows serial, the best OpenMP configuration, and the CUDA pipeline with single-threaded preprocessing. The right chart is compute-only: only the hidden layer, the output layer and the argmax - for the CPU it is the sum of those timed stages, for the GPU it is the kernel time measured with CUDA events.

Compute-only, the GPU kernels are 52.8 times faster than serial and 2.44 times faster than the best OpenMP configuration at batch 4096. End-to-end, the CUDA pipeline is 26.4 times faster than serial and only 1.23 times faster than OpenMP - because preprocessing and copies are included. Notice the batch-1 end: CUDA end-to-end is 0.82 times serial, which means it is slower; even compute-only the kernels are just 1.11 times faster. The GPU needs enough work to amortize its overheads.

A caution on one number: comparing the kernel time with OpenMP's end-to-end time would give about 2.49; the like-for-like compute-only comparison is 2.44.

## Slide 14: Where the CUDA Pipeline Time Goes

**Estimated speaking time:** 1.25 min

**On the slide:** Batch 1: kernels 72.4 %, copies 19.8 %; batch 4096: kernels 49.3 %, preprocessing 43.3 %, copies 7.3 %.

**What to say:**

RQ4: how much GPU time is spent on data transfer? This stacked chart splits the end-to-end time of the CUDA pipeline into stages, as a percentage, for each batch size.

Look at the two ends. At batch 1 the kernels are 72.4 percent of the time, the copies are 19.8 percent, and launch, API and synchronization overhead is 6.4 percent. At batch 4096 the picture flips: kernels are 49.3 percent, the single-threaded CPU preprocessing is 43.3 percent - 20.2 milliseconds that stay constant for every batch size - and the copies are only 7.3 percent.

So transfers matter most for small batches, but for large batches the dominant non-GPU cost is not the PCIe copy, it is the single-threaded preprocessing on the CPU. That is the lesson: a fast kernel does not automatically make a fast application. The gray "other" segment is the part of the wall-clock time not covered by the four timed stages - launch, API calls and synchronization - so it is a residual, not a directly timed quantity.

## Slide 15: Hybrid Execution Reduces End-to-End Time

**Estimated speaking time:** 1.75 min

**On the slide:** Hybrid 24.7 ms vs CUDA pipeline 46.7 ms (batch 4096); effects: 1.62× preprocessing, 1.16× overlap; hybrid faster than OpenMP from batch 32.

**What to say:**

RQ5: does hybrid execution improve end-to-end performance? This chart compares three configurations at every batch size: the CUDA pipeline, the hybrid-sequential control, and the pipelined hybrid. Each hybrid point uses the best OpenMP thread count for that batch size.

The pipelined hybrid is faster than the CUDA pipeline at all eight batch sizes - by 1.89 to 2.57 times; the 95 percent confidence intervals are tiny and a Welch test gives p below ten to the minus thirty-two for every batch size. At batch 4096 it needs 24.7 milliseconds against 46.7.

Two effects, separated by the control. First, parallel preprocessing alone - the hybrid-sequential control - gives 1.62 times over the CUDA pipeline at batch 4096. Second, overlapping the batches adds another 1.16 times. The hybrid time is only 1.07 times the kernel-only time, so preprocessing and copies are nearly hidden behind the kernels.

But I do not claim hybrid is always best. Against the best OpenMP configuration, the hybrid is faster only from batch 32 upward; at batch sizes 1 and 8, plain OpenMP is faster, because there the GPU path is dominated by overhead.

## Slide 16: The Best Implementation Depends on Batch Size

**Estimated speaking time:** 1.25 min

**On the slide:** Fastest / runner-up per batch size (end-to-end, Spartan).

**What to say:**

This table brings the results together. For every batch size it lists the fastest end-to-end implementation, its time, the runner-up and its time - all measured on the Spartan node.

For a batch of one image and a batch of eight, plain OpenMP on the multicore CPU is the fastest: the GPU path is dominated by launch, copy and synchronization overhead. From batch 32 upward the pipelined hybrid is fastest, by about a factor of two over the runner-up, because the GPU now gets enough work and the CPU preprocessing overlaps with GPU execution.

Notice what never wins: the CUDA pipeline with single-threaded preprocessing is never the fastest end-to-end, even though its kernels are the fastest compute-only from batch 32 on. That is the whole message of the project: the choice depends on workload size and overhead, not on assuming that one platform is always fastest.

One honest caveat that is also in the paper: CUDA uses a fixed 16 by 16 block, while OpenMP and the hybrid use their best thread count - so this is not a best-versus-best comparison. The best CUDA block would change the CUDA time by at most 2.8 percent.

## Slide 17: Why Speedup Eventually Stops Increasing

**Estimated speaking time:** 1.25 min

**On the slide:** S(N) = 1/((1−P)+P/N); Xeon f = 0.006 (batch 4096), 0.088 (batch 1); limitations list.

**What to say:**

RQ6: how do the results relate to Amdahl's law? The law says that if P is the parallel portion of the work, the speedup on N processors is one divided by one minus P plus P over N. The serial portion, one minus P, limits the speedup no matter how many threads you add.

I fitted this to my OpenMP measurements. For batch 4096 on the Xeon the fitted serial fraction is only 0.006, which would allow a ceiling of 179.3 times - so the 21.6 times I measured with 24 threads is not limited by the serial fraction. For a batch of one image the fitted serial fraction is 0.088, a ceiling of only 11.4 times. So the batch size changes the effective serial fraction.

The same logic explains the CUDA pipeline: its single-threaded preprocessing, copies and launches behave like a serial part, which is why the end-to-end speedup is smaller than the kernel speedup, and why the hybrid, which parallelizes and overlaps that part, helps.

And the limitations, which I want to state clearly: the GPU is an old Tesla K40m; the network is small and fully connected; my kernels are not tuned; the cluster is shared; the comparison uses a fixed CUDA block against tuned OpenMP thread counts; and results may differ on modern GPUs.

## Slide 18: Conclusions and Future Work

**Estimated speaking time:** 1.5 min

**On the slide:** Four conclusions; future work; final statement.

**What to say:**

Let me finish with four conclusions, all of them backed by measurements. One: OpenMP gives strong CPU speedup - 21.6 times with 24 threads on the Xeon for large batches - until scaling limits appear: batch size 1, and on the Apple M4 the efficiency cores. Two: CUDA kernels can be very fast - 52.8 times faster than serial compute-only - but the end-to-end pipeline is only 26.4 times, because it includes preprocessing and transfers. Three: hybrid execution reduces end-to-end time when CPU preprocessing overlaps with GPU computation - 24.7 milliseconds against 46.7 for the CUDA pipeline at batch 4096. Four: the best execution model depends on batch size: OpenMP for batches of 1 and 8, the hybrid from batch 32 up.

Future work: shared-memory-tiled CUDA kernels, a comparison with cuBLAS, GPU-side preprocessing, a newer GPU, larger networks, convolutional networks, and energy measurements.

The main result is that CPU, GPU and hybrid parallelism should be selected according to workload size and overhead - not by assuming that one platform is always fastest. Thank you. I am happy to take questions; I have backup slides for the full timing table, block sizes, compiler flags, cold start, variation, hardware limits, correctness details and kernel code.

## Backup 19: Backup: Full end-to-end timing table (Spartan)

**Estimated speaking time:** 0 min

**On the slide:** Full timing table.

**What to say:**

Full table of end-to-end times per pass for every batch size. OpenMP and Hybrid show the best thread count in brackets. The GPU-kernels column is the compute-only kernel time. Speedups are over serial.

## Backup 20: Backup: Compute-only comparison (stages 1–3)

**Estimated speaking time:** 0 min

**On the slide:** Compute-only table.

**What to say:**

Compute-only means just the hidden layer, output layer and argmax. At batch 4096 the GPU kernels take 23.0 milliseconds against 56.1 for the best OpenMP configuration: 2.44 times. If one divides OpenMP's end-to-end time, which includes preprocessing, by the kernel time, one gets about 2.49 - but that mixes a compute-only number with an end-to-end number, so I do not use it.

## Backup 21: Backup: OpenMP on the Apple M4 (separate platform)

**Estimated speaking time:** 0 min

**On the slide:** M4 OpenMP charts.

**What to say:**

The Apple M4 has 10 cores: 4 performance and 6 efficiency. The speedup follows the ideal line up to 4 threads - 3.85 times at batch 4096 - then flattens at 5.56 times with 10 threads. With one image per batch OpenMP is slower than serial: 0.13 times with 10 threads. These results are never compared with the Spartan GPU results.

## Backup 22: Backup: CUDA block-size comparison

**Estimated speaking time:** 0 min

**On the slide:** Block-size chart.

**What to say:**

Block size only matters at small batches. At batch 64 the kernels take 37.3 ms with 8 by 8 blocks, 34.4 with 16 by 16 and 48.6 with 32 by 32. At batch 4096 all three are within one percent. If the best of the three block sizes were used, the CUDA end-to-end time would improve by at most 2.8 percent, so the main comparison, which uses a fixed 16 by 16 block, is not best-versus-best, and is labelled that way.

## Backup 23: Backup: Compiler settings and flag sensitivity

**Estimated speaking time:** 0 min

**On the slide:** Compiler table.

**What to say:**

Compiler settings of the three builds. On Spartan one binary is built with g++ 11.4.1 through nvcc 11.7; the reference build adds -march=native, the sensitivity build does not. The Mac uses Apple clang with no architecture flag. There is no fast-math, and the floating-point contraction options were not set, so each compiler's default applies. Plain -O3 changes the serial time by about five percent.

## Backup 24: Backup: Cold-start timing

**Estimated speaking time:** 0 min

**On the slide:** Cold-start table.

**What to say:**

One-time costs excluded from the steady-state times, measured in ten fresh processes: CUDA context creation 106.8 ms on average, weight upload 0.40 ms, buffer allocation 2.97 ms - 110.7 ms in total, about 2.01 times a steady-state CUDA pass. After the set-up the first CUDA pass shows no penalty; the first 24-thread OpenMP pass is 27.9 percent slower than the second.

## Backup 25: Backup: Run-to-run variation

**Estimated speaking time:** 0 min

**On the slide:** Variation table.

**What to say:**

Variation is small: the median coefficient of variation is 0.2 percent on Spartan. The largest is the hybrid-pipelined configuration at batch 256 with 4 threads: mean 28.25 ms, median 26.89, standard deviation 6.10, minimum 26.78, maximum 54.18. One pass is above 1.5 times the median. I did not remove it; it is in all statistics and in the raw data.

## Backup 26: Backup: Measured hardware limits (Spartan)

**Estimated speaking time:** 0 min

**On the slide:** Micro-benchmarks.

**What to say:**

Micro-benchmark results used in the analysis: PCIe bandwidth, device memory copy rate, kernel launch cost, CPU memory bandwidth and OpenMP fork-join cost. No hardware peak numbers are assumed; everything here was measured.

## Backup 27: Backup: Detailed correctness results (Spartan, reference build)

**Estimated speaking time:** 0 min

**On the slide:** Detailed correctness.

**What to say:**

Detailed correctness table for the reference build: number of passing comparisons, maximum and mean logit difference, minimum prediction agreement and accuracy for each comparison group. In the plain -O3 sensitivity build the largest CUDA difference is 1.1×10⁻⁵.

## Backup 28: Backup: Kernel and OpenMP code details

**Estimated speaking time:** 0 min

**On the slide:** Code excerpts.

**What to say:**

Two short excerpts from the source code. The hidden-layer kernel: each thread computes one output element, with the hidden unit index varying fastest so that consecutive threads read consecutive weight addresses. The OpenMP region: one parallel region covers the whole pass, each stage is a work-shared loop, and the implicit barrier after each loop is required because the next stage reads data written by other threads.
