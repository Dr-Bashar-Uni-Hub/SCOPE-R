#!/usr/bin/env bash
# Regenerates every benchmark in the paper, using the exact invocations of the recorded runs.
# Runs in a scratch copy (results_rerun/) so committed CSVs are never overwritten.
# Total runtime: several hours on one core. Instances depend only on (n, seed, regime), so chunking
# (REGIME/SEEDS for bench.py, START for bench_heart.py) does not change instances or update streams.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
W="$ROOT/results_rerun"; rm -rf "$W"; mkdir -p "$W"
cp -r "$ROOT/phase122" "$ROOT/phase123" "$ROOT/phase124" "$W/"
rm -rf "$W/phase123/results" "$W/phase124/results"
cd "$W/phase123"
ALL7=mbr,bnb,exh,pomdp,fresh121,closure,lazy115
python3 bench.py S 12 16 6 24 $ALL7
python3 bench.py M 16 24 6 24 $ALL7
for reg in balanced cost_dominated; do for sd in 0 1 2 3 4; do
  REGIME=$reg SEEDS=$sd python3 bench.py L 20 28 5 24 mbr,bnb,exh,pomdp,closure,lazy115; done; done
python3 merge.py L
for reg in balanced cost_dominated; do for sd in 0 1 2 3; do
  REGIME=$reg SEEDS=$sd python3 bench.py XL 24 36 4 24 mbr,bnb,exh,closure; done; done
python3 merge.py XL
for reg in balanced cost_dominated; do for sd in 0 1 2; do
  REGIME=$reg SEEDS=$sd python3 bench.py XXL 32 44 3 24 mbr,bnb,exh; done; done
python3 merge.py XXL
python3 bench.py XXXL 40 52 4 24 mbr,bnb
python3 bench.py LH 20 28 5 24 mbrH,bnbH,mbr,bnb,exh
REGIME=balanced python3 bench.py XLH 24 36 4 24 mbrH,bnbH,mbr,bnb; python3 merge.py XLH
python3 analyze.py S M L XL XXL XXXL
REF=mbrH FB=bnbH python3 analyze.py LH XLH
python3 ablation.py M 16 24 6 24
python3 ablation_only.py L 20 28 3 24
cd "$W/phase124"
for st in 0 2 4 6; do n=2; [ $st -eq 6 ] && n=1; START=$st python3 bench_heart.py 12 $n 30; done
for st in 0 3; do n=$([ $st -eq 0 ] && echo 3 || echo 5); START=$st python3 bench_heart.py 16 $n 30 overlap mbr,bnb,exh; done
python3 analyze_heart.py heart_D12_overlap heart_D16_overlap
cp -r "$ROOT/phase128" "$W/" && rm -rf "$W/phase128/results" && cd "$W/phase128"
for k in delay safety region; do python3 isolation.py syn20 $k 60; done
for d in syn24 heart12 heart16; do for k in delay safety region; do python3 isolation.py $d $k 40; done; done
python3 analyze_isolation.py
python3 seq_heart_noL3s.py 12 0 7
cp -r "$ROOT/phase129" "$W/" && rm -rf "$W/phase129/results" && cd "$W/phase129"
for k in delay safety region; do python3 lazy_bench.py syn20 $k 60; python3 lazy_bench.py syn24 $k 40; python3 lazy_bench.py syn32 $k 30; done
for d in heart12 heart16; do for k in delay safety region; do python3 lazy_bench.py $d $k 20 0; python3 lazy_bench.py $d $k 20 20; done; done
python3 analyze_lazy.py; python3 seq_heart_lazy.py 12 0 7
