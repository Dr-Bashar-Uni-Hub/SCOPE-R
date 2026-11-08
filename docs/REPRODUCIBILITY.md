# Reproducibility guide: manuscript number → source artifact

## IJAR manuscript (current) — table and section map
| IJAR manuscript item | Source | Regenerate |
|---|---|---|
| Table 2, heuristic control (Section 7.2) | `phase123/results/` | `python phase123/analyze.py S M L XL XXL XXXL`; `REF=mbrH FB=bnbH python phase123/analyze.py LH XLH` |
| Table 3 (Section 7.3) | `phase123/results/ablation/` | `python phase123/ablation_only.py L 20 28 3 24` |
| Table 4 and sequence-level check (Section 7.3) | `phase129/results/` | see `phase129/README.md` |
| Tables 5–6 (Section 7.4) | `phase124/` | `bash scripts/smoke_test.sh`; `python phase124/analyze_heart.py heart_D12_overlap heart_D16_overlap` |
| Section 5 instances | `phase130/counterexamples.py` | `python phase130/counterexamples.py` |
| Figures 1–5 | `figures/out/*.png`, `*.pdf`, `fig5_data.csv` | `python figures/make_figures.py` (asserts Table 5 values and the Figure 1 policy values) |
| Appendix A (Proposition H) | `docs/PROPOSITION_H.md`; `phase128/propH_audit.py`; `phase129/test_huffman_definition.py` | as named |
| Correctness counts (Section 7.1) | `phase123/test_*.py`, `phase128/test_edge_cases.py`, `phase129/test_lazy.py`, `phase122/fuzz/` | `bash scripts/run_verification.sh` |

## Earlier (ESWA, Phase 127–128) numbering — kept for the record

All numbers below were produced by the code in this repository; the CSVs are the raw outputs.
Environment of record: Python 3.12.3, standard library, one Intel Xeon @ 2.10 GHz core, Linux.
Timing protocol: `time.perf_counter_ns`, garbage collection forced before and disabled during each timed call,
randomised solver order per update, initialisation included. Statistics: median of per-sequence total-time
ratios; percentile bootstrap 95% CI, 10,000 resamples, fixed seed (`analyze.py`, `analyze_heart.py`).

| Manuscript item | Source | Regenerate |
|---|---|---|
| Table: synthetic scaling (12/16 … 40/52) | `phase123/results/{S,M,L,XL,XXL,XXXL}/sequences.csv`, `updates.csv`; summary `phase123/results/headline_all.txt` | `scripts/run_benchmarks.sh` then `python analyze.py S M L XL XXL XXXL` |
| Heuristic control (2.17×, 3.28×) | `phase123/results/{LH,XLH}/` | `REF=mbrH FB=bnbH python analyze.py LH XLH` |
| Ablation (single-removal, 16/24) | `phase123/results/ablation/M.csv` | `python ablation.py M 16 24 6 24` |
| Ablation (single-component, 20/28; 50,783 → 17,422) | `phase123/results/ablation/L_only.csv` | `python ablation_only.py L 20 28 3 24` |
| ClosureRepair init 6.35 s / 565 MB at n = 24 | console measurement (Phase 123 session log; not stored as CSV) | `python -c` snippet in `docs/RESULTS_AND_DECISION.md` §B context; re-measure on your machine |
| Table 5 — real-data price-of-deadline table, safety infeasibility, binary-region value | deterministic; recomputed by `scripts/smoke_test.sh` | `bash scripts/smoke_test.sh` |
| Table 6 — real-data replanning (3.76×, 4.70×, 48.5×; 6.60×, 3.48×) | `phase124/results/heart_D12_overlap/`, `heart_D16_overlap/`, `phase124/results/summary_D1{2,6}.txt` | `python analyze_heart.py heart_D12_overlap heart_D16_overlap` |
| 100,000 root-value checks (incl. 14,880 exact-rational) | `phase123/test_exact*.py` console output (68,000 + 32,000) | `scripts/run_verification.sh` |
| 79,475 state-level checks; Phase 113 regression | `phase123/test_lemmas.py` | same |
| Huffman bound admissibility (78,795 states) | `phase123/test_heuristic.py` | same |
| 1,602 benchmark updates checked vs exhaustive DP | `updates.csv` row counts of S, M, L, XL, XXL (1,152) and heart D12, D16 (450) | — |
| Phase 121 audit (reproduction, 0.72–0.80× balanced, reversal of Phase 115 claim) | `phase122/repro121/run1..run5/` | `cd phase122/repro121 && python benchmark_portable.py` |
| Frozen-solver fuzz (32,000 checks) | `phase122/fuzz/` | `scripts/run_verification.sh` |

| Table 4 (certificate isolation) | `phase128/results/isolation_*.csv`, `isolation_summary.csv` | see `phase128/README.md` |
| Sequence-level certificate check (3–8%) | `phase128/results/seq_heart_D12_noL3s_0.csv` | `python phase128/seq_heart_noL3s.py 12 0 7` |
| Edge-case exactness (40,000 updates), safety net 0/27,290 | `phase128/test_edge_cases.py` console output | `python test_edge_cases.py mixed`; `... feasible` |
| Proposition H audit (488,362 states) | `phase128/propH_audit.py` console output | `python propH_audit.py` |
| Determinism / ±10% timing noise (Section 6.1) | re-run of `bench.py S 12 16 6 24 ...` compared to `phase123/results/S/updates.csv` | see `phase128/README.md` |

| Phase 129 lazy-certificate benchmark | `phase129/results/lazy_*.csv`, `lazy_summary.csv`, `results_table.md` | see `phase129/README.md` |
| Phase 129 sequence-level real-data check | `phase129/results/seq_heart_D12_lazy_0.csv` | `python phase129/seq_heart_lazy.py 12 0 7` |
| Proposition H formal proof | `docs/PROPOSITION_H.md`; `phase129/test_huffman_definition.py` | `python test_huffman_definition.py` |

| Phase 130 counterexamples CE1–CE4, Lemma D | `phase130/counterexamples.py` console output | `python phase130/counterexamples.py` |

Known reproducibility caveats
1. Absolute times depend on hardware; ratios were stable across our repeated runs but are not guaranteed elsewhere.
2. The ClosureRepair memory figure was read from `resource.getrusage` in an interactive session and was not written to a file.
3. `phase123/results_v1_gcconfounded/` is retained only as a negative finding.
4. 14,880 exact-rational checks = 9,880 (test_exact*, feasible variant) + 5,000 (Huffman variants).
