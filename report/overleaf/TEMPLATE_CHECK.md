# Template check: `cs259.cls` versus the instructor's template

Compared: page 1 of the instructor's `CS259-TermPaper-Format-Template.doc.pdf` (Google Docs export, 2 pages) with
page 1 of `template_demo.pdf` (3 pages, built by tectonic/XeTeX from `template_demo.tex`).
Side-by-side renders: `check/page1_template_vs_ours.png`, `check/lastpage_template_vs_ours.png`.
Reproduce the numbers with `python3 check/measure.py <instructor-template.pdf> template_demo.pdf`
(needs poppler and Pillow; the instructor's PDF is only read, it is not stored in the repository).

Measurement notes: positions are in PDF points (bp, 1/72 in). Text baselines were measured from rendered ink at
300 dpi, so they are accurate to about 0.25 pt. `pdftotext -bbox-layout` boxes depend on each font's
ascent/descent, so box heights are only comparable after dividing by the font's box-to-size ratio (see section 3).
All layout lengths in `cs259.cls` are in bp, the unit of the Word template, not TeX points (which are 0.4 % smaller).

## 1. Page and columns

| Item | Instructor template | `cs259.cls` | Difference |
|---|---|---|---|
| Page size | 612 x 792 pt (US Letter) | 612 x 792 pt (US Letter) | none |
| Text rectangle | x 54-558, y 72-738 (7 x 9.25 in at 0.75 in / 1 in) | `\textwidth` 504 bp, `\textheight` 664 bp, left 54 bp, top 72 bp | height is 2 bp short of 666 so descenders of the last line stay inside the rectangle |
| Ink bounding box of all pages | page 1: x 54.0-557.8 | pages 1-3: x 53.5-559.0, y 72.0-737.8 | up to 1 bp of glyph overhang (hyphens at line ends); nothing below 738 |
| Column 1 left / right ink edge | 54.2 / 293.0 | 54.2 / 293.5 | +0.5 pt on the right (ragged glyph ends) |
| Column 2 left / right ink edge | 318.2 / 556.8 | 318.2 / 557.3 | +0.5 pt on the right |
| Column width / gutter | 240 / 24 pt (text edges 54-294, 318-558) | 240 / 24 pt (`\columnsep` 24 bp) | none (the "3.33 in / 0.33 in" of the template text equals 239.8 / 23.8 pt; the template file itself uses 240 / 24) |
| Headers, footers, page numbers | none | none: no text above y = 66 or below y = 746 on any page | none |

## 2. Page 1 vertical positions (baseline-to-baseline, pt)

| Distance | Template | Ours |
|---|---|---|
| top of page to title baseline | 89.3 | 89.3 |
| title (last line) -> author name | 19.9 | 19.9 |
| author -> first affiliation line | 13.2 | 13.2 |
| affiliation line pitch | 12.5-12.7 | 12.5-12.7 |
| last affiliation line -> e-mail | 18.5 (from the phone line) | 18.5 |
| e-mail -> `ABSTRACT` | 38.6 | 38.9 |
| `ABSTRACT` -> first abstract line | 11.0 | 11.0 |
| body line pitch | 10.32 (10.35 nominal) | 10.32 (10.35 nominal) |
| paragraph gap (last line -> first line of next paragraph) | 16.4 | 16.3 nominal; 16.6-17.0 in columns that LaTeX stretches to flush the bottom |
| body -> section / subsection head | 19.2-19.4 | 19.2 natural; up to about 20 in stretched columns |
| section head -> first body line | 10.8-11.0 | 11.0-11.3 |
| section head -> subsection head directly below | 13.4-13.7 | 13.9 |
| body -> subsubsection head | 18.2 | 18.0 |
| heading at the very top of a column: baseline from page top | 83.2 | 82.8 |
| heading text x position (hanging indent after the number) | 90.0 | 90.0 |

("Natural" = measured in a test document with `\raggedbottom`; in the demo `\flushbottom` stretches the glue by a
fraction of a point per gap so that both columns end on the same line.)

## 3. Fonts and sizes

Sizes are read from the PDF content streams (`Tf` operators), box heights from `pdftotext -bbox-layout`.
The template's fonts are Times New Roman and Helvetica Neue; those are not available to TeX, so metric-compatible
Times/Helvetica clones are used.

| Element | Template font, size | Template box height | Ours (tectonic/XeLaTeX) | Our box height |
|---|---|---|---|---|
| Title | Helvetica Neue Bold 18 | 22.7 | TeX Gyre Heros Bold 18 | 18.0 |
| Author name | Helvetica Neue 12 | 15.1 | TeX Gyre Heros 12 | 12.0 |
| Affiliation | Helvetica Neue 10 | 12.6 | TeX Gyre Heros 10 | 10.0 |
| E-mail | Helvetica Neue 12 | 15.1 | TeX Gyre Heros 12 | 12.0 |
| `ABSTRACT`, section heads (caps), subsection heads | Times New Roman Bold 12 | 13.3 | TeX Gyre Termes Bold 12 | 12.0 |
| Subsubsection heads | Times New Roman Italic 11 | 12.2 | TeX Gyre Termes Italic 11 | 11.0 |
| Body, abstract text, footnotes | Times New Roman 9 | 10.0 | TeX Gyre Termes 9 | 9.0 |
| Captions ("Table 1.", "Figure 1.") | Times New Roman Bold 9 | 10.0 | TeX Gyre Termes Bold 9 | 9.0 |

Box heights differ only because the font box is 1.26 em (Helvetica Neue), 1.107 em (Times New Roman) or about
1.0 em (TeX Gyre) tall; the point sizes match. With pdfLaTeX (Overleaf) the faces are Nimbus Roman No9 L
(Times) and Nimbus Sans L (Helvetica) from `psnfss`, same sizes. Other sizes (not in the template): table text 8 pt,
inline `\code` 8 pt, listings 7.5 pt (Latin Modern Mono / Typewriter).

Captions: figure captions are centered below, table captions centered above, words spelled out
(checked in `template_demo.pdf`). Section heads are ALL CAPS and numbered (`1.`), flush left, number in a
36 bp hanging field so wrapped heads align at x = 90 (as in the template).

## 4. Last page

| | Template | Ours (`template_demo.pdf`, page 3) |
|---|---|---|
| Bottom of column 1 / column 2 | 350.3 / 256.7 pt (difference 93.6 pt; the template PDF itself does not satisfy its own rule because its figure overlaps the text) | 547.9 / 547.9 pt (difference 0.0 pt) |

Balancing uses `flushend`; it works at line granularity, so a difference of up to one line is possible when the
total number of lines is odd, and it can leave a single line (widow) at the top of the second column.
A `figure*` or `table*` on the last page can also upset it: re-check the last page after the final edit.

## 5. Remaining deviations (all of them)

1. **Typefaces** are clones, not Times New Roman / Helvetica Neue; line breaks can differ from Word by a word here
   and there.
2. **Title block.** The paper's title needs two lines (the template's sample is one line), and the e-mail line follows
   the affiliation directly because the phone line is omitted as instructed. The block is 22.6 pt taller (second title
   line) and 12.7 pt shorter (no phone line) than the template's; all spacings inside it match to 0.25 pt.
3. **Spacing noise.** E-mail -> ABSTRACT 38.9 vs 38.6 pt (+0.3, at the resolution of the measurement); section
   head -> first line 11.0-11.3 vs 10.8-11.0; head -> subhead 13.9 vs 13.4-13.7. In columns stretched by
   `\flushbottom` gaps grow by up to about 1 pt. The template (Word) is ragged at the column bottoms, ours is flush.
4. **Right edge of text** is 0.5 pt further right than the template's on average and glyph overhang (hyphens) reaches
   up to 1 bp past x = 558.
5. **Paragraphs** follow the template (no indent, 6 pt gap). `\documentclass[indent]{cs259}` gives indented paragraphs.
6. **References.** Numbered `[1]`, label at the column edge, text hanging 18 pt, 4 pt between entries,
   ragged right, alphabetical by first author (`cs259.bst`, verified with a 22-entry list and with the demo list).
   The template's *rendered* reference list is justified although its text says "ragged right"; we follow the text.
   Entry wording is BibTeX's ("Last, F. M. Title. Journal, vol(no):pages, year. URL"), close to but not identical to the
   Communications of the ACM examples in the template.
7. **Tables** use booktabs rules (the template's sample table has none) and 8 pt text (the sample uses 9 pt);
   change with `\renewcommand{\tablefont}{\normalsize}`.
8. **Two-column floats** (`figure*`, `table*`) can only be placed at the top of a page by LaTeX; the template asks for
   "as close to the reference as possible", so wide floats must be placed in the source before the text that cites them.
9. **Heading hyphenation** is switched off; a long heading wraps at word boundaries.
10. **pdfLaTeX was not run here.** No `pdflatex` binary is installed on this machine, so the Overleaf engine
    itself could not be executed. Verified instead: (a) the full project compiles error-free and without
    warnings with tectonic (XeTeX) and `build.sh` reports no overfull box; (b) the class's pdfLaTeX font branch
    (`T1`, `mathptmx`, `helvet`, `lmtt`, `microtype` without expansion) was compiled by forcing that branch under
    tectonic and gives the same layout with Nimbus Roman / Nimbus Sans; (c) every kernel macro the class redefines
    was compared against the TeX Live 2026 `latex.ltx`/`article.cls` sources. Not exercised: pdfTeX-specific lines
    (`\pdfpagewidth`, microtype font expansion) and pdfTeX's handling of the `\code` string loop.
