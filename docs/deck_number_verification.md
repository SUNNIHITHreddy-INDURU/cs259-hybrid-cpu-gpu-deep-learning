# Deck number verification

Deck: `CS259_Hybrid_CPU_GPU_Induru.pptx`; recomputed from `results/raw/*.csv` with independent code (`scripts/verify_deck_numbers.py`).

**57 of 57 claims verified on their slides.**

| Slide(s) | Claim | Expected text | Recomputed value | Status |
|---|---|---|---|---|
| 2, 13, 18 | GPU kernels vs serial, compute-only, batch 4096 | `52.8` | 52.77 | OK |
| 2, 13, 18 | CUDA pipeline end-to-end speedup, batch 4096 | `26.4` | 26.44 | OK |
| 13 | GPU kernels vs best OpenMP compute-only, batch 4096 (like for like) | `2.44` | 2.437 | OK |
| 13 | CUDA pipeline vs best OpenMP end-to-end, batch 4096 | `1.23` | 1.227 | OK |
| 13 | CUDA end-to-end speedup, batch 1 (slower than serial) | `0.82` | 0.8194 | OK |
| 13 | GPU kernels vs serial compute-only, batch 1 | `1.11` | 1.112 | OK |
| 12, 17, 18 | OpenMP speedup with 24 threads, batch 4096 | `21.6` | 21.55 | OK |
| 12 | OpenMP efficiency with 24 threads, batch 4096 | `0.90` | 0.898 | OK |
| 12 | OpenMP best speedup, batch 1 | `7.6` | 7.586 | OK |
| 12 | OpenMP efficiency with 24 threads, batch 1 | `0.31` | 0.3065 | OK |
| 12 | Apple M4 speedup, 10 threads, batch 4096 | `5.6` | 5.564 | OK |
| 21 | Apple M4 speedup, 10 threads, batch 4096 (backup notes) | `5.56` | 5.564 | OK |
| 12, 21 | Apple M4 speedup, 4 threads, batch 4096 | `3.85` | 3.853 | OK |
| 21 | Apple M4 speedup, 10 threads, batch 1 (slower than serial) | `0.13` | 0.1289 | OK |
| 14 | kernel share, batch 1 | `72.4` | 72.4 | OK |
| 14 | copy share (H2D + D2H), batch 1 | `19.8` | 19.82 | OK |
| 14 | launch/API/sync residual share, batch 1 | `6.4` | 6.427 | OK |
| 14 | kernel share of CUDA pipeline, batch 4096 | `49.3` | 49.29 | OK |
| 14 | preprocessing share, batch 4096 | `43.3` | 43.32 | OK |
| 14 | copy share (H2D + D2H), batch 4096 | `7.3` | 7.321 | OK |
| 14 | preprocessing time per pass, batch 4096 (ms) | `20.2` | 20.24 | OK |
| 14 | H2D copy time, batch 4096 (ms) | `3.27` | 3.272 | OK |
| 15, 18 | hybrid-pipelined time, batch 4096 (ms) | `24.7` | 24.7 | OK |
| 15, 18 | CUDA pipeline time, batch 4096 (ms) | `46.7` | 46.72 | OK |
| 15 | parallel preprocessing effect (hybrid-seq vs CUDA), batch 4096 | `1.62` | 1.625 | OK |
| 15 | overlap effect (pipelined vs hybrid-seq), batch 4096 | `1.16` | 1.164 | OK |
| 15 | hybrid time / kernel-only time, batch 4096 | `1.07` | 1.073 | OK |
| 15 | smallest hybrid-vs-CUDA speedup over batch sizes | `1.89` | 1.892 | OK |
| 15 | largest hybrid-vs-CUDA speedup over batch sizes | `2.57` | 2.567 | OK |
| 15, 16, 18 | first batch size where hybrid beats the best CPU configuration | `32` | 32 | OK |
| 16 | fastest end-to-end time, batch 1 (ms) | `162.8` | 162.8 | OK |
| 16 | runner-up end-to-end time, batch 1 (ms) | `650.9` | 650.9 | OK |
| 16 | fastest end-to-end time, batch 8 (ms) | `75.5` | 75.48 | OK |
| 16 | runner-up end-to-end time, batch 8 (ms) | `87.5` | 87.46 | OK |
| 16 | fastest end-to-end time, batch 32 (ms) | `33.3` | 33.3 | OK |
| 16 | runner-up end-to-end time, batch 32 (ms) | `61.9` | 61.9 | OK |
| 16 | fastest end-to-end time, batch 64 (ms) | `27.9` | 27.94 | OK |
| 16 | runner-up end-to-end time, batch 64 (ms) | `59.2` | 59.24 | OK |
| 16 | fastest end-to-end time, batch 128 (ms) | `26.5` | 26.5 | OK |
| 16 | runner-up end-to-end time, batch 128 (ms) | `58.2` | 58.25 | OK |
| 16 | fastest end-to-end time, batch 256 (ms) | `26.0` | 25.98 | OK |
| 16 | runner-up end-to-end time, batch 256 (ms) | `55.1` | 55.15 | OK |
| 16 | fastest end-to-end time, batch 1024 (ms) | `25.2` | 25.21 | OK |
| 16 | runner-up end-to-end time, batch 1024 (ms) | `48.3` | 48.32 | OK |
| 16 | fastest end-to-end time, batch 4096 (ms) | `24.7` | 24.7 | OK |
| 16 | runner-up end-to-end time, batch 4096 (ms) | `46.7` | 46.72 | OK |
| 17 | Amdahl serial fraction, batch 4096 | `0.006` | 0.005578 | OK |
| 17 | Amdahl serial fraction, batch 1 | `0.088` | 0.08767 | OK |
| 17 | Amdahl ceiling 1/f, batch 1 | `11.4` | 11.41 | OK |
| 17 | Amdahl ceiling 1/f, batch 4096 | `179.3` | 179.3 | OK |
| 11 | OpenMP: passing comparisons | `16 / 16` | 16 | OK |
| 11 | CUDA: passing comparisons | `12 / 12` | 12 | OK |
| 11 | hybrid-sequential: passing comparisons | `16 / 16` | 16 | OK |
| 11 | hybrid-pipelined: passing comparisons | `32 / 32` | 32 | OK |
| 11 | CUDA max logit difference | `7.6×10` | 7.629e-06 | OK |
| 5, 11 | model accuracy (%) | `97.97` | 97.97 | OK |
| 10 | total one-time GPU set-up (ms) | `110.7` | 110.7 | OK |

## 2.44x versus 2.49x

- Like-for-like compute-only ratio (best OpenMP stages 1-3 / GPU kernels): 2.437x -> shown as 2.44x.
- Mixed ratio (best OpenMP END-TO-END / GPU kernels): 2.489x -> 2.49x; it mixes a compute-only time with an end-to-end time and is NOT used as a result.
- The string `2.49` appears on slide(s): [13, 20] (only in explanatory notes/captions).

## Apple M4 separation

- M4/Mac/Apple mentioned on the CPU-vs-GPU slides 13-16: none.

## Over-claim scan

- Phrases such as 'always fastest': none found outside negated statements.
