# Research questions

| RQ | Question | Experiment | Metric | Figure / table | Discussed in |
|---|---|---|---|---|---|
| RQ1 | How much speedup does OpenMP provide over serial? | thread sweep 1-10 (M4), 1-n (GPU host) | speedup, efficiency | OpenMP time/speedup/efficiency figures, scaling table | Results, Discussion |
| RQ2 | How does CUDA compare with serial and OpenMP? | all batch sizes, same machine | end-to-end time, kernel-only vs end-to-end speedup | CPU-vs-GPU table, kernel-vs-e2e figure | Results |
| RQ3 | How does batch size affect CPU and GPU performance? | batch 1-4096 | time, throughput | exec-time and throughput figures | Results, Discussion |
| RQ4 | How much of GPU time is memory transfer? | CUDA stage breakdown (CUDA events) | transfer % of end-to-end | breakdown figure/table | Results |
| RQ5 | Does hybrid improve end-to-end performance? | OpenMP vs CUDA (single-threaded preprocessing) vs hybrid-sequential (control) vs hybrid-pipelined | e2e time, speedup vs CUDA, Welch t-test | hybrid figure/table | Results, Discussion |
| RQ6 | How do results relate to Amdahl's law, overhead, bandwidth, transfers? | Amdahl fit, Karp-Flatt, micro-benchmarks | serial fraction, fork-join cost, bandwidths | Amdahl figure/table, micro table | Discussion |
