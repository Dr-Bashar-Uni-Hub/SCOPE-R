#!/usr/bin/env bash
# Quick check (~1 min): exactness, state-level lemma checks, Phase 113 regression, real-data headline values.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/phase123"
python3 test_exact.py 123001 60
python3 test_lemmas.py
cd "$ROOT/phase124"
python3 - <<'PY'
from heart import load, consistent, HeartInstance
from mbr import BnB
rows, dropped = consistent(load(), 'overlap')
print('patients', len(rows), 'dropped', dropped)
for D in (8, 12, 16, 20, 40):
    print('D=%d value' % D, round(BnB(HeartInstance(rows, D, 'overlap', safe_num=99)).value, 2))
print('safety (num>=3), D=16 value', BnB(HeartInstance(rows, 16, 'overlap', safe_num=3)).value)
r2, _ = consistent(load(), 'binary')
print('binary regions, D=16 value', round(BnB(HeartInstance(r2, 16, 'binary', safe_num=99)).value, 2))
PY
