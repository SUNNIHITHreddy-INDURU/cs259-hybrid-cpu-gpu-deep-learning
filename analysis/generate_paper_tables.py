#!/usr/bin/env python3
"""Write the tables used in the paper (report/overleaf/tables/*.tex) from the measured results.

Every column header carries its unit. Values are taken from results/processed (derived from results/raw).
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_results as ar

ROOT = ar.ROOT
OUT = Path(os.environ.get("CS259_PAPER_TABLES", ROOT / "report" / "overleaf" / "tables"))
REF, SENS, MAC = "spartan_k40_native", "spartan_k40_o3", "mac_m4"
BLOCK = 16


def num(x, nd=1):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "--"
    return f"{x:,.{nd}f}".replace(",", "{,}")


def sci(x):
    if x == 0:
        return "0"
    m, e = f"{x:.1e}".split("e")
    return f"${m}\\times10^{{{int(e)}}}$"


def write(name, header_lines, rows, colspec):
    OUT.mkdir(parents=True, exist_ok=True)
    lines = [f"\\begin{{tabular}}{{{colspec}}}", "\\toprule"] + header_lines + ["\\midrule"]
    lines += [" & ".join(r) + " \\\\" for r in rows]
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / f"{name}.tex").write_text("\n".join(lines) + "\n")
    print("paper table:", name)


def best(S, impl, **kw):
    d = S[S.impl == impl]
    for k, v in kw.items():
        d = d[d[k] == v]
    return d.loc[d.groupby("batch").e2e_mean_ms.idxmin()].set_index("batch")


def main():
    raw = ar.load_bench()
    S = {p: ar.summarise(g) for p, g in raw.groupby("platform")}
    s = S[REF]
    ser = s[s.impl == "serial"].set_index("batch")
    omp = best(s, "openmp")
    cu = s[(s.impl == "cuda") & (s.block == BLOCK)].set_index("batch")
    hs = best(s, "hybrid_seq", block=BLOCK)
    hy = best(s, "hybrid", block=BLOCK)
    batches = sorted(ser.index)

    # ---- 1. OpenMP scaling on the Spartan node (batch 1, 256, 4096)
    o = s[s.impl == "openmp"]
    rows = []
    for T in sorted(o.threads.unique()):
        r = [str(int(T))]
        for b in (1, 256, 4096):
            x = o[(o.threads == T) & (o.batch == b)].iloc[0]
            r += [num(x.e2e_mean_ms), num(x.speedup_vs_serial, 2), num(x.efficiency, 2)]
        rows.append(r)
    write("omp_spartan",
          ["Threads & \\multicolumn{3}{c}{Batch 1} & \\multicolumn{3}{c}{Batch 256} & \\multicolumn{3}{c}{Batch 4096} \\\\",
           "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\\cmidrule(lr){8-10}",
           " & Time (ms) & $S$ ($\\times$) & $E$ & Time (ms) & $S$ ($\\times$) & $E$ & Time (ms) & $S$ ($\\times$) & $E$ \\\\"],
          rows, "r" + "rrr" * 3)

    # ---- 2. CPU vs GPU, all batch sizes
    rows = []
    for b in batches:
        rows.append([str(b), num(ser.loc[b, "e2e_mean_ms"]), f"{num(omp.loc[b, 'e2e_mean_ms'])} ({int(omp.loc[b, 'threads'])})",
                     num(cu.loc[b, "kernel_mean_ms"]), num(cu.loc[b, "e2e_mean_ms"]),
                     f"{num(hy.loc[b, 'e2e_mean_ms'])} ({int(hy.loc[b, 'threads'])})",
                     num(ser.loc[b, "e2e_mean_ms"] / cu.loc[b, "kernel_mean_ms"], 2),
                     num(ser.loc[b, "e2e_mean_ms"] / cu.loc[b, "e2e_mean_ms"], 2),
                     num(ser.loc[b, "e2e_mean_ms"] / hy.loc[b, "e2e_mean_ms"], 2)])
    write("cpu_vs_gpu",
          ["Batch & Serial & OpenMP (threads) & CUDA kernel & CUDA end-to-end & Hybrid (threads) & \\multicolumn{3}{c}{Speedup over serial ($\\times$)} \\\\",
           "\\cmidrule(lr){7-9}",
           " & (ms) & (ms) & only (ms) & (ms) & (ms) & kernel-only & CUDA e2e & Hybrid \\\\"],
          rows, "rrrrrrrrr")

    # ---- 2b. compute-only comparison: stages 1-3 (hidden layer, output layer, argmax); no preprocessing, no copies
    rows = []
    for b in batches:
        cser = ser.loc[b, "layer1_mean_ms"] + ser.loc[b, "layer2_mean_ms"]
        ob = o[o.batch == b].assign(comp=lambda d: d.layer1_mean_ms + d.layer2_mean_ms)
        ob = ob.loc[ob.comp.idxmin()]
        k = cu.loc[b, "kernel_mean_ms"]
        rows.append([str(b), num(cser), f"{num(ob.comp)} ({int(ob.threads)})", num(k), num(cser / k, 2), num(ob.comp / k, 2)])
    write("compute_only",
          ["Batch & Serial & OpenMP (threads) & GPU kernels & \\multicolumn{2}{c}{GPU kernels' speedup ($\\times$)} \\\\",
           "\\cmidrule(lr){5-6}",
           " & (ms) & (ms) & (ms) & vs serial & vs OpenMP \\\\"],
          rows, "rrrrrr")

    # ---- 3. CUDA stage breakdown
    rows = []
    for b in batches:
        r = cu.loc[b]
        other = max(r.e2e_mean_ms - r.pre_mean_ms - r.h2d_mean_ms - r.kernel_mean_ms - r.d2h_mean_ms, 0)
        rows.append([str(b), num(r.pre_mean_ms), num(r.h2d_mean_ms), num(r.kernel_mean_ms), num(r.d2h_mean_ms), num(other),
                     num(r.e2e_mean_ms), num((r.h2d_mean_ms + r.d2h_mean_ms) / r.e2e_mean_ms * 100)])
    write("cuda_breakdown",
          ["Batch & Preprocess & H2D copy & Kernels & D2H copy & Other & Total & Copies share \\\\",
           " & (ms) & (ms) & (ms) & (ms) & (ms) & (ms) & (\\% of total) \\\\"],
          rows, "rrrrrrrr")

    # ---- 4. hybrid ablation with significance
    tests = pd.read_csv(ar.PROC / f"tests_{REF}.csv")
    rows = []
    for b in batches:
        p = float(tests[(tests.batch == b) & (tests.a == "hybrid") & (tests.b == "cuda")].p_value.iloc[0])
        rows.append([str(b), num(cu.loc[b, "e2e_mean_ms"]), f"{num(hs.loc[b, 'e2e_mean_ms'])} ({int(hs.loc[b, 'threads'])})",
                     f"{num(hy.loc[b, 'e2e_mean_ms'])} ({int(hy.loc[b, 'threads'])})",
                     num(cu.loc[b, "e2e_mean_ms"] / hs.loc[b, "e2e_mean_ms"], 2), num(cu.loc[b, "e2e_mean_ms"] / hy.loc[b, "e2e_mean_ms"], 2),
                     num(omp.loc[b, "e2e_mean_ms"] / hy.loc[b, "e2e_mean_ms"], 2), sci(p)])
    write("hybrid_ablation",
          ["Batch & CUDA (1-thr. pre.) & Hybrid-seq. control (thr.) & Hybrid-pipelined (thr.) & Control vs CUDA & Pipelined vs CUDA & Pipelined vs OpenMP & Welch $p$ \\\\",
           " & (ms) & (ms) & (ms) & ($\\times$) & ($\\times$) & ($\\times$) & (pipelined vs CUDA) \\\\"],
          rows, "rrrrrrrr")

    # ---- 5. measured platform limits (micro-benchmarks)
    def micro(path):
        return pd.read_csv(path).set_index(["metric", "threads"]).value
    mref = micro(sorted(ar.RAW.glob(f"{REF}_*_micro.csv"))[0])
    mmac = micro(sorted(ar.RAW.glob(f"{MAC}_*_micro.csv"))[0])
    rows = [
        ["PCIe host-to-device, pageable / pinned", f"{num(mref[('h2d_pageable_bandwidth', 0)])} / {num(mref[('h2d_pinned_bandwidth', 0)])} GB/s"],
        ["PCIe device-to-host, pageable / pinned", f"{num(mref[('d2h_pageable_bandwidth', 0)])} / {num(mref[('d2h_pinned_bandwidth', 0)])} GB/s"],
        ["GPU device-to-device copy", f"{num(mref[('d2d_copy_bandwidth', 0)])} GB/s"],
        ["Kernel launch, asynchronous / with sync", f"{num(mref[('kernel_launch_async', 0)], 2)} / {num(mref[('kernel_launch_sync', 0)], 2)} $\\mu$s"],
        ["Xeon memory bandwidth, 1 / 8 / 24 threads", f"{num(mref[('cpu_triad_bandwidth', 1)])} / {num(mref[('cpu_triad_bandwidth', 8)])} / {num(mref[('cpu_triad_bandwidth', 24)])} GB/s"],
        ["Xeon OpenMP fork--join, 8 / 24 threads", f"{num(mref[('openmp_fork_join', 8)], 2)} / {num(mref[('openmp_fork_join', 24)], 2)} $\\mu$s"],
        ["M4 memory bandwidth, 1 / 10 threads", f"{num(mmac[('cpu_triad_bandwidth', 1)])} / {num(mmac[('cpu_triad_bandwidth', 10)])} GB/s"],
        ["M4 OpenMP fork--join, 4 / 10 threads", f"{num(mmac[('openmp_fork_join', 4)], 2)} / {num(mmac[('openmp_fork_join', 10)], 2)} $\\mu$s"],
    ]
    write("micro", ["Quantity & Measured value \\\\"], rows, "@{}lr@{}")

    # ---- 5b. fastest implementation per batch size
    rows = []
    for b in batches:
        cand = {"Serial": ser.loc[b, "e2e_mean_ms"], "OpenMP": omp.loc[b, "e2e_mean_ms"], "CUDA (1-thr. pre.)": cu.loc[b, "e2e_mean_ms"],
                "Hybrid-pipelined": hy.loc[b, "e2e_mean_ms"]}
        order = sorted(cand, key=cand.get)
        rows.append([str(b), order[0], num(cand[order[0]]), order[1], num(cand[order[1]]), num(cand[order[1]] / cand[order[0]], 2)])
    write("best_choice", ["Batch & Fastest & Time & Second fastest & Time & Gap \\\\", " & implementation & (ms) & implementation & (ms) & ($\\times$) \\\\"],
          rows, "rlrlrr")

    # ---- 6. compiler-flag sensitivity at two batch sizes
    s3 = S[SENS]
    rows = []
    for label, f in (("Serial", lambda d: d[d.impl == "serial"]), ("OpenMP, best thread count", lambda d: d[d.impl == "openmp"]),
                     ("CUDA, 1-thr. preproc. (16$\\times$16)", lambda d: d[(d.impl == "cuda") & (d.block == BLOCK)]),
                     ("Hybrid-pipelined, best", lambda d: d[(d.impl == "hybrid") & (d.block == BLOCK)])):
        r = [label]
        for b in (256, 4096):
            a = f(s)[f(s).batch == b].e2e_mean_ms.min()
            c = f(s3)[f(s3).batch == b].e2e_mean_ms.min()
            r += [num(a), num(c), num(c / a, 2)]
        rows.append(r)
    write("flags",
          ["Implementation & \\multicolumn{3}{c}{Batch 256} & \\multicolumn{3}{c}{Batch 4096} \\\\",
           "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}",
           " & native (ms) & \\texttt{-O3} (ms) & ratio & native (ms) & \\texttt{-O3} (ms) & ratio \\\\"],
          rows, "lrrrrrr")

    # ---- 7. cold start (Spartan, 10 fresh processes)
    cf = sorted(ar.RAW.glob(f"{REF}_*_cold.csv"))
    if cf:
        cd = pd.read_csv(cf[0])
        items = [("CUDA context creation", "cuda_init_ms"), ("Weight upload", "weight_upload_ms"), ("Buffer, stream and event allocation", "buffer_alloc_ms"),
                 ("Total one-time GPU set-up", "constructor_total_ms"), ("CUDA pass, 1st", "cuda_pass1_ms"), ("CUDA pass, 3rd", "cuda_pass3_ms"),
                 ("Hybrid pass, 1st", "hybrid_pass1_ms"), ("Hybrid pass, 2nd", "hybrid_pass2_ms"), ("OpenMP (24 threads) pass, 1st", "openmp_pass1_ms"),
                 ("OpenMP (24 threads) pass, 2nd", "openmp_pass2_ms"), ("Serial pass, 1st", "serial_pass1_ms"), ("Serial pass, 2nd", "serial_pass2_ms")]
        rows = []
        for label, col in items:
            v = cd[col]
            rows.append([label, num(v.mean(), 2), num(v.median(), 2), num(v.std(ddof=1), 2), num(v.min(), 2), num(v.max(), 2)])
        write("cold", ["Quantity & Mean & Median & Std. dev. & Min & Max \\\\", " & (ms) & (ms) & (ms) & (ms) & (ms) \\\\"], rows, "lrrrrr")


if __name__ == "__main__":
    main()
