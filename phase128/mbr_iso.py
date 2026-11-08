"""Phase 128: instrumented MBR for the novelty-isolation ablation.

Reimplements MBR.update (phase123/mbr.py, unchanged) with independent switches:
  L1   locality (world-local updates keep entries whose belief excludes w)
  L2   tightening: old exact values / old bounds become lower bounds
  L3c  Lemma 3, cost-increase case (established; sensitivity-analysis special case)
  L3s  Lemma 3, structural cases: delay increase, waiting-safety removal, decision-region shrink (proposed)
  L4   single-use cost bound;  use_ub  replay upper bound (Lemma 5);  temporal  Lemma 6 bounds
and counts, per update, exact entries retained by Lemma 1 vs Lemma 3. With all switches on, cache
decisions are identical to phase123 MBR (verified by verify_equivalence() below).
"""
import os, sys
H = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(H, '../phase123')]
from mbr import MBR, INF, EPS


class MBRIso(MBR):
    def __init__(self, p, L1=True, L2=True, L3c=True, L3s=True, L4=True, use_ub=True, temporal=True):
        self.L3c, self.L3s = L3c, L3s
        super().__init__(p, temporal=temporal, use_ub=use_ub, L1=L1, L2=L2, L3=True, L4=L4)
        self.stats = {}

    def update(self, kind, s, w):
        p = self.p
        oc = self.c
        self.compile()
        bitw = 1 << w
        E, L = self.E, self.L
        ub = self._replay_ub(oc) if self.use_ub else INF
        newE, newL = {}, {}
        kept1 = kept3 = 0
        tighten = False
        if kind == 'cost':
            d = p.cost[s] - self.o_cost[s]
            use3 = self.L3c
            if d >= 0:
                tighten = True
                flag = self._touch_flags(oc, lambda b, ss: ss == s, lambda z: False) if use3 else {}
            for k, (v, ss) in E.items():
                if d >= 0:
                    if use3 and not flag.get(k, True):
                        newE[k] = [v, ss]; kept3 += 1
                    elif v > 0 and self.L2:
                        newL[k] = v
                elif self.L4 and v + d > 0:
                    newL[k] = v + d
            for k, v in L.items():
                if k in newE or (d >= 0 and not self.L2) or (d < 0 and not self.L4):
                    continue
                nv = v if d >= 0 else v + d
                if nv > newL.get(k, 0):
                    newL[k] = nv
        elif kind == 'delay':
            d = p.delay[s] - self.o_delay[s]
            if d >= 0:
                tighten = True
                flag = self._touch_flags(oc, lambda b, ss: ss == s, lambda z: False) if self.L3s else {}
                for k, (v, ss) in E.items():
                    if self.L3s and not flag.get(k, True):
                        newE[k] = [v, ss]; kept3 += 1
                    elif v > 0 and self.L2:
                        newL[k] = v
                for k, v in L.items():
                    if self.L2 and k not in newE and v > newL.get(k, 0):
                        newL[k] = v
        else:
            if kind == 'wait':
                tighten = (self.o_wait[s][w] and not p.wait[s][w])
                touches = lambda b, ss: ss == s and bool(b & bitw)
                leafbad = lambda z: False
            elif kind == 'viability':
                tighten = (p.actions[w] & ~self.o_actions[w]) == 0
                touches = lambda b, ss: False
                leafbad = lambda z: bool(z & bitw) and not self.c.terminal(z)
            else:
                tighten = False
                touches = lambda b, ss: True
                leafbad = lambda z: False
            use3 = tighten and self.L3s
            flag = self._touch_flags(oc, touches, leafbad) if use3 else {}
            for k, (v, ss) in E.items():
                if self.L1 and not (k[0] & bitw):
                    newE[k] = [v, ss]; kept1 += 1
                elif tighten:
                    if use3 and not flag.get(k, True):
                        newE[k] = [v, ss]; kept3 += 1
                    elif v > 0 and self.L2:
                        newL[k] = v
            for k, v in L.items():
                if k in newE:
                    continue
                if (self.L1 and not (k[0] & bitw)) or (tighten and self.L2):
                    if v > newL.get(k, 0):
                        newL[k] = v
        self.E, self.L = newE, newL
        self.Et = {}
        for (b, t) in newE:
            self.Et.setdefault(b, set()).add(t)
        self.snap(p)
        root_kept = self.root in newE
        self.stats = dict(kept_exact=len(newE), kept_L1=kept1, kept_L3=kept3, kept_lb=len(newL),
                          tighten=tighten, ub_finite=ub < INF, root_retained=root_kept, old_entries=len(E))
        r = self.root[0]
        if ub < INF:
            ub = ub * (1 + 1e-9) + 1e-9
        v = self.solve(r, 0, ub)
        if v > ub + EPS:
            v = self.solve(r, 0, INF)
        self.value = v


def verify_equivalence(n_inst=150, seed=128200):
    """With all switches on, MBRIso must keep exactly the same exact/bound entries as phase123 MBR."""
    import random, copy
    sys.path[:0] = [os.path.join(H, '../phase123')]
    class P: pass
    def gen(r, n, m):
        p = P(); p.n, p.m, p.deadline = n, m, r.randint(3, 9)
        p.actions = [(1 << r.randrange(4)) | ((1 << r.randrange(4)) if r.random() < .3 else 0) for _ in range(n)]
        p.outcomes = [[r.randrange(2) for _ in range(n)] for _ in range(m)]
        p.delay = [r.choice([1, 1, 2, 3, 4, 5]) for _ in range(m)]
        p.wait = [[r.random() > .06 for _ in range(n)] for _ in range(m)]
        p.cost = [float(r.choice([0, 1, 2, 3, 5, 8, 13])) for _ in range(m)]
        return p
    def mutate(p, r, kind):
        s = r.randrange(p.m); w = r.randrange(p.n)
        if kind == 'cost': p.cost[s] = float(r.choice([0, 1, 2, 3, 5, 8, 13, 21]))
        elif kind == 'delay': p.delay[s] = r.randint(1, 5)
        elif kind == 'outcome': p.outcomes[s][w] ^= 1
        elif kind == 'wait': p.wait[s][w] = not p.wait[s][w]
        else: p.actions[w] = r.randrange(1, 16) if r.random() < .3 else 1 << r.randrange(4)
        return s, w
    r = random.Random(seed); n = 0
    for inst in range(n_inst):
        p = gen(r, r.randint(4, 10), r.randint(3, 10)); a = MBR(p); b = MBRIso(p)
        for step in range(30):
            kind = r.choice(['cost', 'delay', 'outcome', 'wait', 'viability']); s, w = mutate(p, r, kind)
            a.update(kind, s, w); b.update(kind, s, w); n += 1
            assert a.E == b.E and a.L == b.L and a.value == b.value, (inst, step, kind)
    return n
