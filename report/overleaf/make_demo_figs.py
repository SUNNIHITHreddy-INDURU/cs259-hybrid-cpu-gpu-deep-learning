#!/usr/bin/env python3
"""Generate the placeholder figures used by template_demo.tex.

Usage (from report/overleaf/):   python3 make_demo_figs.py
Writes small vector PDFs to demo_figs/.  The numbers are synthetic and only
exercise the page layout; they are not results of the study.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_figs")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.size": 7,
    "axes.titlesize": 7,
    "axes.labelsize": 7,
    "legend.fontsize": 6.5,
    "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.6,
    "lines.linewidth": 1.1,
    "pdf.fonttype": 42,
    "pdf.compression": 9,
})

C = {"serial": "#555555", "omp": "#1f77b4", "cuda": "#d62728", "hyb": "#2ca02c"}

# --- one-column figure: speedup versus threads (3.3 in wide) -------------
threads = np.array([1, 2, 4, 8, 16])
fig, ax = plt.subplots(figsize=(3.3, 2.0), constrained_layout=True)
ax.plot(threads, threads * 0.92, "o-", color=C["omp"], label="OpenMP")
ax.plot(threads, np.full_like(threads, 14.0, dtype=float), "s--",
        color=C["cuda"], label="CUDA")
ax.plot(threads, 14.0 + threads * 0.55, "^-", color=C["hyb"], label="Hybrid")
ax.set_xscale("log", base=2)
ax.set_xticks(threads)
ax.set_xticklabels([str(t) for t in threads])
ax.set_xlabel("CPU threads")
ax.set_ylabel("Speedup over serial")
ax.legend(frameon=False, loc="upper left")
fig.savefig(os.path.join(OUT, "demo_col.pdf"))
plt.close(fig)

# --- two-column wide figure: stacked time breakdown (7 in wide) ----------
labels = ["Serial", "OpenMP", "CUDA", "Hybrid"]
compute = np.array([9.1, 1.4, 0.35, 0.30])
transfer = np.array([0.0, 0.0, 0.22, 0.12])
other = np.array([0.4, 0.2, 0.10, 0.10])
fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.1), constrained_layout=True,
                         gridspec_kw={"width_ratios": [1.1, 1]})
ax = axes[0]
x = np.arange(len(labels))
ax.bar(x, compute, color=C["omp"], width=0.6, label="Compute")
ax.bar(x, transfer, bottom=compute, color=C["cuda"], width=0.6,
       label="H2D/D2H transfer")
ax.bar(x, other, bottom=compute + transfer, color="#bbbbbb", width=0.6,
       label="Other")
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel("Time per epoch (s)")
ax.legend(frameon=False)
ax = axes[1]
batch = np.array([32, 64, 128, 256, 512])
ax.plot(batch, 3200 / np.sqrt(batch) + 800, "o-", color=C["cuda"], label="CUDA")
ax.plot(batch, 3600 / np.sqrt(batch) + 900, "^-", color=C["hyb"], label="Hybrid")
ax.plot(batch, 600 + 0 * batch, "s--", color=C["omp"], label="OpenMP")
ax.set_xscale("log", base=2)
ax.set_xticks(batch)
ax.set_xticklabels([str(b) for b in batch])
ax.set_xlabel("Batch size")
ax.set_ylabel("Throughput (img/s)")
ax.legend(frameon=False)
fig.savefig(os.path.join(OUT, "demo_wide.pdf"))
plt.close(fig)
print("wrote", sorted(os.listdir(OUT)))
