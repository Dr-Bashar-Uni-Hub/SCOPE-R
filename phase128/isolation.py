"""Phase 128 novelty-isolation ablation: established reuse (Lemma 2 lower bounds + locality + replay)
versus the proposed structural retained-exactness certificate (Lemma 3, structural cases).

Usage: python isolation.py DATASET KIND TRIALS [START]
  DATASET: syn20 (n=20,m=28) | syn24 (n=24,m=36) | heart12 | heart16 (Cleveland, 6 h / 8 h deadline)
  KIND:    delay (delay increase +1 slot) | safety (waiting-safety removal for one test-patient pair)
           | region (remove one acceptable action from a hypothesis with >= 2 actions)
Design: controlled, paired. Each trial builds an instance, applies an identical random 3-update history to
all variants (so caches reflect realistic state), then times ONE tightening update of KIND.
Variants: full = all MBR components; noL3s = full minus Lemma-3 structural cases (Lemma 2 lower bounds,
locality, replay and temporal bounds kept); L1only = locality only (no tightening bounds, no
certificate, no replay); fresh = branch-and-bound from scratch. GC collected before / disabled during each
timed call; variant order randomised; every value checked against the independent exhaustive DP.
"""
import sys, os, random, time, gc, csv, math
H = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [H, os.path.join(H, '../phase123'), os.path.join(H, '../phase124')]
from mbr_iso import MBRIso
from mbr import BnB, exhaustive, INF
from gen_hard import Inst

ds, kind, trials = sys.argv[1], sys.argv[2], int(sys.argv[3])
start = int(sys.argv[4]) if len(sys.argv) > 4 else 0

def make(trial):
    if ds.startswith('syn'):
        n, m = (20, 28) if ds == 'syn20' else (24, 36)
        return Inst(n, m, 128000 + 1000 * (ds == 'syn24') + trial, deadline=10)
    import heart
    rows, _ = heart.consistent(heart.load(), 'overlap')
    return heart.HeartInstance(rows, 12 if ds == 'heart12' else 16, 'overlap', safe_num=99)

REG3 = [0b011, 0b110, 0b100]
def history_step(p, r):
    """Random mixed update (any kind/direction) used to build cache history."""
    k = r.choice(['cost', 'delay', 'outcome', 'wait', 'viability']); s = r.randrange(p.m); w = r.randrange(p.n)
    if k == 'cost': p.cost[s] = max(0.0, round(p.cost[s] * r.choice([0.8, 0.9, 1.1, 1.25]), 4))
    elif k == 'delay': p.delay[s] = max(1, p.delay[s] + r.choice([-1, 1]))
    elif k == 'outcome': p.outcomes[s][w] ^= 1
    elif k == 'wait': p.wait[s][w] = not p.wait[s][w]
    else:
        acts = sorted({a for a in p.actions})
        p.actions[w] = r.choice([a for a in acts if a != p.actions[w]] or [p.actions[w]])
    return k, s, w

def measured_step(p, r):
    """One tightening update of the requested kind; returns None if no eligible element exists."""
    if kind == 'delay':
        s = r.randrange(p.m); p.delay[s] += 1; return 'delay', s, 0
    if kind == 'safety':
        cand = [(s, w) for s in range(p.m) for w in range(p.n) if p.wait[s][w]]
        s, w = r.choice(cand); p.wait[s][w] = False; return 'wait', s, w
    cand = [w for w in range(p.n) if bin(p.actions[w]).count('1') >= 2]
    if not cand: return None
    w = r.choice(cand); bits = [b for b in range(8) if p.actions[w] >> b & 1]
    p.actions[w] &= ~(1 << r.choice(bits)); return 'viability', 0, w

VARIANTS = {'full': lambda p: MBRIso(p), 'noL3s': lambda p: MBRIso(p, L3s=False),
            'L1only': lambda p: MBRIso(p, L2=False, L3c=False, L3s=False, L4=False, use_ub=False),
            'fresh': lambda p: BnB(p)}
os.makedirs(os.path.join(H, 'results'), exist_ok=True)
out = os.path.join(H, 'results', f'isolation_{ds}_{kind}_{start}.csv')
rows = []
for trial in range(start, start + trials):
    r = random.Random(f'{ds}-{kind}-{trial}')
    p = make(trial)
    obj = {k: f(p) for k, f in VARIANTS.items()}
    for _ in range(3):
        k, s, w = history_step(p, r)
        for o in obj.values(): o.update(k, s, w)
    old_value = obj['full'].value
    old_root_sensor = obj['full'].E.get(obj['full'].root, [None, -1])[1]
    ms = measured_step(p, r)
    if ms is None: continue
    k, s, w = ms
    order = list(obj); r.shuffle(order); rec = {}
    for name in order:
        o = obj[name]; e0 = o.expanded
        gc.collect(); gc.disable(); t0 = time.perf_counter_ns(); o.update(k, s, w); dt = time.perf_counter_ns() - t0; gc.enable()
        rec[name] = (dt, o.expanded - e0)
    truth = exhaustive(p)[0]
    for name, o in obj.items():
        assert o.value == truth or (math.isfinite(truth) and abs(o.value - truth) <= 1e-7 * max(1, truth)), \
            (ds, kind, trial, name, o.value, truth)
    st = obj['full'].stats
    row = dict(dataset=ds, kind=kind, trial=trial, n=p.n, m=p.m, old_value=old_value, new_value=truth,
               value_changed=not (old_value == truth or (math.isfinite(truth) and math.isfinite(old_value) and abs(old_value - truth) < 1e-9)),
               feasible=math.isfinite(truth), old_entries=st['old_entries'], kept_L1=st['kept_L1'],
               kept_L3=st['kept_L3'], kept_lb_full=st['kept_lb'], root_retained_by_L3=st['root_retained'],
               noL3s_kept_exact=obj['noL3s'].stats['kept_exact'], noL3s_kept_lb=obj['noL3s'].stats['kept_lb'])
    for name, (dt, ex) in rec.items():
        row[name + '_ns'] = dt; row[name + '_exp'] = ex
    rows.append(row)
with open(out, 'w', newline='') as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
print('DONE', ds, kind, 'trials', len(rows), '->', os.path.basename(out))
