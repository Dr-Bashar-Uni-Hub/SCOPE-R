"""Phase 128 audit of Proposition H (Huffman-type bound) under overlapping acceptable-action sets.
Checks h(B,t) <= V(B,t) for EVERY nonempty subset B and every t in [0,D] (not only reachable states),
with V computed by an independent exhaustive DP; adversarial generators with heavy overlap and up to
6 actions; plus a hill-climbing search maximising h/V to hunt for counterexamples."""
import sys, os, random, math, itertools
H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.join(H, '../phase123')]
from mbr import CompiledH, INF
class P: pass
def model(r, n, m, K, overlap, D):
    p = P(); p.n, p.m, p.deadline = n, m, D
    p.actions = []
    for w in range(n):
        a = 1 << r.randrange(K)
        while r.random() < overlap: a |= 1 << r.randrange(K)
        p.actions.append(a)
    p.outcomes = [[r.randrange(2) for _ in range(n)] for _ in range(m)]
    p.delay = [r.choice([1, 1, 2, 3]) for _ in range(m)]
    p.wait = [[r.random() > .05 for _ in range(n)] for _ in range(m)]
    p.cost = [float(r.choice([0, 1, 1, 2, 3, 5, 8])) for _ in range(m)]
    return p
def Vtab(p):
    c = CompiledH(p); memo = {}
    def V(b, t):
        k = (b, t)
        if k in memo: return memo[k]
        if c.terminal(b): memo[k] = 0.0; return 0.0
        best = INF
        for s in range(p.m):
            t2 = t + c.delay[s]
            if t2 > c.D or b & ~c.safe[s]: continue
            x = b & c.pos[s]; y = b ^ x
            if not x or not y: continue
            vx, vy = V(x, t2), V(y, t2)
            if vx < INF and vy < INF:
                best = min(best, c.cost[s] + (x.bit_count() * vx + y.bit_count() * vy) / b.bit_count())
        memo[k] = best; return best
    return c, V
def check_all(p):
    c, V = Vtab(p); worst = 0.0; viol = []; n_states = 0; tight = 0
    for b in range(1, 1 << p.n):
        for t in range(p.deadline + 1):
            v = V(b, t); h = c.h(b, t); n_states += 1
            if h > v + 1e-9: viol.append((b, t, h, v))
            if v < INF and v > 0:
                worst = max(worst, h / v); tight += h > c.cmin_t[t] + 1e-9
    return n_states, viol, worst, tight
r = random.Random(128001); tot = 0; allv = []; worst = 0; tight = 0; overl = 0
for trial in range(600):
    n = r.randint(3, 9); m = r.randint(2, 8); K = r.choice([2, 3, 4, 5, 6])
    ov = r.choice([0.0, 0.3, 0.6, 0.85]); D = r.randint(2, 8)
    p = model(r, n, m, K, ov, D); overl += sum(bin(a).count('1') > 1 for a in p.actions)
    ns, v, w, tg = check_all(p); tot += ns; allv += v; worst = max(worst, w); tight += tg
print('exhaustive all-subset check: instances 600, states', tot, 'violations', len(allv),
      'multi-action worlds', overl, 'max h/V', round(worst, 4), 'states where bound > cmin', tight)
# adversarial hill-climbing on h/V
best = (0, None); r = random.Random(128002)
for start in range(150):
    n = r.randint(4, 8); m = r.randint(3, 7); K = r.choice([3, 4, 5]); p = model(r, n, m, K, 0.5, r.randint(3, 7))
    cur = check_all(p)[2]
    for step in range(40):
        q = P(); q.__dict__ = {k: (list(map(list, v)) if k in ('outcomes', 'wait') else (list(v) if isinstance(v, list) else v)) for k, v in p.__dict__.items()}
        kind = r.randrange(4)
        if kind == 0: q.actions[r.randrange(n)] = r.randrange(1, 1 << K)
        elif kind == 1: s = r.randrange(m); w = r.randrange(n); q.outcomes[s][w] ^= 1
        elif kind == 2: q.cost[r.randrange(m)] = float(r.choice([0, 1, 2, 5, 9]))
        else: q.delay[r.randrange(m)] = r.choice([1, 2, 3])
        ns, v, w, _ = check_all(q)
        if v: print('COUNTEREXAMPLE', q.__dict__, v[:3]); sys.exit(1)
        if w >= cur: p, cur = q, w
    if cur > best[0]: best = (cur, p.__dict__)
print('adversarial search: 150 starts x 40 steps, no violation; max h/V reached', round(best[0], 4))
