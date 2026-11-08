"""Phase 129 correctness tests for the lazy certificate.
For each update (random mixed streams incl. failed replay and infeasibility transitions):
  - values of MBRNoCert, MBREager, MBRLazy equal the independent exhaustive DP (and the exact-rational
    oracle on small instances);
  - STATE LEVEL: every exact cache entry of MBRLazy (incl. promoted ones) equals the true optimum of that
    state, every stored lower bound is <= the true optimum.
Usage: python test_lazy.py MODE(mixed|feasible|structural) INSTANCES SEED"""
import sys, os, random, math, collections
H = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [H, os.path.join(H, '../phase123'), os.path.join(H, '../phase122/fuzz')]
from mbr_lazy import MBRNoCert, MBREager, MBRLazy
from mbr import exhaustive, Compiled, INF
import oracle
MODE, NI, SEED = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
class P: pass
def gen(r):
    p = P(); n = r.randint(4, 9); m = r.randint(3, 9); p.n, p.m = n, m
    p.deadline = r.randint(2, 7) if MODE == 'mixed' else r.randint(6, 11)
    p.actions = [(1 << r.randrange(4)) | ((1 << r.randrange(4)) if r.random() < .4 else 0) for _ in range(n)]
    p.outcomes = [[r.randrange(2) for _ in range(n)] for _ in range(m)]
    p.delay = [r.choice([1, 1, 2, 3, 4]) for _ in range(m)]
    p.wait = [[r.random() > (.12 if MODE == 'mixed' else .02) for _ in range(n)] for _ in range(m)]
    p.cost = [float(r.choice([0, 1, 2, 3, 5, 8])) for _ in range(m)]
    return p
def mutate(p, r):
    kinds = ['cost', 'delay', 'outcome', 'wait', 'viability'] if MODE != 'structural' else ['delay', 'wait', 'viability', 'delay', 'wait', 'viability', 'outcome', 'cost']
    kind = r.choice(kinds); s = r.randrange(p.m); w = r.randrange(p.n)
    if kind == 'cost': p.cost[s] = float(r.choice([0, 1, 2, 3, 5, 8, 13]))
    elif kind == 'delay': p.delay[s] = max(1, p.delay[s] + r.choice([1, 1, 2, -1])) if MODE == 'structural' else r.randint(1, 5)
    elif kind == 'outcome': p.outcomes[s][w] ^= 1
    elif kind == 'wait': p.wait[s][w] = (not p.wait[s][w]) if MODE != 'structural' else (r.random() < .25)
    else:
        if MODE == 'structural' and bin(p.actions[w]).count('1') >= 2 and r.random() < .8:
            bits = [b for b in range(4) if p.actions[w] >> b & 1]; p.actions[w] &= ~(1 << r.choice(bits))
        else: p.actions[w] = r.randrange(1, 16)
    return kind, s, w
def truthfn(p):
    c = Compiled(p); memo = {}
    def V(b, t):
        k = (b, t)
        if k in memo: return memo[k]
        if c.terminal(b): memo[k] = 0.0; return 0.0
        best = INF
        for s in range(c.m):
            t2 = t + c.delay[s]
            if t2 > c.D or b & ~c.safe[s]: continue
            x = b & c.pos[s]; y = b ^ x
            if not x or not y: continue
            vx, vy = V(x, t2), V(y, t2)
            if vx < INF and vy < INF: best = min(best, c.cost[s] + (x.bit_count() * vx + y.bit_count() * vy) / b.bit_count())
        memo[k] = best; return best
    return V
def same(a, b): return a == b or (math.isfinite(a) and math.isfinite(b) and abs(a - b) <= 1e-7 * max(1, abs(b)))
r = random.Random(SEED); cat = collections.Counter(); nE = nL = rat = 0; PROMO = 0; CERTN = 0
for inst in range(NI):
    p = gen(r); X = {'nocert': MBRNoCert(p), 'eager': MBREager(p), 'lazy': MBRLazy(p)}
    for step in range(35):
        pr0 = X['lazy'].promoted
        old = X['lazy'].value; kind, s, w = mutate(p, r)
        for o in X.values(): o.update(kind, s, w)
        tv = exhaustive(p)[0]
        if p.n <= 7 and step % 4 == 0:
            o = oracle.solve(p.n, p.m, tuple(p.actions), tuple(map(tuple, p.outcomes)), tuple(p.delay), tuple(map(tuple, p.wait)), tuple(int(c) for c in p.cost), p.deadline)
            assert same(INF if o is None else float(o), tv); rat += 1
        for nm, o in X.items():
            if not same(o.value, tv): print('VALUE FAIL', nm, inst, step, kind, o.value, tv); sys.exit(1)
        V = truthfn(p); L = X['lazy']
        for (b, t), (v, _) in L.E.items():
            nE += 1
            if not same(v, V(b, t)): print('EXACT-ENTRY FAIL', inst, step, kind, b, t, v, V(b, t)); sys.exit(1)
        for (b, t), v in L.L.items():
            nL += 1
            if v > V(b, t) + 1e-7 * max(1, abs(v) if v < INF else 1): print('BOUND FAIL', inst, step, kind, v, V(b, t)); sys.exit(1)
        st = L.stats; cat['updates'] += 1
        if L.promoted > pr0: cat['updates with lazy promotions'] += 1
        PROMO += L.promoted - pr0
        cat['replay failed (budget +inf)' if not st['ub_finite'] else 'replay ok'] += 1
        fo, fn = math.isfinite(old), math.isfinite(tv)
        if fo and not fn: cat['feasible->infeasible'] += 1
        if not fo and fn: cat['infeasible->feasible'] += 1
        if not fn: cat['infeasible after update'] += 1
cat['lazy entries promoted (total)'] = PROMO
print(f'mode {MODE}: updates {cat["updates"]}, exact-rational checks {rat}, lazy exact entries checked {nE}, lazy bounds checked {nL} — ALL CORRECT')
for k, v in sorted(cat.items()):
    if k != 'updates': print(f'   {k:30s} {v}')
