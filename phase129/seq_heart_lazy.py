"""Sequence-level real-data check (Table 6 streams; same event generator and seeds as phase124/bench_heart.py):
no certificate vs eager vs lazy. Usage: python seq_heart_lazy.py D START N"""
import sys, os, random, time, gc, csv
H = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [H, os.path.join(H, '../phase128'), os.path.join(H, '../phase124'), os.path.join(H, '../phase123')]
from mbr_lazy import MBRNoCert, MBREager, MBRLazy
from mbr import exhaustive
import heart
D, S0, N = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
sys.argv = [sys.argv[0], str(D), '1', '1']
import bench_heart as bh
rows, _ = heart.consistent(heart.load(), 'overlap'); out = []
for st in range(S0, S0 + N):
    p = heart.HeartInstance(rows, D, 'overlap', safe_num=99); r = random.Random(124000 + D * 100 + st)
    X = {'nocert': MBRNoCert(p), 'eager': MBREager(p), 'lazy': MBRLazy(p)}; T = {k: 0 for k in X}
    for k in range(30):
        kind, s, w = bh.event(p, r); order = list(X); r.shuffle(order)
        for name in order:
            gc.collect(); gc.disable(); t = time.perf_counter_ns(); X[name].update(kind, s, w); T[name] += time.perf_counter_ns() - t; gc.enable()
        v = X['nocert'].value
        assert all(o.value == v or abs(o.value - v) < 1e-7 for o in X.values())
        if k % 10 == 0: tv = exhaustive(p)[0]; assert v == tv or abs(v - tv) < 1e-7
    out.append(dict(D=D, stream=st, **{f'{k}_ns': T[k] for k in T}, nocert_over_lazy=T['nocert'] / T['lazy'], nocert_over_eager=T['nocert'] / T['eager']))
    print(D, st, ' '.join(f'{k}={T[k]/1e9:.3f}s' for k in T), f"nocert/lazy={T['nocert']/T['lazy']:.3f}", flush=True)
with open(os.path.join(H, 'results', f'seq_heart_D{D}_lazy_{S0}.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
