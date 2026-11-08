"""Phase 129 benchmark: no certificate vs eager certificate vs lazy certificate vs fresh BnB.

Usage: python lazy_bench.py DATASET KIND TRIALS [START]
  DATASET: syn20 | syn24 | syn32 | heart12 | heart16 ; KIND: delay | safety | region
Same paired design and the same instance / history / update seeds as phase128/isolation.py.
Pass 1 (timed): GC collected before and disabled during each timed update; variant order randomised.
Pass 2 (memory): deterministic re-run of the same trial with tracemalloc around each measured update
(peak bytes above the pre-update level); timing from pass 1 is never taken under tracemalloc.
Every trial: all variants checked against the independent exhaustive DP (syn32: every 3rd trial; other
trials checked against fresh BnB only, recorded in column 'oracle').
"""
import sys, os, random, time, gc, csv, math, tracemalloc
H = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [H, os.path.join(H, '../phase128'), os.path.join(H, '../phase123'), os.path.join(H, '../phase124')]
from mbr_lazy import MBRNoCert, MBREager, MBRLazy
from mbr import BnB, exhaustive, INF
from gen_hard import Inst

ds, kind, trials = sys.argv[1], sys.argv[2], int(sys.argv[3])
start = int(sys.argv[4]) if len(sys.argv) > 4 else 0
SIZES = {'syn20': (20, 28), 'syn24': (24, 36), 'syn32': (32, 44)}

def make(trial):
    if ds in SIZES:
        n, m = SIZES[ds]
        return Inst(n, m, 128000 + 1000 * (ds == 'syn24') + 2000 * (ds == 'syn32') + trial, deadline=10)
    import heart
    rows, _ = heart.consistent(heart.load(), 'overlap')
    return heart.HeartInstance(rows, 12 if ds == 'heart12' else 16, 'overlap', safe_num=99)

def history_step(p, r):
    k = r.choice(['cost', 'delay', 'outcome', 'wait', 'viability']); s = r.randrange(p.m); w = r.randrange(p.n)
    if k == 'cost': p.cost[s] = max(0.0, round(p.cost[s] * r.choice([0.8, 0.9, 1.1, 1.25]), 4))
    elif k == 'delay': p.delay[s] = max(1, p.delay[s] + r.choice([-1, 1]))
    elif k == 'outcome': p.outcomes[s][w] ^= 1
    elif k == 'wait': p.wait[s][w] = not p.wait[s][w]
    else:
        acts = sorted({a for a in p.actions}); p.actions[w] = r.choice([a for a in acts if a != p.actions[w]] or [p.actions[w]])
    return k, s, w

def measured_step(p, r):
    if kind == 'delay':
        s = r.randrange(p.m); p.delay[s] += 1; return 'delay', s, 0
    if kind == 'safety':
        cand = [(s, w) for s in range(p.m) for w in range(p.n) if p.wait[s][w]]
        s, w = r.choice(cand); p.wait[s][w] = False; return 'wait', s, w
    cand = [w for w in range(p.n) if bin(p.actions[w]).count('1') >= 2]
    if not cand: return None
    w = r.choice(cand); bits = [b for b in range(8) if p.actions[w] >> b & 1]
    p.actions[w] &= ~(1 << r.choice(bits)); return 'viability', 0, w

VARIANTS = {'nocert': MBRNoCert, 'eager': MBREager, 'lazy': MBRLazy, 'fresh': BnB}

def setup(trial):
    r = random.Random(f'{ds}-{kind}-{trial}')
    p = make(trial)
    obj = {k: f(p) for k, f in VARIANTS.items()}
    for _ in range(3):
        k, s, w = history_step(p, r)
        for o in obj.values(): o.update(k, s, w)
    return p, r, obj

rows = []
os.makedirs(os.path.join(H, 'results'), exist_ok=True)
for trial in range(start, start + trials):
    # ---------------- pass 1: timing ----------------
    p, r, obj = setup(trial)
    old_value = obj['nocert'].value
    ms = measured_step(p, r)
    if ms is None: continue
    k, s, w = ms
    order = list(obj); r.shuffle(order); rec = {}
    for name in order:
        o = obj[name]; e0 = o.expanded; c0 = getattr(o, 'cert_ns', 0); n0 = getattr(o, 'cert_nodes', 0)
        p0 = getattr(o, 'promoted', 0)
        gc.collect(); gc.disable(); t0 = time.perf_counter_ns(); o.update(k, s, w); dt = time.perf_counter_ns() - t0; gc.enable()
        rec[name] = dict(ns=dt, exp=o.expanded - e0, cert_ns=getattr(o, 'cert_ns', 0) - c0,
                         cert_nodes=getattr(o, 'cert_nodes', 0) - n0, promoted=getattr(o, 'promoted', 0) - p0,
                         cacheE=len(o.E), cacheL=len(o.L))
    check_exh = (ds != 'syn32') or (trial % 3 == 0)
    truth = exhaustive(p)[0] if check_exh else obj['fresh'].value
    for name, o in obj.items():
        assert o.value == truth or (math.isfinite(truth) and abs(o.value - truth) <= 1e-7 * max(1, truth)), (ds, kind, trial, name, o.value, truth)
    st = obj['nocert'].stats
    # ---------------- pass 2: memory (same trial, deterministic) ----------------
    p2, r2, obj2 = setup(trial); ms2 = measured_step(p2, r2); assert ms2 == ms
    mem = {}
    tracemalloc.start()
    for name, o in obj2.items():
        gc.collect(); tracemalloc.reset_peak(); before = tracemalloc.get_traced_memory()[0]
        o.update(k, s, w); mem[name] = tracemalloc.get_traced_memory()[1] - before
    tracemalloc.stop()
    row = dict(dataset=ds, kind=kind, trial=trial, n=p.n, m=p.m, old_value=old_value, new_value=truth,
               oracle='exhaustive' if check_exh else 'fresh BnB', feasible=math.isfinite(truth),
               replay_failed=not st['ub_finite'], eager_kept_L3=obj['eager'].stats['kept_L3'],
               old_entries=obj['eager'].stats['old_entries'])
    for name, d in rec.items():
        for key, v in d.items(): row[f'{name}_{key}'] = v
        row[f'{name}_peak_bytes'] = mem[name]
    rows.append(row)
out = os.path.join(H, 'results', f'lazy_{ds}_{kind}_{start}.csv')
with open(out, 'w', newline='') as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
print('DONE', ds, kind, len(rows), 'trials ->', os.path.basename(out))
