# Deck number verification

Deck: `CS259_Hybrid_CPU_GPU_Induru.pptx`; recomputed from `results/raw/*.csv` with independent code (`scripts/verify_deck_numbers.py`).

**101 of 101 claims verified on their slides.**

| Slide(s) | Claim | Expected text | Recomputed value | Status |
|---|---|---|---|---|
| 2, 17, 18 | GPU kernels vs serial, compute-only, batch 4096 | `52.8` | 52.77 | OK |
| 2, 15, 17, 18 | CUDA pipeline end-to-end speedup, batch 4096 | `26.4` | 26.44 | OK |
| 9, 15, 17, 18 | OpenMP speedup with 24 threads, batch 4096 | `21.6` | 21.55 | OK |
| 9 | OpenMP efficiency with 24 threads, batch 4096 | `0.90` | 0.898 | OK |
| 9, 17 | OpenMP best speedup, batch 1 | `7.6` | 7.586 | OK |
| 17 | Apple M4 speedup, 10 threads, batch 4096 | `5.6` | 5.564 | OK |
| 15 | OpenMP speedup, batch 1 | `7.6` | 7.586 | OK |
| 15 | hybrid speedup, batch 4096 | `50.0` | 50.02 | OK |
| 8 | smallest serial time over the 8 batch sizes (ms) | `1234.6` | 1235 | OK |
| 8 | largest serial time over the 8 batch sizes (ms) | `1235.7` | 1236 | OK |
| 8, 15 | serial throughput at batch 4096 (images/s) | `8,094` | 8094 | OK |
| 15 | OpenMP throughput at batch 4096 (images/s) | `174,451` | 1.745e+05 | OK |
| 15 | CUDA pipeline throughput at batch 4096 (images/s) | `214,024` | 2.14e+05 | OK |
| 15 | hybrid throughput at batch 4096 (images/s) | `404,844` | 4.048e+05 | OK |
| 14 | serial time, batch 1 (ms, chart value) | `1235` | 1235 | OK |
| 14 | OpenMP best time, batch 1 (ms, chart value) | `162.8` | 162.8 | OK |
| 14 | CUDA pipeline time, batch 1 (ms, chart value) | `1507` | 1507 | OK |
| 14 | hybrid best time, batch 1 (ms, chart value) | `650.9` | 650.9 | OK |
| 14 | serial time, batch 8 (ms, chart value) | `1236` | 1236 | OK |
| 14 | OpenMP best time, batch 8 (ms, chart value) | `75.48` | 75.48 | OK |
| 14 | CUDA pipeline time, batch 8 (ms, chart value) | `218.8` | 218.8 | OK |
| 14 | hybrid best time, batch 8 (ms, chart value) | `87.46` | 87.46 | OK |
| 14 | serial time, batch 32 (ms, chart value) | `1235` | 1235 | OK |
| 14 | OpenMP best time, batch 32 (ms, chart value) | `61.9` | 61.9 | OK |
| 14 | CUDA pipeline time, batch 32 (ms, chart value) | `85.49` | 85.49 | OK |
| 14 | hybrid best time, batch 32 (ms, chart value) | `33.3` | 33.3 | OK |
| 14 | serial time, batch 128 (ms, chart value) | `1235` | 1235 | OK |
| 14 | OpenMP best time, batch 128 (ms, chart value) | `58.25` | 58.25 | OK |
| 14 | CUDA pipeline time, batch 128 (ms, chart value) | `58.62` | 58.62 | OK |
| 14 | hybrid best time, batch 128 (ms, chart value) | `26.5` | 26.5 | OK |
| 14 | serial time, batch 256 (ms, chart value) | `1235` | 1235 | OK |
| 14 | OpenMP best time, batch 256 (ms, chart value) | `58.85` | 58.85 | OK |
| 14 | CUDA pipeline time, batch 256 (ms, chart value) | `55.15` | 55.15 | OK |
| 14 | hybrid best time, batch 256 (ms, chart value) | `25.98` | 25.98 | OK |
| 14 | serial time, batch 4096 (ms, chart value) | `1235` | 1235 | OK |
| 14 | OpenMP best time, batch 4096 (ms, chart value) | `57.32` | 57.32 | OK |
| 14 | CUDA pipeline time, batch 4096 (ms, chart value) | `46.72` | 46.72 | OK |
| 14 | hybrid best time, batch 4096 (ms, chart value) | `24.7` | 24.7 | OK |
| 16 | copy share (H2D + D2H), batch 1 | `19.8` | 19.82 | OK |
| 16 | launch/API/sync residual share, batch 1 | `6.4` | 6.427 | OK |
| 16 | kernel share of CUDA pipeline, batch 4096 | `49.3` | 49.29 | OK |
| 16 | preprocessing share, batch 4096 | `43.3` | 43.32 | OK |
| 16 | copy share (H2D + D2H), batch 4096 | `7.3` | 7.321 | OK |
| 16 | preprocessing time per pass, batch 4096 (ms) | `20.2` | 20.24 | OK |
| 16 | kernel-only time, batch 4096 (ms) | `23.0` | 23.03 | OK |
| 16 | CUDA end-to-end, batch 4096 (ms) | `46.7` | 46.72 | OK |
| 16 | hybrid-sequential (control) time, batch 4096 (ms) | `28.8` | 28.76 | OK |
| 16, 18 | hybrid-pipelined time, batch 4096 (ms) | `24.7` | 24.7 | OK |
| 16 | parallel preprocessing effect (hybrid-seq vs CUDA), batch 4096 | `1.62` | 1.625 | OK |
| 16 | overlap effect (pipelined vs hybrid-seq), batch 4096 | `1.16` | 1.164 | OK |
| 16 | hybrid time / kernel-only time, batch 4096 | `1.07` | 1.073 | OK |
| 14, 16, 18 | first batch size where hybrid beats the best CPU configuration | `32` | 32 | OK |
| 17 | Amdahl serial fraction, batch 4096 | `0.006` | 0.005578 | OK |
| 17 | Amdahl serial fraction, batch 1 | `0.088` | 0.08767 | OK |
| 17 | Amdahl ceiling 1/f, batch 1 | `11.4` | 11.41 | OK |
| 17 | Amdahl ceiling 1/f, batch 4096 | `179.3` | 179.3 | OK |
| 13 | OpenMP: passing comparisons | `16 / 16` | 16 | OK |
| 13 | CUDA: passing comparisons | `12 / 12` | 12 | OK |
| 13 | hybrid-sequential: passing comparisons | `16 / 16` | 16 | OK |
| 13 | hybrid-pipelined: passing comparisons | `32 / 32` | 32 | OK |
| 13 | CUDA max logit difference | `7.6×10` | 7.629e-06 | OK |
| 6, 13 | model accuracy (%) | `97.97` | 97.97 | OK |
| 12 | total one-time GPU set-up (ms) | `110.7` | 110.7 | OK |
| QA | CUDA kernels, batch 64, block 8x8 (ms) | `37.3` | 37.32 | OK |
| QA | CUDA kernels, batch 64, block 16x16 (ms) | `34.4` | 34.43 | OK |
| QA | CUDA kernels, batch 64, block 32x32 (ms) | `48.7` | 48.65 | OK |
| QA | block sizes within x % at batch 4096 | `0.6 %` | 0.6151 | OK |
| QA | best block would improve CUDA end-to-end by at most (%) | `2.8 %` | 2.83 | OK |
| QA | best OpenMP compute-only (stages 1-3), batch 4096 (ms) | `56.1` | 56.13 | OK |
| QA | compute-only ratio best OpenMP / GPU kernels, batch 4096 | `2.44` | 2.437 | OK |
| QA | mixed ratio OpenMP end-to-end / GPU kernels (not used) | `2.49` | 2.489 | OK |
| QA | best OpenMP end-to-end, batch 4096 (ms) | `57.3` | 57.32 | OK |
| QA | plain -O3 serial time, batch 4096 (ms) | `1,295.6` | 1296 | OK |
| QA | native-flag serial time, batch 4096 (ms) | `1,235.4` | 1235 | OK |
| QA | plain -O3 serial slower by (%) | `4.9 %` | 4.868 | OK |
| QA | largest CUDA logit difference, plain -O3 build | `1.1×10` | 1.144 | OK |
| QA | CUDA context creation (ms) | `106.8` | 106.8 | OK |
| QA | weight upload (ms) | `0.40` | 0.3977 | OK |
| QA | buffer allocation (ms) | `2.97` | 2.972 | OK |
| QA | one-time set-up total (ms) | `110.7` | 110.7 | OK |
| QA | set-up total / steady CUDA pass at batch 256 | `2.01` | 2.007 | OK |
| QA | first 24-thread OpenMP pass slower than second (%) | `27.9 %` | 27.87 | OK |
| QA | median coefficient of variation (%) | `0.2 %` | 0.1941 | OK |
| QA | slowest-variation config (hybrid, batch 256, 4 threads): mean (ms) | `28.25` | 28.25 | OK |
| QA | slowest-variation config (hybrid, batch 256, 4 threads): median (ms) | `26.89` | 26.89 | OK |
| QA | slowest-variation config (hybrid, batch 256, 4 threads): standard deviation (ms) | `6.10` | 6.103 | OK |
| QA | slowest-variation config (hybrid, batch 256, 4 threads): minimum (ms) | `26.78` | 26.78 | OK |
| QA | slowest-variation config (hybrid, batch 256, 4 threads): maximum (ms) | `54.18` | 54.18 | OK |
| QA | passes above 1.5x the median in that config | `One of the 20 passes` | 1 | OK |
| QA | serial GFLOP/s at batch 4096 (end-to-end) | `3.3` | 3.291 | OK |
| QA | OpenMP best GFLOP/s at batch 4096 (end-to-end) | `70.9` | 70.92 | OK |
| QA | CUDA kernels-only GFLOP/s at batch 4096 | `176.5` | 176.5 | OK |
| QA | kernel time per batch at batch size 1 (us) | `109.1 µs` | 109.1 | OK |
| QA | launch/API/sync residual per batch at batch size 1 (us) | `9.7 µs` | 9.684 | OK |
| QA | CUDA pipeline end-to-end speedup at batch 1 | `0.82` | 0.8194 | OK |
| QA | best OpenMP compute-only / GPU kernels at batch 32 | `1.27` | 1.268 | OK |
| QA | hybrid-pipelined over CUDA pipeline at batch 4096 | `1.89` | 1.892 | OK |
| QA | hybrid-pipelined time at batch 32 (ms) | `33.3` | 33.3 | OK |
| QA | M4 speedup with 4 threads, batch 4096 | `3.85` | 3.853 | OK |
| QA | M4 speedup with 10 threads, batch 4096 | `5.56` | 5.564 | OK |
| QA | M4 speedup with 10 threads, batch 1 | `0.13` | 0.1289 | OK |

## 2.44x versus 2.49x

- Like-for-like compute-only ratio (best OpenMP stages 1-3 / GPU kernels): 2.437x -> 2.44x (appears in the Q&A document, not on the 18 slides).
- Mixed ratio (best OpenMP END-TO-END / GPU kernels): 2.489x -> 2.49x; it mixes a compute-only time with an end-to-end time and is NOT used as a result.
- The string `2.49` appears on slide(s): [] (slides only; the Q&A document mentions it solely to explain why it is not used).

## Apple M4 separation

- M4/Mac/Apple mentioned on the CPU-vs-GPU result slides 14-16: none.

## Over-claim scan

- Phrases such as 'always fastest': none found outside negated statements.
