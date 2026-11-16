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
        line(ax, best_by_batch(S, "hybrid", block=DEFAULT_BLOCK), "hybrid", label="Hybrid-pipelined (best threads)")
    ax.set_yscale("log")
    log2_axis(ax, S.batch.unique())
    ax.set_xlabel("Batch size (images per batch)")
    ax.set_ylabel("End-to-end time for 10,000 images (ms)")
    ax.legend(loc="best")
    st.save(fig, f"exec_time_{plat}", f"Execution time vs batch size, {pn(plat)}")


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
    st.save(fig, f"throughput_{plat}", f"Throughput vs batch size, {pn(plat)}")


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
                                           "efficiency": "OpenMP efficiency vs threads"}[kind] + f", {pn(plat)}")


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
    st.save(fig, f"amdahl_fit_{plat}", f"Measured speedup and fitted Amdahl curves, {pn(plat)}")


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
    ks = (s.loc[c.batch, "layer1_mean_ms"].values + s.loc[c.batch, "layer2_mean_ms"].values) / c.kernel_mean_ms.values  # compute-only: serial stages 1-3 / GPU kernels
    es = s.loc[c.batch, "e2e_mean_ms"].values / c.e2e_mean_ms.values
    b.plot(x, ks, color=COLOR["cuda"], marker="^", label="Kernel-only vs serial stages 1-3 (compute-only)")
    b.plot(x, es, color=COLOR["cuda"], marker="^", linestyle="--", markerfacecolor="white", label="CUDA end-to-end vs serial end-to-end")
    b.axhline(1, color=COLOR["serial"], linewidth=0.8)
    b.set_yscale("log")
    b.set_xticks(x)
    b.set_xticklabels(c.batch.astype(int))
    b.set_xlabel("Batch size")
    b.set_ylabel("Speedup over serial CPU (x)")
    b.set_ylim(top=b.get_ylim()[1] * 3)
    b.legend(loc="upper left")
    st.save(fig, f"cuda_kernel_vs_e2e_{plat}", f"CUDA: kernel-only vs end-to-end, {pn(plat)}")


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
    st.save(fig, f"transfer_breakdown_{plat}", f"CUDA time breakdown by stage, {pn(plat)}")


def fig_hybrid(st, S, plat):
    if not has(S, "cuda", "hybrid"):
        return
    fig, (a, b) = st.figure(wide=True, aspect=0.36, ncols=2)
    line(a, best_by_batch(S, "openmp"), "openmp", label="OpenMP (best thread count)")
    line(a, sel(S, "cuda", block=DEFAULT_BLOCK), "cuda", label="CUDA (1-thread preprocessing)")
    if has(S, "hybrid_seq"):
        line(a, best_by_batch(S, "hybrid_seq", block=DEFAULT_BLOCK), "hybrid_seq", label="Hybrid-sequential control (best threads)")
    line(a, best_by_batch(S, "hybrid", block=DEFAULT_BLOCK), "hybrid", label="Hybrid-pipelined (best threads)")
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
              label=LABEL[impl] + " vs CUDA")
    b.axhline(1, color=COLOR["serial"], linewidth=0.9, linestyle="--")
    b.set_xticks(np.arange(len(base)))
    b.set_xticklabels(base.index.astype(int))
    b.set_xlabel("Batch size")
    b.set_ylabel("Speedup over CUDA (x)")
    b.set_ylim(0, b.get_ylim()[1] * 1.3)
    b.legend(loc="upper left", ncol=1)
    st.save(fig, f"hybrid_compare_{plat}", f"Hybrid vs non-hybrid execution, {pn(plat)}")


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
    st.save(fig, f"cuda_block_size_{plat}", f"CUDA thread-block size (kernel time), {pn(plat)}")


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


def _lane_label(ax, y, h, text):
    ax.text(0.0, y + h / 2, text, ha="left", va="center", fontsize=plt.rcParams["font.size"] + 0.5, fontweight="bold", color=COLOR["ink"])


def fig_architecture(st):
    """Figure: the four implementations, with OpenMP threads, copies, kernels, the three CUDA streams and the batch overlap."""
    fig, ax = st.figure(wide=True, aspect=0.50)
    ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.grid(False)
    fs = plt.rcParams["font.size"] - 1
    x0, bw, gp = 0.17, 0.135, 0.03

    def chain(y, h, boxes, label):
        _lane_label(ax, y, h, label)
        for j, (t, c) in enumerate(boxes):
            x = x0 + j * (bw + gp)
            _box(ax, x, y, bw, h, t, c, fs=fs)
            if j:
                _arrow(ax, x - gp, y + h / 2, x, y + h / 2)
        xe = x0 + len(boxes) * (bw + gp) - gp
        _box(ax, 0.885, y + 0.15 * h, 0.105, 0.7 * h, "predicted\ndigits", "#E5E7EB", tc=COLOR["ink"], fs=fs)
        _arrow(ax, xe, y + h / 2, 0.885, y + h / 2)

    h = 0.10
    chain(0.89, h, [("Preprocess\n(1 thread)", COLOR["serial"]), ("Hidden layer\n784\u2192256, ReLU", COLOR["serial"]),
                     ("Output layer\n256\u219210", COLOR["serial"]), ("argmax", COLOR["serial"])], "Serial CPU")
    chain(0.76, h, [("Preprocess\n(T OpenMP threads)", COLOR["openmp"]), ("Hidden layer\n(parallel for)", COLOR["openmp"]),
                     ("Output layer\n(parallel for)", COLOR["openmp"]), ("argmax\n(parallel for)", COLOR["openmp"])], "OpenMP CPU")
    chain(0.63, h, [("Preprocess\n(1 CPU thread)", COLOR["serial"]), ("H2D copy\n(pageable)", COLOR["transfer"]),
                     ("Kernels: hidden,\noutput, argmax", COLOR["cuda"]), ("D2H copy", COLOR["transfer"])], "CUDA (1-thread\npreprocessing)")
    # hybrid lane: OpenMP preprocessing of batch i+1, then three CUDA streams carrying batches i, i-1, i-2
    yb, ht = 0.07, 0.47
    _lane_label(ax, yb, ht, "Hybrid\nOpenMP + CUDA")
    _box(ax, x0, yb + 0.17, bw, 0.13, "Preprocess batch i+1\n(T OpenMP threads,\npinned buffer)", COLOR["openmp"], fs=fs)
    rx0, rw = 0.355, 0.50
    ax.add_patch(Rectangle((rx0, yb - 0.045), rw, ht + 0.01, fc="none", ec=COLOR["hybrid"], lw=0.9, ls="--"))
    ax.text(rx0 + rw / 2, yb + ht - 0.03, "three CUDA streams: batch i uses stream (i mod 3) and its own buffers",
            ha="center", va="bottom", fontsize=fs, color=COLOR["hybrid"])
    sh = 0.115
    for k in range(3):
        y = yb + 0.30 - k * (sh + 0.045)
        ax.text(rx0 + 0.01, y + sh / 2, f"stream {k}", ha="left", va="center", fontsize=fs, color=COLOR["ink"])
        for j, (t, c) in enumerate((("H2D async", COLOR["transfer"]), ("kernels", COLOR["cuda"]), ("D2H async", COLOR["transfer"]))):
            x = rx0 + 0.095 + j * 0.135
            _box(ax, x, y, 0.115, sh, t, c, fs=fs)
            if j:
                _arrow(ax, x - 0.02, y + sh / 2, x, y + sh / 2)
    _arrow(ax, x0 + bw, yb + 0.235, rx0, yb + 0.235)
    _box(ax, 0.885, yb + 0.235 - 0.07, 0.105, 0.14, "predicted\ndigits", "#E5E7EB", tc=COLOR["ink"], fs=fs)
    _arrow(ax, rx0 + rw, yb + 0.235, 0.885, yb + 0.235)
    ax.text(x0 + bw / 2, yb + 0.06, "overlap: while the GPU copies and\ncomputes batch i, the CPU\npreprocesses batch i+1", ha="center", va="center",
            fontsize=fs, color=COLOR["hybrid"])
    handles = [Rectangle((0, 0), 1, 1, fc=COLOR[k]) for k in ("serial", "openmp", "cuda", "transfer")]
    ax.legend(handles, ["CPU, one thread", "CPU, OpenMP threads", "GPU, CUDA kernels", "PCIe copy"], loc="lower center", ncol=4,
              bbox_to_anchor=(0.5, -0.095))
    st.save(fig, "architecture", "Project execution architecture: four implementations of the same workload")


def fig_hybrid_timeline(st):
    """Schematic (not to scale) time line of the pipelined hybrid: CPU preprocessing of batch i+1 overlaps copy and compute of batch i."""
    fig, ax = st.figure(wide=True, aspect=0.36)
    fs = plt.rcParams["font.size"] - 1
    rows = ["CPU (OpenMP threads)", "CUDA stream 0", "CUDA stream 1", "CUDA stream 2"]
    ypos = {r: len(rows) - 1 - i for i, r in enumerate(rows)}
    H, K, D = 0.5, 1.0, 0.4          # schematic durations of H2D, kernels, D2H relative to one preprocessing step
    n = 6
    for i in range(n):
        ax.add_patch(Rectangle((i, ypos[rows[0]] - 0.32), 1, 0.64, fc=COLOR["openmp"], ec="white", lw=0.8))
        ax.text(i + 0.5, ypos[rows[0]], f"preprocess\nbatch {i}", ha="center", va="center", color="white", fontsize=fs)
        r = rows[1 + i % 3]
        t = i + 1
        for dur, col, lab in ((H, COLOR["transfer"], "H2D"), (K, COLOR["cuda"], f"kernels {i}"), (D, COLOR["transfer"], "D2H")):
            ax.add_patch(Rectangle((t, ypos[r] - 0.32), dur, 0.64, fc=col, ec="white", lw=0.8))
            ax.text(t + dur / 2, ypos[r], lab, ha="center", va="center", color="white", fontsize=fs - 0.5 if dur < 0.5 else fs)
            t += dur
    # event guard: batch 3 reuses the buffers of batch 0 (stream 0)
    end0 = 1 + H + K + D
    ax.annotate("", xy=(3, ypos[rows[0]] - 0.34), xytext=(end0, ypos[rows[1]] + 0.34),
                arrowprops=dict(arrowstyle="-|>", color=COLOR["hybrid"], lw=1.0, ls="--", shrinkA=0, shrinkB=0))
    ax.text(3.2, 2.5, "CUDA event: batch 3 may overwrite slot 0 only after batch 0 has finished", fontsize=fs, color=COLOR["hybrid"], va="center")
    ax.set_yticks([ypos[r] for r in rows])
    ax.set_yticklabels(rows)
    ax.set_xlim(-0.05, n + 2.0)
    ax.set_ylim(-0.7, len(rows) - 0.35)
    ax.set_xticks([])
    ax.set_xlabel("Time (schematic, not to scale)  \u2192")
    ax.grid(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    st.save(fig, "hybrid_timeline", "Pipelined hybrid: time line of batches")


def fig_network(st):
    """Figure: the workload as a flow chart (MNIST image -> preprocessing -> hidden layer -> ReLU -> output layer -> argmax -> digit)."""
    fig, ax = st.figure(wide=True, aspect=0.25)
    ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.grid(False)
    fs = plt.rcParams["font.size"] - 0.5
    items = [("MNIST image\n28\u00d728 uint8\n(784 bytes)", "#E5E7EB", COLOR["ink"], ""),
             ("Preprocessing\nper-image\nstandardization", COLOR["openmp"], "white", "stage 0"),
             ("Hidden layer\n784\u2192256\nW1, b1", COLOR["cuda"], "white", "stage 1"),
             ("ReLU\nmax(0, x)", COLOR["cuda"], "white", "stage 1"),
             ("Output layer\n256\u219210\nW2, b2", COLOR["cuda"], "white", "stage 2"),
             ("argmax\nover 10 logits", COLOR["hybrid"], "white", "stage 3"),
             ("Predicted\ndigit\n(0\u20139)", "#E5E7EB", COLOR["ink"], "")]
    n = len(items); bw = 0.12; gap = (1 - n * bw) / (n - 1)
    for i, (t, c, tc, stg) in enumerate(items):
        x = i * (bw + gap)
        _box(ax, x, 0.30, bw, 0.62, t, c, tc=tc, fs=fs)
        if stg:
            ax.text(x + bw / 2, 0.20, stg, ha="center", va="center", fontsize=fs - 0.5, color=COLOR["ink"], style="italic")
        if i:
            _arrow(ax, x - gap, 0.61, x, 0.61)
    ax.text(0.5, 0.04, "203,530 parameters  |  203,264 multiply-accumulates (406,528 floating-point operations) per image  |  float32",
            ha="center", fontsize=fs, color=COLOR["ink"])
    st.save(fig, "network_architecture", "Workload: MNIST MLP 784 \u2192 256 \u2192 ReLU \u2192 10")


def fig_speedup(st, S, plat):
    """Figure: speedup over serial (same machine and batch size) of the four primary implementations."""
    if not has(S, "serial", "cuda", "hybrid"):
        return
    ser = sel(S, "serial").set_index("batch").e2e_mean_ms
    fig, ax = st.figure(aspect=0.78)
    ax.axhline(1, color=COLOR["serial"], linestyle="-", linewidth=1.0, label="Serial CPU (1.0x)")
    for impl, d, lab in (("openmp", best_by_batch(S, "openmp"), "OpenMP CPU (best thread count)"),
                         ("cuda", sel(S, "cuda", block=DEFAULT_BLOCK), LABEL["cuda"]),
                         ("hybrid", best_by_batch(S, "hybrid", block=DEFAULT_BLOCK), "Hybrid-pipelined (best threads)")):
        ax.plot(d.batch, ser.loc[d.batch].values / d.e2e_mean_ms.values, color=COLOR[impl], marker=MARKER[impl], linestyle=LSTYLE[impl], label=lab)
    ax.set_yscale("log")
    log2_axis(ax, S.batch.unique())
    ax.set_yticks([0.5, 1, 2, 5, 10, 20, 50])
    ax.set_yticklabels(["0.5", "1", "2", "5", "10", "20", "50"])
    ax.set_xlabel("Batch size (images per batch)")
    ax.set_ylabel("End-to-end speedup over serial CPU (x)")
    ax.legend(loc="center right", bbox_to_anchor=(1.0, 0.36))
    st.save(fig, f"speedup_{plat}", f"End-to-end speedup over serial, {pn(plat)}")


def fig_cold(st):
    """Figure: cold start (10 fresh processes, batch 256, 24 threads) against steady state."""
    files = sorted(ar.RAW.glob("spartan_k40_native_*_cold.csv"))
    if not files:
        return
    c = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    fig, (a, b) = st.figure(wide=True, aspect=0.40, ncols=2, gridspec_kw={"width_ratios": [1.5, 1]})
    fs = plt.rcParams["font.size"]
    names = [("Serial CPU", "serial"), ("OpenMP CPU\n(24 threads)", "openmp"), ("CUDA\n(1-thread pre.)", "cuda"), ("Hybrid-\npipelined", "hybrid")]
    x = np.arange(len(names)); w = 0.38
    first = [c[f"{k}_pass1_ms"].mean() for _, k in names]
    later = [c[f"{k}_pass2_ms"].mean() for _, k in names]
    fe = [c[f"{k}_pass1_ms"].std() for _, k in names]
    le = [c[f"{k}_pass2_ms"].std() for _, k in names]
    cols = [COLOR[k] for _, k in names]
    a.bar(x - w / 2, first, w, yerr=fe, capsize=1.5, color=cols, hatch="////", edgecolor="white")
    a.bar(x + w / 2, later, w, yerr=le, capsize=1.5, color=cols)
    for xi, (f1, l1) in enumerate(zip(first, later)):
        a.text(xi - w / 2, f1 * 1.18, f"{f1:,.1f}", ha="center", va="bottom", fontsize=fs - 2)
        a.text(xi + w / 2, l1 * 1.18, f"{l1:,.1f}", ha="center", va="bottom", fontsize=fs - 2)
    a.set_yscale("log")
    a.set_ylim(top=a.get_ylim()[1] * 2)
    a.set_xticks(x); a.set_xticklabels([n for n, _ in names])
    a.set_ylabel("Time for 10,000 images (ms)")
    a.set_title("(a) First pass versus second pass", fontsize=fs)
    ha = [Rectangle((0, 0), 1, 1, fc=COLOR["other"], hatch="////", ec="white"), Rectangle((0, 0), 1, 1, fc=COLOR["other"])]
    a.legend(ha, ["first pass after set-up", "second pass (steady state)"], loc="upper right")
    comps = [("cuda_init_ms", "CUDA context creation", COLOR["cuda"]), ("weight_upload_ms", "Weight upload", COLOR["transfer"]),
             ("buffer_alloc_ms", "Buffer, stream and event allocation", COLOR["other"])]
    left, handles = 0.0, []
    for key, lab, col in comps:
        v = c[key].mean()
        b.barh([1], [v], left=left, color=col, edgecolor="white", linewidth=0.4)
        handles.append((Rectangle((0, 0), 1, 1, fc=col), f"{lab}: {v:.2f} ms"))
        left += v
    total = c.constructor_total_ms.mean()
    rest = total - left
    b.barh([1], [rest], left=left, color="#E5E7EB", edgecolor=COLOR["other"], linewidth=0.4)
    handles.append((Rectangle((0, 0), 1, 1, fc="#E5E7EB", ec=COLOR["other"]), f"Other set-up code (not itemized): {rest:.2f} ms"))
    steady = c.cuda_pass3_ms.mean()
    b.barh([0], [steady], color=COLOR["cuda"], hatch="////", edgecolor="white")
    b.text(total * 1.02, 1, f"{total:.1f} ms", va="center", fontsize=fs - 1)
    b.text(steady * 1.04, 0, f"{steady:.1f} ms", va="center", fontsize=fs - 1)
    b.set_yticks([1, 0]); b.set_yticklabels(["One-time GPU\nset-up (total)", "One steady-state\nCUDA pass"])
    b.set_xlabel("Time (ms)")
    b.set_xlim(0, total * 1.28)
    b.set_ylim(-0.6, 1.6)
    b.set_title("(b) One-time set-up (excluded)", fontsize=fs)
    fig.legend([h for h, _ in handles], [t for _, t in handles], loc="outside lower right", ncol=1, fontsize=fs - 1)
    st.save(fig, "cold_start", "Cold start versus steady state")


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
        fig_hybrid_timeline(st)
        fig_network(st)
        fig_cold(st)
        fig_correctness(st)
        main_plats = [p for p in ('mac_m4', 'spartan_k40_native') if p in summaries]
        fig_omp_combined(st, summaries, main_plats)
        fig_amdahl_combined(st, summaries, main_plats)
        for plat, S in summaries.items():
            fig_exec_time(st, S, plat)
            fig_throughput(st, S, plat)
            fig_speedup(st, S, plat)
            fig_omp_scaling(st, S, plat)
            fig_amdahl(st, S, plat)
            fig_kernel_vs_e2e(st, S, plat)
            fig_transfer(st, S, plat)
            fig_hybrid(st, S, plat)
            fig_blocksize(st, S, plat)


if __name__ == "__main__":
    sys.exit(main())
