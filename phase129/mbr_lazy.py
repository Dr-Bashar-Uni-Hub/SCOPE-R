"""Phase 129: lazy (on-demand) evaluation of the structural retained-exactness certificate (Lemma 3,
structural cases: delay increase, waiting-safety removal, decision-region shrink).

Variants (all share phase123 BnB search, locality, Lemma 2 bounds, Lemma 4, replay, temporal bounds, and
the eager cost-increase case of Lemma 3, so they differ ONLY in how the structural certificate is used):
  MBRNoCert : structural certificate off (== phase128 MBRIso(L3s=False))
  MBREager  : structural certificate checked eagerly over the whole cache (== phase128 MBRIso()), timed
  MBRLazy   : structural certificate checked on demand when the search reaches an eligible entry

Lazy mechanism. On a structural tightening update every old exact entry that the eager certificate would
examine becomes a lower bound (valid by Lemma 2, exactly as in MBRNoCert) and is additionally recorded as
*pending* with its old optimal test. When solve() reaches a pending state, the untouched condition of
Section 4.2 is evaluated for that state's old optimal sub-policy only (memoised within the update, over the
previous cache and previous compiled model). If untouched, the state and every untouched descendant found
during the check are promoted to exact entries (Lemma 3) and no expansion is performed; otherwise the
state is searched normally from its lower bound. Pending marks not reached are discarded at the next update
(their lower bounds remain and are transformed by the usual rules). Correctness therefore rests on exactly
the same lemmas as the eager variant.
"""
import os, sys, time
H = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(H, '../phase128'), os.path.join(H, '../phase123')]
from mbr_iso import MBRIso
from mbr import INF, EPS


class MBRNoCert(MBRIso):
    def __init__(self, p):
        self.cert_ns = 0; self.cert_nodes = 0
        super().__init__(p, L3s=False)


class MBREager(MBRIso):
    """Eager structural certificate (Phase 128 behaviour); certificate time is measured."""
    def __init__(self, p):
        self.cert_ns = 0; self.cert_nodes = 0; self._in_structural = False
        super().__init__(p)

    def update(self, kind, s, w):
        self._in_structural = kind in ('delay', 'wait', 'viability')
        super().update(kind, s, w)
        self._in_structural = False

    def _touch_flags(self, oc, touches_node, leaf_bad):
        t0 = time.perf_counter_ns()
        f = super()._touch_flags(oc, touches_node, leaf_bad)
        if self._in_structural:
            self.cert_ns += time.perf_counter_ns() - t0; self.cert_nodes += len(f)
        return f


class MBRLazy(MBRIso):
    def __init__(self, p):
        self.pending = {}; self.oldE = None; self.cflag = {}
        self.cert_ns = 0; self.cert_nodes = 0; self.promoted = 0
        super().__init__(p, L3s=False)          # structural cases handled lazily below

    # ---- update: identical cache transform to MBRNoCert, plus pending marks for structural tightening
    def update(self, kind, s, w):
        self.pending = {}; self.oldE = None; self.cflag = {}
        p = self.p
        oldE = self.E; oc = self.c
        structural_tight = False
        if kind == 'delay' and p.delay[s] >= self.o_delay[s]:
            structural_tight = True
            self._touches = (lambda b, ss, s=s: ss == s); self._leafbad = (lambda z: False)
            elig = list(oldE.items())
        elif kind == 'wait' and self.o_wait[s][w] and not p.wait[s][w]:
            structural_tight = True; bw = 1 << w
            self._touches = (lambda b, ss, s=s, bw=bw: ss == s and bool(b & bw)); self._leafbad = (lambda z: False)
            elig = [(k, e) for k, e in oldE.items() if k[0] & bw]
        elif kind == 'viability' and (p.actions[w] & ~self.o_actions[w]) == 0:
            structural_tight = True; bw = 1 << w
            self._touches = (lambda b, ss: False)
            self._leafbad = None; self._vbw = bw   # leaf test needs the new model: set at install time
            elig = [(k, e) for k, e in oldE.items() if k[0] & bw]
        if structural_tight:
            self.oldE = oldE; self._oc = oc
            self._pending_src = elig
        self._structural_tight = structural_tight
        super().update(kind, s, w)               # transform cache (no structural certificate) and solve
        self.pending = {}; self.oldE = None      # discard unreached marks

    # hook: MBRIso.update calls compile() first and solve() last; pending marks are installed lazily at
    # the first solve() call of the update, when the new compiled model and the new cache both exist.
    def compile(self):
        super().compile()
        if getattr(self, '_structural_tight', False) and getattr(self, '_pending_src', None) is not None:
            self._install_after_compile = True

    def solve(self, b, t, ub):
        if getattr(self, '_install_after_compile', False):
            self._install_pending()
        key = (b, t)
        if self.pending and key in self.pending:
            t0 = time.perf_counter_ns()
            touched = self._cert(key)
            self.cert_ns += time.perf_counter_ns() - t0
            if not touched:
                return self.E[key][0]
            self.pending.pop(key, None)
        return super().solve(b, t, ub)

    def _install_pending(self):
        self._install_after_compile = False
        if self._leafbad is None:           # viability shrink: need the new compiled model
            bw = self._vbw
            nc = self.c
            self._leafbad = (lambda z, bw=bw, nc=nc: bool(z & bw) and not nc.terminal(z))
        self.pending = {k: e for k, e in self._pending_src if k not in self.E}
        self._pending_src = None

    def _cert(self, k0):
        """Untouched check for the old optimal sub-policy at k0 (memoised); promotes untouched nodes."""
        flag, E0, oc = self.cflag, self.oldE, self._oc
        touches, leafbad = self._touches, self._leafbad
        if k0 in flag:
            return flag[k0]
        newly = []
        stack = [(k0, False)]
        while stack:
            k, done = stack.pop()
            if k in flag and not done:
                continue
            v, s = E0[k]
            b, t = k
            if s < 0:
                flag[k] = (v == INF)
                if not flag[k]: newly.append(k)
                continue
            x = b & oc.pos[s]; y = b ^ x; t2 = t + oc.delay[s]
            kids = []
            for z in (x, y):
                if oc.terminal(z):
                    if leafbad(z):
                        kids.append(None)
                else:
                    kids.append((z, t2))
            if not done:
                self.cert_nodes += 1
                if touches(b, s) or None in kids:
                    flag[k] = True; continue
                stack.append((k, True))
                for kk in kids:
                    if kk not in flag:
                        if kk in E0:
                            stack.append((kk, False))
                        else:
                            flag[kk] = True
            else:
                flag[k] = any(flag.get(kk, True) for kk in kids)
                if not flag[k]: newly.append(k)
        for k in newly:                          # promote every untouched node found (Lemma 3)
            if k not in self.E:
                v, s = E0[k]
                self.store_exact(k[0], k[1], v, s)
                self.pending.pop(k, None); self.promoted += 1
        return flag[k0]
