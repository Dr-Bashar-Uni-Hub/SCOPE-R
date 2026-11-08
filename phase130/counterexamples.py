"""Phase 130 — brute-force-verified counterexamples for certificates after NON-MONOTONE updates
(outcome flips). Every value is computed by the independent exhaustive DP of phase123 (all subsets
enumerable where stated). These are verification scripts for mathematical claims, not a method."""
import sys, os, copy, itertools
H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.join(H, '../phase123')]
from mbr import exhaustive, Compiled, CompiledH, INF
class P: pass
def model(n, actions, outcomes, cost, delay=None, D=20):
    p = P(); p.n, p.m, p.deadline = n, len(outcomes), D
    p.actions = list(actions); p.outcomes = [list(o) for o in outcomes]
    p.delay = list(delay) if delay else [1] * p.m; p.wait = [[True] * n for _ in range(p.m)]
    p.cost = [float(c) for c in cost]; return p
def Vall(p):
    c = Compiled(p); memo = {}
    def V(b, t=0):
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
def flip(p, s, w): q = copy.deepcopy(p); q.outcomes[s][w] ^= 1; return q

print('CE1  unbounded value change after one outcome flip (no sensitivity interval exists)')
for M in [10, 1000]:
    # worlds a=0 (action 1), b=1 (action 2); test 0 (cost 1) separates; test 1 (cost M) separates
    p = model(2, [0b01, 0b10], [[0, 1], [0, 1]], [1, M]); q = flip(p, 0, 1)
    print(f'   M={M}: V before = {exhaustive(p)[0]}, after flipping test0 at b = {exhaustive(q)[0]}  (factor {exhaustive(q)[0]/exhaustive(p)[0]:.0f})')
p = model(2, [0b01, 0b10], [[0, 1]], [1]); print(f'   single test: V before = {exhaustive(p)[0]}, after flip = {exhaustive(flip(p, 0, 1))[0]}  (finite -> infinite)')

print('\nCE2  old-policy-local information cannot decide whether the root value changes')
# 4 worlds, actions 1,2,3,4 (identification). test0 cost 1 splits {0,1}|{2,3}; test1 cost 1 splits {0,2}|{1,3};
# test2 = off-policy test with cost u, splits {0,1,2}|{3}; flip: test1 at world 3.
def ce2(u):
    p = model(4, [1, 2, 4, 8], [[0, 0, 1, 1], [0, 1, 0, 1], [0, 0, 0, 1]], [1, 1, u]); return p
for u in [1.0, 3.0]:
    p = ce2(u); q = flip(p, 1, 3); Vp, Vq = Vall(p), Vall(q)
    print(f'   off-policy cost u={u}: V before {Vp((1<<4)-1):.4f} | old optimal-policy states identical across u: '
          f'V({{0,1}})={Vp(0b0011):.2f}, V({{2,3}})={Vp(0b1100):.2f} | V after flip {Vq((1<<4)-1):.4f}')
print('   -> same old policy and same values on its states before the update; after the identical flip the root value')
print('      differs between the two instances only because of the off-policy test u: certificates must look off-policy.')

print('\nCE3  touched (input-affected) region grows as 2^(n-1) while the value-affected region stays tiny and the root is unchanged')
for n in [6, 8, 10, 12]:
    # world 0 = w with its own action; test0 isolates w (cost 1); tests 1..k random-like but fixed splits of the rest
    acts = [1] + [2 if i % 2 else 4 for i in range(1, n)]
    outs = [[1] + [0] * (n - 1)]
    for j in range(1, n):
        outs.append([((i >> (j % 4)) & 1) ^ (j % 2) for i in range(n)])
    cost = [1.0] + [1.0] * (n - 1)
    p = model(n, acts, outs, cost); q = flip(p, 2, 0); Vp, Vq = Vall(p), Vall(q)
    root = (1 << n) - 1; changed = 0; wstates = 0
    for b in range(1, 1 << n):
        if b & 1:
            wstates += 1
            a, c2 = Vp(b), Vq(b)
            if not (a == c2 or (a < INF and c2 < INF and abs(a - c2) < 1e-9)): changed += 1
    print(f'   n={n:2d}: states containing w = {wstates:5d}, states whose value changes = {changed:5d}, root before/after = {Vp(root):.4f}/{Vq(root):.4f}')

print('\nCE4  minimal re-certification sets are not unique (two disjoint minimal certificates), with the REAL Prop. H bound')
# 8 worlds with overlapping acceptable-action sets (no single-action class -> Prop. H reduces to c_min).
# X = {0,1,2,3}, Y = {4,5,6,7}; sets {1,2},{2,3},{3,4},{4,1} repeated. Tests:
#   s  (cost 1)  : X | Y
#   iX (cost 5.5): {0,1} | rest       (resolves X)        iY (cost 5.5): {4,5} | rest (resolves Y)
#   K  (cost 2.5): {0,1,4,5} | {2,3,6,7}  (both children terminal) -> competitor with value 2.5
#   (first attempt with K cost 4 FAILED: K also resolves X and Y, so opening one side proved only 3.5 < 4)
sets = [0b0011, 0b0110, 0b1100, 0b1001] * 2
outs = [[0,0,0,0,1,1,1,1], [1,1,0,0,0,0,0,0], [0,0,0,0,1,1,0,0], [1,1,0,0,1,1,0,0]]
KC = 2.5
p = model(8, sets, outs, [1.0, 5.5, 5.5, KC]); V = Vall(p); cH = CompiledH(p)
bX, bY, root = 0b00001111, 0b11110000, 0b11111111
hX, hY = cH.h(bX, 1), cH.h(bY, 1)
print(f'   V(root) = {V(root)} (via K), V(X) = {V(bX,1)}, V(Y) = {V(bY,1)}, Prop.H bounds h(X) = {hX}, h(Y) = {hY}')
Vr, VX, VY = V(root), V(bX, 1), V(bY, 1)
none_ = 1 + (4*hX + 4*hY)/8; onlyX = 1 + (4*VX + 4*hY)/8; onlyY = 1 + (4*hX + 4*VY)/8
print(f'   no state opened : 1 + (4*{hX} + 4*{hY})/8 = {none_}  >= {Vr} ? {none_ >= Vr}')
print(f'   X opened only   : 1 + (4*{VX} + 4*{hY})/8 = {onlyX}  >= {Vr} ? {onlyX >= Vr}')
print(f'   Y opened only   : 1 + (4*{hX} + 4*{VY})/8 = {onlyY}  >= {Vr} ? {onlyY >= Vr}')
others_ok = min(5.5, 5.5) > Vr
ok = (none_ < Vr) and (onlyX >= Vr) and (onlyY >= Vr) and others_ok
print(f'   root alternatives iX, iY (cost 5.5) excluded without opening: {others_ok}')
print('   VERIFIED: every certificate opens X or Y; {X} and {Y} are both minimal and disjoint.' if ok else '   NOT VERIFIED: construction does not establish the claim.')
print('\nLemma D (deletion / similarity bound) — brute-force check: V(B \\ {w}, t) <= |B|/(|B|-1) * V(B, t)')
import random
r = random.Random(130); viol = chk = 0
for trial in range(300):
    n = r.randint(3, 8); m = r.randint(2, 7)
    acts = [(1 << r.randrange(4)) | ((1 << r.randrange(4)) if r.random() < .4 else 0) for _ in range(n)]
    q = model(n, acts, [[r.randrange(2) for _ in range(n)] for _ in range(m)], [r.choice([0,1,2,3,5]) for _ in range(m)],
              delay=[r.choice([1,1,2,3]) for _ in range(m)], D=r.randint(2, 8))
    q.wait = [[r.random() > .1 for _ in range(n)] for _ in range(m)]
    Vq = Vall(q)
    for b in range(1, 1 << n):
        if b.bit_count() < 2: continue
        for t in range(q.deadline + 1):
            v = Vq(b, t)
            for w in range(n):
                if b >> w & 1:
                    chk += 1; vd = Vq(b & ~(1 << w), t); k = b.bit_count()
                    if v < INF and vd > k / (k - 1) * v + 1e-9: viol += 1
print(f'   {chk} (state, hypothesis) pairs, violations {viol}. Valid for any update because B \\ {{w}} is unaffected by updates at w;')
print('   it is the expected-cost analogue of the similarity lower bound of MurTree (Demirovic et al. 2022) — known type, not new.')
