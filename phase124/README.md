# SCOPE-R Phase 124 — Real-data case study (Cleveland heart disease) and novelty gate

Data: data/processed.cleveland.data (UCI; fetched from raw.githubusercontent.com/StatQuest/logistic_regression_demo;
sha256 a74b7efa387bc9d108d7d0115d831fe9b414b29ae7124f331b622b4efa0427c8). 303 rows, 297 complete.
Costs: Turney 1995 JAIR Table 17 (first-in-group = no-discount setting). Delays: Sheng & Ling ICML 2006 Table 1 (hours),
converted to half-hour units, min 1. Cut-points, decision regions, safety rule: modelling assumptions (heart.py docstring).

Files: heart.py (instance), mbr.py (copy of Phase 123 solver), bench_heart.py (replanning benchmark, chunked via START env),
analyze_heart.py (merge + bootstrap CIs). results/heart_D12_overlap, results/heart_D16_overlap, results/summary_*.txt.

Reproduce: python bench_heart.py 12 7 30           # mbr,bnb,exh,closure
           python bench_heart.py 16 8 30 overlap mbr,bnb,exh
           python analyze_heart.py heart_D12_overlap heart_D16_overlap
