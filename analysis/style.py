"""Shared plotting style: fixed colours per implementation, paper (final size) and slide variants.

Palette (checked with a colour-vision-deficiency / contrast validator; serial is intentionally a
neutral gray as required, so identity is also carried by marker shape, line style and labels):
  Serial CPU gray, OpenMP CPU blue, CUDA GPU green, Hybrid purple, transfer orange.
"""
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = Path(os.environ.get("CS259_FIG", ROOT / "results" / "figures"))

COLOR = dict(serial="#4B5563", openmp="#2563EB", cuda="#16A34A", hybrid="#7C3AED",
             hybrid_seq="#A78BFA", transfer="#C2570C", transfer2="#F0A36B", other="#9CA3AF",
             grid="#D9D9D9", ink="#1F2937")
LABEL = dict(serial="Serial CPU", openmp="OpenMP CPU", cuda="CUDA GPU (serial preprocessing)",
             hybrid_seq="Hybrid, sequential", hybrid="Hybrid, pipelined")
MARKER = dict(serial="s", openmp="o", cuda="^", hybrid="D", hybrid_seq="v")
LSTYLE = dict(serial="-", openmp="-", cuda="-", hybrid="-", hybrid_seq="--")


class Style:
    def __init__(self, name, w1, w2, font, titles, dpi, lw):
        self.name, self.w1, self.w2, self.font, self.titles, self.dpi, self.lw = name, w1, w2, font, titles, dpi, lw

    def apply(self):
        f = self.font
        plt.rcParams.update({
            "font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": f,
            "axes.labelsize": f, "axes.titlesize": f, "legend.fontsize": f - 0.5,
            "xtick.labelsize": f - 0.5, "ytick.labelsize": f - 0.5,
            "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
            "lines.linewidth": self.lw, "lines.markersize": 3.6 if self.name == "paper" else 7,
            "axes.grid": True, "grid.color": COLOR["grid"], "grid.linewidth": 0.4, "axes.axisbelow": True,
            "legend.frameon": False, "savefig.dpi": self.dpi, "pdf.fonttype": 42, "ps.fonttype": 42,
            "figure.constrained_layout.use": True,
        })

    def figure(self, wide=False, aspect=0.72, **kw):
        w = self.w2 if wide else self.w1
        return plt.subplots(figsize=(w, w * aspect), **kw)

    def save(self, fig, name, title=None):
        out = FIG_DIR / self.name
        out.mkdir(parents=True, exist_ok=True)
        if self.titles and title:
            fig.suptitle(title, fontsize=self.font + 1, fontweight="bold")
        fig.savefig(out / f"{name}.png")
        if self.name == "paper":
            fig.savefig(out / f"{name}.pdf")
        plt.close(fig)
        print("figure:", (out / f"{name}.png").relative_to(ROOT) if str(FIG_DIR).startswith(str(ROOT)) else out / f"{name}.png")


PAPER = Style("paper", 3.33, 7.0, 7.5, False, 300, 1.1)
SLIDE = Style("slides", 5.4, 9.2, 11.5, True, 220, 2.0)
STYLES = (PAPER, SLIDE)


def log2_axis(ax, values, which="x"):
    values = sorted(set(int(v) for v in values))
    if which == "x":
        ax.set_xscale("log", base=2)
        ax.set_xticks(values)
        ax.set_xticklabels([str(v) for v in values])
        ax.minorticks_off()
    else:
        ax.set_yscale("log", base=2)
        ax.set_yticks(values)
        ax.set_yticklabels([str(v) for v in values])


PLAT_NAME = {"spartan_k40_native": "Spartan node: Tesla K40m + Xeon E5-2680 v4", "spartan_k40_o3": "Spartan node, plain -O3",
             "mac_m4": "Apple M4"}


def pn(plat):
    return PLAT_NAME.get(plat, plat)
