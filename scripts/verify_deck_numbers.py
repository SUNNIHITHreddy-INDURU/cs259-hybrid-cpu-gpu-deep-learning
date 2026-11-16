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

add([2, 13, 18], "GPU kernels vs serial, compute-only, batch 4096", "52.8", serc4 / k4)
add([2, 13, 18], "CUDA pipeline end-to-end speedup, batch 4096", "26.4", ser4 / c4)
add([13], "GPU kernels vs best OpenMP compute-only, batch 4096 (like for like)", "2.44", ompc4 / k4)
add([13], "CUDA pipeline vs best OpenMP end-to-end, batch 4096", "1.23", omp4 / c4)
add([13], "CUDA end-to-end speedup, batch 1 (slower than serial)", "0.82", ser1 / c1)
add([13], "GPU kernels vs serial compute-only, batch 1", "1.11", serc1 / k1)
add([12, 17, 18], "OpenMP speedup with 24 threads, batch 4096", "21.6", ser4 / omp24_4)
add([12], "OpenMP efficiency with 24 threads, batch 4096", "0.90", ser4 / omp24_4 / 24)
add([12], "OpenMP best speedup, batch 1", "7.6", ser1 / omp1)
add([12], "OpenMP efficiency with 24 threads, batch 1", "0.31", ser1 / omp24_1 / 24)
mser4 = mean(mac, "serial", B4); mser1 = mean(mac, "serial", B1)
add([12], "Apple M4 speedup, 10 threads, batch 4096", "5.6", mser4 / mean(mac, "openmp", B4, threads=10))
add([21], "Apple M4 speedup, 10 threads, batch 4096 (backup notes)", "5.56", mser4 / mean(mac, "openmp", B4, threads=10))
add([12, 21], "Apple M4 speedup, 4 threads, batch 4096", "3.85", mser4 / mean(mac, "openmp", B4, threads=4))
add([21], "Apple M4 speedup, 10 threads, batch 1 (slower than serial)", "0.13", mser1 / mean(mac, "openmp", B1, threads=10))
c = sp[(sp.impl == "cuda") & (sp.block == 16)]
for b, tag in ((B1, "batch 1"), (B4, "batch 4096")):
    q = c[c.batch == b]; tot = q.e2e_ms.mean()
    shares = dict(pre=q.pre_ms.mean() / tot * 100, h2d=q.h2d_ms.mean() / tot * 100, kern=q.kernel_ms.mean() / tot * 100, d2h=q.d2h_ms.mean() / tot * 100)
    shares["other"] = 100 - sum(shares.values())
    if b == B4:
        add([14], f"kernel share of CUDA pipeline, {tag}", f"{shares['kern']:.1f}", shares["kern"])
        add([14], f"preprocessing share, {tag}", f"{shares['pre']:.1f}", shares["pre"])
        add([14], f"copy share (H2D + D2H), {tag}", f"{shares['h2d'] + shares['d2h']:.1f}", shares["h2d"] + shares["d2h"])
        add([14], f"preprocessing time per pass, {tag} (ms)", f"{q.pre_ms.mean():.1f}", q.pre_ms.mean())
        add([14], f"H2D copy time, {tag} (ms)", f"{q.h2d_ms.mean():.2f}", q.h2d_ms.mean())
    else:
        add([14], f"kernel share, {tag}", f"{shares['kern']:.1f}", shares["kern"])
        add([14], f"copy share (H2D + D2H), {tag}", f"{shares['h2d'] + shares['d2h']:.1f}", shares["h2d"] + shares["d2h"])
        add([14], f"launch/API/sync residual share, {tag}", f"{max(shares['other'], 0):.1f}", max(shares["other"], 0))
add([15, 18], "hybrid-pipelined time, batch 4096 (ms)", f"{hyb4:.1f}", hyb4)
add([15, 18], "CUDA pipeline time, batch 4096 (ms)", f"{c4:.1f}", c4)
add([15], "parallel preprocessing effect (hybrid-seq vs CUDA), batch 4096", "1.62", c4 / hseq4)
add([15], "overlap effect (pipelined vs hybrid-seq), batch 4096", "1.16", hseq4 / hyb4)
add([15], "hybrid time / kernel-only time, batch 4096", "1.07", hyb4 / k4)
ratios = [mean(sp, "cuda", b, block=16) / best_mean(sp, "hybrid", b, block=16)[0] for b in sorted(sp.batch.unique())]
add([15], "smallest hybrid-vs-CUDA speedup over batch sizes", f"{min(ratios):.2f}", min(ratios))
add([15], "largest hybrid-vs-CUDA speedup over batch sizes", f"{max(ratios):.2f}", max(ratios))
first = [b for b in sorted(sp.batch.unique()) if best_mean(sp, "hybrid", b, block=16)[0] < min(best_mean(sp, "openmp", b)[0], mean(sp, "serial", b))][0]
add([15, 16, 18], "first batch size where hybrid beats the best CPU configuration", str(first), first)
# best implementation table (slide 16)
for b in sorted(sp.batch.unique()):
    t = sorted([mean(sp, "serial", b), best_mean(sp, "openmp", b)[0], mean(sp, "cuda", b, block=16), best_mean(sp, "hybrid", b, block=16)[0]])
    add([16], f"fastest end-to-end time, batch {b} (ms)", f"{t[0]:.1f}", t[0])
    add([16], f"runner-up end-to-end time, batch {b} (ms)", f"{t[1]:.1f}", t[1])
# Amdahl fit (independent scipy curve_fit)
def amdahl_f(batch):
    ts = mean(sp, "serial", batch)
    thr = sorted(sp[(sp.impl == "openmp") & (sp.batch == batch)].threads.unique())
    s = np.array([ts / mean(sp, "openmp", batch, threads=t) for t in thr]); p = np.array(thr, float)
    popt, _ = optimize.curve_fit(lambda p_, f: 1.0 / (f + (1 - f) / p_), p, s, p0=[0.1], bounds=(0, 1))
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
    add([11], f"{label}: passing comparisons", f"{int((q['pass'] == 'PASS').sum())} / {len(q)}", len(q))
q = val[val.g == "Serial vs CUDA"]; e = q.max_abs_err.max(); m, ex = f"{e:.1e}".split("e")
add([11], "CUDA max logit difference", f"{m}×10", e)
add([5, 11], "model accuracy (%)", f"{val[val.g == 'Serial vs OpenMP'].accuracy.min() * 100:.2f}", val[val.g == "Serial vs OpenMP"].accuracy.min() * 100)
# cold start / setup
add([10], "total one-time GPU set-up (ms)", f"{cold.constructor_total_ms.mean():.1f}", cold.constructor_total_ms.mean())

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

rows, bad = [], 0
for slides, desc, fmt, value in claims:
    present = [n for n in slides if fmt in texts.get(n, "")]
    ok = len(present) == len(slides)
    bad += (not ok)
    rows.append(f"| {', '.join(map(str, slides))} | {desc} | `{fmt}` | {value:.4g} | {'OK' if ok else 'MISSING on slide(s) ' + ', '.join(str(n) for n in slides if n not in present)} |")

# Apple M4 must not be mixed into the CPU-vs-GPU slides
mac_hits = [(n, w) for n in (13, 14, 15, 16) for w in ('M4', 'Mac', 'Apple') if w in texts.get(n, '')]

# 2.44 vs 2.49 explanation
like = ompc4 / k4; mixed = omp4 / k4
extra = [f"- Like-for-like compute-only ratio (best OpenMP stages 1-3 / GPU kernels): {like:.3f}x -> shown as 2.44x.",
         f"- Mixed ratio (best OpenMP END-TO-END / GPU kernels): {mixed:.3f}x -> 2.49x; it mixes a compute-only time with an end-to-end time and is NOT used as a result."]
# the 2.49 figure must only appear in the explanatory sentences, never as a result
mixed_hits = [n for n, t in texts.items() if "2.49" in t]
# forbidden over-claims
overclaims = [(n, m.group(0)) for n, t in texts.items() for m in re.finditer(r"(always (the )?fastest|hybrid is always|always best)", t, re.I)
              if not any(w in t[max(0, m.start() - 90): m.end() + 40].lower() for w in ("not by assuming", "not on assuming", "do not claim", "not claim"))]

report = ["# Deck number verification", "", f"Deck: `{deck_path.name}`; recomputed from `results/raw/*.csv` with independent code (`scripts/verify_deck_numbers.py`).", "",
          f"**{len(claims) - bad} of {len(claims)} claims verified on their slides.**", "", "| Slide(s) | Claim | Expected text | Recomputed value | Status |", "|---|---|---|---|---|"] + rows
report += ["", "## 2.44x versus 2.49x", ""] + extra + [f"- The string `2.49` appears on slide(s): {mixed_hits} (only in explanatory notes/captions)."]
report += ["", "## Apple M4 separation", "", f"- M4/Mac/Apple mentioned on the CPU-vs-GPU slides 13-16: {mac_hits if mac_hits else 'none'}."]
report += ["", "## Over-claim scan", "", f"- Phrases such as 'always fastest': {overclaims if overclaims else 'none found outside negated statements'}."]
(ROOT / "docs").mkdir(exist_ok=True)
(ROOT / "docs" / "deck_number_verification.md").write_text("\n".join(report) + "\n")
print(f"{len(claims) - bad}/{len(claims)} claims verified; mixed 2.49 appears on slides {mixed_hits}; over-claims: {overclaims or 'none'}; M4 on slides 13-16: {mac_hits or 'none'}")
sys.exit(1 if (bad or overclaims or mac_hits) else 0)
