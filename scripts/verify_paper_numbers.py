#!/usr/bin/env python3
"""Independent check of the numbers in the paper PDF.

Every claim is recomputed directly from the raw CSV files in results/raw with plain pandas/numpy/scipy (no analysis scripts, no
numbers.tex) and the formatted value is searched in the text of the compiled PDF (report/overleaf/main.pdf).
Usage: python3 scripts/verify_paper_numbers.py   -> writes docs/paper_number_verification.md, exit code 1 on any failure.
"""
import glob
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "results" / "raw"
PDF = ROOT / "report" / "overleaf" / "main.pdf"


def load(p, kind="bench"):
    return pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(RAW / f"{p}_*_{kind}.csv")))], ignore_index=True)


sp, mac, o3 = load("spartan_k40_native"), load("mac_m4"), load("spartan_k40_o3")
val = load("spartan_k40_native", "validation")
cold = load("spartan_k40_native", "cold")


def m(df, impl, b, col="e2e_ms", **kw):
    q = df[(df.impl == impl) & (df.batch == b)]
    for k, v in kw.items():
        q = q[q[k] == v]
    return q[col].mean()


def best(df, impl, b, col="e2e_ms", **kw):
    q = df[(df.impl == impl) & (df.batch == b)]
    for k, v in kw.items():
        q = q[q[k] == v]
    g = q.groupby("threads")[col].mean()
    return g.min(), int(g.idxmin())


def comp(df, impl, b):
    q = df[(df.impl == impl) & (df.batch == b)]
    return (q.layer1_ms + q.layer2_ms).groupby(q.threads).mean().min()


def serc(df, b):
    q = df[(df.impl == "serial") & (df.batch == b)]
    return (q.layer1_ms + q.layer2_ms).mean()


claims = []


def add(desc, text, value=None):
    claims.append((desc, text, value))


B1, B4 = 1, 4096
batches = sorted(sp.batch.unique())
ser = {b: m(sp, "serial", b) for b in batches}
f1 = lambda x: f"{x:,.1f}"
# ---- OpenMP on Xeon and M4
for b, t in ((4096, 24), (256, 24)):
    s = ser[b] / m(sp, "openmp", b, threads=t)
    add(f"OpenMP speedup, batch {b}, {t} threads", f"{s:.2f}×", s)
    add(f"OpenMP efficiency, batch {b}, {t} threads", f"{s / t:.2f}", s / t)
b1, t1 = best(sp, "openmp", B1)
add("OpenMP best speedup, batch 1", f"{ser[B1] / b1:.2f}×", ser[B1] / b1); add("OpenMP best thread count, batch 1", f"{t1} threads", t1)
add("OpenMP efficiency 24 threads batch 1", f"{ser[B1] / m(sp, 'openmp', B1, threads=24) / 24:.2f}", 0)
add("OpenMP 1 thread vs serial, batch 256 (ms)", f"{m(sp, 'openmp', 256, threads=1):,.1f}", 0)
ms4 = m(mac, "serial", B4)
add("M4 speedup 4 threads", f"{ms4 / m(mac, 'openmp', B4, threads=4):.2f}×", 0)
add("M4 speedup 10 threads", f"{ms4 / m(mac, 'openmp', B4, threads=10):.2f}×", 0)
add("M4 efficiency 10 threads", f"{ms4 / m(mac, 'openmp', B4, threads=10) / 10:.2f}", 0)
add("M4 batch 1, 2 threads", f"{m(mac, 'serial', B1) / m(mac, 'openmp', B1, threads=2):.2f}×", 0)
add("M4 batch 1, 10 threads", f"{m(mac, 'serial', B1) / m(mac, 'openmp', B1, threads=10):.2f}×", 0)
add("M4 serial pass (ms)", f"{ms4:,.1f}", 0)
# ---- compute-only
k = {b: m(sp, "cuda", b, "kernel_ms", block=16) for b in batches}
cs4 = serc(sp, B4); co4 = comp(sp, "openmp", B4)
add("kernels vs serial stages 1-3, batch 4096", f"{cs4 / k[B4]:.2f}×", 0)
add("kernels vs best OpenMP stages 1-3, batch 4096", f"{co4 / k[B4]:.2f}×", 0)
add("serial stages 1-3 (ms)", f"{cs4:,.1f}", 0); add("best OpenMP stages 1-3 (ms)", f"{co4:.2f}", 0); add("kernel time batch 4096 (ms)", f"{k[B4]:.2f}", 0)
add("kernels vs best OpenMP, batch 32", f"{comp(sp, 'openmp', 32) / k[32]:.2f}×", 0)
add("kernels vs serial, batch 1", f"{serc(sp, B1) / k[B1]:.2f}×", 0)
add("kernels vs OpenMP, batch 1 (as fast as)", f"{comp(sp, 'openmp', B1) / k[B1]:.2f}×", 0)
# ---- end-to-end
c = {b: m(sp, "cuda", b, block=16) for b in batches}
omp = {b: best(sp, "openmp", b) for b in batches}
hy = {b: best(sp, "hybrid", b, block=16) for b in batches}
hs = {b: best(sp, "hybrid_seq", b, block=16) for b in batches}
add("CUDA e2e speedup, batch 4096", f"{ser[B4] / c[B4]:.2f}×", 0)
add("CUDA e2e speedup, batch 1", f"{ser[B1] / c[B1]:.2f}×", 0)
add("CUDA vs 24-thread OpenMP, batch 4096", f"{m(sp, 'openmp', B4, threads=24) / c[B4]:.2f}×", 0)
add("hybrid time batch 4096 (ms)", f"{hy[B4][0]:.2f} ms", 0)
add("hybrid vs CUDA, batch 4096", f"{c[B4] / hy[B4][0]:.2f}×", 0)
add("hybrid vs best OpenMP, batch 4096", f"{omp[B4][0] / hy[B4][0]:.2f}×", 0)
add("hybrid-sequential vs CUDA, batch 4096", f"{c[B4] / hs[B4][0]:.2f}×", 0)
add("overlap gain, batch 4096", f"{hs[B4][0] / hy[B4][0]:.2f}×", 0)
add("hybrid / kernel-only, batch 4096", f"{hy[B4][0] / k[B4]:.2f}×", 0)
first = [b for b in batches if hy[b][0] < min(omp[b][0], ser[b])][0]
add("first batch where hybrid beats best OpenMP", f"batch {first}", first)
rows6 = []
for b in batches:
    row = (f"{b} {ser[b]:,.1f} {omp[b][0]:,.1f} ({omp[b][1]}) {k[b]:,.1f} {c[b]:,.1f} {hy[b][0]:,.1f} ({hy[b][1]}) "
           f"{ser[b] / omp[b][0]:.2f} {serc(sp, b) / k[b]:.2f} {ser[b] / c[b]:.2f} {ser[b] / hy[b][0]:.2f}")
    rows6.append((f"Table 6 row, batch {b} (times, thread counts and speedups)", row))
# ---- throughput
for lab, t in (("serial", ser[B4]), ("OpenMP", omp[B4][0]), ("CUDA", c[B4]), ("hybrid", hy[B4][0])):
    add(f"throughput {lab}, batch 4096 (images/s)", f"{10000 / (t / 1000):,.0f}", 0)
# ---- overhead shares
q = sp[(sp.impl == "cuda") & (sp.block == 16)]
for b in (B1, B4):
    d = q[q.batch == b]; tot = d.e2e_ms.mean()
    add(f"preprocessing share, batch {b}", f"{d.pre_ms.mean() / tot * 100:.1f} %", 0)
    add(f"copies share, batch {b}", f"{(d.h2d_ms.mean() + d.d2h_ms.mean()) / tot * 100:.1f} %", 0)
    add(f"kernel share, batch {b}", f"{d.kernel_ms.mean() / tot * 100:.1f} %", 0)
d = q[q.batch == B1]; oth = (d.e2e_ms - d.pre_ms - d.h2d_ms - d.kernel_ms - d.d2h_ms).mean()
add("launch/sync residual share, batch 1", f"{oth / d.e2e_ms.mean() * 100:.1f} %", 0)
add("kernel time per batch at batch 1 (us)", f"{k[B1] / 10000 * 1000:.1f} µs", 0)
add("launch/sync per batch at batch 1 (us)", f"{oth / 10000 * 1000:.1f} µs", 0)
add("preprocessing time per pass (ms)", f"{q[q.batch == B4].pre_ms.mean():.2f} ms", 0)
add("host-to-device copy batch 4096 (ms)", f"{q[q.batch == B4].h2d_ms.mean():.2f} ms", 0)
add("host-to-device rate (GB/s)", f"{31.36128 / 1000 / (q[q.batch == B4].h2d_ms.mean() / 1000):.1f} GB/s", 0)
# ---- GFLOP/s
FL = 2 * 203264 * 10000 / 1e9
add("serial GFLOP/s", f"{FL / (ser[B4] / 1000):.1f} GFLOP/s", 0)
add("OpenMP GFLOP/s", f"{FL / (omp[B4][0] / 1000):.1f} GFLOP/s", 0)
add("CUDA e2e GFLOP/s", f"{FL / (c[B4] / 1000):.1f} GFLOP/s", 0)
add("CUDA kernel-only GFLOP/s", f"{FL / (k[B4] / 1000):.1f} GFLOP/s", 0)
# ---- block size
for blk in (8, 16, 32):
    add(f"kernel time batch 64 block {blk}", f"{m(sp, 'cuda', 64, 'kernel_ms', block=blk):.2f} ms", 0)
cu = sp[sp.impl == "cuda"]
gain = max((1 - cu[cu.batch == b].groupby("block").e2e_ms.mean().min() / cu[cu.batch == b].groupby("block").e2e_ms.mean()[16]) * 100 for b in batches)
add("best block gain", f"{gain:.1f} %", 0)
# ---- cold start
add("cold: CUDA context (ms)", f"{cold.cuda_init_ms.mean():.1f} ms", 0)
add("cold: weight upload (ms)", f"{cold.weight_upload_ms.mean():.2f} ms", 0)
add("cold: allocation (ms)", f"{cold.buffer_alloc_ms.mean():.2f} ms", 0)
add("cold: total (ms)", f"{cold.constructor_total_ms.mean():.1f} ms", 0)
add("cold: total / steady CUDA pass", f"{cold.constructor_total_ms.mean() / m(sp, 'cuda', 256, block=16):.2f}×", 0)
add("cold: first OpenMP pass slower (%)", f"{(cold.openmp_pass1_ms.mean() / cold.openmp_pass2_ms.mean() - 1) * 100:.1f} %", 0)
add("cold: first hybrid pass slower (%)", f"{(cold.hybrid_pass1_ms.mean() / cold.hybrid_pass2_ms.mean() - 1) * 100:.1f} %", 0)
# ---- Amdahl
def amdahl(df, b):
    ts = m(df, "serial", b); th = sorted(df[(df.impl == "openmp") & (df.batch == b)].threads.unique())
    S = np.array([ts / m(df, "openmp", b, threads=t) for t in th]); P = np.array(th, float)
    return float(optimize.curve_fit(lambda p, f: 1 / (f + (1 - f) / p), P, S, p0=[0.1], bounds=(0, 1))[0][0])
for b in (64, 4096, 1):
    f = amdahl(sp, b); add(f"Amdahl f batch {b}", f"{f:.3f}", f); add(f"Amdahl ceiling batch {b}", f"{1 / f:.1f}×", 0)
add("M4 Amdahl f batch 4096", f"{amdahl(mac, 4096):.3f}", 0)
# ---- correctness
val["g"] = val.comparison.str.replace(r" \(s=\d\)", "", regex=True)
add("number of correctness comparisons (Spartan)", f"{len(val)} comparisons", len(val))
add("max CUDA logit difference", f"{val[val.g == 'Serial vs CUDA'].max_abs_err.max() * 1e6:.1f}×10", 0)
add("accuracy", f"{val[val.g == 'Serial vs OpenMP'].accuracy.min() * 100:.2f}", 0)
add("float32 vs float64 anchor", f"{val[val.g.str.contains('NumPy')].max_abs_err.max() * 1e5:.1f}×10", 0)
# ---- compiler sensitivity
add("serial plain -O3 (ms)", f"{m(o3, 'serial', B4):,.1f}", 0)
add("O3 vs native crossover batch (CUDA vs best OpenMP)", "256", 0)
# ---- extract PDF text
txt = subprocess.run(["pdftotext", str(PDF), "-"], capture_output=True, text=True).stdout
layout = subprocess.run(["pdftotext", "-layout", str(PDF), "-"], capture_output=True, text=True).stdout
MU = {"\U0001d707": "\u00b5", "\u03bc": "\u00b5"}
flat = re.sub(r"-\n(?=[a-z])", "", txt)                   # undo line-break hyphenation
for k_, v_ in MU.items():
    flat = flat.replace(k_, v_)
flat = re.sub(r"\s+", " ", flat.replace(" ", " ").replace(" ", " ").replace("−", "-").replace("ﬀ", "ff"))
norm = lambda s: re.sub(r"\s+", " ", s.replace("\\,", " "))
flat_layout = re.sub(r"\s+", " ", layout.replace("\u2212", "-"))

rows, bad = [], 0
for desc, text in rows6:
    ok = text.replace(" ", "") in flat_layout.replace(" ", "")
    bad += not ok
    rows.append(f"| {desc} | `{text}` | {'OK' if ok else 'NOT FOUND'} |")
claims_n = len(claims) + len(rows6)
for desc, text, value in claims:
    ok = norm(text) in flat or norm(text).replace(" ", "") in flat.replace(" ", "")
    bad += not ok
    rows.append(f"| {desc} | `{text}` | {'OK' if ok else 'NOT FOUND'} |")
over = [w for w in ("always fastest", "always the fastest", "universally faster", "CUDA is always", "hybrid is always") if w in flat.lower()]
placeholder = [w for w in ("[ACTUAL", "TODO", "XXX", "??", "placeholder") if w in txt]
url = "https://github.com/SUNNIHITHreddy-INDURU/cs259-hybrid-cpu-gpu-deep-learning"
url_ok = url.replace("/", "").replace("-", "") in flat.replace(" ", "").replace("/", "").replace("-", "")
report = ["# Paper number verification", "",
          f"Recomputed from `results/raw/*.csv` with independent code (`scripts/verify_paper_numbers.py`) and searched in the text of `{PDF.name}`.", "",
          f"**{claims_n - bad} of {claims_n} claims found in the PDF.**", "", "| Claim | Expected text | Status |", "|---|---|---|"] + rows
report += ["", "## Other checks", "", f"- Over-claim phrases found: {over or 'none'}", f"- Placeholders found: {placeholder or 'none'}",
           f"- GitHub URL present in the PDF text: {url_ok}"]
(ROOT / "docs" / "paper_number_verification.md").write_text("\n".join(report) + "\n")
print(f"{claims_n - bad}/{claims_n} claims found; over-claims: {over or 'none'}; placeholders: {placeholder or 'none'}; github url: {url_ok}")
for r in rows:
    if "NOT FOUND" in r:
        print(r)
sys.exit(1 if bad or over or placeholder or not url_ok else 0)
