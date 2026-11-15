#!/usr/bin/env python3
"""Aggregate raw benchmark CSVs into per-configuration statistics.

Input : results/raw/<platform>_<timestamp>_bench.csv   (one row per measured pass)
Output: results/processed/summary_<platform>.csv       (one row per configuration)

Statistics per configuration (all from the recorded passes, nothing assumed):
  n runs, mean, standard deviation, median, min, max, 95 % confidence interval of the mean
  (Student t), and for the summed stage times their means.
Derived metrics: throughput (images/s), speedup vs serial at the same batch size,
  OpenMP efficiency (speedup / threads), GPU transfer share = (H2D + D2H) / e2e.
"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
RAW = Path(os.environ.get("CS259_RAW", ROOT / "results" / "raw"))
PROC = Path(os.environ.get("CS259_PROC", ROOT / "results" / "processed"))
KEYS = ["platform", "impl", "batch", "threads", "block", "streams"]
STAGES = ["pre_ms", "layer1_ms", "layer2_ms", "h2d_ms", "kernel_ms", "d2h_ms"]


def ci95(x):
    x = np.asarray(x, dtype=float)
    if len(x) < 2:
        return float("nan")
    return float(stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)))


def load_bench(platform_filter=None):
    frames = []
    for f in sorted(RAW.glob("*_bench.csv")):
        df = pd.read_csv(f)
        df["source_file"] = f.name
        frames.append(df)
    if not frames:
        raise SystemExit("no *_bench.csv files in results/raw")
    df = pd.concat(frames, ignore_index=True)
    if platform_filter:
        df = df[df.platform == platform_filter]
    return df


def summarise(df):
    rows = []
    for key, g in df.groupby(KEYS):
        e = g.e2e_ms.values
        r = dict(zip(KEYS, key))
        r.update(
            n_runs=len(e), n_samples=int(g.n_samples.iloc[0]),
            e2e_mean_ms=e.mean(), e2e_std_ms=e.std(ddof=1) if len(e) > 1 else float("nan"),
            e2e_median_ms=float(np.median(e)), e2e_min_ms=e.min(), e2e_max_ms=e.max(),
            e2e_ci95_ms=ci95(e), accuracy_min=g.accuracy.min(), accuracy_max=g.accuracy.max(),
            cpu_model=g.cpu_model.iloc[0], gpu_model=g.gpu_model.iloc[0], compiler=g.compiler.iloc[0],
            cuda_runtime=g.cuda_runtime.iloc[0],
        )
        for s in STAGES:
            r[s.replace("_ms", "_mean_ms")] = g[s].mean()
        rows.append(r)
    s = pd.DataFrame(rows)
    s["throughput_img_s"] = s.n_samples / (s.e2e_mean_ms / 1000.0)
    # speedup vs the serial run of the same platform and batch size
    base = s[s.impl == "serial"].set_index(["platform", "batch"]).e2e_mean_ms
    s["speedup_vs_serial"] = [base.get((p, b), np.nan) / m for p, b, m in zip(s.platform, s.batch, s.e2e_mean_ms)]
    s["efficiency"] = np.where(s.impl == "openmp", s.speedup_vs_serial / s.threads, np.nan)
    gpu = s.h2d_mean_ms + s.kernel_mean_ms + s.d2h_mean_ms
    s["transfer_share_of_gpu_time"] = np.where(s.impl == "cuda", (s.h2d_mean_ms + s.d2h_mean_ms) / gpu, np.nan)
    s["transfer_share_of_e2e"] = np.where(s.impl == "cuda", (s.h2d_mean_ms + s.d2h_mean_ms) / s.e2e_mean_ms, np.nan)
    return s.sort_values(KEYS).reset_index(drop=True)


def main():
    PROC.mkdir(parents=True, exist_ok=True)
    df = load_bench()
    for platform, g in df.groupby("platform"):
        s = summarise(g)
        out = PROC / f"summary_{platform}.csv"
        s.to_csv(out, index=False)
        print(f"{platform}: {len(g)} rows -> {len(s)} configurations -> {out}")


if __name__ == "__main__":
    main()
