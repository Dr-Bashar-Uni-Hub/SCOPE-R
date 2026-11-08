"""Sequence-level check: real-data replanning streams (same generator and seeds as phase124/bench_heart.py)
with full MBR vs MBR without the structural Lemma-3 cases. Usage: python seq_heart_noL3s.py D START N"""
import sys, os, random, time, gc, csv, math
H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [H, os.path.join(H, '../phase124'), os.path.join(H, '../phase123')]
from mbr_iso import MBRIso
from mbr import exhaustive
import heart
sys.argv_saved = sys.argv; D, S0, N = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
sys.argv = [sys.argv[0], str(D), '1', '1']
import bench_heart as bh           # reuse its exact event() generator
rows, _ = heart.consistent(heart.load(), 'overlap'); out = []
for st in range(S0, S0 + N):
    p = heart.HeartInstance(rows, D, 'overlap', safe_num=99); r = random.Random(124000 + D * 100 + st)
    A, B = MBRIso(p), MBRIso(p, L3s=False); ta = tb = 0
    for k in range(30):
        kind, s, w = bh.event(p, r)
        for name in (['A', 'B'] if k % 2 else ['B', 'A']):
            o = A if name == 'A' else B
            gc.collect(); gc.disable(); t = time.perf_counter_ns(); o.update(kind, s, w); dt = time.perf_counter_ns() - t; gc.enable()
            if name == 'A': ta += dt
            else: tb += dt
        assert abs(A.value - B.value) < 1e-7 or A.value == B.value
        if k % 10 == 0:
            v = exhaustive(p)[0]; assert A.value == v or abs(A.value - v) < 1e-7
    out.append(dict(D=D, stream=st, full_update_ns=ta, noL3s_update_ns=tb, ratio_noL3s_over_full=tb / ta))
    print(D, st, 'update time full %.3fs  noL3s %.3fs  ratio %.2f' % (ta / 1e9, tb / 1e9, tb / ta), flush=True)
fn = os.path.join(H, 'results', f'seq_heart_D{D}_noL3s_{S0}.csv')
with open(fn, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
