#!/usr/bin/env python3
"""Measure page geometry and typography of a PDF and print a report.

    python3 check/measure.py <instructor-template.pdf> <our.pdf>

Needs poppler's pdftotext/pdftoppm/pdfinfo/pdffonts on the PATH and Pillow +
numpy.  The instructor's template PDF is only read, never copied.
Baselines are measured from rendered ink (300 dpi), so they are accurate to
about +-0.25 pt.
"""
import collections, os, re, subprocess, sys, tempfile, zlib
import numpy as np
from PIL import Image

DPI = 300


def run(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def lines(pdf, page):
    out = run("pdftotext", "-bbox-layout", "-f", str(page), "-l", str(page), pdf, "-")
    res = []
    for m in re.finditer(r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</line>', out, re.S):
        words = re.findall(r'>([^<]+)</word>', m.group(5))
        x0, y0, x1, y1 = map(float, m.groups()[:4])
        t = ' '.join(words).replace('​', '').strip()
        if t:
            res.append((x0, y0, x1, y1, t))
    return res


def npages(pdf):
    return int(re.search(r'Pages:\s+(\d+)', run("pdfinfo", pdf)).group(1))


def render(pdf, page):
    d = tempfile.mkdtemp()
    subprocess.run(["pdftoppm", "-r", str(DPI), "-f", str(page), "-l", str(page), "-gray", "-png", pdf, os.path.join(d, "r")], check=True)
    f = [x for x in os.listdir(d) if x.endswith(".png")][0]
    return np.array(Image.open(os.path.join(d, f)).convert("L"))


def baselines(pdf, page):
    img = render(pdf, page)
    s = DPI / 72.0
    out = []
    for x0, y0, x1, y1, t in lines(pdf, page):
        a = int(max(0, (y0 - 1) * s)); b = int(min(img.shape[0], (y1 + 1) * s))
        crop = img[a:b, int(x0 * s):int(x1 * s) + 1] < 140
        rows = crop.sum(axis=1)
        if rows.size == 0 or rows.max() == 0:
            continue
        idx = np.where(rows >= 0.30 * rows.max())[0]
        out.append((x0, x1, (a + idx[-1] + 1) / s, t))
    return out


def font_sizes(pdf, page):
    """Return Counter {(font, size_pt): n} from the content stream of one page."""
    data = open(pdf, 'rb').read()
    objs = {int(m.group(1)): m.group(2) for m in re.finditer(rb'(?<![0-9])(\d+) 0 obj(.*?)endobj', data, re.S)}
    for n, body in list(objs.items()):
        if b'/ObjStm' in body:
            sd = re.search(rb'stream\r?\n(.*)\r?\nendstream', body, re.S).group(1)
            try:
                dec = zlib.decompress(sd)
            except Exception:
                continue
            N = int(re.search(rb'/N\s+(\d+)', body).group(1)); first = int(re.search(rb'/First\s+(\d+)', body).group(1))
            hdr = [int(x) for x in dec[:first].split()]
            pr = [(hdr[2 * i], hdr[2 * i + 1]) for i in range(N)]
            for i, (on, off) in enumerate(pr):
                end = pr[i + 1][1] if i + 1 < N else len(dec) - first
                objs[on] = dec[first + off:first + end]

    def leaves(n):
        b = objs.get(n, b'')
        km = re.search(rb'/Kids\s*\[(.*?)\]', b, re.S)
        if re.search(rb'/Type\s*/Page(?!s)', b) or not km:
            return [n]
        o = []
        for k in re.findall(rb'(\d+) 0 R', km.group(1)):
            o += leaves(int(k))
        return o
    root = [n for n, b in objs.items() if re.search(rb'/Type\s*/Pages', b) and b'/Parent' not in b][0]
    body = objs[leaves(root)[page - 1]]
    rm = re.search(rb'/Resources\s+(\d+) 0 R', body)
    res = objs[int(rm.group(1))] if rm else body
    fm = re.search(rb'/Font\s*(\d+) 0 R', res)
    fd = objs[int(fm.group(1))] if fm else re.search(rb'/Font\s*<<(.*?)>>', res, re.S).group(1)
    fmap = {}
    for name, num in re.findall(rb'/(\w+)\s+(\d+) 0 R', fd):
        fo = objs.get(int(num), b'')
        bf = re.search(rb'/BaseFont\s*/([^\s/>\]]+)', fo)
        if not bf:
            d = re.search(rb'/DescendantFonts\s*\[?\s*(\d+) 0 R', fo)
            if d:
                bf = re.search(rb'/BaseFont\s*/([^\s/>\]]+)', objs.get(int(d.group(1)), b''))
        fmap[name.decode()] = bf.group(1).decode().split('+')[-1] if bf else '?'
    cm = re.search(rb'/Contents\s*(\[.*?\]|\d+ 0 R)', body, re.S)
    txt = b''
    for n in [int(x) for x in re.findall(rb'(\d+) 0 R', cm.group(1))]:
        sd = re.search(rb'stream\r?\n(.*)\r?\nendstream', objs[n], re.S).group(1)
        try:
            sd = zlib.decompress(sd)
        except Exception:
            pass
        txt += sd + b'\n'
    txt = txt.decode('latin1')
    scale = 1.0
    sm = re.search(r'([\d.]+)\s+0\s+0\s+-([\d.]+)\s+0\s+[\d.]+\s+cm', txt)   # Skia-style page flip
    if sm:
        scale = float(sm.group(1))
    elif 'xdvipdfmx' in run("pdfinfo", pdf) or 'pdfTeX' in run("pdfinfo", pdf):
        scale = 72.27 / 72.0                                                   # TeX bp -> pt
    c = collections.Counter()
    for m in re.finditer(r'/(\w+)\s+([\d.]+)\s+Tf', txt):
        c[(fmap.get(m.group(1), m.group(1)), round(float(m.group(2)) * scale, 1))] += 1
    return c


def report(label, pdf):
    print(f"\n===== {label}: {os.path.basename(pdf)} =====")
    info = run("pdfinfo", pdf)
    print(re.search(r'Page size:.*', info).group(0), '| pages:', npages(pdf))
    L = lines(pdf, 1)
    x0 = min(l[0] for l in L); x1 = max(l[2] for l in L); y0 = min(l[1] for l in L); y1 = max(l[3] for l in L)
    print(f"page-1 text bbox  x {x0:.1f}-{x1:.1f}  y {y0:.1f}-{y1:.1f}   (rectangle: x 54-558, y 72-738)")
    ytop = min([l[1] for l in L if l[4].startswith('ABSTRACT')] or [0])
    img = render(pdf, 1)
    sc = DPI / 72.0
    sub = img[int((ytop + 15) * sc):int(min(738, y1 + 2) * sc)] < 150     # below the title block
    for name, lo, hi in (("col 1", 0, 306), ("col 2", 306, 612)):
        Lft, Rgt = [], []
        for r in range(sub.shape[0]):
            w = np.where(sub[r, int(lo * sc):int(hi * sc)])[0]
            if len(w):
                Lft.append(lo + w.min() / sc); Rgt.append(lo + w.max() / sc)
        l5, r95 = np.percentile(Lft, 5), np.percentile(Rgt, 95)
        print(f"{name}: ink left edge (5th pct of rows) {l5:.1f}  ink right edge (95th pct) {r95:.1f}  width {r95 - l5:.1f}")
    fonts = run("pdffonts", pdf).splitlines()[2:]
    print("fonts:", '; '.join(sorted(set(f.split()[0].split('+')[-1] for f in fonts if f.strip()))))
    print("font sizes on page 1 (pt, runs):", dict(sorted(font_sizes(pdf, 1).items(), key=lambda kv: -kv[1])[:10]))
    B = baselines(pdf, 1)
    print("baseline distances, page 1 (pt):")
    col1 = [(x, xe, b, t) for x, xe, b, t in B if x < 300]
    col1.sort(key=lambda r: (round(r[2], 0), r[0]))
    out = []
    last = None
    for x, xe, b, t in col1:
        if last is not None and b - last[0] > 5:
            out.append((b - last[0], last[1][:22], t[:22]))
        if last is None or b - last[0] > 5:
            last = (b, t)
    for d, a, c in out[:28]:
        print(f"   {d:6.2f}   {a:24s} -> {c}")
    # headers / footers / page numbers on every page
    bad = []
    for p in range(1, npages(pdf) + 1):
        for lx0, ly0, lx1, ly1, t in lines(pdf, p):
            if ly0 < 66.0 or ly1 > 746.0:      # text block is 72..738; allow descent / line-box slack
                bad.append((p, round(ly0, 1), round(ly1, 1), t[:30]))
    print("text above y=66 or below y=746 (headers/footers/page numbers):", bad or "none")
    # last page balance
    n = npages(pdf)
    lp = [l for l in lines(pdf, n) if l[2] - l[0] > 20]
    c1 = [l for l in lp if l[0] < 300]; c2 = [l for l in lp if l[0] >= 300]
    if c1 and c2:
        print(f"last page ({n}): column bottoms  col1 {max(l[3] for l in c1):.1f}  col2 {max(l[3] for l in c2):.1f}  "
              f"(difference {abs(max(l[3] for l in c1) - max(l[3] for l in c2)):.1f} pt)")


if __name__ == '__main__':
    report("INSTRUCTOR TEMPLATE", sys.argv[1])
    report("OURS", sys.argv[2])
