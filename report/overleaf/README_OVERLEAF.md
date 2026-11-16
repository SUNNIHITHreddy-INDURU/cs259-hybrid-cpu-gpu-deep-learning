# CS 259 term paper: Overleaf project

LaTeX project that reproduces the instructor's CS 259 (ACM-style, two-column)
template. Paper: *Performance Evaluation of Hybrid CPU-GPU Parallelism for Deep
Learning Using OpenMP and CUDA*.

## Files

| File | Purpose |
|---|---|
| `main.tex` | the paper skeleton (11 sections, `% TODO` placeholders); edit this |
| `cs259.cls` | the template: page geometry, fonts, headings, captions, references, helpers |
| `cs259ieee.bst` | BibTeX style of the paper: IEEE reference format, numbered `[1]`; copy of `IEEEtran.bst` 1.14 (LPPL) renamed, with `doi` and `urldate` fields added. It does not sort, so `main.tex` cites all keys once, alphabetically, with `\nocite` before the first `\cite` |
| `cs259.bst` | BibTeX style of the 3-page layout demo only: numbered `[1]`, sorted alphabetically by first author (Communications of the ACM flavour) |
| `refs.bib` | bibliography database (maintained separately) |
| `figures/` | put the paper's figures here (`\graphicspath` already points to it) |
| `latexmkrc` | makes Overleaf/latexmk use pdfLaTeX + BibTeX and `main.tex` |
| `template_demo.tex`, `demo_refs.bib`, `demo_figs/`, `make_demo_figs.py` | 3-page layout demo that exercises every element (not part of the paper) |
| `build.sh` | local build + overfull-box check |
| `TEMPLATE_CHECK.md`, `check/` | measured comparison with the instructor's template |

## Upload to Overleaf

1. Create the zip with the files at the **root** of the archive (from the repo root):

   ```bash
   cd report/overleaf
   zip -r ../cs259-overleaf.zip . -x 'build/*' 'check/*' '*.pdf' '*.DS_Store' 'make_demo_figs.py' 'build.sh' 'TEMPLATE_CHECK.md' 'README_OVERLEAF.md'
   ```

2. Overleaf: **New Project -> Upload Project** -> pick `cs259-overleaf.zip`.
3. **Menu** (top left) and check:
   * **Compiler: pdfLaTeX**
   * **TeX Live version:** any recent one (2021 or newer; the default is fine)
   * **Main document: `main.tex`**
   * The bibliography uses **BibTeX** (`\bibliographystyle{cs259}` + `\bibliography{refs}`),
     not biber. Overleaf runs BibTeX automatically because `latexmkrc` is in the project root.
4. Click **Recompile**. If the references look stale: *Recompile from scratch* (the arrow next to the
   Recompile button -> "Recompile from scratch").
5. To compile the layout demo instead, set **Main document** to `template_demo.tex` (and switch back afterwards).

Notes
* `figure*` / `table*` (two-column floats) can only be placed at the top of a page by LaTeX; put them in the
  source *before* the paragraph that discusses them so they land on the right page.
* The last page's two columns are balanced automatically (package `flushend`). Re-check the last page after
  every edit; a float on the last page can leave it unbalanced.
* Only references that are cited with `\cite{key}` appear in the list.

## Build locally

The class works with pdfLaTeX (what Overleaf uses) and with XeLaTeX/tectonic. Fonts differ slightly
(pdfLaTeX: Times/Helvetica clones from `psnfss`; tectonic/XeLaTeX: TeX Gyre Termes/Heros); both are
metric-compatible with Times/Helvetica.

```bash
cd report/overleaf

# any installed engine, with the overfull-box check (exit code != 0 on error or overfull box > 5 pt):
./build.sh                  # builds main.tex   -> main.pdf
./build.sh template_demo    # builds the demo   -> template_demo.pdf

# pdfLaTeX + BibTeX by hand
pdflatex main && bibtex main && pdflatex main && pdflatex main

# latexmk (uses latexmkrc)
latexmk main.tex

# tectonic (runs BibTeX itself; downloads packages on first use)
tectonic main.tex
```

If you installed **BasicTeX** (macOS), add the few packages it does not include:

```bash
sudo tlmgr update --self
sudo tlmgr install helvetic sttools siunitx      # Helvetica fonts, flushend, siunitx (optional)
```

`template_demo.pdf` needs the figures first: `python3 make_demo_figs.py` (matplotlib; the generated PDFs
in `demo_figs/` are already included).

## Adding figures and tables

Put figure files in `figures/` (PDF or PNG; vector PDF is best) and refer to them by file name.

```latex
% one-column figure (caption is placed below, "Figure N.")
\colfigure{speedup.pdf}{Speedup over the serial baseline.}{fig:speedup}
\colfigure[tb][0.8\columnwidth]{speedup.pdf}{Narrower figure.}{fig:speedup2}   % [placement][width]

% two-column (wide) figure, up to 7 in
\widefigure{breakdown.pdf}{Time breakdown per epoch.}{fig:breakdown}

% one-column table (caption above, "Table N."), booktabs rules, 8 pt text
\begin{coltable}{Hardware used.}{tab:hw}
\begin{tabular}{@{}ll@{}}
\toprule
Item & Value \\
\midrule
CPU & 16 cores \\
GPU & 16 GB \\
\bottomrule
\end{tabular}
\end{coltable}

% two-column (wide) table
\begin{widetable}{Median time per epoch.}{tab:results}
\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lrrr@{}}
\toprule
Implementation & Time (s) & Speedup & Eff. \\
\midrule
Serial CPU & 9.50 & 1.0$\times$ & 1.00 \\
OpenMP     & 1.62 & 5.9$\times$ & 0.37 \\
\bottomrule
\end{tabular*}
\end{widetable}
```

* The plain `figure`, `figure*`, `table`, `table*` environments work too; captions are formatted
  automatically (figures: below, tables: above).
* Scale an over-wide tabular: `\fitcol{\begin{tabular}...\end{tabular}}` or `\fitwide{...}`.
* Reference with `\figref{fig:speedup}`, `\tabref{tab:hw}`, `\secref{sec:x}`, `\eqnref{eq:y}`
  (or `Figure~\ref{...}`).
* Code: `\begin{lstlisting}[language=CUDA] ... \end{lstlisting}` (7.5 pt monospace; languages C++ and CUDA
  are set up). To number and caption a listing, put it in a figure:
  `\begin{figure}[t] \begin{lstlisting}...\end{lstlisting} \caption{...} \label{...} \end{figure}`.
* Inline code: `\code{omp_set_num_threads}` (underscores and `#` need no escaping).
* Math: `$...$`, `equation`, `align` (amsmath). Units: `\documentclass[siunitx]{cs259}` enables `\SI{16}{\giga\byte}`.
* Subsubsection heads: `\subsubsection{...}` (5.1.1); a fourth level with `\paragraph{...}` (5.1.1.1) needs a
  `\subsubsection` above it.
* Class options: `siunitx`, `indent` (indent paragraphs instead of the template's 6 pt gap), `nobalance`.

### Bibliography tips (BibTeX)

* Put `{...}` around capitalized words in titles you want kept (`{ImageNet}`, `{CUDA}`), otherwise BibTeX
  lowercases them.
* Hyphenated first names: write `Hwu, Wen-mei W.` (Last, First) or `{Wen-mei} W. Hwu`.
* The paper uses `cs259ieee.bst` (IEEE format): write author names as `First Last`, titles in sentence case, journal and proceedings names abbreviated
  (`Commun. ACM`, `Proc. IEEE`), `doi = {10.xxxx/yyyy}` for papers and `url` + `urldate = {Nov. 16, 2026}` for web documents.
* Order: the style does not sort. Add the new key to the `\nocite{...}` list in `main.tex` at its alphabetical position (first author),
  otherwise it is numbered by its first `\cite`.
* `python3 scripts/verify_references.py` re-checks every entry against Crossref / arXiv / the web page and against the rendered PDF.
