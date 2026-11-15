#!/usr/bin/env python3
"""Generate every figure from the measured results (results/raw -> results/figures).

Each data figure is drawn from the CSV files only. Two variants are written per figure:
  results/figures/paper/<name>_<platform>.{pdf,png}   final column width, no title (caption in the paper)
  results/figures/slides/<name>_<platform>.png        large fonts, with title
Figures that need data an platform does not have (e.g. CUDA on the Mac) are skipped.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

import analyze_results as ar
from style import COLOR, LABEL, LSTYLE, MARKER, STYLES, log2_axis, pn

DEFAULT_BLOCK = 16


# ---------------------------------------------------------------------------------- data helpers
def sel(S, impl, **kw):
    d = S[S.impl == impl]
    for k, v in kw.items():
        d = d[d[k] == v]
    return d.sort_values("batch")


def best_by_batch(S, impl, **kw):
    """For every batch size the configuration with the lowest mean end-to-end time."""
    d = sel(S, impl, **kw)
    if d.empty:
        return d
    return d.loc[d.groupby("batch").e2e_mean_ms.idxmin()].sort_values("batch")


def has(S, *impls):
    return all((S.impl == i).any() for i in impls)


def line(ax, d, impl, y="e2e_mean_ms", err="e2e_ci95_ms", label=None, **kw):
    ax.errorbar(d.batch, d[y], yerr=d[err] if err else None, color=COLOR[impl], marker=MARKER[impl],
                linestyle=LSTYLE[impl], capsize=1.5, label=label or LABEL[impl], **kw)


# ---------------------------------------------------------------------------------- figures 3,10
def fig_exec_time(st, S, plat):
    if not has(S, "serial", "openmp"):
        return
    fig, ax = st.figure(aspect=0.78)
    line(ax, sel(S, "serial"), "serial")
    line(ax, best_by_batch(S, "openmp"), "openmp", label="OpenMP CPU (best thread count)")
    if has(S, "cuda"):
        line(ax, sel(S, "cuda", block=DEFAULT_BLOCK), "cuda")
    if has(S, "hybrid"):
        line(ax, best_by_batch(S, "hybrid", block=DEFAULT_BLOCK), "hybrid", label="Hybrid, pipelined (best threads)")
    ax.set_yscale("log")
    log2_axis(ax, S.batch.unique())
    ax.set_xlabel("Batch size (images per batch)")
    ax.set_ylabel("End-to-end time for 10,000 images (ms)")
    ax.legend(loc="best")
    st.save(fig, f"exec_time_{plat}", f"Execution time vs batch size ({pn(plat)})")


def fig_throughput(st, S, plat):
    if not has(S, "serial"):
        return
    fig, ax = st.figure(aspect=0.78)
    for impl, d in (("serial", sel(S, "serial")), ("openmp", best_by_batch(S, "openmp")),
                    ("cuda", sel(S, "cuda", block=DEFAULT_BLOCK)),
                    ("hybrid", best_by_batch(S, "hybrid", block=DEFAULT_BLOCK))):
        if len(d):
            ax.plot(d.batch, d.throughput_img_s, color=COLOR[impl], marker=MARKER[impl], linestyle=LSTYLE[impl], label=LABEL[impl])
    ax.set_yscale("log")
    log2_axis(ax, S.batch.unique())
    ax.set_xlabel("Batch size (images per batch)")
    ax.set_ylabel("Throughput (images / s)")
    ax.legend(loc="best")
    st.save(fig, f"throughput_{plat}", f"Throughput vs batch size ({pn(plat)})")


# ---------------------------------------------------------------------------------- figures 4,5,6,13
def _omp_batches(S):
    all_b = sorted(S[S.impl == "openmp"].batch.unique())
    want = [1, 32, 256, 1024, 4096]
    return [b for b in want if b in all_b] or all_b[:5]


def _p_core_marker(ax, S):
    if "M4" in str(S.cpu_model.iloc[0]):
        ax.axvline(4, color=COLOR["other"], linestyle=":", linewidth=0.9)
        ax.text(4, ax.get_ylim()[1], " 4 performance\n cores", va="top", ha="left", fontsize=plt.rcParams["font.size"] - 1.5, color=COLOR["ink"])


def fig_omp_scaling(st, S, plat):
    if not has(S, "openmp"):
        return
    batches = _omp_batches(S)
    cmap = plt.get_cmap("Blues")
    shades = [cmap(0.35 + 0.65 * i / max(1, len(batches) - 1)) for i in range(len(batches))]
    mk = ["o", "s", "^", "D", "v"]
    threads = sorted(S[S.impl == "openmp"].threads.unique())
    for kind in ("time", "speedup", "efficiency"):
        fig, ax = st.figure(aspect=0.78)
        for i, b in enumerate(batches):
            d = S[(S.impl == "openmp") & (S.batch == b)].sort_values("threads")
            y = {"time": d.e2e_mean_ms, "speedup": d.speedup_vs_serial, "efficiency": d.efficiency}[kind]
            ax.plot(d.threads, y, color=shades[i], marker=mk[i % 5], label=f"batch {b}")
        if kind == "speedup":
            ax.plot(threads, threads, color=COLOR["serial"], linestyle="--", linewidth=0.9, label="ideal (linear)")
            ax.axhline(1, color=COLOR["other"], linewidth=0.6)
        if kind == "efficiency":
            ax.axhline(1, color=COLOR["serial"], linestyle="--", linewidth=0.9, label="ideal (1.0)")
        if kind == "time":
            ax.set_yscale("log")
        log2_axis(ax, threads)
        ax.set_xlabel("OpenMP threads")
        ax.set_ylabel({"time": "End-to-end time for 10,000 images (ms)", "speedup": "Speedup over serial (x)",
                       "efficiency": "Parallel efficiency (speedup / threads)"}[kind])
        _p_core_marker(ax, S)
        ax.legend(loc="best", ncol=1)
        st.save(fig, f"omp_{kind}_{plat}", {"time": "OpenMP execution time vs threads", "speedup": "OpenMP speedup vs threads",
                                           "efficiency": "OpenMP efficiency vs threads"}[kind] + f" ({pn(plat)})")


def fig_amdahl(st, S, plat):
    path = ar.PROC / f"amdahl_{plat}.csv"
    if not has(S, "openmp") or not path.exists():
        return
    fits = pd.read_csv(path)
    from statistical_analysis import amdahl
    batches = _omp_batches(S)
    cmap = plt.get_cmap("Blues")
    fig, ax = st.figure(aspect=0.78)
    threads = np.array(sorted(S[S.impl == "openmp"].threads.unique()), float)
    grid = np.linspace(threads.min(), threads.max(), 100)
    for i, b in enumerate(batches):
        c = cmap(0.35 + 0.65 * i / max(1, len(batches) - 1))
        d = S[(S.impl == "openmp") & (S.batch == b)].sort_values("threads")
        f = float(fits[fits.batch == b].serial_fraction.iloc[0])
        ax.plot(d.threads, d.speedup_vs_serial, color=c, marker="o", linestyle="none")
        ax.plot(grid, amdahl(grid, f), color=c, linewidth=0.9, label=f"batch {b}: f = {f:.3f}")
    ax.plot(threads, threads, color=COLOR["serial"], linestyle="--", linewidth=0.9, label="ideal")
    log2_axis(ax, threads)
    ax.set_xlabel("OpenMP threads")
    ax.set_ylabel("Speedup over serial (x)")
    ax.legend(loc="upper left")
    st.save(fig, f"amdahl_fit_{plat}", f"Measured speedup and fitted Amdahl curves ({pn(plat)})")


# ---------------------------------------------------------------------------------- figures 7,8,9,12
def fig_kernel_vs_e2e(st, S, plat):
    if not has(S, "cuda", "serial"):
        return
    c = sel(S, "cuda", block=DEFAULT_BLOCK)
    s = sel(S, "serial").set_index("batch")
    x = np.arange(len(c))
    fig, (a, b) = st.figure(wide=True, aspect=0.36, ncols=2)
    w = 0.38
    a.bar(x - w / 2, c.kernel_mean_ms, w, color=COLOR["cuda"], label="Kernel only (CUDA events)")
    a.bar(x + w / 2, c.e2e_mean_ms, w, color=COLOR["cuda"], hatch="////", edgecolor="white", label="End-to-end (wall clock)")
    a.set_yscale("log")
    a.set_xticks(x)
    a.set_xticklabels(c.batch.astype(int))
    a.set_xlabel("Batch size")
    a.set_ylabel("Time for 10,000 images (ms)")
    a.legend(loc="upper right")
    ks = s.loc[c.batch, "e2e_mean_ms"].values / c.kernel_mean_ms.values
    es = s.loc[c.batch, "e2e_mean_ms"].values / c.e2e_mean_ms.values
    b.plot(x, ks, color=COLOR["cuda"], marker="^", label="Kernel-only speedup over serial")
    b.plot(x, es, color=COLOR["cuda"], marker="^", linestyle="--", markerfacecolor="white", label="End-to-end speedup over serial")
    b.axhline(1, color=COLOR["serial"], linewidth=0.8)
    b.set_yscale("log")
    b.set_xticks(x)
    b.set_xticklabels(c.batch.astype(int))
    b.set_xlabel("Batch size")
    b.set_ylabel("Speedup over serial CPU (x)")
    b.set_ylim(top=b.get_ylim()[1] * 3)
    b.legend(loc="upper left")
    st.save(fig, f"cuda_kernel_vs_e2e_{plat}", f"CUDA: kernel-only vs end-to-end ({pn(plat)})")


def fig_transfer(st, S, plat):
    if not has(S, "cuda"):
        return
    c = sel(S, "cuda", block=DEFAULT_BLOCK)
    parts = [("pre_mean_ms", "Preprocessing (CPU)", COLOR["openmp"], None),
             ("h2d_mean_ms", "Host-to-device copy", COLOR["transfer"], None),
             ("kernel_mean_ms", "Kernels (GPU)", COLOR["cuda"], None),
             ("d2h_mean_ms", "Device-to-host copy", COLOR["transfer2"], "////")]
    total = c.e2e_mean_ms.values
    acc = np.zeros(len(c))
    other = np.clip(total - sum(c[k].values for k, *_ in parts), 0, None)
    fig, ax = st.figure(aspect=0.85)
    x = np.arange(len(c))
    for key, lab, col, hatch in parts + [("other", "Launch / API / sync overhead", COLOR["other"], None)]:
        v = (other if key == "other" else c[key].values) / total * 100
        ax.bar(x, v, 0.72, bottom=acc, color=col, hatch=hatch, edgecolor="white", linewidth=0.6, label=lab)
        acc += v
    ax.set_xticks(x)
    ax.set_xticklabels(c.batch.astype(int))
    ax.set_ylim(0, 100)
    ax.set_xlabel("Batch size")
    ax.set_ylabel("Share of end-to-end time (%)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2)
    st.save(fig, f"transfer_breakdown_{plat}", f"CUDA time breakdown by stage ({pn(plat)})")


def fig_hybrid(st, S, plat):
    if not has(S, "cuda", "hybrid"):
        return
    fig, (a, b) = st.figure(wide=True, aspect=0.36, ncols=2)
    line(a, best_by_batch(S, "openmp"), "openmp", label="OpenMP-only (best threads)")
    line(a, sel(S, "cuda", block=DEFAULT_BLOCK), "cuda", label="CUDA-only")
    if has(S, "hybrid_seq"):
        line(a, best_by_batch(S, "hybrid_seq", block=DEFAULT_BLOCK), "hybrid_seq", label="Hybrid, sequential (best threads)")
    line(a, best_by_batch(S, "hybrid", block=DEFAULT_BLOCK), "hybrid", label="Hybrid, pipelined (best threads)")
    a.set_yscale("log")
    log2_axis(a, S.batch.unique())
    a.set_xlabel("Batch size")
    a.set_ylabel("End-to-end time for 10,000 images (ms)")
    a.set_ylim(top=a.get_ylim()[1] * 4)
    a.legend(loc="upper right")
    base = sel(S, "cuda", block=DEFAULT_BLOCK).set_index("batch").e2e_mean_ms
    for impl, off in (("hybrid_seq", -0.2), ("hybrid", 0.2)):
        d = best_by_batch(S, impl, block=DEFAULT_BLOCK)
        if d.empty:
            continue
        xs = np.arange(len(d))
        b.bar(xs + off, base.loc[d.batch].values / d.e2e_mean_ms.values, 0.38, color=COLOR[impl],
              label=LABEL[impl] + " vs CUDA-only")
    b.axhline(1, color=COLOR["serial"], linewidth=0.9, linestyle="--")
    b.set_xticks(np.arange(len(base)))
    b.set_xticklabels(base.index.astype(int))
    b.set_xlabel("Batch size")
    b.set_ylabel("Speedup over CUDA-only (x)")
    b.set_ylim(0, b.get_ylim()[1] * 1.3)
    b.legend(loc="upper left", ncol=1)
    st.save(fig, f"hybrid_compare_{plat}", f"Hybrid vs non-hybrid execution ({pn(plat)})")


def fig_blocksize(st, S, plat):
    c = S[S.impl == "cuda"]
    if c.block.nunique() < 2:
        return
    fig, ax = st.figure(aspect=0.78)
    shades = {8: "#86EFAC", 16: COLOR["cuda"], 32: "#14532D"}
    marks = {8: "o", 16: "^", 32: "s"}
    for blk, d in c.groupby("block"):
        d = d.sort_values("batch")
        ax.plot(d.batch, d.kernel_mean_ms, color=shades.get(blk, COLOR["cuda"]), marker=marks.get(blk, "o"), label=f"{blk} x {blk} threads")
    ax.set_yscale("log")
    log2_axis(ax, c.batch.unique())
    ax.set_xlabel("Batch size")
    ax.set_ylabel("Kernel time for 10,000 images (ms)")
    ax.legend(title="Hidden-layer block", loc="best")
    st.save(fig, f"cuda_block_size_{plat}", f"CUDA thread-block size (kernel time, {plat})")


# ---------------------------------------------------------------------------------- figure 11
def fig_correctness(st, plat_label="all"):
    files = [f for f in sorted(ar.RAW.glob("*_validation.csv")) if ("mac_m4" in f.name or "spartan_k40_native" in f.name or "FAKE" in f.name)]
    if not files:
        return
    v = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    v["group"] = v.comparison.str.replace(r" \(s=\d\)", "", regex=True)
    order = ["Serial float32 vs NumPy float64", "Serial batch-invariance", "Serial vs OpenMP", "Serial vs CUDA",
             "Serial vs Hybrid-sequential", "Serial vs Hybrid-pipelined"]
    g = v.groupby("group").agg(max_err=("max_abs_err", "max"), n=("pass", "size")).reindex([o for o in order if o in set(v.group)])
    fig, ax = st.figure(aspect=0.78)
    y = np.arange(len(g))[::-1]
    cols = {"Serial float32 vs NumPy float64": COLOR["serial"], "Serial batch-invariance": COLOR["serial"], "Serial vs OpenMP": COLOR["openmp"],
            "Serial vs CUDA": COLOR["cuda"], "Serial vs Hybrid-sequential": COLOR["hybrid_seq"], "Serial vs Hybrid-pipelined": COLOR["hybrid"]}
    ax.barh(y, g.max_err.values, 0.6, color=[cols[i] for i in g.index])
    ax.set_xscale("symlog", linthresh=1e-9)
    ax.axvline(1e-4, color=COLOR["transfer"], linestyle="--", linewidth=1)
    ax.text(1e-4, y.max() + 0.55, " tolerance 1e-4", color=COLOR["transfer"], fontsize=plt.rcParams["font.size"] - 1, va="bottom")
    for yi, (name, r) in zip(y, g.iterrows()):
        ax.text(max(r.max_err, 1e-9) * 1.6 if r.max_err > 0 else 2e-9, yi, "0 (bit-identical)" if r.max_err == 0 else f"{r.max_err:.1e}",
                va="center", fontsize=plt.rcParams["font.size"] - 1, color=COLOR["ink"])
    ax.set_yticks(y)
    ax.set_yticklabels([f"{n}\n({int(c)} comparisons)" for n, c in zip(g.index, g.n)], fontsize=plt.rcParams["font.size"] - 1.5)
    ax.set_xlim(0, 1e-2)
    ax.set_xlabel("Worst-case max |logit difference|")
    st.save(fig, f"correctness_{plat_label}", "Correctness: maximum logit difference vs reference")


# ---------------------------------------------------------------------------------- figures 1,2 (diagrams)
def _box(ax, x, y, w, h, text, fc, tc="white", fs=None, hatch=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.015", fc=fc, ec="white", lw=1, hatch=hatch))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc, fontsize=fs or plt.rcParams["font.size"] - 0.5, linespacing=1.15)


def _arrow(ax, x0, y0, x1, y1):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=7, color=COLOR["ink"], lw=0.8))


def fig_architecture(st):
    fig, ax = st.figure(wide=True, aspect=0.44)
    ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.grid(False)
    lanes = [
        ("Serial CPU", [("Preprocess\n(1 thread)", COLOR["serial"]), ("Hidden layer\n784→256, ReLU", COLOR["serial"]), ("Output layer\n256→10 + argmax", COLOR["serial"])]),
        ("OpenMP CPU", [("Preprocess\n(T threads)", COLOR["openmp"]), ("Hidden layer\n(image, block)", COLOR["openmp"]), ("Output layer\n+ argmax", COLOR["openmp"])]),
        ("CUDA GPU", [("Preprocess\n(1 CPU thread)", COLOR["serial"]), ("H2D copy", COLOR["transfer"]), ("Kernels:\nhidden, output,\nargmax", COLOR["cuda"]), ("D2H copy", COLOR["transfer"])]),
        ("Hybrid\nOpenMP + CUDA", [("Preprocess\n(T threads,\npinned buf.)", COLOR["openmp"]), ("H2D copy\n(async)", COLOR["transfer"]), ("Kernels\n(streams)", COLOR["cuda"]), ("D2H copy\n(async)", COLOR["transfer"])]),
    ]
    h, gap = 0.17, 0.045
    for i, (name, boxes) in enumerate(lanes):
        y = 0.97 - (i + 1) * (h + gap) + gap
        ax.text(0.0, y + h / 2, name, ha="left", va="center", fontsize=plt.rcParams["font.size"] + 0.5, fontweight="bold", color=COLOR["ink"])
        n = len(boxes); x0, bw = 0.17, 0.14
        for j, (t, c) in enumerate(boxes):
            x = x0 + j * (bw + 0.03)
            _box(ax, x, y, bw, h, t, c)
            if j:
                _arrow(ax, x - 0.03, y + h / 2, x, y + h / 2)
        xe = x0 + n * (bw + 0.03) - 0.03
        _box(ax, 0.85, y + 0.03, 0.14, h - 0.06, "predicted\ndigits", "#E5E7EB", tc=COLOR["ink"])
        _arrow(ax, xe, y + h / 2, 0.85, y + h / 2)
    ax.text(0.83, 0.08, "Hybrid: preprocessing of batch i+1 overlaps with\ncopy + kernels of batch i (software pipeline)", fontsize=plt.rcParams["font.size"] - 1, color=COLOR["hybrid"], ha="center", va="center")
    handles = [Rectangle((0, 0), 1, 1, fc=COLOR[k]) for k in ("serial", "openmp", "cuda", "transfer")]
    ax.legend(handles, ["CPU, one thread", "CPU, OpenMP threads", "GPU, CUDA threads", "PCIe transfer"], loc="lower left", ncol=4, bbox_to_anchor=(0.0, -0.02))
    st.save(fig, "architecture", "Project execution architecture: four implementations of the same workload")


def fig_network(st):
    fig, ax = st.figure(wide=True, aspect=0.22)
    ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.grid(False)
    items = [("Raw image\n28×28 uint8\n(784 bytes)", "#E5E7EB", COLOR["ink"]), ("Per-image\nstandardisation\n(preprocess)", COLOR["openmp"], "white"),
             ("Input\n784 float32", COLOR["serial"], "white"), ("Hidden\n256 units\nW1: 784×256\nReLU", COLOR["cuda"], "white"),
             ("Output\n10 logits\nW2: 256×10", COLOR["cuda"], "white"), ("argmax\n→ digit 0-9", COLOR["hybrid"], "white")]
    n = len(items); bw = 0.13; gap = (1 - n * bw) / (n - 1)
    for i, (t, c, tc) in enumerate(items):
        x = i * (bw + gap)
        _box(ax, x, 0.22, bw, 0.76, t, c, tc=tc, fs=plt.rcParams["font.size"])
        if i:
            _arrow(ax, x - gap, 0.60, x, 0.60)
    ax.text(0.5, 0.04, "203,530 parameters  |  203,264 multiply-accumulates (406,528 floating-point operations) per image  |  float32",
            ha="center", fontsize=plt.rcParams["font.size"] - 0.5, color=COLOR["ink"])
    st.save(fig, "network_architecture", "Workload: MNIST MLP 784 → 256 → ReLU → 10")



# ---------------------------------------------------------------------------------- composites (two platforms)
def _plat_label(S):
    cpu = str(S.cpu_model.iloc[0]).replace("Intel(R) Xeon(R) CPU ", "Xeon ").replace("(R)", "").replace("(TM)", "")
    cpu = cpu.split(" @")[0]
    return f"{cpu}, up to {int(S[S.impl == 'openmp'].threads.max())} threads"


def fig_omp_combined(st, summaries, plats):
    plats = [p for p in plats if p in summaries and has(summaries[p], "openmp")]
    if not plats:
        return
    cmap = plt.get_cmap("Blues")
    fig, axes = st.figure(wide=True, aspect=0.50 if len(plats) > 1 else 0.40, nrows=2, ncols=len(plats), squeeze=False)
    for j, plat in enumerate(plats):
        S = summaries[plat]
        batches = [b for b in (1, 64, 256, 4096) if b in set(S[S.impl == "openmp"].batch)]
        threads = sorted(S[S.impl == "openmp"].threads.unique())
        for i, b in enumerate(batches):
            c = cmap(0.35 + 0.65 * i / max(1, len(batches) - 1))
            d = S[(S.impl == "openmp") & (S.batch == b)].sort_values("threads")
            axes[0][j].plot(d.threads, d.speedup_vs_serial, color=c, marker="osD^"[i % 4], label=f"batch {b}")
            axes[1][j].plot(d.threads, d.efficiency, color=c, marker="osD^"[i % 4], label=f"batch {b}")
        axes[0][j].plot(threads, threads, color=COLOR["serial"], linestyle="--", linewidth=0.9, label="ideal")
        axes[0][j].axhline(1, color=COLOR["other"], linewidth=0.6)
        axes[1][j].axhline(1, color=COLOR["serial"], linestyle="--", linewidth=0.9)
        for r in (0, 1):
            log2_axis(axes[r][j], threads)
            if "M4" in str(S.cpu_model.iloc[0]):
                axes[r][j].axvline(4, color=COLOR["other"], linestyle=":", linewidth=0.9)
        axes[0][j].set_title(_plat_label(S), fontsize=plt.rcParams["font.size"] - 0.5)
        axes[1][j].set_xlabel("OpenMP threads")
        axes[0][j].set_ylabel("Speedup over serial (x)")
        axes[1][j].set_ylabel("Efficiency")
    axes[0][0].legend(loc="upper left", fontsize=plt.rcParams["font.size"] - 1.5)
    st.save(fig, "omp_combined", "OpenMP speedup and efficiency")


def fig_amdahl_combined(st, summaries, plats):
    from statistical_analysis import amdahl
    plats = [p for p in plats if p in summaries and has(summaries[p], "openmp") and (ar.PROC / f"amdahl_{p}.csv").exists()]
    if not plats:
        return
    cmap = plt.get_cmap("Blues")
    fig, axes = st.figure(wide=True, aspect=0.36, ncols=len(plats), squeeze=False)
    for j, plat in enumerate(plats):
        S, ax = summaries[plat], axes[0][j]
        fits = pd.read_csv(ar.PROC / f"amdahl_{plat}.csv")
        threads = np.array(sorted(S[S.impl == "openmp"].threads.unique()), float)
        grid = np.linspace(threads.min(), threads.max(), 100)
        batches = [b for b in (8, 64, 256, 4096) if b in set(fits.batch)]
        for i, b in enumerate(batches):
            c = cmap(0.35 + 0.65 * i / max(1, len(batches) - 1))
            d = S[(S.impl == "openmp") & (S.batch == b)].sort_values("threads")
            f = float(fits[fits.batch == b].serial_fraction.iloc[0])
            ax.plot(d.threads, d.speedup_vs_serial, color=c, marker="o", linestyle="none")
            ax.plot(grid, amdahl(grid, f), color=c, linewidth=0.9, label=f"batch {b}: f = {f:.3f}")
        ax.plot(threads, threads, color=COLOR["serial"], linestyle="--", linewidth=0.9, label="ideal")
        log2_axis(ax, threads)
        ax.set_title(_plat_label(S), fontsize=plt.rcParams["font.size"] - 0.5)
        ax.set_xlabel("OpenMP threads")
        ax.set_ylabel("Speedup over serial (x)")
        ax.legend(loc="upper left", fontsize=plt.rcParams["font.size"] - 1.5)
    st.save(fig, "amdahl_combined", "Measured speedup and fitted Amdahl curves")


# ---------------------------------------------------------------------------------- main
def main():
    raw = ar.load_bench()
    summaries = {p: ar.summarise(g) for p, g in raw.groupby("platform")}
    for st in STYLES:
        st.apply()
        fig_architecture(st)
        fig_network(st)
        fig_correctness(st)
        main_plats = [p for p in ('mac_m4', 'spartan_k40_native') if p in summaries]
        fig_omp_combined(st, summaries, main_plats)
        fig_amdahl_combined(st, summaries, main_plats)
        for plat, S in summaries.items():
            fig_exec_time(st, S, plat)
            fig_throughput(st, S, plat)
            fig_omp_scaling(st, S, plat)
            fig_amdahl(st, S, plat)
            fig_kernel_vs_e2e(st, S, plat)
            fig_transfer(st, S, plat)
            fig_hybrid(st, S, plat)
            fig_blocksize(st, S, plat)


if __name__ == "__main__":
    sys.exit(main())
