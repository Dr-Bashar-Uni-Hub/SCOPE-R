# Phase 122–123 results and research decision (7 Nov 2026)

Environment: Python 3.12.3, standard library only, single Intel Xeon @ 2.10 GHz core, Linux.
Timing: perf_counter_ns, GC collected before and disabled during each timed call, randomised solver
order per update, initialisation included. Statistics: median of per-sequence total-time ratios,
percentile bootstrap 95% CI over sequences (10,000 resamples). Updates follow Phase 121 `change()`;
balanced and cost-dominated regimes; 24 updates per sequence. Instances: `gen_hard.Inst`
(synthetic; 4 terminal actions, 30% two-action worlds, ¼ action-correlated noisy sensors,
deadline 10).

## A. Phase 122 audit findings
1. Archive SHA-256: 125/125 verified.
2. Phase 121 exactness reproduced (384/384). Timing reproduced only partly: balanced 0.72–0.80×
   (frozen 0.96×), cost-dominated 1.33–1.49× (frozen 1.405×). Frozen "Phase 115 beats ClosureRepair
   on cost-dominated" **reversed** (0.92–0.96×, 3–5/12 wins).
3. Frozen solvers exact under broader semantics: 32,000 fuzz checks, 0 failures (independent rational oracle).
4. Frozen benchmark instances are trivial (134–442 reachable states; sub-millisecond updates).
5. Methodological flaw: GC pauses contaminate timings (an 878 ms pause on a 79-expansion update).
   First Phase 123 pass retained in `results_v1_gcconfounded/` and not used.

## B. Headline results (median speedup of MBR, 95% CI, MBR wins/sequences)

| Worlds/sensors | vs fresh BnB | vs exhaustive DP | vs matched POMDP (Ph.121) | vs ClosureRepair | vs Phase 115 | Expansion ratio BnB/MBR (aggregate) |
|---|---|---|---|---|---|---|
| 12/16 | 1.91 [1.52, 2.13] 12/12 | 6.6 | 6.5 | 8.0 [6.8, 9.8] | 7.5 | 2.87 |
| 16/24 | 2.25 [2.01, 2.65] 12/12 | 17.6 | 19.4 | 22.8 [20.4, 25.0] | 21.9 | 3.27 |
| 20/28 | 2.63 [2.28, 3.00] 10/10 | 34.4 | 64.3 | 38.3 [23.1, 62.5] | 38.4 | 3.73 |
| 24/36 | 2.66 [2.24, 3.70] 8/8 | 86.4 | – (2^n tables) | 104 [84, 130] | – | 3.70 |
| 32/44 | 2.78 [2.33, 3.34] 6/6 | 138 [105, 334] | – | – (memory/time) | – | 3.41 |
| 40/52 | 2.83 [2.37, 3.48] 8/8 | – | – | – | – | 3.41 |

31–42% of updates needed **zero** node expansions (certificate from retained entries).
The 40/52 size has no independent oracle (checked against fresh BnB only).

**Stronger-heuristic control** (Huffman bound in both solvers): MBR-H vs fresh BnB-H = 2.17
[1.95, 2.82] (20/28, 10/10) and 3.28 [2.57, 4.29] (24/36 balanced, 4/4); expansion ratio 2.88 / 4.73.
Negative: the Huffman bound cuts expansions ~20% but is slower in wall-clock (plain MBR 1.3–1.4×
faster than MBR-H) because of Python overhead.

**Ablation** (expansions; identical streams):
- Removing one component (16/24, 12 seq.): locality +58%, monotone bounds +21%, untouched certificate
  +10%, temporal +6%, single-use +4%, replay +4%; all removed = fresh BnB (×3.08, identical counts —
  consistency check).
- Single component only (20/28, 6 seq.; fresh BnB = 50,783 expansions; full MBR = 17,422):
  monotone bounds (L2+L3) 28,233 (−44%); locality 38,185 (−25%); single-use 48,726 (−4%); replay
  48,700 (−4%).
- Interpretation: the monotone-update certificates are the main driver; locality is standard but
  complementary; single-use and replay are marginal and could be dropped from a paper.

Weak spots: cost decreases and delay decreases retain little (no lower bounds survive delay decrease).

## C. Research decision

**Not ready for ESWA submission yet; scientifically justified to continue on this line**, because for
the first time in the project there is (i) a precisely delimited technical contribution (C1–C2 in
NOVELTY.md), (ii) proofs, and (iii) a large, reproducible, CI-supported advantage over the strongest
fresh baseline of the *same* search family, plus 8–138× over all frozen SCOPE-R methods.

The frozen ClosureRepair/Phase-115 line should be **closed**: superseded on every size tested and
not novel (Ramalingam–Reps family).

Remaining gates before submission, in priority order:
1. Exhaustive literature search (Scopus/WoS) on incremental AO*/LAO*, dynamic test sequencing,
   and warm-started optimal decision trees — novelty of C1 depends on it.
2. External application: real diagnostic or inspection data with measured test costs and delays
   (e.g. Turney 1995 cost-sensitive medical datasets, or a published test-sequencing system
   dependency matrix) and justified safety/deadline constraints. ESWA reviewers will expect this.
3. Stronger external baselines: best-first AO* (Pattipati-style) and an LPA*-style incremental AO*
   adaptation; compiled-language reimplementation or at least a check that ratios hold.
4. Extend Lemma 2–4 analysis to nonuniform priors (straightforward) and report it.
5. Improve loosening updates (cost/delay decreases), the identified weak spot.

## D. Proposed manuscript structure (ESWA)
1. Introduction — repeated exact replanning in diagnostic/inspection expert systems.
2. Related work — DRD, test sequencing (AO*), shielding/almost-sure POMDPs, incremental heuristic
   search (LPA*, Adaptive A*), POMDP model-change reuse (ABT, PBPT).
3. Problem formulation (DRD + deadlines + support shielding) and Theorem 0.
4. Update-monotonicity taxonomy and certificates (Lemmas 1–6, Prop. H).
5. MBR algorithm and exactness theorem.
6. Experiments — synthetic scaling (this phase), real-data case study (to do), ablation, heuristic control.
7. Discussion — limits (deterministic sensors, NP-hardness), negative results (Phases 113–115, 121
   reproduction, GC confound, Huffman overhead).
8. Conclusion.
