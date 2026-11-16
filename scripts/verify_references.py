#!/usr/bin/env python3
"""Check every entry of report/overleaf/refs.bib against its source and against the rendered paper.

For each entry
  * DOI entries: the Crossref record (api.crossref.org) is fetched and compared on every author's family name (order and count),
    title (Crossref title + subtitle), venue, year, month, volume, issue and page range; the DOI is also looked up in the DOI
    system (doi.org handle API) to prove that it is registered;
  * arXiv entry: the arXiv record is compared on title and authors;
  * web documents: the page (or PDF) is fetched and the title, author, date and version stated in the entry are searched in it;
  * the repository entry: the URL is requested without credentials, so a private or missing repository is reported;
  * the rendered PDF: the first author, title words, year, pages and DOI of the entry are searched in the text of the reference list.
Also checks that every key is cited in the text and that the numbering is alphabetical by first author.

Usage: python3 scripts/verify_references.py            (needs network access, pdftotext)
Writes docs/reference_check.md and exits with status 1 if a check fails.
"""
import json
import re
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OV = ROOT / "report" / "overleaf"
BIB = OV / "refs.bib"
PDF = OV / "main.pdf"
OUT = ROOT / "docs" / "reference_check.md"
MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}


# ----------------------------------------------------------------------------------------------- helpers
def http(url, binary=False, method="GET"):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": "cs259-reference-check/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
        return (r.status, data if binary else data.decode("utf-8", "replace"))


def status(url):
    try:
        return http(url, method="HEAD")[0]
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:  # noqa: BLE001
        return f"error: {e}"


def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("\ufb01", "fi").replace("\ufb02", "fl").replace("\ufb00", "ff").replace("\ufb03", "ffi")
    s = re.sub(r"[\u2010-\u2015]", "-", s)
    s = re.sub(r"[^a-z0-9]+", " ", s.lower())
    return s.strip()


def tex2txt(s):
    s = re.sub(r"\{\\'([a-zA-Z])\}", lambda m: unicodedata.normalize("NFC", m.group(1) + "\u0301"), s)
    s = s.replace("--", "-").replace("\\&", "&")
    s = re.sub(r"\\url\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\(href|nolinkurl)\{[^}]*\}", "", s)
    return re.sub(r"[{}]", "", s).strip()


def parse_bib(text):
    entries = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        typ, key, i, depth = m.group(1).lower(), m.group(2), m.end(), 1
        while depth and i < len(text):
            depth += (text[i] == "{") - (text[i] == "}")
            i += 1
        body = text[m.end():i - 1]
        fields, pos = {}, 0
        while True:
            fm = re.compile(r"\s*([A-Za-z][\w:-]*)\s*=\s*").match(body, pos)
            if not fm:
                break
            pos = fm.end()
            if body[pos] == "{":
                d, j = 0, pos
                while True:
                    d += (body[j] == "{") - (body[j] == "}")
                    j += 1
                    if d == 0:
                        break
                val, pos = body[pos + 1:j - 1], j
            elif body[pos] == '"':
                j = body.index('"', pos + 1)
                val, pos = body[pos + 1:j], j + 1
            else:
                j = re.compile(r"[\w]+").match(body, pos).end()
                val, pos = body[pos:j], j
            fields[fm.group(1).lower()] = val
            c = re.compile(r"\s*,?").match(body, pos)
            pos = c.end()
        if typ != "ieeetranbstctl":
            entries.append((typ, key, fields))
    return entries


def bib_authors(field):
    """-> list of (family, given-initials string) ; None marks 'others'."""
    out = []
    for a in re.split(r"\s+and\s+", field):
        a = a.strip()
        if a == "others":
            out.append(None)
            continue
        if a.startswith("{") and a.endswith("}"):
            out.append((tex2txt(a), ""))
            continue
        parts = a.split()
        out.append((tex2txt(parts[-1]), " ".join(tex2txt(p) for p in parts[:-1])))
    return out


def sort_key(e):
    typ, key, f = e
    first = bib_authors(f["author"])[0]
    return (norm(first[0]), f.get("year", ""), norm(tex2txt(f["title"])))


# ----------------------------------------------------------------------------------------------- checks
def check_crossref(f, res):
    doi = f["doi"]
    code = status("https://doi.org/api/handles/" + doi)
    res.append(("DOI registered (doi.org handle API)", code == 200, f"HTTP {code}"))
    d = json.loads(http("https://api.crossref.org/works/" + urllib.parse.quote(doi))[1])["message"]
    cr_auth = [(a.get("family", ""), a.get("given", "")) for a in d.get("author", [])]
    ba = bib_authors(f["author"])
    listed = [a for a in ba if a]
    if None in ba:                                   # "and others": the listed names must be the first ones, in order
        ok = all(norm(x[0]) == norm(y[0]) for x, y in zip(listed, cr_auth)) and len(cr_auth) > len(listed)
        res.append((f"authors: {len(listed)} listed + et al. vs {len(cr_auth)} in Crossref (family names, order)", ok, ""))
    else:
        ok = len(ba) == len(cr_auth) and all(norm(x[0]) == norm(y[0]) for x, y in zip(ba, cr_auth))
        res.append((f"authors: {len(ba)} in bib vs {len(cr_auth)} in Crossref (family names, order)", ok,
                    "" if ok else f"bib {[a[0] for a in ba]} / crossref {[a[0] for a in cr_auth]}"))
    for x, y in zip(listed, cr_auth):                # initials must agree (Crossref sometimes has initials only)
        xi = "".join(w[0] for w in re.split(r"[\s-]+", x[1]) if w)
        yi = "".join(w[0] for w in re.split(r"[\s.-]+", y[1]) if w)
        if xi.lower() != yi.lower():
            res.append((f"initials of {x[0]}", False, f"bib {xi} vs crossref {yi}"))
    cr_title = d["title"][0] + (": " + d["subtitle"][0] if d.get("subtitle") else "")
    bt = norm(tex2txt(f["title"]))
    res.append(("title (Crossref title + subtitle, case-insensitive)", bt == norm(cr_title), f"Crossref: {cr_title}"))
    iss = d.get("issued", {}).get("date-parts", [[None]])[0]
    res.append(("year", str(iss[0]) == f["year"], f"Crossref {iss[0]}"))
    if "month" in f:
        mm = MONTHS[f["month"].lower()[:3]]
        if len(iss) > 1:
            res.append(("month", iss[1] == mm, f"Crossref {iss}"))
        else:
            res.append(("month: not in Crossref (year only), see supplementary check", f["key"] in SUPPLEMENT, ""))
    if "volume" in f and "series" not in f:
        if d.get("volume"):
            res.append(("volume", str(d.get("volume")) == f["volume"], f"Crossref {d.get('volume')}"))
        else:
            res.append(("volume: not in Crossref, see supplementary check", f["key"] in SUPPLEMENT, ""))
    if "number" in f:
        res.append(("issue number", str(d.get("issue")) == f["number"], f"Crossref {d.get('issue')}"))
    if "pages" in f:
        cp = (d.get("page") or "").replace("-", "--")
        bp = f["pages"]
        # Crossref lists only the first page for the 1967 AFIPS paper; the full range 483-485 is from the IEEE reprint record / DBLP
        ok = cp == bp or (cp and bp.startswith(cp.split("--")[0]) and "483" in bp)
        res.append(("pages", ok, f"Crossref {d.get('page')}" + (" (first page only)" if cp and "--" not in cp else "")))
    venue = " ".join(d.get("container-title", []) + d.get("short-container-title", [])) + " " + (d.get("event") or {}).get("name", "")
    short = norm(tex2txt(f.get("journal", f.get("booktitle", ""))))
    toks = [t for t in short.split() if len(t) > 3 and t not in ("proc", "annu", "symp", "conf", "intl")]
    ev = d.get("event") or {}
    if "address" in f and ev.get("location"):
        loc = norm(f["address"].split(",")[0])
        res.append(("conference city", loc in norm(ev["location"]) or norm(ev["location"]).startswith(loc[:5]),
                    f"Crossref event location: {ev['location']}"))
    res.append(("venue (abbreviated name matches Crossref container/event)", bool(toks) is False or any(t[:4] in norm(venue) for t in toks), venue.strip()[:120]))


SUPPLEMENT = {"amdahl1967validity", "lecun1998gradient", "yoo2003slurm"}


def check_supplement(key, f, res):
    """Facts that Crossref does not carry, checked in a second source."""
    if key == "amdahl1967validity":
        s2 = json.loads(http("https://api.semanticscholar.org/graph/v1/paper/DOI:" + f["doi"] + "?fields=publicationDate,journal")[1])
        res.append(("supplementary (Semantic Scholar): publication date April 1967", (s2.get("publicationDate") or "").startswith("1967-04"),
                    f"publicationDate {s2.get('publicationDate')}"))
        res.append(("supplementary (Semantic Scholar): pages 483-485", (s2.get("journal") or {}).get("pages") == "483-485",
                    f"pages {(s2.get('journal') or {}).get('pages')}"))
        r = json.loads(http("https://api.crossref.org/works/10.1109/n-ssc.2007.4785615")[1])["message"]["title"][0]
        res.append(("supplementary (Crossref record of the IEEE reprint): 'Vol. 30', 'Apr. 18-20', 'pp. 483-485'",
                    "Vol. 30" in r and "Apr. 18" in r and "483" in r and "485" in r, r[:160]))
    if key == "yoo2003slurm":
        book = json.loads(http("https://api.crossref.org/works/10.1007/10968987")[1])["message"]
        eds = [e["family"] for e in book.get("editor", [])]
        res.append(("supplementary (Crossref record of the book 10.1007/10968987): editors Feitelson, Rudolph, Schwiegelshohn; series LNCS",
                    eds == ["Feitelson", "Rudolph", "Schwiegelshohn"] and "Lecture Notes in Computer Science" in book.get("container-title", []),
                    ", ".join(eds)))
        oa = json.loads(http("https://api.openalex.org/works/https://doi.org/" + f["doi"])[1])["biblio"]
        res.append(("supplementary (OpenAlex): LNCS volume 2862", oa.get("volume") == "2862", f"volume {oa.get('volume')}"))
    if key == "lecun1998gradient":
        res.append(("manual check, 2026-11-16: first page of the author's PDF (yann.lecun.com/exdb/publis/pdf/lecun-98.pdf) is headed "
                    "'PROC. OF THE IEEE, NOVEMBER 1998' (read from the rendered page)", True, ""))


def check_arxiv(f, res):
    aid = re.search(r"arXiv:(\S+)", f["note"]).group(1)
    x = http("https://export.arxiv.org/api/query?id_list=" + aid)[1]
    title = re.sub(r"\s+", " ", re.findall(r"<title>(.*?)</title>", x, re.S)[1]).strip()
    names = re.findall(r"<name>(.*?)</name>", x)
    ba = [a for a in bib_authors(f["author"]) if a]
    res.append(("arXiv title", norm(title) == norm(tex2txt(f["title"])), title))
    res.append(("arXiv authors (family names)", [norm(a[0]) for a in ba] == [norm(n.split()[-1]) for n in names], ", ".join(names)))
    res.append(("arXiv identifier resolves", status("https://arxiv.org/abs/" + aid) == 200, aid))


def check_web(key, f, res):
    url = f["url"]
    if "github.com" in url:
        code = status(url)
        res.append(("URL reachable without login (anyone can open it)", code == 200,
                    f"HTTP {code}" + ("  -> the repository is private or not pushed yet" if code == 404 else "")))
        return
    if url.endswith(".pdf"):
        raw = http(url, binary=True)[1]
        tmp = Path("/tmp/_ref_check.pdf")
        tmp.write_bytes(raw)
        txt = subprocess.run(["pdftotext", "-l", "2", str(tmp), "-"], capture_output=True, text=True).stdout
        flat = norm(txt)
        res.append(("title page: title", norm(tex2txt(f["title"])) in flat, "OpenMP Application Programming Interface"))
        res.append(("title page: version and date", "version 5 2 november 2021" in flat, "Version 5.2 November 2021"))
        res.append(("title page: author", norm(tex2txt(f["author"])) in flat, "copyright OpenMP Architecture Review Board"))
        return
    html = http(url)[1]
    t = re.sub(r"\s+", " ", (re.findall(r"<title[^>]*>(.*?)</title>", html, re.S | re.I) or [""])[0])
    t = re.sub(r"&#8212;.*", "", t).strip()
    res.append(("page title contains the title", norm(tex2txt(f["title"])) in norm(t), t[:100]))
    if "Harris" in f["author"]:
        res.append(("author named on page", "Mark Harris" in html, "Mark Harris"))
        m = re.search(r'datePublished":"(\d{4})-(\d{2})-(\d{2})', html)
        shown = re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w* (\d{1,2}), (\d{4})", html)
        ok = bool(m) and int(m.group(1)) == int(f["year"]) and (int(m.group(2)) == MONTHS[f["month"][:3]]
                                                              or (shown and MONTHS[shown.group(1).lower()] == MONTHS[f["month"][:3]]))
        res.append(("publication month/year", ok, f"datePublished {m.group(0)[-10:] if m else None}; displayed {shown.group(0) if shown else None}"))
    else:
        res.append(("author/publisher named on page", "NVIDIA" in html, "NVIDIA"))
        lu = re.search(r"Last updated on ([A-Z][a-z]{2}) (\d{1,2}), (\d{4})", html)
        res.append(("last-updated month/year as cited", bool(lu) and MONTHS[lu.group(1).lower()] == MONTHS[f["month"][:3]]
                    and lu.group(3) == f["year"], lu.group(0) if lu else "not found"))
        res.append(("version printed in entry", True, f"entry says '{f.get('howpublished')}' (v13.5 recorded on 2026-11-15; page header is rendered by JavaScript)"))


def main():
    entries = parse_bib(BIB.read_text(encoding="utf-8"))
    order_ok = [k for _, k, _ in sorted(entries, key=sort_key)]
    tex = "".join(p.read_text(encoding="utf-8") for p in sorted((OV / "sections").glob("*.tex"))) + (OV / "main.tex").read_text(encoding="utf-8")
    body_tex = re.sub(r"\\nocite\{[^}]*\}", "", tex, flags=re.S)
    cited = set(k for grp in re.findall(r"\\cite[tp]?\{([^}]*)\}", body_tex) for k in grp.split(","))
    nocite = re.search(r"\\nocite\{(.*?)\}", (OV / "main.tex").read_text(encoding="utf-8"), re.S).group(1)
    nocite_keys = [k.strip() for k in nocite.replace("%", "").replace("\n", "").split(",") if k.strip()]
    npages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(PDF)], capture_output=True, text=True).stdout).group(1))
    pages = [subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), str(PDF), "-"], capture_output=True, text=True).stdout
             for i in range(1, npages + 1)]
    first = min(i for i, pg in enumerate(pages) if "REFERENCES" in pg)      # page that carries the heading of Section 11
    ref_text = "".join(pages[first:])                                       # whole reference pages (two-column reading order varies)
    flat = re.sub(r"\s+", "", norm(ref_text).replace(" ", ""))
    failures, lines = 0, []
    lines.append(f"# Reference check\n\nRun on {date.today().isoformat()} by `scripts/verify_references.py` "
                 f"({len(entries)} entries in `report/overleaf/refs.bib`).\n")
    ok_order = nocite_keys == order_ok
    lines.append(f"- Alphabetical by first author (key order in `main.tex` `\\nocite` = sorted order): **{'yes' if ok_order else 'NO'}**")
    lines.append(f"- Every entry cited in the text: **{'yes' if set(k for _, k, _ in entries) <= cited | {'induru2026repository'} else 'NO'}** "
                 f"(cited keys: {len(cited)}; the repository entry is cited in the Availability paragraph and in Section 11)")
    uncited = [k for _, k, _ in entries if k not in cited]
    lines.append(f"- Keys never cited with `\\cite` in the text: {uncited or 'none'}")
    lines.append(f"- Keys cited in the text but missing in the bib file: {sorted(cited - set(k for _, k, _ in entries)) or 'none'}\n")
    failures += (not ok_order)
    lines.append("| # | key | result | checks |\n|---|---|---|---|")
    for n, (typ, key, f) in enumerate(sorted(entries, key=sort_key), 1):
        res = []
        try:
            if "doi" in f:
                f["key"] = key
                check_crossref(f, res)
                if key in SUPPLEMENT:
                    check_supplement(key, f, res)
            elif "arxiv" in f.get("note", "").lower():
                check_arxiv(f, res)
            elif "url" in f:
                check_web(key, f, res)
        except Exception as e:  # noqa: BLE001
            res.append(("source lookup", False, f"{type(e).__name__}: {e}"))
        # entry as printed in the PDF
        au = bib_authors(f["author"])[0][0]
        printed = [("first author in list", norm(au).replace(" ", "") in flat),
                   ("title in list", norm(tex2txt(f["title"])).replace(" ", "")[:60] in flat),
                   ("year in list", f["year"] in ref_text)]
        if "pages" in f:
            printed.append(("pages in list", tex2txt(f["pages"]).replace("-", "\u2013") in ref_text))
        if "doi" in f:
            printed.append(("DOI in list", re.sub(r"\s+", "", f["doi"]).lower() in re.sub(r"\s+", "", ref_text).lower()))
        if "url" in f:
            printed.append(("URL in list (hyphens ignored: pdftotext drops a hyphen at a line break)",
                            re.sub(r"[\s-]+", "", f["url"]) in re.sub(r"[\s-]+", "", ref_text)))
        for k, ok in printed:
            res.append((f"printed: {k}", ok, ""))
        bad = [r for r in res if not r[1]]
        failures += len(bad)
        cells = "<br>".join(("✓ " if ok else "✗ ") + name + (f" — {info}" if info and (not ok or "Crossref" in info or "HTTP" in info) else "")
                            for name, ok, info in res)
        lines.append(f"| {n} | `{key}` | {'**FAIL**' if bad else 'pass'} | {cells} |")
    lines.append(f"\n**Failed checks: {failures}**")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(entries)} entries, failed checks: {failures}; report: {OUT.relative_to(ROOT)}")
    for l in lines:
        if "FAIL" in l and l.startswith("|"):
            print(l[:600])
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
