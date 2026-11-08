# SCOPE-R Phase 122–123 (interim package; frozen Phase 121 untouched)

Phase 122 (`phase122/`): independent audit.
- `repro121/` — portable Phase 121 copy re-run 6x (`run1..run5`, plus top-level CSVs).
- `fuzz/oracle.py` — independent exact-rational oracle (frozensets + Fraction).
- `fuzz/fuzz.py`, `fuzz/fuzz_stats.py` — adversarial fuzz of frozen ClosureRepair / Phase 115 (32,000 checks, 0 failures).

Phase 123 (`phase123/`): Monotone Bound Reuse (MBR) exact replanning.
- `mbr.py` — `exhaustive` (independent oracle DP), `BnB` (fresh exact branch-and-bound), `MBR`.
- `gen_hard.py` — harder synthetic inspection instances (4 terminal actions so frozen solvers run unchanged).
- `test_exact.py`, `test_exact_feasible.py` — exactness tests vs exhaustive DP, frozen `verified.fresh`, and rational oracle.
- `bench.py` — sequential benchmark (Phase 121 `change()` update semantics, randomized order, init included,
  GC collected before and disabled during each timed call). Chunking: `REGIME=balanced SEEDS=0 python bench.py ...`.
- `merge.py`, `analyze.py` — merge chunks; bootstrap CIs (10,000 resamples) and expansion ratios.
- `results/` — GC-controlled results (authoritative). `results_v1_gcconfounded/` — first pass, retained as a
  negative methodological finding (GC pauses contaminated timings). Do not cite v1 numbers.

Reproduce (Python 3.10+, stdlib only), from `phase123/`:
  python test_exact.py 123001 200
  python bench.py S 12 16 6 24 mbr,bnb,exh,pomdp,fresh121,closure,lazy115 && python analyze.py S

## Added in the completed Phase 123
- `../docs/THEORY.md` — formal model, Lemmas 1–7, Proposition H, exactness theorem; proof vs. empirical status.
- `../docs/NOVELTY.md` — verified prior-art matrix and the narrow, falsifiable contribution claim.
- `../docs/RESULTS_AND_DECISION.md` — audit findings, headline tables with CIs, ablation, heuristic control,
  ESWA decision, manuscript outline.
- `test_lemmas.py` — state-level check of every retained exact entry / lower bound + Phase 113 regression.
- `test_heuristic.py` — admissibility of the Huffman bound at every reachable state.
- `ablation.py`, `ablation_only.py` — component ablations (results in `results/ablation/`).
- `mbr_v1_noflags.py` — MBR before ablation switches were added (behaviour identical with defaults).
- `results/headline_all.txt`, `results/summary_*.csv` — statistics produced by `analyze.py`.
- Variants: `BnBH`, `MBRH` (Huffman heuristic) in `mbr.py`.

Expected outputs: test_exact.py → ALL EXACT; test_lemmas.py → 0 violations, PASS;
test_heuristic.py → 78,795 states, 0 violations.
Larger sizes: run chunked, e.g. `REGIME=balanced SEEDS=0 python bench.py XL 24 36 4 24 mbr,bnb,exh,closure`
then `python merge.py XL && python analyze.py XL` (REF/FB env vars select the compared pair).
