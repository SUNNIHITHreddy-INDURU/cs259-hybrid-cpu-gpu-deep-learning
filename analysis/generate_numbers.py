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
        put(f"{P}:cv:p90", one(float((S.e2e_std_ms / S.e2e_mean_ms * 100).quantile(0.9))))
        ser = S[S.impl == "serial"].set_index("batch")
        GF = 2 * 203264 * 10000 / 1e9   # GFLOP in stages 1-2 of one pass of 10,000 images
        gf = lambda ms_: f"{GF / (ms_ / 1000.0):.1f}"
        for b, r in ser.iterrows():
            put(f"{P}:serial:gflops:{b}", gf(r.e2e_mean_ms))
            put(f"{P}:serial:usimg:{b}", one(r.e2e_mean_ms * 0.1))
            put(f"{P}:serial:wtraffic:{b}", one(803840 * 10000 / 1e9 / (r.e2e_mean_ms / 1000.0)))   # ms per 10,000 images -> microseconds per image
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
                put(f"{P}:{tag}:best:gflops:{b}", gf(r.e2e_mean_ms))
                put(f"{P}:{tag}:best:wtraffic:{b}", one(803840 * 10000 / 1e9 / (r.e2e_mean_ms / 1000.0)))
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
            put(f"{P}:cuda:kspeedup:{b}", two((ser.loc[b, "layer1_mean_ms"] + ser.loc[b, "layer2_mean_ms"]) / r.kernel_mean_ms))  # compute-only: serial stages 1-3 / GPU kernels
            put(f"{P}:cuda:tshare:{b}", one((r.h2d_mean_ms + r.d2h_mean_ms) / r.e2e_mean_ms * 100))
            put(f"{P}:cuda:kshare:{b}", one(r.kernel_mean_ms / r.e2e_mean_ms * 100))
            put(f"{P}:cuda:preshare:{b}", one(r.pre_mean_ms / r.e2e_mean_ms * 100))
            other = max(r.e2e_mean_ms - r.pre_mean_ms - r.h2d_mean_ms - r.kernel_mean_ms - r.d2h_mean_ms, 0)
            put(f"{P}:cuda:othershare:{b}", one(other / r.e2e_mean_ms * 100))
            put(f"{P}:cuda:tput:{b}", f"{r.throughput_img_s:,.0f}".replace(",", "{,}"))
            put(f"{P}:cuda:gflops:{b}", gf(r.e2e_mean_ms))
            nb = -(-10000 // int(b))                                   # number of batches in a pass
            put(f"{P}:cuda:kus:{b}", one(r.kernel_mean_ms * 1000.0 / nb))      # kernel microseconds per batch
            other_ms = max(r.e2e_mean_ms - r.pre_mean_ms - r.h2d_mean_ms - r.kernel_mean_ms - r.d2h_mean_ms, 0)
            put(f"{P}:cuda:otherus:{b}", one(other_ms * 1000.0 / nb))          # launch/API/sync microseconds per batch
            put(f"{P}:cuda:otherms:{b}", ms(other_ms))
            put(f"{P}:cuda:h2dgbs:{b}", f"{3136 * 10000 / 1e9 / (r.h2d_mean_ms / 1000.0):.1f}")   # 3,136 B per image
            put(f"{P}:cuda:kgflops:{b}", gf(r.kernel_mean_ms))
        for blk in sorted(S[S.impl == "cuda"].block.unique()):
            for _, r in S[(S.impl == "cuda") & (S.block == blk)].iterrows():
                put(f"{P}:cuda:blk{int(blk)}:kernel:{r.batch}", ms(r.kernel_mean_ms))
                put(f"{P}:cuda:blk{int(blk)}:e2e:{r.batch}", ms(r.e2e_mean_ms))

        # ---- worst-variance configuration: full statistics (the run is kept, nothing is removed)
        cvs = S.assign(cv=S.e2e_std_ms / S.e2e_mean_ms * 100)
        wr = cvs.loc[cvs.cv.idxmax()]
        sel_ = g[(g.impl == wr.impl) & (g.batch == wr.batch) & (g.threads == wr.threads) & (g.block == wr.block) & (g.streams == wr.streams)].e2e_ms.values
        put(f"{P}:slow:impl", {"openmp": "OpenMP", "serial": "serial", "cuda": "CUDA", "hybrid": "hybrid-pipelined", "hybrid_seq": "hybrid-sequential"}[wr.impl])
        put(f"{P}:slow:batch", str(int(wr.batch)))
        put(f"{P}:slow:threads", str(int(wr.threads)))
        put(f"{P}:slow:n", str(len(sel_)))
        put(f"{P}:slow:mean", ms(float(np.mean(sel_))))
        put(f"{P}:slow:median", ms(float(np.median(sel_))))
        put(f"{P}:slow:std", ms(float(np.std(sel_, ddof=1))))
        put(f"{P}:slow:min", ms(float(np.min(sel_))))
        put(f"{P}:slow:max", ms(float(np.max(sel_))))
        put(f"{P}:slow:count", str(int((sel_ > 1.5 * np.median(sel_)).sum())))
        put(f"{P}:slow:cv", one(float(wr.cv)))
        # ---- compute-only comparison: stages 1-3 (hidden layer, output layer, argmax); no preprocessing, no copies
        cser = S[S.impl == "serial"].set_index("batch")
        comp_serial = cser.layer1_mean_ms + cser.layer2_mean_ms
        om = S[S.impl == "openmp"].assign(comp=lambda d: d.layer1_mean_ms + d.layer2_mean_ms)
        ck = S[(S.impl == "cuda") & (S.block == BLOCK)].set_index("batch")
        for b in sorted(cser.index):
            put(f"{P}:comp:serial:{b}", ms(comp_serial[b]))
            r_ = om[om.batch == b].loc[om[om.batch == b].comp.idxmin()]
            put(f"{P}:comp:omp:{b}", ms(r_.comp)); put(f"{P}:comp:ompthr:{b}", str(int(r_.threads)))
            put(f"{P}:comp:ompspeedup:{b}", two(comp_serial[b] / r_.comp))
            if b in ck.index:
                put(f"{P}:comp:kernel:{b}", ms(ck.loc[b, "kernel_mean_ms"]))
                put(f"{P}:comp:gpuvsserial:{b}", two(comp_serial[b] / ck.loc[b, "kernel_mean_ms"]))
                put(f"{P}:comp:gpuvsomp:{b}", two(r_.comp / ck.loc[b, "kernel_mean_ms"]))
        # ---- CUDA block-size sensitivity: fixed 16x16 versus best of {8, 16, 32} (end-to-end)
        cb_ = S[S.impl == "cuda"]
        if cb_.block.nunique() > 1:
            gains = {}
            for b, dd in cb_.groupby("batch"):
                e16 = float(dd[dd.block == BLOCK].e2e_mean_ms.iloc[0]); eb = dd.loc[dd.e2e_mean_ms.idxmin()]
                gains[b] = ((e16 - eb.e2e_mean_ms) / e16 * 100, int(eb.block), eb.e2e_mean_ms)
                put(f"{P}:cuda:bestblock:e2e:{b}", ms(eb.e2e_mean_ms)); put(f"{P}:cuda:bestblock:size:{b}", str(int(eb.block)))
            bmax = max(gains, key=lambda x: gains[x][0])
            put(f"{P}:cuda:blockgain:max", one(gains[bmax][0])); put(f"{P}:cuda:blockgain:argb", str(bmax))
            cwb = [b for b in sorted(gains) if gains[b][2] < S[(S.batch == b) & S.impl.isin(["serial", "openmp"])].e2e_mean_ms.min()]
            put(f"{P}:cuda:bestblock:crossover", str(cwb[0]) if cwb else "none")

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
                h1 = hy[hy.threads == 1]
                if len(h1):
                    put(f"{P}:hyb:vscuda1:{b}", two(c.loc[b, "e2e_mean_ms"] / float(h1.e2e_mean_ms.iloc[0])))
                rh = hy.loc[hy.e2e_mean_ms.idxmin()]
                put(f"{P}:hyb:vskernel:{b}", two(rh.e2e_mean_ms / c.loc[b, "kernel_mean_ms"]))
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
        # Karp-Flatt
        kf = ar.PROC / f"karp_flatt_{plat}.csv"
        if kf.exists():
            for _, r in pd.read_csv(kf).iterrows():
                put(f"{P}:kf:{int(r.batch)}:{int(r.threads)}", f"{r.karp_flatt:.3f}")
        # significance tests
        tf = ar.PROC / f"tests_{plat}.csv"
        if tf.exists():
            tt = pd.read_csv(tf)
            for (a_, b_), gg in tt.groupby(["a", "b"]):
                tag_ = f"{a_}-{b_}".replace("hybrid_seq", "hseq").replace("hybrid", "hyb")
                put(f"{P}:test:{tag_}:maxp", sci(gg.p_value.max()))
            for _, r in tt.iterrows():
                tag = f"{r.a}-{r.b}".replace("hybrid_seq", "hseq").replace("hybrid", "hyb")
                put(f"{P}:test:{tag}:p:{int(r.batch)}", sci(r.p_value))
                put(f"{P}:test:{tag}:cilo:{int(r.batch)}", two(r.ratio_ci95_low))
                put(f"{P}:test:{tag}:cihi:{int(r.batch)}", two(r.ratio_ci95_high))
    # cross-platform / cross-build ratios of the serial baseline
    summ = {SHORT.get(p, p): ar.summarise(g) for p, g in raw.groupby("platform")}
    def sref(P, b):
        d = summ[P][(summ[P].impl == "serial") & (summ[P].batch == b)]
        return float(d.e2e_mean_ms.iloc[0])
    for b in (1, 4096):
        if "Mac" in summ and "Sp" in summ:
            put(f"X:serial:SpOverMac:{b}", one(sref("Sp", b) / sref("Mac", b)))
        if "SpO3" in summ and "Sp" in summ:
            put(f"X:serial:O3OverNative:{b}", two(sref("SpO3", b) / sref("Sp", b)))
    # cold start (10 fresh processes per platform; -1 means not measured)
    short_c = {"cuda_init_ms": "init", "weight_upload_ms": "upload", "buffer_alloc_ms": "alloc", "constructor_total_ms": "ctor",
               "cuda_pass1_ms": "cuda1", "cuda_pass2_ms": "cuda2", "cuda_pass3_ms": "cuda3", "hybrid_pass1_ms": "hyb1", "hybrid_pass2_ms": "hyb2",
               "serial_pass1_ms": "ser1", "serial_pass2_ms": "ser2", "openmp_pass1_ms": "omp1", "openmp_pass2_ms": "omp2"}
    for f in sorted(ar.RAW.glob("*_cold.csv")):
        cd = pd.read_csv(f)
        P = SHORT.get(cd.platform.iloc[0], cd.platform.iloc[0])
        put(f"{P}:cold:n", str(len(cd)))
        for col, tag in short_c.items():
            v = cd[col][cd[col] >= 0]
            if len(v):
                for st, val in (("mean", v.mean()), ("median", v.median()), ("std", v.std(ddof=1)), ("min", v.min()), ("max", v.max())):
                    put(f"{P}:cold:{tag}:{st}", f"{val:.2f}" if val < 100 else f"{val:.1f}")
        if (cd.cuda_pass1_ms >= 0).all():
            put(f"{P}:cold:ctorvspass", two(cd.constructor_total_ms.mean() / cd.cuda_pass2_ms.mean()))
            put(f"{P}:cold:hyb:firstpenalty", one((cd.hybrid_pass1_ms.mean() / cd.hybrid_pass2_ms.mean() - 1) * 100))
        put(f"{P}:cold:omp:firstpenalty", one((cd.openmp_pass1_ms.mean() / cd.openmp_pass2_ms.mean() - 1) * 100))
    put("X:weights:GB", "8.04")        # 803,840 B x 10,000 images
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
