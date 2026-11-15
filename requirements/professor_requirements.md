# Professor requirements (CS 259 - Advanced Parallel Processing)

## Sources actually available
1. **Formatting template** - `CS259-TermPaper-Format-Template.doc.pdf` and `CS259 - PDF Sample Template.pdf`
   (same content; ACM two-column "CS259-A: ACM Word Template for Parallel Processing"). Not copied into
   this repository.
2. **Project proposal** submitted by the student (one page, "CS 259 - Project Proposal").
3. **Statements by the student** (this project's author) about the course: see "Confirmed by the student".

No separate assignment sheet, grading rubric, page limit or submission form was provided. Nothing below
is invented: items that no source states are listed as *not specified*.

## Summary of the instructions
- Write a term paper in the provided ACM-style two-column format (below).
- The project (from the proposal): compare **sequential CPU, OpenMP, CUDA and hybrid CPU-GPU**
  implementations of a computational workload used in deep learning, in terms of **execution time,
  speedup and scalability across different workload sizes**, to determine when CPU parallelism,
  GPU acceleration or a hybrid approach is most effective.

## Deliverables
| Deliverable | Source | Status |
|---|---|---|
| Term paper as PDF in the template format | template + student | planned (Overleaf source + compiled PDF) |
| Overleaf (LaTeX) project including the code | student | planned |
| Slides, sent to the professor by e-mail (PowerPoint) | student | planned |
| Oral presentation, 20 minutes | student | planned |
| Rubric / page limit / submission portal | - | **not specified** |

## Formatting requirements (from the template)
- US Letter; text block 7 x 9.25 in, centred, 1 in top and bottom, 0.75 in left/right margins.
- Two columns, each 3.33 in wide, 0.33 in gutter. Figures/tables may span both columns up to 7 in.
- Body: Times (Roman) 9 pt, justified. Sans-serif / monospace only for special purposes (e.g. source code).
- Title Helvetica 18 pt bold; author Helvetica 12 pt; affiliation Helvetica 10 pt; e-mail Helvetica 12 pt;
  title block one column wide across the page.
- Section heads: Times 12 pt bold, ALL CAPS, flush left, numbered, 6 pt above. Subsections: 12 pt bold, initial
  capitals only, numbered. Subsubsections: 11 pt italic, numbered.
- Captions: Times 9 pt bold, "Table 1" / "Figure 1" spelled out; figure captions centred below,
  table captions centred above.
- References: Communications of the ACM style, numbered list at the end, ordered alphabetically by first
  author, cited by number in brackets, 9 pt, ragged right. Only publicly accessible material.
- No headers, footers or page numbers. Columns on the last page balanced.

## Confirmed by the student (messages, 2026-11-15)
- Due date: **2026-11-16** (tomorrow at the time of writing).
- No grading rubric and no further requirements from the professor.
- Presentation length: **20 minutes**.
- Slides will be e-mailed to the professor as a PowerPoint file.
- Paper needed as PDF, plus the Overleaf version of the source together with the code.
- Title as submitted to the professor: "Perf Eval of Hybrid CPU-GPU Parallelism for Deep Learning using
  OpenMP & CUDA"; the paper uses the spelled-out form "Performance Evaluation of Hybrid CPU-GPU Parallelism for
  Deep Learning Using OpenMP and CUDA".
- GitHub repository must be private; the only contributor is the student.
- Spartan (SJSU HPC) and Colab Pro may be used for the experiments.
- Report only numbers that were measured; no assumed values.

## Compliance checklist
See `requirements/compliance_matrix.md`.
