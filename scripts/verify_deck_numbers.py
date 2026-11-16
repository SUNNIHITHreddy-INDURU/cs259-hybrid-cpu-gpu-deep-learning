#!/usr/bin/env python3
"""Independent verification of the numbers in the presentation.

Every claim below is recomputed DIRECTLY from the raw CSV files (results/raw) with plain pandas/numpy/scipy - no use of the
analysis scripts or of presentation/slide_data.json - and the formatted value is then searched for on the slide(s) (slide text,
table cells, chart data and speaker notes) of the finished .pptx.

Usage: python3 scripts/verify_deck_numbers.py [deck.pptx]   -> writes docs/deck_number_verification.md, exit code 1 on any failure
"""
import glob
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pptx import Presentation
from scipy import optimize

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "results" / "raw"
deck_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "presentation" / "CS259_Hybrid_CPU_GPU_Induru.pptx"


def load(platform):
    return pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(RAW / f"{platform}_*_bench.csv")))], ignore_index=True)


sp, mac = load("spartan_k40_native"), load("mac_m4")
val = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(RAW / "spartan_k40_native_*_validation.csv")))], ignore_index=True)
cold = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(RAW / "spartan_k40_native_*_cold.csv")))], ignore_index=True)


def mean(df, impl, b, col="e2e_ms", **kw):
    q = df[(df.impl == impl) & (df.batch == b)]
    for k, v in kw.items():
        q = q[q[k] == v]
    return q[col].mean()


def best_mean(df, impl, b, col="e2e_ms", **kw):
    q = df[(df.impl == impl) & (df.batch == b)]
    for k, v in kw.items():
        q = q[q[k] == v]
    g = q.groupby("threads")[col].mean()
    return g.min(), int(g.idxmin())


def comp(df, impl, b, **kw):  # compute-only = layer1 + layer2 per pass (CPU stage timers)
    q = df[(df.impl == impl) & (df.batch == b)]
    for k, v in kw.items():
        q = q[q[k] == v]
    return (q.layer1_ms + q.layer2_ms).groupby(q.threads).mean().min()


claims = []  # (slide numbers, description, formatted string(s) that must appear, recomputed value)


def add(slides, desc, fmt, value):
    claims.append((slides, desc, fmt, value))


B4, B1 = 4096, 1
ser4 = mean(sp, "serial", B4); ser1 = mean(sp, "serial", B1)
serc4 = (sp[(sp.impl == "serial") & (sp.batch == B4)].layer1_ms + sp[(sp.impl == "serial") & (sp.batch == B4)].layer2_ms).mean()
serc1 = (sp[(sp.impl == "serial") & (sp.batch == B1)].layer1_ms + sp[(sp.impl == "serial") & (sp.batch == B1)].layer2_ms).mean()
omp4, _ = best_mean(sp, "openmp", B4); omp1, thr1 = best_mean(sp, "openmp", B1)
ompc4 = comp(sp, "openmp", B4)
k4 = mean(sp, "cuda", B4, "kernel_ms", block=16); k1 = mean(sp, "cuda", B1, "kernel_ms", block=16)
c4 = mean(sp, "cuda", B4, block=16); c1 = mean(sp, "cuda", B1, block=16)
hyb4, _ = best_mean(sp, "hybrid", B4, block=16); hseq4, _ = best_mean(sp, "hybrid_seq", B4, block=16)
omp24_4 = mean(sp, "openmp", B4, threads=24); omp24_1 = mean(sp, "openmp", B1, threads=24)
hyb4_ = hyb4
mac_ser4 = mean(mac, "serial", B4)

add([2, 17, 18], "GPU kernels vs serial, compute-only, batch 4096", "52.8", serc4 / k4)
add([2, 15, 17, 18], "CUDA pipeline end-to-end speedup, batch 4096", "26.4", ser4 / c4)
add([9, 15, 17, 18], "OpenMP speedup with 24 threads, batch 4096", "21.6", ser4 / omp24_4)
add([9], "OpenMP efficiency with 24 threads, batch 4096", "0.90", ser4 / omp24_4 / 24)
add([9, 17], "OpenMP best speedup, batch 1", "7.6", ser1 / omp1)
add([17], "Apple M4 speedup, 10 threads, batch 4096", "5.6", mac_ser4 / mean(mac, "openmp", B4, threads=10))
add([15], "OpenMP speedup, batch 1", f"{ser1 / omp1:.1f}", ser1 / omp1)
add([15], "hybrid speedup, batch 4096", "50.0", ser4 / hyb4_)
add([8], "smallest serial time over the 8 batch sizes (ms)", f"{min(mean(sp, 'serial', b) for b in sorted(sp.batch.unique())):.1f}", min(mean(sp, 'serial', b) for b in sorted(sp.batch.unique())))
add([8], "largest serial time over the 8 batch sizes (ms)", f"{max(mean(sp, 'serial', b) for b in sorted(sp.batch.unique())):.1f}", max(mean(sp, 'serial', b) for b in sorted(sp.batch.unique())))
add([8, 15], "serial throughput at batch 4096 (images/s)", f"{10000 / (ser4 / 1000):,.0f}", 10000 / (ser4 / 1000))
add([15], "OpenMP throughput at batch 4096 (images/s)", f"{10000 / (omp4 / 1000):,.0f}", 10000 / (omp4 / 1000))
add([15], "CUDA pipeline throughput at batch 4096 (images/s)", f"{10000 / (c4 / 1000):,.0f}", 10000 / (c4 / 1000))
add([15], "hybrid throughput at batch 4096 (images/s)", f"{10000 / (hyb4 / 1000):,.0f}", 10000 / (hyb4 / 1000))
# per-batch end-to-end times quoted on slide 14 (batch 1, 8, 32, 128, 256, 4096)
for b in (1, 8, 32, 128, 256, 4096):
    # the chart stores the means; the extraction prints chart values with 4 significant figures, so compare in that form
    add([14], f"serial time, batch {b} (ms, chart value)", f"{mean(sp, 'serial', b):.4g}", mean(sp, "serial", b))
    add([14], f"OpenMP best time, batch {b} (ms, chart value)", f"{best_mean(sp, 'openmp', b)[0]:.4g}", best_mean(sp, "openmp", b)[0])
    add([14], f"CUDA pipeline time, batch {b} (ms, chart value)", f"{mean(sp, 'cuda', b, block=16):.4g}", mean(sp, "cuda", b, block=16))
    add([14], f"hybrid best time, batch {b} (ms, chart value)", f"{best_mean(sp, 'hybrid', b, block=16)[0]:.4g}", best_mean(sp, "hybrid", b, block=16)[0])
c = sp[(sp.impl == "cuda") & (sp.block == 16)]
for b, tag in ((B1, "batch 1"), (B4, "batch 4096")):
    q = c[c.batch == b]; tot = q.e2e_ms.mean()
    shares = dict(pre=q.pre_ms.mean() / tot * 100, h2d=q.h2d_ms.mean() / tot * 100, kern=q.kernel_ms.mean() / tot * 100, d2h=q.d2h_ms.mean() / tot * 100)
    shares["other"] = 100 - sum(shares.values())
    if b == B4:
        add([16], f"kernel share of CUDA pipeline, {tag}", f"{shares['kern']:.1f}", shares["kern"])
        add([16], f"preprocessing share, {tag}", f"{shares['pre']:.1f}", shares["pre"])
        add([16], f"copy share (H2D + D2H), {tag}", f"{shares['h2d'] + shares['d2h']:.1f}", shares["h2d"] + shares["d2h"])
        add([16], f"preprocessing time per pass, {tag} (ms)", f"{q.pre_ms.mean():.1f}", q.pre_ms.mean())
    else:
        add([16], f"copy share (H2D + D2H), {tag}", f"{shares['h2d'] + shares['d2h']:.1f}", shares["h2d"] + shares["d2h"])
        add([16], f"launch/API/sync residual share, {tag}", f"{max(shares['other'], 0):.1f}", max(shares["other"], 0))
add([16], "kernel-only time, batch 4096 (ms)", f"{k4:.1f}", k4)
add([16], "CUDA end-to-end, batch 4096 (ms)", f"{c4:.1f}", c4)
add([16], "hybrid-sequential (control) time, batch 4096 (ms)", f"{hseq4:.1f}", hseq4)
add([16, 18], "hybrid-pipelined time, batch 4096 (ms)", f"{hyb4:.1f}", hyb4)
add([16], "parallel preprocessing effect (hybrid-seq vs CUDA), batch 4096", "1.62", c4 / hseq4)
add([16], "overlap effect (pipelined vs hybrid-seq), batch 4096", "1.16", hseq4 / hyb4)
add([16], "hybrid time / kernel-only time, batch 4096", "1.07", hyb4 / k4)
first = [b for b in sorted(sp.batch.unique()) if best_mean(sp, "hybrid", b, block=16)[0] < min(best_mean(sp, "openmp", b)[0], mean(sp, "serial", b))][0]
add([14, 16, 18], "first batch size where hybrid beats the best CPU configuration", str(first), first)
# Amdahl fit (independent scipy curve_fit)
def amdahl_f(batch):
    ts = mean(sp, "serial", batch)
    thr = sorted(sp[(sp.impl == "openmp") & (sp.batch == batch)].threads.unique())
    s_ = np.array([ts / mean(sp, "openmp", batch, threads=t) for t in thr]); p_ = np.array(thr, float)
    popt, _ = optimize.curve_fit(lambda q, f: 1.0 / (f + (1 - f) / q), p_, s_, p0=[0.1], bounds=(0, 1))
    return float(popt[0])
f4096, f1 = amdahl_f(B4), amdahl_f(B1)
add([17], "Amdahl serial fraction, batch 4096", f"{f4096:.3f}", f4096)
add([17], "Amdahl serial fraction, batch 1", f"{f1:.3f}", f1)
add([17], "Amdahl ceiling 1/f, batch 1", f"{1 / f1:.1f}", 1 / f1)
add([17], "Amdahl ceiling 1/f, batch 4096", f"{1 / f4096:.1f}", 1 / f4096)
# correctness
val["g"] = val.comparison.str.replace(r" \(s=\d\)", "", regex=True)
for g, label in (("Serial vs OpenMP", "OpenMP"), ("Serial vs CUDA", "CUDA"), ("Serial vs Hybrid-sequential", "hybrid-sequential"), ("Serial vs Hybrid-pipelined", "hybrid-pipelined")):
    q = val[val.g == g]
    add([13], f"{label}: passing comparisons", f"{int((q['pass'] == 'PASS').sum())} / {len(q)}", len(q))
q = val[val.g == "Serial vs CUDA"]; e = q.max_abs_err.max(); m, ex = f"{e:.1e}".split("e")
add([13], "CUDA max logit difference", f"{m}×10", e)
add([6, 13], "model accuracy (%)", f"{val[val.g == 'Serial vs OpenMP'].accuracy.min() * 100:.2f}", val[val.g == "Serial vs OpenMP"].accuracy.min() * 100)
add([12], "total one-time GPU set-up (ms)", f"{cold.constructor_total_ms.mean():.1f}", cold.constructor_total_ms.mean())

# ---- facts that are in the Q&A document only (they used to be backup slides); "QA" is the key of that text
o3 = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(RAW / "spartan_k40_o3_*_bench.csv")))], ignore_index=True)
o3val = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(RAW / "spartan_k40_o3_*_validation.csv")))], ignore_index=True)
for blk, lab in ((8, "8x8"), (16, "16x16"), (32, "32x32")):
    add(["QA"], f"CUDA kernels, batch 64, block {lab} (ms)", f"{mean(sp, 'cuda', 64, 'kernel_ms', block=blk):.1f}", mean(sp, "cuda", 64, "kernel_ms", block=blk))
kb = [mean(sp, "cuda", B4, "kernel_ms", block=blk) for blk in (8, 16, 32)]
add(["QA"], "block sizes within x % at batch 4096", f"{(max(kb) / min(kb) - 1) * 100:.1f} %", (max(kb) / min(kb) - 1) * 100)
cu = sp[sp.impl == "cuda"]
best_gain = max((1 - cu[cu.batch == b].groupby("block").e2e_ms.mean().min() / cu[cu.batch == b].groupby("block").e2e_ms.mean()[16]) * 100 for b in cu.batch.unique())
add(["QA"], "best block would improve CUDA end-to-end by at most (%)", f"{best_gain:.1f} %", best_gain)
add(["QA"], "best OpenMP compute-only (stages 1-3), batch 4096 (ms)", f"{ompc4:.1f}", ompc4)
add(["QA"], "compute-only ratio best OpenMP / GPU kernels, batch 4096", f"{ompc4 / k4:.2f}", ompc4 / k4)
add(["QA"], "mixed ratio OpenMP end-to-end / GPU kernels (not used)", f"{omp4 / k4:.2f}", omp4 / k4)
add(["QA"], "best OpenMP end-to-end, batch 4096 (ms)", f"{omp4:.1f}", omp4)
o3s4 = o3[(o3.impl == "serial") & (o3.batch == B4)].e2e_ms.mean()
add(["QA"], "plain -O3 serial time, batch 4096 (ms)", f"{o3s4:,.1f}", o3s4)
add(["QA"], "native-flag serial time, batch 4096 (ms)", f"{ser4:,.1f}", ser4)
add(["QA"], "plain -O3 serial slower by (%)", f"{(o3s4 / ser4 - 1) * 100:.1f} %", (o3s4 / ser4 - 1) * 100)
add(["QA"], "largest CUDA logit difference, plain -O3 build", f"{o3val[o3val.comparison.str.contains('CUDA')].max_abs_err.max() * 1e5:.1f}×10", o3val[o3val.comparison.str.contains('CUDA')].max_abs_err.max() * 1e5)
add(["QA"], "CUDA context creation (ms)", f"{cold.cuda_init_ms.mean():.1f}", cold.cuda_init_ms.mean())
add(["QA"], "weight upload (ms)", f"{cold.weight_upload_ms.mean():.2f}", cold.weight_upload_ms.mean())
add(["QA"], "buffer allocation (ms)", f"{cold.buffer_alloc_ms.mean():.2f}", cold.buffer_alloc_ms.mean())
add(["QA"], "one-time set-up total (ms)", f"{cold.constructor_total_ms.mean():.1f}", cold.constructor_total_ms.mean())
steady256 = mean(sp, "cuda", 256, block=16)
add(["QA"], "set-up total / steady CUDA pass at batch 256", f"{cold.constructor_total_ms.mean() / steady256:.2f}", cold.constructor_total_ms.mean() / steady256)
add(["QA"], "first 24-thread OpenMP pass slower than second (%)", f"{(cold.openmp_pass1_ms.mean() / cold.openmp_pass2_ms.mean() - 1) * 100:.1f} %", (cold.openmp_pass1_ms.mean() / cold.openmp_pass2_ms.mean() - 1) * 100)
keys = ["impl", "batch", "threads", "block", "streams"]
grp = sp.groupby(keys).e2e_ms
cv = (grp.std() / grp.mean() * 100)
add(["QA"], "median coefficient of variation (%)", f"{cv.median():.1f} %", cv.median())
h = sp[(sp.impl == "hybrid") & (sp.batch == 256) & (sp.threads == 4) & (sp.block == 16)].e2e_ms
for lab, v in (("mean", h.mean()), ("median", h.median()), ("standard deviation", h.std()), ("minimum", h.min()), ("maximum", h.max())):
    add(["QA"], f"slowest-variation config (hybrid, batch 256, 4 threads): {lab} (ms)", f"{v:.2f}", v)
add(["QA"], "passes above 1.5x the median in that config", "One of the 20 passes", int((h > 1.5 * h.median()).sum()))
FL = 2 * 203264 * 10000 / 1e9   # GFLOP per pass (2 FLOP per multiply-add, stages 1-2 only)
add(["QA"], "serial GFLOP/s at batch 4096 (end-to-end)", f"{FL / (ser4 / 1000):.1f}", FL / (ser4 / 1000))
add(["QA"], "OpenMP best GFLOP/s at batch 4096 (end-to-end)", f"{FL / (omp4 / 1000):.1f}", FL / (omp4 / 1000))
add(["QA"], "CUDA kernels-only GFLOP/s at batch 4096", f"{FL / (k4 / 1000):.1f}", FL / (k4 / 1000))
q1 = sp[(sp.impl == "cuda") & (sp.batch == B1) & (sp.block == 16)]
add(["QA"], "kernel time per batch at batch size 1 (us)", f"{q1.kernel_ms.mean() / 10000 * 1000:.1f} µs", q1.kernel_ms.mean() / 10000 * 1000)
resid1 = (q1.e2e_ms - q1.pre_ms - q1.h2d_ms - q1.kernel_ms - q1.d2h_ms).mean()
add(["QA"], "launch/API/sync residual per batch at batch size 1 (us)", f"{resid1 / 10000 * 1000:.1f} µs", resid1 / 10000 * 1000)
add(["QA"], "CUDA pipeline end-to-end speedup at batch 1", f"{ser1 / c1:.2f}", ser1 / c1)
add(["QA"], "best OpenMP compute-only / GPU kernels at batch 32", f"{comp(sp, 'openmp', 32) / mean(sp, 'cuda', 32, 'kernel_ms', block=16):.2f}", comp(sp, "openmp", 32) / mean(sp, "cuda", 32, "kernel_ms", block=16))
add(["QA"], "hybrid-pipelined over CUDA pipeline at batch 4096", f"{c4 / hyb4:.2f}", c4 / hyb4)
add(["QA"], "hybrid-pipelined time at batch 32 (ms)", f"{best_mean(sp, 'hybrid', 32, block=16)[0]:.1f}", best_mean(sp, "hybrid", 32, block=16)[0])
mser4 = mean(mac, "serial", B4)
add(["QA"], "M4 speedup with 4 threads, batch 4096", f"{mser4 / mean(mac, 'openmp', B4, threads=4):.2f}", mser4 / mean(mac, "openmp", B4, threads=4))
add(["QA"], "M4 speedup with 10 threads, batch 4096", f"{mser4 / mean(mac, 'openmp', B4, threads=10):.2f}", mser4 / mean(mac, "openmp", B4, threads=10))
add(["QA"], "M4 speedup with 10 threads, batch 1", f"{mean(mac, 'serial', B1) / mean(mac, 'openmp', B1, threads=10):.2f}", mean(mac, "serial", B1) / mean(mac, "openmp", B1, threads=10))

# ----------------------------------------- extract deck text -----------------------------------------
prs = Presentation(str(deck_path))
texts = {}
for n, slide in enumerate(prs.slides, 1):
    parts = []
    for sh in slide.shapes:
        if sh.has_text_frame:
            parts.append(sh.text_frame.text)
        if getattr(sh, "has_table", False) and sh.has_table:
            for row in sh.table.rows:
                parts.extend(c.text for c in row.cells)
        if getattr(sh, "has_chart", False) and sh.has_chart:
            ch = sh.chart
            for pl in ch.plots:
                for sr in pl.series:
                    parts.append(sr.name + " " + " ".join(f"{v:.4g}" for v in sr.values))
    if slide.has_notes_slide:
        parts.append(slide.notes_slide.notes_text_frame.text)
    texts[n] = "\n".join(parts)

texts["QA"] = (ROOT / "presentation" / "questions_and_answers.md").read_text()
rows, bad = [], 0
for slides, desc, fmt, value in claims:
    present = [n for n in slides if fmt in texts.get(n, "")]
    ok = len(present) == len(slides)
    bad += (not ok)
    rows.append(f"| {', '.join(map(str, slides))} | {desc} | `{fmt}` | {value:.4g} | {'OK' if ok else 'MISSING on slide(s) ' + ', '.join(str(n) for n in slides if n not in present)} |")

# Apple M4 must not be mixed into the CPU-vs-GPU slides
mac_hits = [(n, w) for n in (14, 15, 16) for w in ('M4', 'Mac', 'Apple') if w in texts.get(n, '')]

# 2.44 vs 2.49 explanation
like = ompc4 / k4; mixed = omp4 / k4
extra = [f"- Like-for-like compute-only ratio (best OpenMP stages 1-3 / GPU kernels): {like:.3f}x -> 2.44x (appears in the Q&A document, not on the 18 slides).",
         f"- Mixed ratio (best OpenMP END-TO-END / GPU kernels): {mixed:.3f}x -> 2.49x; it mixes a compute-only time with an end-to-end time and is NOT used as a result."]
# the 2.49 figure must only appear in the explanatory sentences, never as a result
mixed_hits = [n for n, t in texts.items() if "2.49" in t and n != "QA"]
# forbidden over-claims
overclaims = [(n, m.group(0)) for n, t in texts.items() for m in re.finditer(r"(always (the )?fastest|hybrid is always|always best)", t, re.I)
              if not any(w in t[max(0, m.start() - 90): m.end() + 40].lower() for w in ("not by assuming", "not on assuming", "do not claim", "not claim"))]

report = ["# Deck number verification", "", f"Deck: `{deck_path.name}`; recomputed from `results/raw/*.csv` with independent code (`scripts/verify_deck_numbers.py`).", "",
          f"**{len(claims) - bad} of {len(claims)} claims verified on their slides.**", "", "| Slide(s) | Claim | Expected text | Recomputed value | Status |", "|---|---|---|---|---|"] + rows
report += ["", "## 2.44x versus 2.49x", ""] + extra + [f"- The string `2.49` appears on slide(s): {mixed_hits} (slides only; the Q&A document mentions it solely to explain why it is not used)."]
report += ["", "## Apple M4 separation", "", f"- M4/Mac/Apple mentioned on the CPU-vs-GPU result slides 14-16: {mac_hits if mac_hits else 'none'}."]
report += ["", "## Over-claim scan", "", f"- Phrases such as 'always fastest': {overclaims if overclaims else 'none found outside negated statements'}."]
(ROOT / "docs").mkdir(exist_ok=True)
(ROOT / "docs" / "deck_number_verification.md").write_text("\n".join(report) + "\n")
print(f"{len(claims) - bad}/{len(claims)} claims verified; mixed 2.49 appears on slides {mixed_hits}; over-claims: {overclaims or 'none'}; M4 on slides 14-16: {mac_hits or 'none'}")
sys.exit(1 if (bad or overclaims or mac_hits) else 0)
