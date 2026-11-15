#!/usr/bin/env python3
"""Write every number quoted in the paper's prose as a LaTeX value, straight from the measurements.

Output: report/overleaf/numbers.tex  (+ results/processed/numbers.csv for lookup)
In the paper:  \\val{Mac:serial:e2e:4096}  expands to the measured mean (a string such as 138.7).
A key that does not exist makes LaTeX fail, so a number can never silently be invented.

Key scheme   <platform>:<what>:<metric>:<batch>[:<threads>]
  platform   Mac | Sp (Spartan K40, -march=native) | SpO3 (Spartan K40, plain -O3)
  what       serial | omp | cuda | hseq (hybrid sequential) | hyb (hybrid pipelined)
             omp / hseq / hyb also have  best  (lowest mean over thread counts), e.g. Mac:omp:best:speedup:4096
  metric     e2e (ms), speedup, eff, thr (threads of the best configuration), kernel, h2d, d2h, pre, tshare (%),
             tput (images/s), ci (95 % CI half-width, ms), accuracy (%)
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_results as ar

ROOT = ar.ROOT
OUT_TEX = Path(os.environ.get("CS259_NUMBERS", ROOT / "report" / "overleaf" / "numbers.tex"))
SHORT = {"mac_m4": "Mac", "spartan_k40_native": "Sp", "spartan_k40_o3": "SpO3"}
BLOCK = 16


def ms(x):
    return f"{x:,.1f}".replace(",", "{,}") if x >= 100 else f"{x:.2f}"


def two(x):
    return f"{x:.2f}"


def one(x):
    return f"{x:.1f}"


def sci(x):
    if x == 0:
        return "0"
    m, e = f"{x:.1e}".split("e")
    return f"\\ensuremath{{{m}\\times10^{{{int(e)}}}}}"


def main():
    raw = ar.load_bench()
    vals = {}

    def put(key, text):
        vals[key] = text

    for plat, g in raw.groupby("platform"):
        P = SHORT.get(plat, plat)
        S = ar.summarise(g)
        put(f"{P}:cpu", str(g.cpu_model.iloc[0]))
        put(f"{P}:gpu", str(g.gpu_model.iloc[0]))
        put(f"{P}:cpuThreads", str(int(g.cpu_logical_threads.iloc[0])))
        put(f"{P}:compiler", str(g.compiler.iloc[0]))
        put(f"{P}:cudaRuntime", str(g.cuda_runtime.iloc[0]))
        put(f"{P}:runs", str(int(S.n_runs.min())))
        put(f"{P}:accuracy", f"{S.accuracy_min.min() * 100:.2f}")
        put(f"{P}:cv:median", one(float((S.e2e_std_ms / S.e2e_mean_ms * 100).median())))
        put(f"{P}:cv:max", one(float((S.e2e_std_ms / S.e2e_mean_ms * 100).max())))
        ser = S[S.impl == "serial"].set_index("batch")
        for b, r in ser.iterrows():
            put(f"{P}:serial:e2e:{b}", ms(r.e2e_mean_ms))
            put(f"{P}:serial:tput:{b}", f"{r.throughput_img_s:,.0f}".replace(",", "{,}"))
            put(f"{P}:serial:pre:{b}", ms(r.pre_mean_ms))
            put(f"{P}:serial:l1:{b}", ms(r.layer1_mean_ms))
            put(f"{P}:serial:l2:{b}", ms(r.layer2_mean_ms))
            put(f"{P}:serial:l1share:{b}", one(r.layer1_mean_ms / (r.pre_mean_ms + r.layer1_mean_ms + r.layer2_mean_ms) * 100))
            put(f"{P}:serial:preshare:{b}", one(r.pre_mean_ms / (r.pre_mean_ms + r.layer1_mean_ms + r.layer2_mean_ms) * 100))
        for impl, tag in (("openmp", "omp"), ("hybrid_seq", "hseq"), ("hybrid", "hyb")):
            d = S[S.impl == impl]
            if d.empty:
                continue
            for _, r in d.iterrows():
                key = f"{P}:{tag}"
                put(f"{key}:e2e:{r.batch}:{r.threads}", ms(r.e2e_mean_ms))
                put(f"{key}:speedup:{r.batch}:{r.threads}", two(r.speedup_vs_serial))
                if impl == "openmp":
                    put(f"{key}:eff:{r.batch}:{r.threads}", two(r.efficiency))
            for b, dd in d.groupby("batch"):
                r = dd.loc[dd.e2e_mean_ms.idxmin()]
                put(f"{P}:{tag}:best:e2e:{b}", ms(r.e2e_mean_ms))
                put(f"{P}:{tag}:best:thr:{b}", str(int(r.threads)))
                put(f"{P}:{tag}:best:speedup:{b}", two(r.speedup_vs_serial))
                put(f"{P}:{tag}:best:tput:{b}", f"{r.throughput_img_s:,.0f}".replace(",", "{,}"))
                if impl == "openmp":
                    put(f"{P}:{tag}:best:eff:{b}", two(r.efficiency))
        # OpenMP at 1 thread vs serial: runtime overhead
        # CUDA
        c = S[(S.impl == "cuda") & (S.block == BLOCK)].set_index("batch")
        for b, r in c.iterrows():
            put(f"{P}:cuda:e2e:{b}", ms(r.e2e_mean_ms))
            put(f"{P}:cuda:ci:{b}", two(r.e2e_ci95_ms))
            put(f"{P}:cuda:kernel:{b}", ms(r.kernel_mean_ms))
            put(f"{P}:cuda:h2d:{b}", ms(r.h2d_mean_ms))
            put(f"{P}:cuda:d2h:{b}", ms(r.d2h_mean_ms))
            put(f"{P}:cuda:pre:{b}", ms(r.pre_mean_ms))
            put(f"{P}:cuda:speedup:{b}", two(r.speedup_vs_serial))
            put(f"{P}:cuda:kspeedup:{b}", two(ser.loc[b, "e2e_mean_ms"] / r.kernel_mean_ms))
            put(f"{P}:cuda:tshare:{b}", one((r.h2d_mean_ms + r.d2h_mean_ms) / r.e2e_mean_ms * 100))
            put(f"{P}:cuda:kshare:{b}", one(r.kernel_mean_ms / r.e2e_mean_ms * 100))
            put(f"{P}:cuda:preshare:{b}", one(r.pre_mean_ms / r.e2e_mean_ms * 100))
            other = max(r.e2e_mean_ms - r.pre_mean_ms - r.h2d_mean_ms - r.kernel_mean_ms - r.d2h_mean_ms, 0)
            put(f"{P}:cuda:othershare:{b}", one(other / r.e2e_mean_ms * 100))
            put(f"{P}:cuda:tput:{b}", f"{r.throughput_img_s:,.0f}".replace(",", "{,}"))
        for blk in sorted(S[S.impl == "cuda"].block.unique()):
            for _, r in S[(S.impl == "cuda") & (S.block == blk)].iterrows():
                put(f"{P}:cuda:blk{int(blk)}:kernel:{r.batch}", ms(r.kernel_mean_ms))
                put(f"{P}:cuda:blk{int(blk)}:e2e:{r.batch}", ms(r.e2e_mean_ms))
        # comparisons between implementations at each batch size
        for b in sorted(S.batch.unique()):
            best_cpu = S[(S.batch == b) & S.impl.isin(["serial", "openmp"])]
            if len(best_cpu):
                r = best_cpu.loc[best_cpu.e2e_mean_ms.idxmin()]
                put(f"{P}:cpubest:e2e:{b}", ms(r.e2e_mean_ms))
                put(f"{P}:cpubest:impl:{b}", "OpenMP" if r.impl == "openmp" else "serial")
            if b in c.index and len(best_cpu):
                put(f"{P}:cuda:vscpu:{b}", two(r.e2e_mean_ms / c.loc[b, "e2e_mean_ms"]))
            hs = S[(S.impl == "hybrid_seq") & (S.batch == b) & (S.block == BLOCK)]
            hy = S[(S.impl == "hybrid") & (S.batch == b) & (S.block == BLOCK)]
            if len(hy) and b in c.index:
                rh = hy.loc[hy.e2e_mean_ms.idxmin()]
                put(f"{P}:hyb:vscuda:{b}", two(c.loc[b, "e2e_mean_ms"] / rh.e2e_mean_ms))
                put(f"{P}:hyb:best:ci:{b}", two(rh.e2e_ci95_ms))
                if len(best_cpu):
                    put(f"{P}:hyb:vscpu:{b}", two(r.e2e_mean_ms / rh.e2e_mean_ms))
                put(f"{P}:hyb:best:pre:{b}", ms(rh.pre_mean_ms))
                put(f"{P}:hyb:best:h2d:{b}", ms(rh.h2d_mean_ms))
                put(f"{P}:hyb:best:kernel:{b}", ms(rh.kernel_mean_ms))
                put(f"{P}:hyb:best:d2h:{b}", ms(rh.d2h_mean_ms))
                gsum = rh.pre_mean_ms + rh.h2d_mean_ms + rh.kernel_mean_ms + rh.d2h_mean_ms
                put(f"{P}:hyb:overlap:{b}", two(gsum / rh.e2e_mean_ms))
            if len(hs) and b in c.index:
                rs = hs.loc[hs.e2e_mean_ms.idxmin()]
                put(f"{P}:hseq:vscuda:{b}", two(c.loc[b, "e2e_mean_ms"] / rs.e2e_mean_ms))
                if len(hy):
                    put(f"{P}:hyb:vshseq:{b}", two(rs.e2e_mean_ms / rh.e2e_mean_ms))
        # crossover: smallest batch at which CUDA beats the best CPU configuration
        cw = [b for b in sorted(c.index) if (c.loc[b, "e2e_mean_ms"] < S[(S.batch == b) & S.impl.isin(["serial", "openmp"])].e2e_mean_ms.min())]
        if len(c):
            put(f"{P}:cuda:crossover", str(cw[0]) if cw else "none")
        hw_ = [b for b in sorted(S[S.impl == "hybrid"].batch.unique()) if (S[(S.impl == "hybrid") & (S.batch == b)].e2e_mean_ms.min() < S[(S.batch == b) & S.impl.isin(["serial", "openmp"])].e2e_mean_ms.min())]
        if (S.impl == "hybrid").any():
            put(f"{P}:hyb:crossover", str(hw_[0]) if hw_ else "none")
        # Amdahl
        af = ar.PROC / f"amdahl_{plat}.csv"
        if af.exists():
            for _, r in pd.read_csv(af).iterrows():
                put(f"{P}:amdahl:f:{int(r.batch)}", f"{r.serial_fraction:.3f}")
                put(f"{P}:amdahl:ceil:{int(r.batch)}", one(r.ceiling_speedup) if r.serial_fraction > 0.001 else "inf")
                put(f"{P}:amdahl:r2:{int(r.batch)}", f"{r.r_squared:.2f}")
        # significance tests
        tf = ar.PROC / f"tests_{plat}.csv"
        if tf.exists():
            for _, r in pd.read_csv(tf).iterrows():
                tag = f"{r.a}-{r.b}".replace("hybrid_seq", "hseq").replace("hybrid", "hyb")
                put(f"{P}:test:{tag}:p:{int(r.batch)}", sci(r.p_value))
                put(f"{P}:test:{tag}:cilo:{int(r.batch)}", two(r.ratio_ci95_low))
                put(f"{P}:test:{tag}:cihi:{int(r.batch)}", two(r.ratio_ci95_high))
    # micro-benchmarks
    for f in sorted(ar.RAW.glob("*_micro.csv")):
        m = pd.read_csv(f)
        P = SHORT.get(m.platform.iloc[0], m.platform.iloc[0])
        for _, r in m.iterrows():
            key = f"{P}:micro:{r.metric}:{int(r.threads)}"
            put(key, f"{r.value:.2f}" if r.value < 100 else f"{r.value:.1f}")
    # correctness
    for f in sorted(ar.RAW.glob("*_validation.csv")):
        v = pd.read_csv(f)
        P = SHORT.get(v.platform.iloc[0].replace("_smoke", ""), v.platform.iloc[0])
        v["grp"] = v.comparison.str.replace(r" \(s=\d\)", "", regex=True)
        tags = {"Serial float32 vs NumPy float64": "numpy", "Serial batch-invariance": "batch", "Serial vs OpenMP": "omp",
                "Serial vs CUDA": "cuda", "Serial vs Hybrid-sequential": "hseq", "Serial vs Hybrid-pipelined": "hyb"}
        for grp, g in v.groupby("grp"):
            t = tags.get(grp)
            if t:
                put(f"{P}:val:{t}:maxerr", sci(g.max_abs_err.max()))
                put(f"{P}:val:{t}:meanerr", sci(g.mean_abs_err.max()))
                put(f"{P}:val:{t}:agree", f"{g.pred_agreement.min() * 100:.2f}")
                put(f"{P}:val:{t}:n", str(len(g)))
        put(f"{P}:val:total", str(len(v)))
        put(f"{P}:val:passed", str(int((v["pass"] == "PASS").sum())))

    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)
    lines = ["% Generated by analysis/generate_numbers.py from results/raw -- do not edit by hand.",
             "\\providecommand{\\val}[1]{\\csname v:#1\\endcsname}"]
    for k in sorted(vals):
        lines.append(f"\\expandafter\\gdef\\csname v:{k}\\endcsname{{{vals[k]}}}")
    OUT_TEX.write_text("\n".join(lines) + "\n")
    ar.PROC.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(sorted(vals.items()), columns=["key", "value"]).to_csv(ar.PROC / "numbers.csv", index=False)
    print(f"wrote {len(vals)} values -> {OUT_TEX}")


if __name__ == "__main__":
    main()
