#!/usr/bin/env python3
"""Export the table data used on the slides (presentation/slide_data.json) from the measured results."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import analyze_results as ar  # noqa: E402

REF, SENS, MAC, BLOCK = "spartan_k40_native", "spartan_k40_o3", "mac_m4", 16
raw = ar.load_bench()
S = {p: ar.summarise(g) for p, g in raw.groupby("platform")}
s = S[REF]


def best(d, impl, **kw):
    x = d[d.impl == impl]
    for k, v in kw.items():
        x = x[x[k] == v]
    return x.loc[x.groupby("batch").e2e_mean_ms.idxmin()].set_index("batch")


ser = s[s.impl == "serial"].set_index("batch")
omp, hy = best(s, "openmp"), best(s, "hybrid", block=BLOCK)
cu = s[(s.impl == "cuda") & (s.block == BLOCK)].set_index("batch")
out = {"best": [], "cpugpu": [], "flags": [], "micro": []}
for b in sorted(ser.index):
    cand = {"Serial": ser.loc[b, "e2e_mean_ms"], "OpenMP": omp.loc[b, "e2e_mean_ms"], "CUDA (1-thread pre.)": cu.loc[b, "e2e_mean_ms"],
            "Hybrid": hy.loc[b, "e2e_mean_ms"]}
    o = sorted(cand, key=cand.get)
    out["best"].append(dict(batch=int(b), fastest=o[0], t1=round(cand[o[0]], 1), second=o[1], t2=round(cand[o[1]], 1)))
    out["cpugpu"].append(dict(batch=int(b), serial=round(ser.loc[b, "e2e_mean_ms"], 1), omp=round(omp.loc[b, "e2e_mean_ms"], 1), ompthr=int(omp.loc[b, "threads"]),
                              kernel=round(cu.loc[b, "kernel_mean_ms"], 1), cuda=round(cu.loc[b, "e2e_mean_ms"], 1),
                              hyb=round(hy.loc[b, "e2e_mean_ms"], 1), hybthr=int(hy.loc[b, "threads"]),
                              ks=round(ser.loc[b, "e2e_mean_ms"] / cu.loc[b, "kernel_mean_ms"], 2), cs=round(ser.loc[b, "e2e_mean_ms"] / cu.loc[b, "e2e_mean_ms"], 2),
                              hs=round(ser.loc[b, "e2e_mean_ms"] / hy.loc[b, "e2e_mean_ms"], 2)))
s3 = S[SENS]
for label, f in (("Serial", lambda d: d[d.impl == "serial"]), ("OpenMP (best threads)", lambda d: d[d.impl == "openmp"]),
                 ("CUDA (1-thread pre.)", lambda d: d[(d.impl == "cuda") & (d.block == BLOCK)]), ("Hybrid (best threads)", lambda d: d[(d.impl == "hybrid") & (d.block == BLOCK)])):
    r = {"impl": label}
    for b in (256, 4096):
        a, c = f(s)[f(s).batch == b].e2e_mean_ms.min(), f(s3)[f(s3).batch == b].e2e_mean_ms.min()
        r[f"native{b}"], r[f"o3{b}"] = round(a, 1), round(c, 1)
    out["flags"].append(r)
import pandas as pd
m = pd.read_csv(sorted(ar.RAW.glob(f"{REF}_*_micro.csv"))[0]).set_index(["metric", "threads"]).value
out["micro"] = [["PCIe host-to-device (pageable / pinned)", f"{m[('h2d_pageable_bandwidth', 0)]:.1f} / {m[('h2d_pinned_bandwidth', 0)]:.1f} GB/s"],
                ["PCIe device-to-host (pageable / pinned)", f"{m[('d2h_pageable_bandwidth', 0)]:.1f} / {m[('d2h_pinned_bandwidth', 0)]:.1f} GB/s"],
                ["GPU device-to-device copy", f"{m[('d2d_copy_bandwidth', 0)]:.1f} GB/s"],
                ["Kernel launch (async / with sync)", f"{m[('kernel_launch_async', 0)]:.2f} / {m[('kernel_launch_sync', 0)]:.2f} µs"],
                ["Xeon memory bandwidth (1 / 8 / 24 threads)", f"{m[('cpu_triad_bandwidth', 1)]:.1f} / {m[('cpu_triad_bandwidth', 8)]:.1f} / {m[('cpu_triad_bandwidth', 24)]:.1f} GB/s"],
                ["Xeon OpenMP fork-join (8 / 24 threads)", f"{m[('openmp_fork_join', 8)]:.2f} / {m[('openmp_fork_join', 24)]:.2f} µs"]]
import re
nums = {}
sup = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
for _, r in pd.read_csv(ROOT / "results" / "processed" / "numbers.csv", dtype=str).iterrows():
    v = str(r.value).replace("{,}", ",")
    mm = re.match(r"\\ensuremath\{([\d.]+)\\times10\^\{(-?\d+)\}\}", v)
    if mm:
        v = f"{mm.group(1)}×10{mm.group(2).translate(sup)}"
    nums[r.key] = v
out["num"] = nums
(ROOT / "presentation" / "slide_data.json").write_text(json.dumps(out, indent=1))
print("wrote presentation/slide_data.json")


# ======================= chart series with 95 % CIs, recomputed from the raw CSVs =======================
import glob
import numpy as np
from scipy import stats as _st

def _ci(x):
    x = np.asarray(x, float)
    return float(_st.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else 0.0

def _raw(plat):
    return pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(ROOT / "results" / "raw" / f"{plat}_*_bench.csv")))], ignore_index=True)

def _stat(df, col):
    return float(df[col].mean()), _ci(df[col].values)

def build_series():
    d, m = _raw(REF), _raw(MAC)
    batches = sorted(d.batch.unique())
    ser = {"batches": [int(b) for b in batches]}
    keys = ["serial", "omp", "cuda", "kernel", "hseq", "hyb", "serial_c", "omp_c", "pre", "h2d", "d2h", "other"]
    for k in keys:
        ser[k] = []; ser[k + "_ci"] = []
    ser["omp_thr"] = []; ser["hseq_thr"] = []; ser["hyb_thr"] = []; ser["omp_c_thr"] = []
    for b in batches:
        s_ = d[(d.impl == "serial") & (d.batch == b)]
        mu, ci = _stat(s_, "e2e_ms"); ser["serial"].append(mu); ser["serial_ci"].append(ci)
        sc = s_.layer1_ms + s_.layer2_ms; ser["serial_c"].append(float(sc.mean())); ser["serial_c_ci"].append(_ci(sc.values))
        for impl, key in (("openmp", "omp"), ("hybrid_seq", "hseq"), ("hybrid", "hyb")):
            q = d[(d.impl == impl) & (d.batch == b)]
            if impl != "openmp":
                q = q[q.block == 16]
            best = q.groupby("threads").e2e_ms.mean().idxmin()
            mu, ci = _stat(q[q.threads == best], "e2e_ms"); ser[key].append(mu); ser[key + "_ci"].append(ci); ser[key + "_thr"].append(int(best))
        q = d[(d.impl == "openmp") & (d.batch == b)].copy(); q["c"] = q.layer1_ms + q.layer2_ms
        bt = q.groupby("threads").c.mean().idxmin(); qq = q[q.threads == bt]
        ser["omp_c"].append(float(qq.c.mean())); ser["omp_c_ci"].append(_ci(qq.c.values)); ser["omp_c_thr"].append(int(bt))
        c_ = d[(d.impl == "cuda") & (d.batch == b) & (d.block == 16)]
        mu, ci = _stat(c_, "e2e_ms"); ser["cuda"].append(mu); ser["cuda_ci"].append(ci)
        mu, ci = _stat(c_, "kernel_ms"); ser["kernel"].append(mu); ser["kernel_ci"].append(ci)
        for col, key in (("pre_ms", "pre"), ("h2d_ms", "h2d"), ("d2h_ms", "d2h")):
            mu, ci = _stat(c_, col); ser[key].append(mu); ser[key + "_ci"].append(ci)
        oth = c_.e2e_ms - c_.pre_ms - c_.h2d_ms - c_.kernel_ms - c_.d2h_ms
        ser["other"].append(float(max(oth.mean(), 0))); ser["other_ci"].append(_ci(oth.values))
    # thread scaling (time, speedup, efficiency) with first-order propagated CIs
    def scaling(df, bl):
        out = {}
        for b in bl:
            s_ = df[(df.impl == "serial") & (df.batch == b)].e2e_ms
            ts, cs = float(s_.mean()), _ci(s_.values)
            rows = []
            for T in sorted(df[(df.impl == "openmp") & (df.batch == b)].threads.unique()):
                p = df[(df.impl == "openmp") & (df.batch == b) & (df.threads == T)].e2e_ms
                tp, cp = float(p.mean()), _ci(p.values)
                sp = ts / tp; sci = sp * float(np.sqrt((cs / ts) ** 2 + (cp / tp) ** 2))
                rows.append(dict(threads=int(T), time=tp, time_ci=cp, speedup=sp, speedup_ci=sci, eff=sp / T, eff_ci=sci / T))
            out[str(b)] = rows
        return out
    ser["scale_spartan"] = scaling(d, [1, 256, 4096])
    ser["scale_mac"] = scaling(m, [1, 256, 4096])
    # Amdahl fits for batch 1 and 4096 (Spartan)
    am = pd.read_csv(ROOT / "results" / "processed" / f"amdahl_{REF}.csv").set_index("batch")
    ser["amdahl"] = {str(b): dict(f=float(am.loc[b, "serial_fraction"]), r2=float(am.loc[b, "r_squared"])) for b in (1, 4096)}
    # block-size study (kernel and end-to-end, per block)
    blk = {}
    for blkv in sorted(d[d.impl == "cuda"].block.unique()):
        q = d[(d.impl == "cuda") & (d.block == blkv)]
        blk[str(int(blkv))] = dict(kernel=[float(q[q.batch == b].kernel_ms.mean()) for b in batches], e2e=[float(q[q.batch == b].e2e_ms.mean()) for b in batches],
                                   kernel_ci=[_ci(q[q.batch == b].kernel_ms.values) for b in batches])
    ser["blocks"] = blk
    # correctness table (Spartan reference build)
    v = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(ROOT / "results" / "raw" / f"{REF}_*_validation.csv")))], ignore_index=True)
    v["g"] = v.comparison.str.replace(r" \(s=\d\)", "", regex=True)
    ser["validation"] = [dict(group=g, n=int(len(x)), passed=int((x["pass"] == "PASS").sum()), maxerr=float(x.max_abs_err.max()), meanerr=float(x.mean_abs_err.max()),
                              agree=float(x.pred_agreement.min() * 100), acc=float(x.accuracy.min() * 100)) for g, x in v.groupby("g", sort=False)]
    return ser

out["series"] = build_series()
(ROOT / "presentation" / "slide_data.json").write_text(json.dumps(out, indent=1))
print("added chart series ->", len(out["series"]["batches"]), "batch sizes")
