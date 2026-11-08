# SCOPE-R — Certified exact replanning for deadline-constrained diagnostic test selection

Research code, verification artifacts and raw results for the manuscript
*"What can be reused after a model update? Certificates and limits for exact replanning of constrained diagnostic
test strategies"* (prepared for the *International Journal of Approximate Reasoning*; status: in preparation).
An earlier version targeted *Expert Systems with Applications*; it is superseded.

Repository URL: https://github.com/Dr-Bashar-Uni-Hub/SCOPE-R

## What is here

| Path | Content |
|---|---|
| `phase123/mbr.py` | **Main implementation**: `exhaustive` (independent exhaustive DP oracle), `BnB` (fresh exact branch-and-bound), `MBR` (Monotone Bound Reuse replanner, with ablation switches), `BnBH`/`MBRH` (Huffman-type bound variants). |
| `phase123/gen_hard.py` | Synthetic instance generator used for all synthetic benchmarks. |
| `phase123/bench.py`, `analyze.py`, `merge.py` | Synthetic sequential-replanning benchmark, bootstrap statistics, chunk merging. |
| `phase123/test_exact.py`, `test_exact_feasible.py`, `test_exact_H.py`, `test_lemmas.py`, `test_heuristic.py` | Exactness tests (vs exhaustive DP, frozen solver, exact-rational oracle), state-level lemma checks, heuristic admissibility. |
| `phase123/ablation.py`, `ablation_only.py` | Component ablations. |
| `phase123/results/` | **Raw per-update and per-sequence CSVs** (GC-controlled; authoritative). |
| `phase123/results_v1_gcconfounded/`, `logs_v1_gcconfounded/` | First benchmark pass, retained as a documented negative methodological finding (garbage-collection pauses contaminated timings). **Do not cite.** |
| `phase124/` | Real-data case study: `heart.py` (instance builder), `bench_heart.py`, `analyze_heart.py`, `data/processed.cleveland.data`, `results/`. `phase124/mbr.py` is a byte-identical copy of `phase123/mbr.py`. |
| `phase122/` | Independent audit of the frozen SCOPE-R Phase 121 work: `repro121/` (portable copy of frozen Phase 115/120/121 baselines + 6 reproduction runs), `fuzz/` (exact-rational oracle and adversarial fuzz). |
| `literature_screening/` | Novelty-screening scripts and decision logs (raw Scopus/WoS exports are **not** redistributed; see below). |
| `docs/` | Theory and proofs, novelty assessment, results summary, reproducibility guide, reference verification log, clinical review checklist, generative-AI declaration draft. |
| `phase128/` | Final audit: Proposition H admissibility, edge-case exactness, certificate isolation ablation (see `phase128/README.md`). |
| `phase129/` | Lazy structural certificate: four-variant benchmark, correctness tests, verdict (not a reliable improvement over no certificate on real data). |
| `phase130/` | Feasibility investigation of minimal recomputation regions after non-monotone updates: verified counterexamples; verdict in `docs/PHASE130_FEASIBILITY.md`. |
| `figures/` | `make_figures.py` regenerates Figures 1–5 (PNG 300 dpi + vector PDF) from the released data and solvers; `fig_instance.py` defines the Figure 1 instance. |
| `scripts/` | One-command smoke test, verification suite and full benchmark commands. |

## Quick start

Python ≥ 3.10, standard library only for all solvers, tests and benchmarks.

```bash
bash scripts/smoke_test.sh          # ~1 min: exactness, lemma checks, real-data headline values
bash scripts/run_verification.sh    # ~10 min: full verification suite
bash scripts/run_benchmarks.sh      # hours: regenerates all benchmark CSVs (writes to results_rerun/ copies)
```

Expected smoke-test output includes `ALL EXACT`, `violations 0`, `PASS`, and the real-data values
`D=12 value 102.11`, `D=16 value 85.13`, `D=20 value 76.17`, `D=40 value 68.5`.

## Headline results (from the CSVs in this repository)

Synthetic (median per-sequence speed-up of MBR, bootstrap 95% CI): vs fresh BnB 1.91× [1.52, 2.13] (12/16) to 2.83× [2.37, 3.48] (40/52);
vs exhaustive DP 6.6×–138×; vs dependency-graph repair 8.0×–104×.
Real data (Cleveland, 296 patients): 3.76× [3.13, 4.19] (6 h deadline) and 6.60× [5.37, 9.02] (8 h) vs exhaustive DP; median replan 11–15 ms.
Certificate isolation (Phase 128): the structural retained-exactness certificate reduces expansions but speeds up replanning only after delay increases on synthetic instances (1.46×, 1.37×) and slows it elsewhere (0.37–0.92×); MBR's speed-ups come from established reuse (`phase128/`).
Full tables: `docs/RESULTS_AND_DECISION.md`; mapping from every manuscript number to its source file: `docs/REPRODUCIBILITY.md`.

## Scope and limitations (read before use)

* Research prototype in pure Python; absolute timings are machine-specific. Speed-ups are paired, same-machine ratios.
* The clinical case study uses **unvalidated modelling assumptions** (cut-points, decision regions, safety rule). It is **not** clinical decision support and has **not** been validated by clinicians. See `docs/CLINICAL_REVIEW_CHECKLIST.md`.
* Novelty claims are deliberately narrow; see `docs/NOVELTY.md`.

## Data and third-party material

* `phase124/data/processed.cleveland.data`: UCI Heart Disease (Cleveland), Janosi, Steinbrunn, Pfisterer & Detrano (1989), doi:10.24432/C52P4X, licensed **CC BY 4.0**. Obtained from a public mirror; SHA-256 `a74b7efa387bc9d108d7d0115d831fe9b414b29ae7124f331b622b4efa0427c8` (see `phase124/README.md`).
* Test costs: Turney (1995), JAIR 2:369–409, Table 17. Test delays: Sheng & Ling (2006), ICML, Table 1. Values are transcribed as parameters in `phase124/heart.py`.
* Literature screening: Scopus and Web of Science exports are subject to provider terms and are not included; only our scripts and screening decisions (titles/DOIs) are.

## Licence

Code: MIT (see `LICENSE`) — **authors to confirm licence choice and copyright holder before publication.** Data: CC BY 4.0 (UCI). Documentation: CC BY 4.0 unless stated otherwise.

## Citation

See `CITATION.cff` (author fields to be completed).
