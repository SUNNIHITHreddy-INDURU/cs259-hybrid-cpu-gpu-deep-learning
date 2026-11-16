#!/usr/bin/env python3
"""Add native (editable) custom error bars to the line charts of the deck.

pptxgenjs cannot write error bars, so build_deck.js records the 95 % confidence-interval half-widths of every series in
presentation/errbars.json and this script inserts <c:errBars> (custom +/- values) into the chart XML parts.
Usage: python3 presentation/add_error_bars.py presentation/CS259_Hybrid_CPU_GPU_Induru.pptx
"""
import json
import shutil
import sys
import zipfile
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.util import Emu  # noqa: F401  (imported to make python-pptx fail early if broken)

C = "http://schemas.openxmlformats.org/drawingml/2006/chart"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS = {"c": C, "a": A}


def numlit(values):
    pts = "".join(f'<c:pt idx="{i}"><c:v>{float(v):.6g}</c:v></c:pt>' for i, v in enumerate(values))
    return f'<c:numLit><c:formatCode>General</c:formatCode><c:ptCount val="{len(values)}"/>{pts}</c:numLit>'


def errbars_xml(values):
    xml = (f'<c:errBars xmlns:c="{C}" xmlns:a="{A}"><c:errDir val="y"/><c:errBarType val="both"/><c:errValType val="cust"/><c:noEndCap val="0"/>'
           f'<c:plus>{numlit(values)}</c:plus><c:minus>{numlit(values)}</c:minus>'
           '<c:spPr><a:ln w="12700"><a:solidFill><a:srgbClr val="1F2937"/></a:solidFill></a:ln></c:spPr></c:errBars>')
    return etree.fromstring(xml)


def main(path):
    path = Path(path)
    spec = json.loads((path.parent / "errbars.json").read_text())
    prs = Presentation(str(path))
    part_for = {}  # (slide number, chart index) -> part name inside the zip
    for sn, slide in enumerate(prs.slides, 1):
        k = 0
        for shape in slide.shapes:
            if getattr(shape, "has_chart", False) and shape.has_chart:
                part_for[(sn, k)] = str(shape.chart.part.partname).lstrip("/")
                k += 1
    targets, dashes = {}, {}
    for item in spec:
        part = part_for[(item["slide"], item["chart"])]
        targets.setdefault(part, {}).update(item.get("ci", {}))
        dashes.setdefault(part, {}).update(item.get("dash", {}))
    tmp = path.with_suffix(".tmp.pptx")
    added = 0
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename in targets:
                root = etree.fromstring(data)
                for ser in root.iter(f"{{{C}}}ser"):
                    name = "".join(ser.xpath("c:tx//c:v/text()", namespaces=NS))
                    dash = dashes[info.filename].get(name)
                    if dash:                                   # per-series dash style (pptxgenjs only takes one for the whole chart)
                        for pd in ser.xpath("c:spPr/a:ln/a:prstDash", namespaces=NS):
                            pd.set("val", dash)
                        for sym in ser.xpath("c:marker/c:symbol", namespaces=NS):   # dashed reference/fit lines carry no markers
                            sym.set("val", "none")
                    ci = targets[info.filename].get(name)
                    if ci is None or max(ci) == 0:
                        continue
                    cat = ser.find("c:cat", NS)
                    cat.addprevious(errbars_xml(ci))
                    added += 1
                data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
            zout.writestr(info, data)
    shutil.move(str(tmp), str(path))
    print(f"added error bars to {added} series in {len(targets)} charts")


if __name__ == "__main__":
    main(sys.argv[1])
