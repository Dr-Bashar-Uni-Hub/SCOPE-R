"""SCOPE-R Phase 123 — Monotone Bound Reuse (MBR) exact replanning.

Model interface (identical to frozen SCOPE-R objects): p.n, p.m, p.deadline,
p.actions[w] (bitmask of viable terminal actions), p.outcomes[s][w] in {0,1},
p.delay[s] (int>0), p.wait[s][w] (bool), p.cost[s] (float>=0). Uniform prior.

Contents
  exhaustive(p)        : independent fresh exhaustive Bellman DP (no 2^n tables)
  BnB(p)               : fresh exact branch-and-bound (no cross-update reuse)
  MBR(p)               : BnB + monotone bound reuse across model updates
All solvers return exact optimal expected acquisition cost (math.inf if infeasible).
"""
import math
INF = math.inf
EPS = 1e-9


class Compiled:
    """Bit-level view of the current model (O(m*n) to build)."""
    __slots__ = ('n', 'm', 'D', 'pos', 'safe', 'amasks', 'cost', 'delay', 'cmin_t', 'dmin')

    def __init__(self, p):
        n, m = p.n, p.m
        self.n, self.m, self.D = n, m, p.deadline
        self.pos = [sum(1 << w for w in range(n) if p.outcomes[s][w]) for s in range(m)]
        self.safe = [sum(1 << w for w in range(n) if p.wait[s][w]) for s in range(m)]
        acts = 0
        for a in p.actions:
            acts |= a
        self.amasks = [sum(1 << w for w in range(n) if p.actions[w] >> k & 1)
                       for k in range(acts.bit_length()) if acts >> k & 1]
        self.cost = list(p.cost)
        self.delay = list(p.delay)
        self.dmin = min(self.delay) if m else 10 ** 9
        # cheapest sensor still schedulable from time t (ignores safety/informativeness): admissible bound
        self.cmin_t = [min((self.cost[s] for s in range(m) if t + self.delay[s] <= self.D), default=INF)
                       for t in range(self.D + 1)]

    def terminal(self, b):
        for am in self.amasks:
            if b & ~am == 0:
                return True
        return False

    def h(self, b, t):
        """Admissible lower bound for an unexplored state (0 if terminal)."""
        if self.terminal(b):
            return 0.0
        if t > self.D:
            return INF
        return self.cmin_t[t]


def exhaustive(p):
    """Fresh exhaustive exact DP (independent of BnB code paths; used as oracle)."""
    c = Compiled(p)
    memo = {}

    def V(b, t):
        key = (b, t)
        if key in memo:
            return memo[key]
        if c.terminal(b):
            memo[key] = 0.0
            return 0.0
        best = INF
        nb = b.bit_count()
        for s in range(c.m):
            t2 = t + c.delay[s]
            if t2 > c.D or b & ~c.safe[s]:
                continue
            x = b & c.pos[s]
            y = b ^ x
            if not x or not y:
                continue
            vx = V(x, t2)
            if vx == INF:
                continue
            vy = V(y, t2)
            if vy == INF:
                continue
            q = c.cost[s] + (x.bit_count() * vx + y.bit_count() * vy) / nb
            if q < best:
                best = q
        memo[key] = best
        return best

    return V((1 << p.n) - 1, 0), len(memo)


class BnB:
    """Exact depth-first branch-and-bound over belief-time AND/OR graph.

    solve(b,t,ub) contract: returns v. If v <= ub (+EPS) then v is the exact optimum of (b,t)
    and (b,t) is stored in self.E with its argmin sensor; otherwise v is a valid lower bound > ub,
    stored in self.L. Lower bounds come from (i) stored L, (ii) temporal dominance
    V(b,t') <= V(b,t) for t' <= t, (iii) the admissible heuristic h.
    """

    def __init__(self, p, temporal=True):
        self.p = p
        self.temporal = temporal
        self.E = {}   # (b,t) -> [value, sensor]
        self.L = {}   # (b,t) -> lower bound
        self.Et = {}  # b -> set of t with exact entries (for temporal dominance)
        self.expanded = 0
        self.compile()
        self.root = ((1 << p.n) - 1, 0)
        self.value = self.solve(self.root[0], 0, INF)

    def compile(self):
        self.c = Compiled(self.p)

    # ---- bound lookup -------------------------------------------------
    def lb(self, b, t):
        c = self.c
        if c.terminal(b):
            return 0.0
        e = self.E.get((b, t))
        if e is not None:
            return e[0]
        v = self.L.get((b, t), 0.0)
        hv = c.h(b, t)
        if hv > v:
            v = hv
        if self.temporal:
            ts = self.Et.get(b)
            if ts:
                for t2 in ts:
                    if t2 <= t:
                        ev = self.E[(b, t2)][0]
                        if ev > v:
                            v = ev
        return v

    def store_exact(self, b, t, v, s):
        self.E[(b, t)] = [v, s]
        self.L.pop((b, t), None)
        self.Et.setdefault(b, set()).add(t)

    # ---- search ---------------------------------------------------------
    def solve(self, b, t, ub):
        c = self.c
        if c.terminal(b):
            return 0.0
        key = (b, t)
        e = self.E.get(key)
        if e is not None:
            return e[0]
        L0 = self.lb(b, t)
        if L0 > ub + EPS:
            return L0
        self.expanded += 1
        nb = b.bit_count()
        cand = []
        for s in range(c.m):
            t2 = t + c.delay[s]
            if t2 > c.D or b & ~c.safe[s]:
                continue
            x = b & c.pos[s]
            y = b ^ x
            if not x or not y:
                continue
            lx = self.lb(x, t2)
            ly = self.lb(y, t2)
            q = c.cost[s] + (x.bit_count() * lx + y.bit_count() * ly) / nb if lx < INF and ly < INF else INF
            cand.append((q, s, x, y, t2, lx, ly))
        if not cand:
            self.store_exact(b, t, INF, -1)
            return INF
        cand.sort(key=lambda z: z[0])
        best, bests, newlb = INF, -1, INF
        for q, s, x, y, t2, lx, ly in cand:
            bound = ub if best == INF else best
            if q == INF or q > bound + EPS or (best < INF and q >= best - EPS):
                if q < newlb:
                    newlb = q
                continue
            nx, ny = x.bit_count(), y.bit_count()
            cs = c.cost[s]
            # evaluate the larger child first (more mass -> tighter test)
            if ny > nx:
                x, y, nx, ny, lx, ly = y, x, ny, nx, ly, lx
            bx = (bound - cs) * nb / nx - ny * ly / nx if bound < INF else INF
            vx = self.solve(x, t2, bx)
            if vx > bx + EPS:
                qq = cs + (nx * vx + ny * ly) / nb if vx < INF else INF
                if qq < newlb:
                    newlb = qq
                continue
            by = (bound - cs) * nb / ny - nx * vx / ny if bound < INF else INF
            vy = self.solve(y, t2, by)
            qq = cs + (nx * vx + ny * vy) / nb if vy < INF else INF
            if vy > by + EPS or qq > bound + EPS:
                if qq < newlb:
                    newlb = qq
                continue
            if qq < best:
                best, bests = qq, s
        if best < INF and best <= ub + EPS:
            self.store_exact(b, t, best, bests)
            return best
        if best == INF and newlb == INF:   # every alternative proven infeasible
            self.store_exact(b, t, INF, -1)
            return INF
        v = max(L0, newlb)
        self.L[key] = v
        return v

    def policy_size(self):
        seen = set()
        st = [self.root]
        while st:
            k = st.pop()
            if k in seen or k not in self.E:
                continue
            seen.add(k)
            v, s = self.E[k]
            if s < 0:
                continue
            b, t = k
            x = b & self.c.pos[s]
            for z in (x, b ^ x):
                if not self.c.terminal(z):
                    st.append((z, t + self.c.delay[s]))
        return len(seen)

    # Fresh baseline: rebuild everything after any update.
    def update(self, kind, s, w):
        self.E.clear(); self.L.clear(); self.Et.clear(); self.compile()
        self.value = self.solve(self.root[0], 0, INF)


class MBR(BnB):
    """BnB + Monotone Bound Reuse across sequential model updates.

    Update taxonomy (proved in THEORY.md):
      * world-local updates (outcome/wait/viability at world w): every (b,t) with w not in b is
        unaffected -> exact and bound entries retained verbatim (Lemma 1, subproblem locality).
      * tightening updates (cost increase, delay increase, wait True->False, viability shrink):
        old exact values and old lower bounds remain valid lower bounds (Lemma 2, relaxation
        monotonicity); old exact entries whose optimal sub-policy never touches the changed element
        remain exact (Lemma 3, untouched-policy certificate).
      * cost decrease by d: old values minus d are lower bounds (Lemma 4, single-use bound).
      * any update: replaying the old optimal policy under the new model, when well defined and
        feasible, yields an achievable root upper bound (Lemma 5); used as the root budget.
      * all other affected entries are discarded.
    """

    def __init__(self, p, temporal=True, use_ub=True):
        self.use_ub = use_ub
        self.snap(p)
        super().__init__(p, temporal)
        self.stats = {}

    def snap(self, p):
        self.o_cost = list(p.cost); self.o_delay = list(p.delay)
        self.o_wait = [list(r) for r in p.wait]; self.o_actions = list(p.actions)
        self.o_out = [list(r) for r in p.outcomes]

    # -- which old exact entries use the changed element (on their optimal sub-policy)
    def _touch_flags(self, oc, touches_node, leaf_bad):
        """flag[k]=True iff the old optimal sub-policy rooted at exact entry k touches the change.
        oc: compiled OLD model (to replay old partitions/time stamps)."""
        flag = {}
        E = self.E
        for k0 in list(E.keys()):
            if k0 in flag:
                continue
            stack = [(k0, False)]
            while stack:
                k, done = stack.pop()
                if k in flag and not done:
                    continue
                v, s = E[k]
                b, t = k
                if s < 0:                       # infeasible leaf or stored inf
                    flag[k] = True if v == INF else False
                    continue
                x = b & oc.pos[s]; y = b ^ x; t2 = t + oc.delay[s]
                kids = []
                for z in (x, y):
                    if oc.terminal(z):
                        if leaf_bad(z):
                            kids.append(None)       # touched terminal leaf
                    else:
                        kids.append((z, t2))
                if not done:
                    if touches_node(b, s) or None in kids:
                        flag[k] = True
                        continue
                    stack.append((k, True))
                    for kk in kids:
                        if kk not in flag:
                            if kk in E:
                                stack.append((kk, False))
                            else:
                                flag[kk] = True     # missing child: be conservative
                else:
                    flag[k] = any(flag.get(kk, True) for kk in kids)
        return flag

    def _replay_ub(self, oc):
        """Cost under the NEW model of the OLD optimal policy (time stamps may only shrink
        or stay; any inadmissible/undefined step -> INF, i.e. no bound)."""
        nc = self.c
        E = self.E
        memo = {}

        def go(b, t_new, k_old):
            if nc.terminal(b):
                return 0.0
            e = E.get(k_old)
            if e is None or e[1] < 0 or k_old[0] != b:
                return INF
            s = e[1]
            t2n = t_new + nc.delay[s]
            if t2n > nc.D or b & ~nc.safe[s]:
                return INF
            x = b & nc.pos[s]; y = b ^ x
            xo = b & oc.pos[s]
            if not x or not y or x != xo:
                return INF
            t2o = k_old[1] + oc.delay[s]
            mk = (b, t_new)
            if mk in memo:
                return memo[mk]
            vx = go(x, t2n, (x, t2o))
            vy = go(y, t2n, (y, t2o)) if vx < INF else INF
            r = nc.cost[s] + (x.bit_count() * vx + y.bit_count() * vy) / b.bit_count() if vy < INF else INF
            memo[mk] = r
            return r
        return go(self.root[0], 0, self.root)

    def update(self, kind, s, w):
        p = self.p
        oc = self.c                       # old compiled model
        self.compile()                    # new compiled model
        bitw = 1 << w
        E, L = self.E, self.L
        ub = INF
        if self.use_ub:
            ub = self._replay_ub(oc)      # computed before entries are modified
        newE, newL = {}, {}
        tighten = False
        if kind == 'cost':
            d = p.cost[s] - self.o_cost[s]
            if d >= 0:
                tighten = True
                flag = self._touch_flags(oc, lambda b, ss: ss == s, lambda z: False)
            for k, (v, ss) in E.items():
                if d >= 0:
                    if not flag.get(k, True):
                        newE[k] = [v, ss]
                    elif v > 0:
                        newL[k] = v
                else:
                    if v - (-d) > 0:
                        newL[k] = v + d          # V_new >= V_old - |d|
            for k, v in L.items():
                if k in newE:
                    continue
                nv = v if d >= 0 else v + d
                if nv > newL.get(k, 0):
                    newL[k] = nv
        elif kind == 'delay':
            d = p.delay[s] - self.o_delay[s]
            if d >= 0:
                tighten = True
                flag = self._touch_flags(oc, lambda b, ss: ss == s, lambda z: False)
                for k, (v, ss) in E.items():
                    if not flag.get(k, True):
                        newE[k] = [v, ss]
                    elif v > 0:
                        newL[k] = v
                for k, v in L.items():
                    if k not in newE and v > newL.get(k, 0):
                        newL[k] = v
            # delay decrease: no lower bounds survive (only the replay upper bound)
        else:  # world-local updates
            if kind == 'wait':
                tighten = (self.o_wait[s][w] and not p.wait[s][w])
                touches = lambda b, ss: ss == s and bool(b & bitw)
                leafbad = lambda z: False
            elif kind == 'viability':
                old_a, new_a = self.o_actions[w], p.actions[w]
                tighten = (new_a & ~old_a) == 0          # new subset of old
                touches = lambda b, ss: False
                leafbad = lambda z: bool(z & bitw) and not self.c.terminal(z)
            else:  # outcome: non-monotone
                tighten = False
                touches = lambda b, ss: True
                leafbad = lambda z: False
            if tighten:
                flag = self._touch_flags(oc, touches, leafbad)
            for k, (v, ss) in E.items():
                if not (k[0] & bitw):
                    newE[k] = [v, ss]                     # Lemma 1
                elif tighten:
                    if not flag.get(k, True):
                        newE[k] = [v, ss]                 # Lemma 3
                    elif v > 0:
                        newL[k] = v                       # Lemma 2
            for k, v in L.items():
                if k in newE:
                    continue
                if not (k[0] & bitw) or tighten:
                    if v > newL.get(k, 0):
                        newL[k] = v
        self.E, self.L = newE, newL
        self.Et = {}
        for (b, t) in newE:
            self.Et.setdefault(b, set()).add(t)
        self.snap(p)
        self.stats = dict(kept_exact=len(newE), kept_lb=len(newL), tighten=tighten,
                          ub_finite=ub < INF)
        r = self.root[0]
        if ub < INF:
            ub = ub * (1 + 1e-9) + 1e-9
        v = self.solve(r, 0, ub)
        if v > ub + EPS:              # cannot happen if ub is achievable; safety net
            v = self.solve(r, 0, INF)
        self.value = v
