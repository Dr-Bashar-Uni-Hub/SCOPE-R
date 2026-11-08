"""Phase 124: exact replanning on the real Cleveland instance (n=296 patients, 13 tests).

Usage: python bench_heart.py D streams steps [regions] [safety_tests]
Update events (realistic interpretations):
  cost      : fee-schedule revision, cost of test s multiplied by a factor in {0.8,0.9,1.1,1.25}
  delay     : lab-turnaround change of test s by -1/+1 half-hour unit (min 1)
  outcome   : correction of patient w's recorded result on test s
  wait      : patient-specific contraindication for test s discovered / lifted
  viability : reassessment of patient w's diagnosis (region re-drawn from the three regions)
All solvers see identical instance and stream; GC collected before / disabled during each timed call;
every value checked against the independent exhaustive DP.
"""
import sys, os, time, random, math, csv, gc, json, platform
H = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [H, os.path.join(H, '../phase122/repro121/baseline/phase115')]
from heart import load, consistent, HeartInstance, REGIONS
import heart
from mbr import MBR, BnB, exhaustive
from repair import ClosureRepair


class Fresh:
    def __init__(self, p): self.p = p; self.value = exhaustive(p)[0]
    def update(self, kind, s, w): self.value = exhaustive(self.p)[0]


MAK = {'mbr': MBR, 'bnb': BnB, 'exh': Fresh, 'closure': ClosureRepair}
REG3 = [0b011, 0b110, 0b100]


def event(p, r):
    kind = r.choice(['cost', 'delay', 'outcome', 'wait', 'viability'])
    s, w = r.randrange(p.m), r.randrange(p.n)
    if kind == 'cost':
        p.cost[s] = round(p.cost[s] * r.choice([0.8, 0.9, 1.1, 1.25]), 4)
    elif kind == 'delay':
        p.delay[s] = max(1, p.delay[s] + r.choice([-1, 1]))
    elif kind == 'outcome':
        p.outcomes[s][w] ^= 1
    elif kind == 'wait':
        p.wait[s][w] = not p.wait[s][w]
    else:
        p.actions[w] = r.choice([a for a in REG3 if a != p.actions[w]])
    return kind, s, w


def same(a, b):
    return a == b or (math.isfinite(a) and math.isfinite(b) and abs(a - b) <= 1e-7 * max(1, abs(b)))


def main():
    D, streams, steps = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    regions = sys.argv[4] if len(sys.argv) > 4 else 'overlap'
    names = (sys.argv[5] if len(sys.argv) > 5 else 'mbr,bnb,exh,closure').split(',')
    tag = f'heart_D{D}_{regions}'
    out = os.path.join(H, 'results', tag); os.makedirs(out, exist_ok=True)
    rows, dropped = consistent(load(), regions)
    seqs, ups = [], []
    START = int(os.environ.get('START', 0))
    if START or 'START' in os.environ:
        out = os.path.join(out, f'chunk_{START}'); os.makedirs(out, exist_ok=True)
    for st in range(START, START + streams):
        p = HeartInstance(rows, D, regions, safe_num=99)
        r = random.Random(124000 + D * 100 + st)
        obj, tot = {}, {}
        for nm in names:
            gc.collect(); gc.disable(); t = time.perf_counter_ns(); obj[nm] = MAK[nm](p)
            tot[nm] = time.perf_counter_ns() - t; gc.enable()
        ref = 'exh' if 'exh' in names else 'bnb'
        for nm in names:
            assert same(obj[nm].value, obj[ref].value), ('init', nm)
        for k in range(steps):
            kind, s, w = event(p, r)
            order = names[:]; r.shuffle(order); el = {}
            e0 = {nm: obj[nm].expanded for nm in ('mbr', 'bnb') if nm in obj}
            for nm in order:
                gc.collect(); gc.disable(); t = time.perf_counter_ns(); obj[nm].update(kind, s, w)
                el[nm] = time.perf_counter_ns() - t; gc.enable()
            v = obj[ref].value
            for nm in names:
                if not same(obj[nm].value, v):
                    raise AssertionError((tag, st, k, kind, nm, obj[nm].value, v))
            for nm in el: tot[nm] += el[nm]
            row = dict(tag=tag, stream=st, step=k, kind=kind, test=heart.TESTS[s], value=v,
                       **{nm + '_ns': el[nm] for nm in el})
            for nm in e0: row[nm + '_expanded'] = obj[nm].expanded - e0[nm]
            ups.append(row)
        seqs.append(dict(tag=tag, stream=st, steps=steps, **{nm + '_total_ns': tot[nm] for nm in names}))
        print(tag, st, ' '.join('%s=%.3fs' % (nm, tot[nm] / 1e9) for nm in names), flush=True)
    for fn, data in (('updates.csv', ups), ('sequences.csv', seqs)):
        with open(os.path.join(out, fn), 'w', newline='') as f:
            wr = csv.DictWriter(f, fieldnames=list(data[0])); wr.writeheader(); wr.writerows(data)
    json.dump(dict(argv=sys.argv, n=len(rows), dropped=dropped, python=sys.version,
                   platform=platform.platform()), open(os.path.join(out, 'meta.json'), 'w'), indent=1)
    print('DONE', tag, 'checks', len(ups))


if __name__ == '__main__':
    main()
