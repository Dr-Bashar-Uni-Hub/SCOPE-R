# Phase 128 — final scientific audit (8 Nov 2026)

| File | Purpose | Result |
|---|---|---|
| `propH_audit.py` | Proposition H admissibility with overlapping action sets: every subset of hypotheses × every t, 600 instances (up to 6 actions, heavy overlap) + adversarial search maximising h/V | 488,362 states, 0 violations, max h/V = 1.0 → **confirmed** |
| `test_edge_cases.py [mixed|feasible]` | Exactness when replay fails (budget +∞), on feasible↔infeasible transitions; instruments the safety-net re-solve | 40,000 updates exact (9,604 vs exact-rational oracle); 26,355 failed replays; 858 + 691 feasibility transitions; safety net fired 0 / 27,290 |
| `mbr_iso.py` | Instrumented MBR with separate switches for Lemma 2, Lemma 3 (cost) and Lemma 3 (structural); `verify_equivalence()` | identical cache decisions to phase123 MBR on 4,500 updates |
| `isolation.py DATASET KIND TRIALS` + `analyze_isolation.py` | Controlled paired isolation of the structural certificate | `results/isolation_summary.csv`: certificate helps only after delay increases on synthetic instances (1.46×, 1.37×); slowdown 0.37–0.92× in the other 10 settings |
| `seq_heart_noL3s.py 12 0 7` | Sequence-level check on the Table 6 real-data streams | removing the certificate makes updates 3–8% faster on all 7 streams |

Regenerate:
```bash
python propH_audit.py
python test_edge_cases.py mixed; python test_edge_cases.py feasible
python -c "from mbr_iso import verify_equivalence; print(verify_equivalence())"
for d in syn20; do for k in delay safety region; do python isolation.py $d $k 60; done; done
for d in syn24 heart12 heart16; do for k in delay safety region; do python isolation.py $d $k 40; done; done
python analyze_isolation.py
python seq_heart_noL3s.py 12 0 7
```
Also confirmed in this phase (not separate files): re-running `phase123/bench.py S ...` reproduces all 288 optimal values and all MBR/BnB expansion counts exactly; median time ratios move by up to 10% between runs; all reported medians/CIs were recomputed independently from the raw CSVs (numpy) and match (one CI bound at 40/52 differs by resampling: 2.44 vs 2.37).
