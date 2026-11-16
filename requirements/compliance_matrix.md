# Compliance matrix

| # | Requirement | Source | Where satisfied | Verification |
|---|---|---|---|---|
| 1 | Four implementations: serial, OpenMP, CUDA, hybrid | proposal | `src/serial`, `src/openmp`, `src/cuda`, `src/hybrid` | built; `nn_validate` compares all four |
| 2 | Metrics: execution time, speedup, scalability across workload sizes | proposal | `analysis/`, paper Section "Results" | batch sizes 1-4096; thread sweep |
| 3 | Determine when CPU / GPU / hybrid is best | proposal | paper Sections "Results" and "Discussion" | crossover table from measured data |
| 4 | Template page geometry, fonts, headings, captions | template | `report/overleaf/cs259.cls`, `TEMPLATE_CHECK.md` | measured against template PDF |
| 5 | References numbered, alphabetical by first author (template: CACM format; student asked for IEEE entry format, 2026-11-16) | template, student | `report/overleaf/refs.bib`, `cs259ieee.bst` | `docs/reference_check.md` (`scripts/verify_references.py`), `docs/reference_verification.md` |
| 6 | No headers / footers / page numbers | template | class file | visual check of compiled PDF |
| 7 | PDF of the paper | student | `report/` | compiled and inspected page by page |
| 8 | Overleaf project with code | student | `report/overleaf/` (+ code bundle) | zip imports and compiles |
| 9 | Slides as PowerPoint, 20-minute talk | student | `presentation/` | timing in speaker notes |
| 10 | Only measured numbers | student | all tables/figures generated from `results/raw` | scripts in `analysis/` |
| 11 | Private repo, sole contributor | student | git history | `git log` scan before every push |
