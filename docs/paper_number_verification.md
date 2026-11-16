# Paper number verification

Recomputed from `results/raw/*.csv` with independent code (`scripts/verify_paper_numbers.py`) and searched in the text of `main.pdf`.

**84 of 84 claims found in the PDF.**

| Claim | Expected text | Status |
|---|---|---|
| Table 6 row, batch 1 (times, thread counts and speedups) | `1 1,234.8 162.8 (16) 1,091.0 1,507.0 650.9 (1) 7.59 1.11 0.82 1.90` | OK |
| Table 6 row, batch 8 (times, thread counts and speedups) | `8 1,235.7 75.5 (24) 143.9 218.8 87.5 (8) 16.37 8.45 5.65 14.13` | OK |
| Table 6 row, batch 32 (times, thread counts and speedups) | `32 1,235.0 61.9 (24) 47.3 85.5 33.3 (2) 19.95 25.67 14.45 37.09` | OK |
| Table 6 row, batch 64 (times, thread counts and speedups) | `64 1,234.8 59.2 (24) 34.4 65.9 27.9 (24) 20.84 35.28 18.73 44.20` | OK |
| Table 6 row, batch 128 (times, thread counts and speedups) | `128 1,234.6 58.2 (24) 29.8 58.6 26.5 (24) 21.20 40.75 21.06 46.59` | OK |
| Table 6 row, batch 256 (times, thread counts and speedups) | `256 1,235.2 58.9 (24) 28.1 55.1 26.0 (24) 20.99 43.29 22.40 47.54` | OK |
| Table 6 row, batch 1024 (times, thread counts and speedups) | `1024 1,235.0 57.7 (24) 23.7 48.3 25.2 (24) 21.41 51.17 25.56 48.98` | OK |
| Table 6 row, batch 4096 (times, thread counts and speedups) | `4096 1,235.4 57.3 (24) 23.0 46.7 24.7 (24) 21.55 52.77 26.44 50.02` | OK |
| OpenMP speedup, batch 4096, 24 threads | `21.55×` | OK |
| OpenMP efficiency, batch 4096, 24 threads | `0.90` | OK |
| OpenMP speedup, batch 256, 24 threads | `20.99×` | OK |
| OpenMP efficiency, batch 256, 24 threads | `0.87` | OK |
| OpenMP best speedup, batch 1 | `7.59×` | OK |
| OpenMP best thread count, batch 1 | `16 threads` | OK |
| OpenMP efficiency 24 threads batch 1 | `0.31` | OK |
| OpenMP 1 thread vs serial, batch 256 (ms) | `1,205.5` | OK |
| M4 speedup 4 threads | `3.85×` | OK |
| M4 speedup 10 threads | `5.56×` | OK |
| M4 efficiency 10 threads | `0.56` | OK |
| M4 batch 1, 2 threads | `0.53×` | OK |
| M4 batch 1, 10 threads | `0.13×` | OK |
| M4 serial pass (ms) | `138.7` | OK |
| kernels vs serial stages 1-3, batch 4096 | `52.77×` | OK |
| kernels vs best OpenMP stages 1-3, batch 4096 | `2.44×` | OK |
| serial stages 1-3 (ms) | `1,215.2` | OK |
| best OpenMP stages 1-3 (ms) | `56.13` | OK |
| kernel time batch 4096 (ms) | `23.03` | OK |
| kernels vs best OpenMP, batch 32 | `1.27×` | OK |
| kernels vs serial, batch 1 | `1.11×` | OK |
| kernels vs OpenMP, batch 1 (as fast as) | `0.12×` | OK |
| CUDA e2e speedup, batch 4096 | `26.44×` | OK |
| CUDA e2e speedup, batch 1 | `0.82×` | OK |
| CUDA vs 24-thread OpenMP, batch 4096 | `1.23×` | OK |
| hybrid time batch 4096 (ms) | `24.70 ms` | OK |
| hybrid vs CUDA, batch 4096 | `1.89×` | OK |
| hybrid vs best OpenMP, batch 4096 | `2.32×` | OK |
| hybrid-sequential vs CUDA, batch 4096 | `1.62×` | OK |
| overlap gain, batch 4096 | `1.16×` | OK |
| hybrid / kernel-only, batch 4096 | `1.07×` | OK |
| first batch where hybrid beats best OpenMP | `batch 32` | OK |
| throughput serial, batch 4096 (images/s) | `8,094` | OK |
| throughput OpenMP, batch 4096 (images/s) | `174,451` | OK |
| throughput CUDA, batch 4096 (images/s) | `214,024` | OK |
| throughput hybrid, batch 4096 (images/s) | `404,844` | OK |
| preprocessing share, batch 1 | `1.4 %` | OK |
| copies share, batch 1 | `19.8 %` | OK |
| kernel share, batch 1 | `72.4 %` | OK |
| preprocessing share, batch 4096 | `43.3 %` | OK |
| copies share, batch 4096 | `7.3 %` | OK |
| kernel share, batch 4096 | `49.3 %` | OK |
| launch/sync residual share, batch 1 | `6.4 %` | OK |
| kernel time per batch at batch 1 (us) | `109.1 µs` | OK |
| launch/sync per batch at batch 1 (us) | `9.7 µs` | OK |
| preprocessing time per pass (ms) | `20.24 ms` | OK |
| host-to-device copy batch 4096 (ms) | `3.27 ms` | OK |
| host-to-device rate (GB/s) | `9.6 GB/s` | OK |
| serial GFLOP/s | `3.3 GFLOP/s` | OK |
| OpenMP GFLOP/s | `70.9 GFLOP/s` | OK |
| CUDA e2e GFLOP/s | `87.0 GFLOP/s` | OK |
| CUDA kernel-only GFLOP/s | `176.5 GFLOP/s` | OK |
| kernel time batch 64 block 8 | `37.32 ms` | OK |
| kernel time batch 64 block 16 | `34.43 ms` | OK |
| kernel time batch 64 block 32 | `48.65 ms` | OK |
| best block gain | `2.8 %` | OK |
| cold: CUDA context (ms) | `106.8 ms` | OK |
| cold: weight upload (ms) | `0.40 ms` | OK |
| cold: allocation (ms) | `2.97 ms` | OK |
| cold: total (ms) | `110.7 ms` | OK |
| cold: total / steady CUDA pass | `2.01×` | OK |
| cold: first OpenMP pass slower (%) | `27.9 %` | OK |
| cold: first hybrid pass slower (%) | `5.4 %` | OK |
| Amdahl f batch 64 | `0.007` | OK |
| Amdahl ceiling batch 64 | `136.5×` | OK |
| Amdahl f batch 4096 | `0.006` | OK |
| Amdahl ceiling batch 4096 | `179.3×` | OK |
| Amdahl f batch 1 | `0.088` | OK |
| Amdahl ceiling batch 1 | `11.4×` | OK |
| M4 Amdahl f batch 4096 | `0.083` | OK |
| number of correctness comparisons (Spartan) | `80 comparisons` | OK |
| max CUDA logit difference | `7.6×10` | OK |
| accuracy | `97.97` | OK |
| float32 vs float64 anchor | `9.3×10` | OK |
| serial plain -O3 (ms) | `1,295.6` | OK |
| O3 vs native crossover batch (CUDA vs best OpenMP) | `256` | OK |

## Other checks

- Over-claim phrases found: none
- Placeholders found: none
- GitHub URL present in the PDF text: True
