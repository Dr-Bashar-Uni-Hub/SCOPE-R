"""Phase 123 sequential exact-replanning benchmark.

Usage: python bench.py TAG n m seeds steps solvers(comma) [deadline]
Every solver sees the identical instance and identical update stream (Phase 121 change()).
Order of solver invocation is randomised per update. Initialisation time is included in
sequence totals. Every value is checked against the independent exhaustive DP when it is
among the solvers (otherwise against fresh BnB, which is a weaker, same-family check).
"""
import sys, os, time, random, math, csv, json, platform, gc
H = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [H, os.path.join(H, '../phase122/repro121/baseline/phase115'),
                os.path.join(H, '../phase122/repro121')]
from mbr import exhaustive, BnB, MBR, BnBH, MBRH
from gen_hard import Inst
from verified import fresh as frozen_fresh
from benchmark import LazyEligibilityRepair
from repair import ClosureRepair
from benchmark_portable import matched_pomdp, change   # Phase 121 baseline + mutation semantics


class FreshWrap:
    def __init__(self, f, p):
        self.f, self.p = f, p
        self.value = f(p)[0]

    def update(self, kind, s, w):
        self.value = self.f(self.p)[0]


MAKERS = {
    'mbr': lambda p: MBR(p),
    'bnb': lambda p: BnB(p),
    'mbrH': lambda p: MBRH(p),
    'bnbH': lambda p: BnBH(p),
    'exh': lambda p: FreshWrap(exhaustive, p),
    'pomdp': lambda p: FreshWrap(matched_pomdp, p),
    'fresh121': lambda p: FreshWrap(frozen_fresh, p),
    'closure': lambda p: ClosureRepair(p),
    'lazy115': lambda p: LazyEligibilityRepair(p),
}


def same(a, b):
    return a == b or (math.isfinite(a) and math.isfinite(b) and abs(a - b) <= 1e-7 * max(1, abs(b)))


def main():
    tag, n, m, seeds, steps = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    names = sys.argv[6].split(',')
    D = int(sys.argv[7]) if len(sys.argv) > 7 else 10
    ref = 'exh' if 'exh' in names else 'bnb'
    out = os.path.join(H, 'results', tag); os.makedirs(out, exist_ok=True)
    rows, seqs = [], []
    REG = os.environ.get('REGIME', 'balanced,cost_dominated').split(',')
    SEEDS = [int(x) for x in os.environ['SEEDS'].split(',')] if 'SEEDS' in os.environ else list(range(seeds))
    if 'REGIME' in os.environ or 'SEEDS' in os.environ:
        out = os.path.join(H, 'results', tag, 'chunk_' + '_'.join(REG) + '_' + '_'.join(map(str, SEEDS)))
        os.makedirs(out, exist_ok=True)
    for regime in REG:
        for seed in SEEDS:
            base = 123000 + n * 100 + seed + (regime == 'balanced') * 50000
            p = Inst(n, m, base, deadline=D)
            r = random.Random(base + 7)
            tot, obj = {}, {}
            for name in names:
                gc.collect(); gc.disable()
                t = time.perf_counter_ns(); obj[name] = MAKERS[name](p); tot[name] = time.perf_counter_ns() - t
                gc.enable()
            v0 = obj[ref].value
            for name in names:
                assert same(obj[name].value, v0), ('init', name, obj[name].value, v0)
            for step in range(steps):
                kind = r.choice(['cost'] * 7 + ['delay', 'outcome', 'wait', 'viability']) if regime == 'cost_dominated' \
                    else r.choice(['cost', 'delay', 'outcome', 'wait', 'viability'])
                s, w = change(p, r, kind)
                order = names[:]; r.shuffle(order); el = {}
                ex0 = {k: getattr(obj[k], 'expanded', None) for k in ('mbr', 'bnb', 'mbrH', 'bnbH') if k in obj}
                for name in order:
                    gc.collect(); gc.disable()   # GC pauses excluded from every solver alike
                    t = time.perf_counter_ns(); obj[name].update(kind, s, w); el[name] = time.perf_counter_ns() - t
                    gc.enable()
                vref = obj[ref].value
                for name in names:
                    if not same(obj[name].value, vref):
                        raise AssertionError((tag, regime, seed, step, kind, name, obj[name].value, vref))
                for k in el: tot[k] += el[k]
                row = dict(tag=tag, n=n, m=m, regime=regime, seed=seed, step=step, kind=kind,
                           feasible=math.isfinite(vref), value=vref, **{k + '_ns': el[k] for k in el})
                for k in ex0:
                    row[k + '_expanded'] = obj[k].expanded - ex0[k]
                if 'mbr' in obj:
                    st = obj['mbr'].stats
                    row.update(mbr_tighten=st.get('tighten'), mbr_kept_exact=st.get('kept_exact'),
                               mbr_kept_lb=st.get('kept_lb'), mbr_ub_finite=st.get('ub_finite'))
                rows.append(row)
            seq = dict(tag=tag, n=n, m=m, regime=regime, seed=seed, steps=steps,
                       **{k + '_total_ns': tot[k] for k in names})
            seqs.append(seq)
            print(tag, regime, seed, ' '.join('%s=%.3fs' % (k, tot[k] / 1e9) for k in names), flush=True)
    for fn, data in (('updates.csv', rows), ('sequences.csv', seqs)):
        with open(os.path.join(out, fn), 'w', newline='') as f:
            wr = csv.DictWriter(f, fieldnames=list(data[0])); wr.writeheader(); wr.writerows(data)
    json.dump(dict(argv=sys.argv, python=sys.version, platform=platform.platform(),
                   processor=platform.processor(), checks=len(rows), reference=ref),
              open(os.path.join(out, 'meta.json'), 'w'), indent=1)
    print('DONE', tag, 'exact checks', len(rows), 'reference', ref)


if __name__ == '__main__':
    main()
