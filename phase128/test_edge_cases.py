"""Phase 128: exactness of MBR in edge cases of the update step.
Categories per update: replay succeeded (finite root budget) / replay failed (budget +inf);
feasible->infeasible, infeasible->feasible, infeasible->infeasible; root retained exact without search.
Every update is checked against exhaustive DP; small instances also against the exact-rational oracle.
The safety-net re-solve (v > ub) is instrumented and must never fire."""
import sys, os, random, math, collections
H = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(H, '../phase123'), os.path.join(H, '../phase122/fuzz')]
import mbr
from mbr import MBR, MBRH, exhaustive, INF
import oracle
NET = {'fired': 0, 'root_calls_finite_ub': 0}
_orig_solve = mbr.BnB.solve
def _solve(self, b, t, ub):
    v = _orig_solve(self, b, t, ub)
    if t == 0 and b == self.root[0] and ub < INF:
        NET['root_calls_finite_ub'] += 1
        if v > ub + mbr.EPS: NET['fired'] += 1
    return v
mbr.BnB.solve = _solve
class MBRi(MBR):
    def update(self, kind, s, w):
        old = self.value; super().update(kind, s, w)
        self.last = dict(old=old, ub=self.stats.get('ub_finite'))
class MBRHi(MBRH, MBRi): pass
# instrument safety net: wrap MBR.update's second solve by checking root ub vs result inside a subclass
def patched_update(self, kind, s, w, _u=MBR.update):
    return _u(self, kind, s, w)
class P: pass
MODE = sys.argv[1] if len(sys.argv) > 1 else 'mixed'
def gen(r):
    p = P(); n = r.randint(4, 9); m = r.randint(3, 9); p.n, p.m = n, m
    p.deadline = r.randint(2, 7) if MODE == 'mixed' else r.randint(6, 11)
    p.actions = [(1 << r.randrange(4)) | ((1 << r.randrange(4)) if r.random() < .35 else 0) for _ in range(n)]
    p.outcomes = [[r.randrange(2) for _ in range(n)] for _ in range(m)]
    p.delay = [r.choice([1, 1, 2, 3, 4]) for _ in range(m)]
    p.wait = [[r.random() > (.12 if MODE == 'mixed' else .02) for _ in range(n)] for _ in range(m)]
    p.cost = [float(r.choice([0, 1, 2, 3, 5, 8])) for _ in range(m)]
    return p
def mutate(p, r):
    kind = r.choice(['cost', 'delay', 'outcome', 'wait', 'viability']); s = r.randrange(p.m); w = r.randrange(p.n)
    if kind == 'cost': p.cost[s] = float(r.choice([0, 1, 2, 3, 5, 8, 13]))
    elif kind == 'delay': p.delay[s] = r.randint(1, 5)        # large increases frequently break the deadline
    elif kind == 'outcome': p.outcomes[s][w] ^= 1             # frequently breaks replay
    elif kind == 'wait': p.wait[s][w] = not p.wait[s][w]
    else: p.actions[w] = r.randrange(1, 16)
    return kind, s, w
def same(a, b): return a == b or (math.isfinite(a) and math.isfinite(b) and abs(a - b) <= 1e-7 * max(1, abs(b)))
cat = collections.Counter(); r = random.Random(128100); checks = rat = 0
for inst in range(500):
    p = gen(r); A = MBRi(p); B = MBRHi(p)
    for step in range(40):
        old = A.value; kind, s, w = mutate(p, r)
        e0 = A.expanded; A.update(kind, s, w); B.update(kind, s, w)
        truth = exhaustive(p)[0]; checks += 1
        if p.n <= 7 and step % 3 == 0:
            o = oracle.solve(p.n, p.m, tuple(p.actions), tuple(map(tuple, p.outcomes)), tuple(p.delay),
                             tuple(map(tuple, p.wait)), tuple(int(c) for c in p.cost), p.deadline)
            o = INF if o is None else float(o); rat += 1
            assert same(o, truth), ('oracle disagreement', o, truth)
        for nm, X in (('MBR', A), ('MBR-H', B)):
            if not same(X.value, truth):
                print('FAIL', nm, inst, step, kind, X.value, truth, X.stats); sys.exit(1)
        ubf = A.stats['ub_finite']
        cat['replay ok (finite budget)' if ubf else 'replay failed (budget +inf)'] += 1
        fo, fn = math.isfinite(old), math.isfinite(truth)
        cat[{(True, True): 'feasible->feasible', (True, False): 'feasible->INFEASIBLE',
             (False, True): 'INFEASIBLE->feasible', (False, False): 'infeasible->infeasible'}[(fo, fn)]] += 1
        if not fn and ubf: cat['finite budget while infeasible (must be 0)'] += 1
        if A.expanded == e0: cat['answered with zero expansions'] += 1
        if not ubf and not fn: cat['replay failed AND infeasible'] += 1
        if not ubf and fn: cat['replay failed, feasible (exact search from +inf budget)'] += 1
print('mode', MODE, '| updates checked', checks, '(exact-rational oracle on', rat, ') — ALL EXACT for MBR and MBR-H')
for k, v in sorted(cat.items()): print(f'  {k:55s} {v}')
# Direct check that the safety-net branch in MBR.update (re-solve when v > ub) is never taken:
src = open(os.path.join(H, '../phase123/mbr.py')).read()
assert 'if v > ub + EPS:              # cannot happen if ub is achievable; safety net' in src
print('safety-net re-solve fired:', NET['fired'], 'of', NET['root_calls_finite_ub'], 'root calls with a finite replay budget')
assert NET['fired'] == 0
