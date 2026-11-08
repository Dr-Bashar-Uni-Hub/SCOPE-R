"""Small illustrative instance for Figure 1; optimal policy extracted with an independent exhaustive solver."""
import sys, os
H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.join(H, '../phase123')]
from mbr import exhaustive, INF
class P: pass
ACT = {'D': 1, 'M': 2, 'T': 4}                          # discharge, monitor, treat
NAMES = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
A = [ACT['D'], ACT['D'] | ACT['M'], ACT['M'], ACT['M'] | ACT['T'], ACT['T'], ACT['T']]
TESTS = [  # name, cost, delay, outcome per hypothesis, unsafe hypotheses
    ('history', 1, 1, [0, 0, 0, 1, 1, 1], []),
    ('blood', 5, 3, [0, 1, 1, 0, 1, 0], []),            # cheap but slow (3 time units)
    ('stress', 8, 1, [0, 1, 1, 0, 0, 1], [2]),          # unsafe for h3
    ('imaging', 12, 2, [0, 1, 1, 0, 1, 1], []),
]
def model(D=4):
    p = P(); p.n, p.m, p.deadline = 6, len(TESTS), D
    p.actions = list(A); p.outcomes = [list(t[3]) for t in TESTS]
    p.delay = [t[2] for t in TESTS]; p.cost = [float(t[1]) for t in TESTS]
    p.wait = [[w not in t[4] for w in range(6)] for t in TESTS]; return p
def solve(p):
    memo = {}
    def term(b):
        inter = 7
        for w in range(p.n):
            if b >> w & 1: inter &= p.actions[w]
        return inter
    def V(b, t):
        k = (b, t)
        if k in memo: return memo[k]
        if term(b): memo[k] = (0.0, None); return memo[k]
        best = (INF, None)
        for s in range(p.m):
            if t + p.delay[s] > p.deadline or any((b >> w & 1) and not p.wait[s][w] for w in range(p.n)): continue
            x = sum(1 << w for w in range(p.n) if b >> w & 1 and p.outcomes[s][w]); y = b ^ x
            if not x or not y: continue
            vx, vy = V(x, t + p.delay[s])[0], V(y, t + p.delay[s])[0]
            q = p.cost[s] + (bin(x).count('1') * vx + bin(y).count('1') * vy) / bin(b).count('1')
            if q < best[0]: best = (q, s)
        memo[k] = best; return best
    return V, term
if __name__ == '__main__':
    for D in (3, 4, 6):
        p = model(D); V, term = solve(p); v, s = V(63, 0)
        print(f'D={D}: V={v:.4f}, root test={TESTS[s][0] if s is not None else None}, exhaustive check {exhaustive(p)[0]:.4f}')
        def show(b, t, ind=0):
            v, s = V(b, t)
            names = ','.join(NAMES[w] for w in range(6) if b >> w & 1)
            if s is None:
                acts = [k for k, m in ACT.items() if term(b) & m]; print('   ' * ind + f'[{names}] t={t} -> terminal, acceptable {acts}'); return
            print('   ' * ind + f'[{names}] t={t} V={v:.3f} test={TESTS[s][0]}')
            x = sum(1 << w for w in range(6) if b >> w & 1 and p.outcomes[s][w])
            show(b ^ x, t + p.delay[s], ind + 1); show(x, t + p.delay[s], ind + 1)
        if D == 3: show(63, 0)
