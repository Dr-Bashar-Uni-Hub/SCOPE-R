#!/usr/bin/env bash
# Full verification suite (~10 min on one core). All checks compare against independent oracles.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/phase122/fuzz"
python3 fuzz.py 300            # frozen ClosureRepair/Phase 115 vs exact-rational oracle (12,000 checks)
python3 fuzz_stats.py          # nontrivial-instance fuzz (20,000 checks)
cd "$ROOT/phase123"
for s in 123001 123002 123003 123004; do python3 test_exact.py $s 400; done
python3 test_exact_feasible.py 123010 300
python3 test_exact_H.py 123050 400
python3 test_exact_H.py 123051 400
python3 test_lemmas.py
python3 test_heuristic.py
cd "$ROOT/phase128"
python3 propH_audit.py
python3 test_edge_cases.py mixed
python3 test_edge_cases.py feasible
python3 -c "from mbr_iso import verify_equivalence; print('MBRIso equivalence on', verify_equivalence(), 'updates')"
cd "$ROOT/phase129"
python3 test_lazy.py structural 150 129001
python3 test_lazy.py mixed 60 129003
python3 test_lazy.py feasible 60 129004
python3 test_huffman_definition.py
cd "$ROOT/phase130"
python3 counterexamples.py
