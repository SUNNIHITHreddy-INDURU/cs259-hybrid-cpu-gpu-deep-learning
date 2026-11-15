#!/usr/bin/env python3
"""Statistical analysis of the measured results (everything computed from the CSV data).

For each platform with OpenMP data:
  * Amdahl serial-fraction fit  S(p) = 1 / (f + (1 - f) / p)  by least squares on the measured
    speedups, per batch size; predicted ceiling 1/f and the fit's R^2
  * Karp-Flatt metric  e(p) = (1/S - 1/p) / (1 - 1/p)  for every measured thread count
For platforms with GPU data:
  * Welch t-tests (two-sided) and bootstrap 95 % CI of the ratio of means for the comparisons
      hybrid vs cuda,   hybrid vs hybrid_seq,   hybrid_seq vs cuda     at every batch size
  * CPU/GPU crossover: smallest batch where CUDA end-to-end beats the best CPU configuration
Outputs: results/processed/amdahl_<platform>.csv, karp_flatt_<platform>.csv, tests_<platform>.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize, stats

import analyze_results as ar

ROOT = ar.ROOT
RNG = np.random.default_rng(12345)


def amdahl(p, f):
    return 1.0 / (f + (1.0 - f) / p)


def fit_amdahl(threads, speedup):
    res = optimize.least_squares(lambda f: amdahl(threads, f[0]) - speedup, x0=[0.1], bounds=(0.0, 1.0))
    f = float(res.x[0])
    ss_res = float(np.sum((amdahl(threads, f) - speedup) ** 2))
    ss_tot = float(np.sum((speedup - speedup.mean()) ** 2))
    return f, (1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan")


def bootstrap_ratio_ci(a, b, n=5000):
    """95 % CI of mean(a)/mean(b) by resampling both sets of passes."""
    a, b = np.asarray(a), np.asarray(b)
    r = [RNG.choice(a, len(a)).mean() / RNG.choice(b, len(b)).mean() for _ in range(n)]
    return float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))


def main():
    raw = ar.load_bench()
    summ = {p: ar.summarise(g) for p, g in raw.groupby("platform")}
    for platform, s in summ.items():
        g = raw[raw.platform == platform]
        omp = s[s.impl == "openmp"]
        if len(omp):
            rows, kf = [], []
            for batch, d in omp.groupby("batch"):
                d = d.sort_values("threads")
                th, sp = d.threads.values.astype(float), d.speedup_vs_serial.values
                f, r2 = fit_amdahl(th, sp)
                rows.append(dict(platform=platform, batch=batch, serial_fraction=f,
                                 ceiling_speedup=1.0 / f if f > 0 else float("inf"), r_squared=r2,
                                 max_measured_speedup=float(sp.max()), at_threads=int(th[sp.argmax()])))
                for p, sv in zip(th, sp):
                    if p > 1:
                        kf.append(dict(platform=platform, batch=batch, threads=int(p), speedup=sv,
                                       karp_flatt=(1.0 / sv - 1.0 / p) / (1.0 - 1.0 / p)))
            pd.DataFrame(rows).to_csv(ar.PROC / f"amdahl_{platform}.csv", index=False)
            pd.DataFrame(kf).to_csv(ar.PROC / f"karp_flatt_{platform}.csv", index=False)
            print(f"{platform}: Amdahl fit and Karp-Flatt written")
        if (s.impl == "cuda").any():
            tests = []
            best_thr = lambda sub: sub.loc[sub.e2e_mean_ms.idxmin()]
            for batch in sorted(s.batch.unique()):
                def runs(impl, **kw):
                    q = g[(g.impl == impl) & (g.batch == batch)]
                    for k, v in kw.items():
                        q = q[q[k] == v]
                    return q
                # best configuration of each GPU variant at this batch size (by mean e2e)
                cand = {}
                for impl in ("cuda", "hybrid_seq", "hybrid"):
                    sub = s[(s.impl == impl) & (s.batch == batch)]
                    if len(sub):
                        b = best_thr(sub)
                        cand[impl] = runs(impl, threads=int(b.threads), block=int(b.block), streams=int(b.streams)).e2e_ms.values
                for a_name, b_name in (("hybrid", "cuda"), ("hybrid", "hybrid_seq"), ("hybrid_seq", "cuda")):
                    if a_name in cand and b_name in cand:
                        a, b = cand[a_name], cand[b_name]
                        t, pv = stats.ttest_ind(a, b, equal_var=False)
                        lo, hi = bootstrap_ratio_ci(a, b)
                        tests.append(dict(platform=platform, batch=batch, a=a_name, b=b_name,
                                          mean_a_ms=a.mean(), mean_b_ms=b.mean(), ratio_a_over_b=a.mean() / b.mean(),
                                          ratio_ci95_low=lo, ratio_ci95_high=hi, welch_t=t, p_value=pv))
            pd.DataFrame(tests).to_csv(ar.PROC / f"tests_{platform}.csv", index=False)
            cross = []
            for batch in sorted(s.batch.unique()):
                cpu = s[(s.batch == batch) & s.impl.isin(["serial", "openmp"])]
                gpu = s[(s.batch == batch) & (s.impl == "cuda")]
                if len(cpu) and len(gpu):
                    cross.append(dict(platform=platform, batch=batch, best_cpu_ms=cpu.e2e_mean_ms.min(),
                                      best_cpu_config=f"{cpu.loc[cpu.e2e_mean_ms.idxmin()].impl}/{int(cpu.loc[cpu.e2e_mean_ms.idxmin()].threads)}thr",
                                      best_cuda_ms=gpu.e2e_mean_ms.min(), cuda_beats_cpu=bool(gpu.e2e_mean_ms.min() < cpu.e2e_mean_ms.min())))
            pd.DataFrame(cross).to_csv(ar.PROC / f"crossover_{platform}.csv", index=False)
            print(f"{platform}: significance tests and CPU/GPU crossover written")


if __name__ == "__main__":
    main()
