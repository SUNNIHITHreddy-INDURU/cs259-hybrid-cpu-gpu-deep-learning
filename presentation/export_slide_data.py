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
