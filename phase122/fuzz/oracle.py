"""Independent exact oracle (Phase 122). Written from the problem statement only:
frozenset beliefs, Fraction arithmetic (exact rationals), no bitmasks, no shared code."""
from fractions import Fraction
from functools import lru_cache
INF=None  # represent +inf as None
def solve(n,m,actions,outcomes,delay,wait,cost,deadline):
    @lru_cache(None)
    def V(B,t):
        common=None
        for w in B:
            common=actions[w] if common is None else common&actions[w]
        if common: return Fraction(0)
        best=INF
        for s in range(m):
            if t+delay[s]>deadline: continue
            if not all(wait[s][w] for w in B): continue
            parts={}
            for w in B: parts.setdefault(outcomes[s][w],[]).append(w)
            if len(parts)<2: continue
            tot=Fraction(cost[s]).limit_denominator(10**6) if not isinstance(cost[s],int) else Fraction(cost[s])
            ok=True
            for ws in parts.values():
                v=V(frozenset(ws),t+delay[s])
                if v is INF: ok=False;break
                tot+=Fraction(len(ws),len(B))*v
            if ok and (best is INF or tot<best): best=tot
        return best
    return V(frozenset(range(n)),0)
