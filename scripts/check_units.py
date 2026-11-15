#!/usr/bin/env python3
"""Flag every \\val{...} number in the paper prose that is not followed by a unit or a dimensionless marker.

Usage: python3 scripts/check_units.py [report/overleaf/sections/*.tex]
A value passes if the text right after it starts with a unit (ms, us, GB/s, GFLOP/s, GB, MB, MiB, %, x), or its key
names a dimensionless quantity (efficiency, serial fraction, R^2, Karp-Flatt, p-value, ratio interval, counts).
Everything else is printed for review.
"""
import glob
import re
import sys

UNIT = re.compile(r"^(?:\\,|~|\s)*(?:ms\b|\\mu|\$\\mu|GB/s|GFLOP/s|GB\b|MB\b|MiB|KiB|GiB|MHz|GHz|\\%|\\,\\%|\$\\times\$|threads|images|pass(?:es)?\b|--)")
DIMENSIONLESS = re.compile(r":(eff|f|r2|kf|maxp|cilo|cihi|maxerr|meanerr|runs|thr|crossover|n|total|passed|cpuThreads|accuracy|agree|p|cv:[a-z0-9]+)(:|$)")

bad = 0
files = sys.argv[1:] or sorted(glob.glob("report/overleaf/sections/*.tex"))
for path in files:
    text = open(path).read()
    for m in re.finditer(r"\\val\{([^}]+)\}", text):
        key = m.group(1)
        after = text[m.end(): m.end() + 24]
        if UNIT.match(after) or DIMENSIONLESS.search(":" + key + ":") or ":cpu" in key or ":gpu" in key or ":compiler" in key:
            continue
        # a range "a to b" / "a--b" is checked on its last value
        if re.match(r"^\s*(?:to|--)\s*\\val", after) or re.match(r"^\s*,\s*\\val", after) or re.match(r"^\s*and\s*\\val", after):
            continue
        line = text.count("\n", 0, m.start()) + 1
        ctx = text[max(0, m.start() - 40): m.end() + 30].replace("\n", " ")
        print(f"{path}:{line}: \\val{{{key}}}  ...{ctx}...")
        bad += 1
print(f"{bad} value(s) without a recognised unit")
sys.exit(1 if bad else 0)
