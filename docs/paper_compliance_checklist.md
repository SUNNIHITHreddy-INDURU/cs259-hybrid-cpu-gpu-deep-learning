# Paper compliance checklist (final report, 14 pages)

Sources checked: `CS259-TermPaper-Format-Template.doc.pdf`, `CS259 - PDF Sample Template.pdf`, the raw CSV files in `results/raw/`,
the code in `src/`, and the project scripts. The numbers are checked by `scripts/verify_paper_numbers.py`
(result: `docs/paper_number_verification.md`, 84 of 84 claims found in the PDF text).

## 1. Professor's format

| Requirement | Result | How it was checked |
|---|---|---|
| Letter paper, two columns, 7 in text width, 0.75 in side margins, 1 in top/bottom | met | `pdftotext -bbox`: all text lies in x 52.8-559.6 pt and y 71.1-738 pt on all 14 pages (template rectangle 54-558, 72-738; at most 1.6 pt of glyph overhang); `report/overleaf/TEMPLATE_CHECK.md` compares `cs259.cls` with the template page by page |
| 3.33 in columns, 0.33 in gutter | met | 240 pt / 24 pt, as in the template file |
| 9-pt Times body, 18-pt bold title, 12-pt author, 10-pt affiliation | met | `cs259.cls` was not changed in this revision; its sizes and positions were measured against the template in `TEMPLATE_CHECK.md`; fonts are TeX Gyre Termes (Times clone) and TeX Gyre Heros (Helvetica clone) |
| Numbered sections, all-caps 12-pt bold section heads, subsection heads in title case | met | headings 1-11 as requested; subsection titles in title case |
| No headers, footers or page numbers | met | no text above y = 66 pt or below y = 746 pt on any page |
| Justified body text | met | `cs259.cls`; wide tables use left-aligned cells to avoid gaps |
| Table captions above tables, figure captions below figures | met | all 14 tables and 14 figures inspected |
| Tables and figures close to their first discussion | met | each float follows or sits on the page of its first reference |
| References numbered `[1]`, alphabetical by first author | met | 23 entries (22 published works + the author's repository), `cs259ieee.bst`; order checked by `scripts/verify_references.py`; list inspected in the PDF |
| Reference entry format | IEEE style, as the student asked on 2026-11-16 | initials before surnames, quoted sentence-case titles, abbreviated journal and proceedings names, `doi:`, `Accessed:` and `[Online]. Available:` for web documents. The template's own sample list is in Communications of the ACM format; the template's rule (numbered, ordered alphabetically by first author, cited as `[1]`) is kept, which differs from plain IEEE (numbered by first citation) |
| Columns on the last page of equal length | met | page 14: both columns end at the same height |
| No clipped figures, overlapping text or broken glyphs | met | all 14 pages inspected at 100 dpi; fonts embedded; "ff" ligature appears only in `pdftotext` output, not on the page |
| Clean build | met | `build.sh` (tectonic): no overfull box wider than 5 pt; the Overleaf zip compiles from a clean directory to an identical PDF |

## 2. Required structure

1 Introduction; 2 Background and Related Work (2.1 OpenMP and CUDA, 2.2 Scaling Laws, 2.3 Related Work); 3 Workload and Dataset
(3.1 Dataset, 3.2 Neural Network, 3.3 Pipeline); 4 Implementations (4.1 Serial CPU, 4.2 OpenMP, 4.3 CUDA with Single-Threaded
Preprocessing, 4.4 Hybrid OpenMP-CUDA); 5 Experimental Method (5.1 Hardware and Software, 5.2 Measurement Protocol, 5.3 Metrics);
6 Correctness Validation; 7 Performance Results (7.1 OpenMP Scalability, 7.2 End-to-End Comparison, 7.3 CUDA Kernel Versus
End-to-End Performance, 7.4 CUDA Transfer and Preprocessing Overhead, 7.5 Hybrid OpenMP-CUDA Performance, 7.6 CUDA Block Size
and Tuning, 7.7 Initialization and Cold Start); 8 Discussion (8.1 Amdahl's Law and Parallel Overhead, 8.2 Which Implementation Is
Best?); 9 Limitations and Threats to Validity; 10 Conclusion and Future Work; 11 References.
Minor adjustment: the two former discussion subsections "memory traffic" and "launch overhead" are paragraphs of 8.1.

## 3. Figures (final numbering) and what changed

| Final no. | Content | Requested as | Status |
|---|---|---|---|
| 1 | Workload flow chart: MNIST image, preprocessing, hidden layer, ReLU, output layer, argmax, predicted digit (stages 0-3) | Figure 1 | revised (ReLU is its own box, stage labels added) |
| 2 | Execution architecture of serial, OpenMP, CUDA, hybrid with OpenMP threads, H2D, kernels, D2H, three CUDA streams, batch overlap | Figure 2 | revised (three streams and overlap were not drawn before) |
| 3 | Hybrid time line (CPU preprocesses batch i+1 while GPU copies and computes batch i; event guard) | flow chart 3 | new |
| 4 | Worst-case logit difference per comparison | - | existing |
| 5 | OpenMP speedup and efficiency, Apple M4 and Xeon on separate panels | Figure 3 | existing |
| 6 | End-to-end time, four implementations, all batch sizes | Figure 4 | caption revised |
| 7 | Speedup over serial, four implementations | Figure 5 | new |
| 8 | Throughput in images per second | Figure 6 | new in the paper (generated before) |
| 9 | CUDA kernel-only versus end-to-end | Figure 7 | revised: the kernel-only speedup is now compute-only (see 5) |
| 10 | CUDA time breakdown by stage | Figure 8 | existing |
| 11 | Hybrid ablation | - | existing |
| 12 | CUDA block size | Figure 9 | existing |
| 13 | Cold start versus steady state | Figure 11 | new |
| 14 | Amdahl fit and measured OpenMP speedup | Figure 10 | existing |

All data figures are generated from the CSV files by `analysis/generate_figures.py`; the two diagrams are drawn by the same script.

## 4. Tables (final numbering)

| Final no. | Content | Requested as | Status |
|---|---|---|---|
| 1 | Work per image and parameter size | Table 1 | existing |
| 2 | Hardware and software (lscpu: 2 x 14 cores x 1 thread = 28 CPUs, 24 allocated) | Table 2 | existing, cell alignment fixed |
| 3 | Compiler settings | - | existing |
| 4 | Correctness (tests, max logit difference, agreement, accuracy) | Table 3 | existing |
| 5 | OpenMP scaling (time, speedup, efficiency) | Table 4 | existing |
| 6 | End-to-end comparison for every batch size | Table 5 | revised: OpenMP speedup column added, kernel-only speedup corrected (see 5) |
| 7 | Compute-only comparison | - | existing |
| 8 | CUDA time by stage | - | existing |
| 9 | Micro-benchmarks | - | existing |
| 10 | Hybrid ablation | - | existing |
| 11 | Fastest implementation per batch size | - | existing |
| 12 | CUDA block-size comparison | Table 6 | new |
| 13 | Cold start | Table 7 | existing |
| 14 | Compiler-flag sensitivity | Table 8 | existing |

## 5. Correction found during this revision

The kernel-only speedup column of the end-to-end table, the right panel of the kernel-versus-end-to-end figure and one sentence
of the text divided the **serial end-to-end** time by the GPU **kernel** time (53.65x at batch 4096). That mixes an end-to-end time
with a compute-only time. They now divide the serial time of stages 1-3 by the kernel time (52.77x at batch 4096; 1.11x instead of
1.13x at batch 1), as the text of Section 7.3 and the abstract always did. Table and figure captions state the definition.

## 6. Numerical consistency (all recomputed from `results/raw/*.csv`)

| Claim | Value in the paper |
|---|---|
| OpenMP speedup, 24 threads, batch 4096 | 21.55x (efficiency 0.90) |
| GPU kernels vs serial, compute-only, batch 4096 | 52.77x |
| GPU kernels vs best OpenMP, compute-only, batch 4096 | 2.44x (23.03 ms vs 56.13 ms) |
| CUDA end-to-end speedup, batch 4096 / batch 1 | 26.44x / 0.82x |
| Hybrid time, batch 4096 | 24.70 ms |
| Hybrid vs CUDA pipeline / vs best OpenMP, batch 4096 | 1.89x / 2.32x |
| Preprocessing share / copy share of the CUDA pipeline, batch 4096 | 43.3 % / 7.3 % |
| One-time GPU set-up | 110.7 ms (106.83 + 0.40 + 2.97 + 0.45 not itemized) |
| Largest logit difference / tolerance | 7.6e-6 / 1e-4; 80 comparisons, all pass |
| Hybrid first faster than best OpenMP | batch 32; the CUDA pipeline is level with the best OpenMP at batch 128 (58.62 ms vs 58.25 ms) and ahead from batch 256 |

Abstract, results, discussion and conclusion take their measured values from `numbers.tex`, which is generated from the raw data;
a few counts typed by hand (seven thread counts, 20 recorded passes) were checked against the code and the CSV files.
Comparison labels: "compute-only" (stages 1-3, GPU kernels) and "end-to-end" (stages 0-3 with copies) are named wherever a ratio is given.

## 7. References

23 entries, each cited in the text (the repository, reference [11], in the Availability paragraph and in Section 11), numbered in
alphabetical order of the first author. Re-checked on 2026-11-16 with `scripts/verify_references.py` (report:
`docs/reference_check.md`): for the 16 entries with a Crossref record, the DOI is registered in the DOI system and every author's
family name (count and order), the title (with subtitle), year, month, volume, issue, pages and the conference city match Crossref
or the second source named in the report (Amdahl: Semantic Scholar and the Crossref record of the IEEE reprint; LeCun: the heading
of the author's PDF, read by eye; SLURM: the Crossref record of the book and OpenAlex); the arXiv entry (Kingma and Ba) matches the
arXiv record; the three NVIDIA blog posts show the cited title, author and month, the CUDA guide shows "Last updated on Oct 31, 2026"
and the OpenMP specification's title page reads "Version 5.2 November 2021". Every entry's first author, title, year, pages and DOI or
URL were also found in the rendered reference list. One reworded claim: the sentence on Hill and Marty now states what their abstract
says (optimal multicore performance needs more parallelism and faster sequential cores). Topics: Amdahl, Gustafson, Karp-Flatt,
Hill-Marty, roofline, benchmarking practice, OpenMP, CUDA, transfers, streams and overlap, pinned memory, Slurm, CPU-GPU comparison
and collaboration, deep-learning performance, MNIST, initialization and optimizer. Provenance of each field:
`docs/reference_verification.md`.

All 23 entries pass, including the repository entry: with no credentials, `https://github.com/SUNNIHITHreddy-INDURU/cs259-hybrid-cpu-gpu-deep-learning` answers HTTP 200 (see section 9).

Section 11 also carries an "Original material" paragraph: all figures and tables were created by the author for the paper from the
project's own measurements, source code and calculations, none copied or adapted from another publication; the data figures are
generated by scripts from the raw measurements, the three diagrams were drawn by the author; the code, raw measurements and report
source are the author's own work and are reference [11].

## 8. Asymmetries stated in the paper

GPU initialization is excluded from steady-state times (reported separately, Section 7.7); CUDA preprocesses with one thread;
OpenMP and hybrid use the best of seven thread counts per batch size; CUDA uses a fixed 16x16 block ("The main comparison is CUDA
with a fixed block size versus OpenMP and hybrid configurations selected from the tested thread counts; it is not a best-versus-best
comparison."); the GPU is an older Tesla K40m; CPU and GPU code use platform-specific optimizations; the cluster is shared and
timing variation is reported (median coefficient of variation 0.2 %).

## 9. GitHub link

The repository URL in the Availability paragraph and in reference [11] is
`https://github.com/SUNNIHITHreddy-INDURU/cs259-hybrid-cpu-gpu-deep-learning`. On 2026-11-16 the project (18 commits, sole author) was pushed
and the repository was set to **public** at the student's request, so the link opens without logging in (HTTP 200 for the repository page
and for `README.md`). Earlier notes of the student (`requirements/professor_requirements.md`) say the repository must be private;
that conflicts with a link the instructor can open without an invitation. The student was told about the earlier note and confirmed on
2026-11-16 that the repository stays public.
