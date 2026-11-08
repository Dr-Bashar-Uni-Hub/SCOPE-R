# Phase 123 — Theory of Monotone Bound Reuse (MBR)

Status of each result: **[P]** = proved here (pen-and-paper, not machine-checked);
**[E]** = additionally verified empirically (file named). Nothing here is claimed novel unless
stated in NOVELTY.md.

## 0. Model

A model is M = (W, A, S, pos, τ, Safe, c, D): finite worlds W (uniform prior); for each world w a
nonempty viable-action set A(w); binary deterministic sensors s ∈ S with outcome sets pos_s ⊆ W,
integer delays τ_s ≥ 1, waiting-safe sets Safe_s ⊆ W and costs c_s ≥ 0; deadline D.

State (B,t), ∅ ≠ B ⊆ W. B is **terminal** iff ∩_{w∈B} A(w) ≠ ∅. Sensor s is **admissible** at
(B,t) iff t+τ_s ≤ D, B ⊆ Safe_s, and s **splits** B (B∩pos_s and B∖pos_s both nonempty).

    V_M(B,t) = 0                                   if B terminal
    V_M(B,t) = min_{s adm.} c_s + Σ_y (|B_y|/|B|) V_M(B_y, t+τ_s)   otherwise (min ∅ = +∞)

**Theorem 0 (Bellman optimality)** — frozen Phase 119: V_M(B,t) is the minimum expected
acquisition cost over all admissible, deadline-respecting policies whose every leaf is terminal;
+∞ iff none exists. Induction on |B| (children are strict subsets). [P, frozen; E: test_exact.py]

A *policy* from (B,t) is a finite binary tree whose internal nodes carry an admissible sensor and
whose leaves are terminal; J_M(π) denotes its expected cost.

## 1. Structural lemmas

**Lemma 1 (Subproblem locality).** V_M(B,t) depends on M only through (A(w))_{w∈B},
(pos_s ∩ B)_s, (Safe_s ∩ B)_s, τ, c and D. Hence an update that changes A(w), the outcome of
some sensor at w, or Safe_s at w leaves V(B,t) — and the optimal decisions at (B,t) — unchanged
for every B with w ∉ B, for all t. [P]

*Proof.* Induction on |B|. Terminality uses A on B only; admissibility uses τ, D, Safe_s∩B and the
split pos_s∩B; children B_y ⊂ B, to which the hypothesis applies. ∎

**Lemma 6 (Temporal monotonicity).** t ≤ t' ⇒ V_M(B,t) ≤ V_M(B,t'). [P]

*Proof.* Induction on |B|. Terminal: both 0. Otherwise any s admissible at (B,t') is admissible at
(B,t) (t+τ_s ≤ t'+τ_s ≤ D; Safe and split do not depend on time) and its children are at
t+τ_s ≤ t'+τ_s, so by the hypothesis each child value at (B,t) is ≤ its value at (B,t').
Minimising over a superset of sensors gives the claim (∞ handled trivially). ∎

**Lemma 2 (Relaxation monotonicity).** Call M' a *tightening* of M (M ⪯ M') if they share W,
pos and D, and c ≤ c', τ ≤ τ', Safe'_s ⊆ Safe_s, A'(w) ⊆ A(w). Then V_M ≤ V_{M'} pointwise.
In particular every exact value or valid lower bound for M is a valid lower bound for M'. [P]

*Proof.* Induction on |B|. If B is terminal under M, V_M = 0 ≤ V_{M'}. If V_{M'}(B,t) = ∞ the claim
is trivial. Otherwise B is nonterminal under M' and some s attains V_{M'}(B,t). s is admissible
under M: t+τ_s ≤ t+τ'_s ≤ D, B ⊆ Safe'_s ⊆ Safe_s, same split. Then
V_M(B,t) ≤ c_s + Σ p_y V_M(B_y,t+τ_s) ≤ c_s + Σ p_y V_M(B_y,t+τ'_s)   (Lemma 6)
≤ c'_s + Σ p_y V_{M'}(B_y,t+τ'_s) = V_{M'}(B,t)   (induction, c_s ≤ c'_s). ∎

Single-parameter updates classified as tightening: cost increase, delay increase, Safe bit
True→False, viable-set shrink A'(w) ⊆ A(w). Loosening is the reverse direction. Outcome flips and
viability changes that neither shrink nor grow A(w) are **non-monotone**.

**Lemma 3 (Untouched-policy certificate).** Let M ⪯ M' differ in one element and let π be an
optimal policy for (B,t) under M. If π is admissible under M', all its leaves remain terminal
under M', and J_{M'}(π) = J_M(π), then V_{M'}(B,t) = V_M(B,t) and π remains optimal. [P]

*Proof.* V_{M'}(B,t) ≤ J_{M'}(π) = J_M(π) = V_M(B,t) ≤ V_{M'}(B,t) by Lemma 2. ∎

*Implementation condition (sufficient).* MBR declares π "untouched" when (cost or delay of s) π never
queries s; (Safe_s at w) π never queries s at a belief containing w; (A(w) shrink) every leaf of π
containing w is still terminal under M'; any missing descendant entry ⇒ "touched". In each case
time stamps, admissibility of every internal node, terminality of every leaf and every cost term of
π are unchanged, so the hypothesis of Lemma 3 holds. Touched status propagates to all ancestors
(a node is untouched only if all its policy descendants are).

**Lemma 4 (Single-use cost bound).** If only c_j changes, to c_j + δ ≥ 0, then
V_M + min(δ,0) ≤ V_{M'} ≤ V_M + max(δ,0). [P; E: frozen Phase 117 found no violation]

*Proof.* Feasibility does not depend on costs, so both models have the same policy set, and
J_{M'}(π) = J_M(π) + δ·P_π(j queried). Along any root–leaf path j is queried at most once: after
querying j at B every descendant belief lies in one outcome cell of j, so j no longer splits and is
inadmissible. Hence P_π ∈ [0,1]. Minimise over π. ∎

**Lemma 5 (Replay upper bound).** Replaying the stored optimal policy of M under M' — checking at
every node admissibility at the *new* time stamp, identity of the split, and terminality of every
leaf under M' — either fails or yields a policy feasible for M', whose cost J_{M'} ≥ V_{M'}(root). [P]

*Proof.* Every check that defines feasibility is performed explicitly under M'; the cost is computed
with M' costs. Optimality of V_{M'} (Theorem 0) gives the inequality. ∎

**Proposition H (Huffman-type bound, adapted from Pattipati & Alexandridis 1990).** For nonterminal
B, let c_min(t) be the cheapest cost among sensors with t+τ_s ≤ D (+∞ if none), S_k the worlds of B
whose viable set is exactly {k}, and L the minimum weighted path length (Huffman cost) of the weights
(|S_k|)_k (L = 0 if fewer than two classes are present). Then
h(B,t) = c_min(t)·max(1, L/|B|) ≤ V_M(B,t). [P; E: 78,795 states, 0 violations, see console log in
README]

*Proof.* Any policy queries at least once (B nonterminal) and every query at time t' ≥ t uses a
sensor schedulable from t' and therefore from t, costing ≥ c_min(t); so J(π) ≥ c_min(t)·E[#queries]
and E[#queries] ≥ 1. E[#queries] = Σ_w depth(w)/|B| ≥ Σ_k Σ_{w∈S_k} depth(w)/|B|. A terminal leaf
cannot contain worlds from two different single-action classes (their intersection would be empty),
so choosing for each class its shallowest leaf gives distinct leaves of depths d_k with
Σ 2^{-d_k} ≤ 1 (Kraft) and Σ_k Σ_{w∈S_k} depth(w) ≥ Σ_k |S_k| d_k ≥ L (Huffman optimality over all
integer depth vectors satisfying Kraft). ∎

## 2. Search correctness

**Lemma 7 (Branch-and-bound contract).** Suppose every value used by `lb` is a valid lower bound
(stored exact entries, stored L entries, h, and temporal values from Lemma 6). Then
`solve(B,t,ub)` returns v with: v ≤ ub ⇒ v = V(B,t) (and the argmin is stored); v > ub ⇒
v ≤ V(B,t) (stored as a lower bound). [P, modulo floating tolerance ε = 1e-9]

*Proof sketch.* Induction on |B|. Every admissible alternative s has lower bound
q_s = c_s + Σ p_y lb(B_y) ≤ Q_s. An alternative is skipped only if q_s exceeds the current bound
(ub or best value found), or a child call returned a value above its budget — in which case by
induction that value is a child lower bound and the recomputed q_s exceeds the bound. Budgets are
chosen so that child exactness is guaranteed whenever Q_s could beat the bound. If some exact
alternative ≤ ub is found, every skipped alternative has lower bound ≥ that value, so the minimum is
exact. Otherwise every alternative has a lower bound > ub, and their minimum (max'd with prior bounds)
is returned. ∎

**Theorem (Exactness of MBR).** After any finite sequence of single-element updates of the five
kinds, MBR's root value equals V_{M_k}(root). [P from Lemmas 1–7 and H; E below]

*Proof.* By Lemmas 1 and 3 every retained exact entry is exact for M_k; by Lemmas 1, 2 and 4 every
retained bound is valid; h is admissible (Prop. H or c_min alone); the root budget is achievable
(Lemma 5) or +∞. Lemma 7 at the root yields the exact value. Entries whose validity cannot be
established (non-monotone parts, delay decreases, loosening at beliefs containing w) are discarded. ∎

## 3. Empirical verification (distinct from proof)

| Test | File | Checks | Failures |
|---|---|---|---|
| Root values vs exhaustive DP, frozen `verified.fresh`, exact-rational oracle | test_exact.py, test_exact_feasible.py | 68,000 sequential updates (9,880 rational) | 0 |
| Same with Huffman variants | test_exact_H.py | 32,000 (5,000 rational) | 0 |
| **State-level**: every retained exact entry and stored lower bound vs ground truth | test_lemmas.py | 42,173 exact + 37,302 bounds | 0 |
| Phase 113 delay counterexample, all 5 predecessor delays | test_lemmas.py | 5 | 0 |
| Benchmarks (every update vs exhaustive DP up to 32 worlds; vs fresh BnB at 40) | bench.py | 1,680 | 0 |

## 4. Known limits of the theory

Uniform prior and deterministic binary sensors (Lemmas 2–4 extend to nonuniform priors unchanged;
stochastic observations break the "single use" argument of Lemma 4 and the support-set state
representation). No worst-case complexity improvement is claimed: exact planning remains NP-hard
(Hyafil & Rivest 1976); MBR improves the constant via certified reuse. Floating-point comparisons use
ε = 1e-9; exactness was cross-checked with rational arithmetic only on instances up to 8 worlds.

## 5. Status of each result relative to prior work (added Phase 127)

| Result | Status | Prior work |
|---|---|---|
| Theorem 0 (Bellman optimality) | standard | DP for test sequencing (Pattipati & Alexandridis 1990; Liu & Shachter 2015) |
| Lemma 1 (locality) | standard DP property | — |
| Lemma 6 (temporal monotonicity) | elementary property of deadline models | — |
| Lemma 2 (relaxation monotonicity) | known principle, instantiated here | Adaptive A* (Koenig & Likhachev 2005, 2006); MurTree Prop. 11; DynamicHS Property 1 |
| Lemma 3, cost case | known in substance | admissible domains / inactive nodes (Nielsen & Jensen 2003; Bhattacharjya & Shachter 2008) |
| **Lemma 3, structural cases** (delay increase under deadline, waiting-safety removal, decision-region shrink) | **proposed** — no prior statement found in the documented screening | parametric sensitivity analysis assumes probabilities in (0,1) and fixed structure; DynamicHS maintains diagnosis sets, not expected-cost policies; Minimax LPA* maintains worst-case values by cost-change propagation |
| Lemma 4 (single-use cost bound) | special case of known cost-sensitivity results | as above |
| Lemma 5 (replay upper bound) | standard | — |
| Proposition H | adaptation of a known bound | Pattipati & Alexandridis 1990 |
| Lemma 7, Theorem (MBR exactness) | correctness of the proposed algorithm | — |

Mathematical depth. Lemma 3 itself is short: it follows from Lemma 2 plus feasibility of the untouched
sub-policy. The contribution is identifying, per structural update type, a sufficient and cheaply checkable
"untouched" condition, and using it to retain exact values inside exact bounded re-search.

## 6. Phase 128 audit additions
- **Proposition H with overlapping action sets.** Hypotheses with |A(w)| ≥ 2 belong to no single-action class S_k, so they never enter the Kraft argument; overlap can only weaken the bound (to c_min(t) when all hypotheses overlap), never violate it. Checked on 488,362 states incl. every subset of hypotheses (phase128/propH_audit.py). No correction needed.
- **Strengthened Lemma 7.** For any ub ∈ ℝ ∪ {+∞}: returns V(B,t) exactly if V(B,t) ≤ ub, else a valid lower bound > ub; with ub = +∞ the result is always exact, and +∞ iff (B,t) is infeasible. +∞ lower bounds arise only from proven infeasibility (no schedulable test; stored/retained +∞ values, which are retained only for unchanged subproblems (Lemma 1) or under tightening (Lemma 2); temporal bounds (Lemma 6)).
- **Strengthened Theorem.** Cases: (i) replay succeeds → finite achievable budget ≥ V′ → exact; (ii) replay fails → budget +∞ → exact; (iii) updated model infeasible → replay must fail (a replayed policy would be feasible) → case (ii) → returns +∞. The safety-net re-solve is unreachable by (i); fired 0 / 27,290 instrumented root calls.
- **Status of Lemma 3 (structural).** Correct and elementary (immediate from Theorem 0 + Lemma 2). Controlled isolation (phase128) shows its eager evaluation reduces expansions but is a net runtime cost except after delay increases on synthetic instances.
