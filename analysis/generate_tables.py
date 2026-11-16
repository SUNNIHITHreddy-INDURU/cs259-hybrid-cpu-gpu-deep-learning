#!/usr/bin/env python3
"""Turn the measured results into tables (LaTeX tabular + CSV) in results/tables/.

Every number comes from results/raw (via results/processed); nothing is typed in by hand.
LaTeX files contain only the `tabular` so the paper controls caption and placement.
"""
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_results as ar

ROOT = ar.ROOT
TAB = Path(os.environ.get("CS259_TAB", ROOT / "results" / "tables"))
DEFAULT_BLOCK = 16


def esc(x):
    return re.sub(r"([#%&_$])", r"\\\1", str(x))


def fmt(x, nd=2):
    if isinstance(x, (int, np.integer)) and not isinstance(x, bool):
        return str(int(x))
    if isinstance(x, (float, np.floating)):
        if np.isnan(x):
            return "--"
        if x == 0:
            return "0"
        if x != 0 and abs(x) < 0.01:
            return f"{x:.1e}".replace("e-0", "e-").replace("e+0", "e+")
        return f"{x:,.{nd}f}" if abs(x) < 1000 else f"{x:,.0f}"
    return esc(x)


def write(df, name, align=None):
    TAB.mkdir(parents=True, exist_ok=True)
    df.to_csv(TAB / f"{name}.csv", index=False)
    align = align or "l" + "r" * (len(df.columns) - 1)
    lines = [f"\\begin{{tabular}}{{{align}}}", "\\toprule", " & ".join(esc(c) if "$" not in c and "\\" not in c else c for c in df.columns) + " \\\\", "\\midrule"]
    for r in df.itertuples(index=False):
        lines.append(" & ".join(fmt(v) for v in r) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (TAB / f"{name}.tex").write_text("\n".join(lines) + "\n")
    print("table:", name, f"({len(df)} rows)")


def best(S, impl, **kw):
    d = S[S.impl == impl]
    for k, v in kw.items():
        d = d[d[k] == v]
    return d.loc[d.groupby("batch").e2e_mean_ms.idxmin()].set_index("batch") if len(d) else None


def main():
    raw = ar.load_bench()
    for plat, g in raw.groupby("platform"):
        S = ar.summarise(g)
        first = g.iloc[0]
        # ---- platform
        write(pd.DataFrame({"Item": ["CPU", "Logical threads", "GPU", "Host compiler", "CUDA runtime", "Passes per configuration", "Images per pass"],
                            "Value": [first.cpu_model, first.cpu_logical_threads, first.gpu_model, first.compiler,
                                      first.cuda_runtime, int(S.n_runs.min()), int(first.n_samples)]}), f"platform_{plat}", "ll")
        # ---- OpenMP scaling (selected batch sizes)
        omp = S[S.impl == "openmp"]
        if len(omp):
            rows = []
            for b in [1, 64, 256, 4096]:
                for _, r in omp[omp.batch == b].sort_values("threads").iterrows():
                    rows.append({"Batch": b, "Threads": int(r.threads), "Time (ms)": r.e2e_mean_ms, "95% CI (ms)": r.e2e_ci95_ms,
                                 "Speedup": r.speedup_vs_serial, "Efficiency": r.efficiency})
            write(pd.DataFrame(rows), f"openmp_scaling_{plat}")
            am = ar.PROC / f"amdahl_{plat}.csv"
            if am.exists():
                a = pd.read_csv(am)
                write(pd.DataFrame({"Batch": a.batch, "Serial fraction f": a.serial_fraction, "Ceiling 1/f": a.ceiling_speedup, "R2": a.r_squared,
                                    "Best measured": a.max_measured_speedup, "at threads": a.at_threads}), f"amdahl_{plat}")
        # ---- CPU vs GPU
        ser = S[S.impl == "serial"].set_index("batch")
        bo, bc = best(S, "openmp"), best(S, "cuda", block=DEFAULT_BLOCK)
        bh = best(S, "hybrid", block=DEFAULT_BLOCK)
        rows = []
        for b in sorted(ser.index):
            r = {"Batch": b, "Serial (ms)": ser.loc[b, "e2e_mean_ms"]}
            if bo is not None:
                r["OpenMP (ms)"] = bo.loc[b, "e2e_mean_ms"]; r["OMP thr"] = int(bo.loc[b, "threads"])
            if bc is not None:
                r["CUDA kernel (ms)"] = bc.loc[b, "kernel_mean_ms"]; r["CUDA e2e (ms)"] = bc.loc[b, "e2e_mean_ms"]
                r["Kernel-only speedup"] = ser.loc[b, "e2e_mean_ms"] / bc.loc[b, "kernel_mean_ms"]
                r["E2E speedup"] = ser.loc[b, "e2e_mean_ms"] / bc.loc[b, "e2e_mean_ms"]
            if bh is not None:
                r["Hybrid (ms)"] = bh.loc[b, "e2e_mean_ms"]
            rows.append(r)
        write(pd.DataFrame(rows), f"cpu_vs_gpu_{plat}")
        # ---- CUDA stage breakdown
        c = S[(S.impl == "cuda") & (S.block == DEFAULT_BLOCK)].sort_values("batch")
        if len(c):
            other = (c.e2e_mean_ms - c.pre_mean_ms - c.h2d_mean_ms - c.kernel_mean_ms - c.d2h_mean_ms).clip(lower=0)
            write(pd.DataFrame({"Batch": c.batch, "Preproc (ms)": c.pre_mean_ms, "H2D (ms)": c.h2d_mean_ms, "Kernel (ms)": c.kernel_mean_ms,
                                "D2H (ms)": c.d2h_mean_ms, "Other (ms)": other, "E2E (ms)": c.e2e_mean_ms,
                                "Transfer %": (c.h2d_mean_ms + c.d2h_mean_ms) / c.e2e_mean_ms * 100}), f"cuda_breakdown_{plat}")
            blk = S[S.impl == "cuda"].pivot_table(index="batch", columns="block", values="kernel_mean_ms").reset_index()
            blk.columns = ["Batch"] + [f"{int(x)}x{int(x)} kernel (ms)" for x in blk.columns[1:]]
            write(blk, f"cuda_blocksize_{plat}")
        # ---- hybrid ablation
        bs = best(S, "hybrid_seq", block=DEFAULT_BLOCK)
        tp = ar.PROC / f"tests_{plat}.csv"
        if bh is not None and bc is not None:
            t = pd.read_csv(tp) if tp.exists() else None
            rows = []
            for b in sorted(bc.index):
                r = {"Batch": b, "CUDA 1-thread pre. (ms)": bc.loc[b, "e2e_mean_ms"]}
                if bs is not None:
                    r["+OpenMP preproc (ms)"] = bs.loc[b, "e2e_mean_ms"]; r["thr"] = int(bs.loc[b, "threads"])
                r["+pipeline (ms)"] = bh.loc[b, "e2e_mean_ms"]; r["Hybrid thr"] = int(bh.loc[b, "threads"])
                r["Hybrid speedup vs CUDA"] = bc.loc[b, "e2e_mean_ms"] / bh.loc[b, "e2e_mean_ms"]
                if t is not None:
                    q = t[(t.batch == b) & (t.a == "hybrid") & (t.b == "cuda")]
                    if len(q):
                        r["p (Welch)"] = float(q.p_value.iloc[0])
                rows.append(r)
            write(pd.DataFrame(rows), f"hybrid_ablation_{plat}")
    # ---- correctness (one table per platform)
    files = sorted(ar.RAW.glob("*_validation.csv"))
    if files:
        v = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
        v["comparison"] = v.comparison.str.replace(r" \(s=\d\)", "", regex=True)
        for plat, gp in v.groupby("platform"):
            rows = []
            for cmp_, g in gp.groupby("comparison", sort=False):
                rows.append({"Comparison": cmp_.replace("Serial float32 vs NumPy float64", "Serial vs NumPy (float64)"), "Configs": len(g),
                             "Max abs err": g.max_abs_err.max(), "Mean abs err": g.mean_abs_err.max(),
                             "Agree %": g.pred_agreement.min() * 100,
                             "Acc %": "--" if "NumPy" in cmp_ else (f"{g.accuracy.min() * 100:.2f}" if g.accuracy.min() == g.accuracy.max() else f"{g.accuracy.min() * 100:.2f}-{g.accuracy.max() * 100:.2f}"),
                             "Pass": f"{int((g['pass'] == 'PASS').sum())}/{len(g)}"})
            write(pd.DataFrame(rows), f"correctness_{plat}", "lrrrrrr")
    # ---- micro-benchmarks
    mf = sorted(ar.RAW.glob("*_micro.csv"))
    if mf:
        m = pd.concat([pd.read_csv(f) for f in mf], ignore_index=True)
        write(m[["platform", "metric", "threads", "value", "unit"]].rename(columns={"value": "Value"}), "microbench", "llrrl")


if __name__ == "__main__":
    main()
