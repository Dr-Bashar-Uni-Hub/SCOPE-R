# Phase 130 — Novelty and feasibility: minimal recomputation regions after non-monotone updates

Question. After a non-monotone update (outcome flip of test s at hypothesis w; or a viability change that
neither shrinks nor grows A(w)), is there a provably sufficient minimal or near-minimal region of the
policy state space that must be recomputed, without re-solving the whole problem?

Status: investigation only (no method implemented). Counterexamples verified by brute force in
`phase130/counterexamples.py` against the exhaustive solver. Manuscript not modified.

## 1. Formalisation

Model M, update u to M′ (flip of outcome of s at w). States (B, t). Three distinct notions of "region":
* **Touched (input-affected) set** I(u): states (B, t) with w ∈ B at which s is admissible under M or M′ — the
  states whose children change. (All other states keep their children; by Lemma 1, every state with w ∉ B
  keeps its value.)
* **Value-affected set** Δ(u) = { (B,t) : V_M(B,t) ≠ V_M′(B,t) } ⊆ { (B,t) : w ∈ B }.
* **Re-certification set** for the root: a set C of states whose new exact values are computed such that, together
  with information valid without computation (old values of states with w ∉ B, admissible bounds such as
  Proposition H and the deletion bound below), a feasible policy and a lower-bound proof certify V_M′(root).
  A *minimal* certificate is one with no proper sub-certificate.

The user's "provably sufficient minimal region" corresponds to the third notion.

## 2. Closest prior work (all sources verified)

| Area | Work | What it already settles |
|---|---|---|
| Bounded incremental computation | Ramalingam & Reps, TCS 158(1):233–277, 1996, doi:10.1016/0304-3975(95)00079-8 | Measures incremental cost by the size of input + output change; separates polynomially bounded, inherently exponentially bounded and unbounded dynamic problems for locally persistent algorithms. Recomputing exactly the affected portion is the defining target of this theory. |
| Incremental heuristic search | LPA*/D* Lite; Minimax LPA* (Likhachev & Koenig, NIPS 15, 2003, pp. 1595–1602); Adaptive A* | Re-expand only locally inconsistent states, including on minimax AND/OR graphs. |
| Demand-driven incremental computation | Adapton (Hammer et al., PLDI 2014, pp. 156–166) | Dirty-marking plus demand-driven, sound recomputation of exactly what an observer needs. |
| MDP replanning after model change | Prioritized sweeping (Moore & Atkeson 1993); generalized prioritized sweeping (Wingate & Seppi, JMLR 6, 2005); small backups (van Seijen & Sutton 2013) | Back up only states whose Bellman error is affected by a model change. |
| AND/OR search for decision trees / diagnosis | Martelli & Montanari (CACM 1978); Mahanti & Bagchi (JACM 32(1):28–51, 1985); Bayer-Zubek & Dietterich (UAI 2004) | Exact AO* over AND/OR graphs with admissible bounds, incl. diagnostic policies. |
| Complexity of AND/OR evaluation | Saks & Wigderson, FOCS 1986, pp. 29–38, doi:10.1109/SFCS.1986.44 | Deterministic evaluation of AND/OR trees must read all leaves in the worst case; randomized algorithms do provably better — the classical theory of "what any algorithm must examine". |
| Reoptimization | Böckenhauer, Hromkovič, Mömke & Widmayer, SOFSEM 2008, LNCS 4910, pp. 50–65 (and follow-up work) | Generic technique: reoptimization of NP-hard problems given an optimal solution of a locally modified instance is typically NP-hard. |
| Optimal decision trees | MurTree (similarity lower bound; incremental solving), STreeD; fully-dynamic approximate trees (arXiv:2302.03994, 2023) | Bounds transferred between similar datasets; approximate trees maintained under insertions/deletions. |
| Sensitivity analysis | Nielsen & Jensen (2003); Bhattacharjya & Shachter (2008) | Continuous parameters of a fixed structure only (Phase 125–127). |

## 3. Results of the investigation

**R1 (known; Lemma 1).** Δ(u) ⊆ { (B,t) : w ∈ B }; all other states are reusable verbatim.

**R2 — no sensitivity-type certificate (CE1, verified).** One outcome flip can change an optimal value by an
arbitrary factor (1 → M for any M) or from finite to +∞. Hence no interval/Lipschitz certificate of the kind
available for cost changes exists for outcome flips.

**R3 — old-policy-local information is insufficient (CE2, verified).** Two instances share the same old optimal
policies and the same values on every state of those policies; after the identical flip, the root value is
unchanged in one (2.0 → 2.0) and changes in the other (2.0 → 3.0), the difference being the cost of a test the old
policy never uses. Any sound certificate must, in general, inspect off-policy states. Replay and untouched-policy
reasoning (Phases 123–129) cannot be strengthened into a complete certificate.

**R4 — exponential gap between touched and changed (CE3, verified).** In a family of instances the touched set
has 2^(n−1) beliefs (×(D+1) time stamps) for n = 6…12, while only 0–6 states change value and the root never
changes. Change propagation over I(u) (ClosureRepair, LPA*-style repair, Ramalingam–Reps) does work proportional
to I(u), not Δ(u).

**R5 — no canonical minimal region; no deterministic instance-optimality (CE4, verified).** With the actual
Proposition H bound, every certificate of the root value must open subtree X or subtree Y; opening either one
suffices, opening neither does not. Thus {X} and {Y} are both minimal and disjoint: "the" minimal region is not
well defined, and the meaningful object is a minimum-size certificate. In an expansion-only (query) model, a
deterministic algorithm cannot know which side is cheaper to open, and an adversary can make the first-opened side
arbitrarily expensive — the classical argument behind deterministic AND/OR evaluation lower bounds (Saks &
Wigderson 1986). (A first attempt at CE4 failed because the competitor test also resolved X and Y; it is
retained in the script.)

**R6 — worst-case hardness of exact reoptimization (proof sketch via a known technique).** Consider the special
case with unit costs, one distinct action per hypothesis, no deadline and all tests safe: minimising the expected
number of binary tests needed to identify a hypothesis, NP-hard by Hyafil & Rivest (1976). Start from the instance
with all outcome bits 0 (infeasible for n ≥ 2, so its "optimal solution" is trivially known) and reach any target
instance by at most n·m single outcome flips. An optimal policy has at most n − 1 internal nodes, so each
intermediate optimal solution has polynomial size. A polynomial-time algorithm that, given an instance, an optimal
policy for it and one outcome flip, returned an optimal policy for the modified instance would therefore solve
the NP-hard problem in polynomial time. **Unless P = NP, no such algorithm exists.** This is a direct
instantiation of the generic reoptimization-hardness technique of Böckenhauer et al. (2008), not a new result.
Consequence: no "provably sufficient minimal region" can, in the worst case, be both certified and recomputed in
polynomial time from the old optimal policy.

**R7 — the bound that does survive non-monotone updates is known (Lemma D, verified).** For every update at w and
every (B, t) with w ∈ B: V(B∖{w}, t) ≤ |B|/(|B|−1) · V(B, t), so V_M′(B, t) ≥ ((|B|−1)/|B|) · V_M(B∖{w}, t), and
B∖{w} is unaffected by the update. Proof: restricting any policy for B to B∖{w} (skipping nodes that no longer
split) is feasible — subsets of terminal beliefs are terminal, safety only relaxes, earlier time stamps are
feasible by Lemma 6 — and no world's path cost increases. Checked on 587,659 state–hypothesis pairs. It is the
expected-cost analogue of MurTree's similarity bound: a known type of bound, not a contribution. Adding w admits no
such bound (R2).

## 4. Is a stronger certificate mathematically possible, and under what assumptions?

* **Complete, policy-local certificates: impossible** (R3).
* **Perturbation-bounded certificates for outcome flips: impossible** (R2).
* **A canonical minimal region: does not exist in general** (R5); minimum-size certificates are the only
  well-defined target, and deterministic algorithms cannot track them within a bounded factor in a query model (R5).
* **Worst-case polynomial exact reoptimization: impossible unless P = NP** (R6).
* **What remains possible** is only under extra assumptions: (a) monotone updates — already covered by Lemmas 2–3
  and shown to give no reliable runtime gain beyond Lemma 2 (Phases 128–129); (b) the full old value table plus
  change propagation, with work bounded by the touched set I(u) — known (Ramalingam–Reps, LPA*, ClosureRepair);
  (c) restricted test families (e.g. nested/laminar partitions) or randomized expected-work analyses — conceivable
  theoretical questions, with no evidence of tractability, no indication that clinical test batteries satisfy such
  restrictions, and a poor fit with ESWA.

## 5. Verdict

**No defensible ESWA-level research gap was found for this question.** Each precise version of "provably minimal
recomputation region after a non-monotone update" is either already answered by established theory (bounded
incremental computation and change propagation; AND/OR evaluation complexity; reoptimization hardness; similarity
bounds) or provably impossible in the generality required (R2–R6). Identifying affected states and replaying old
policies is established, as stated in the brief. The remaining open variants (special test structures, randomized
or succinct-change boundedness) are theoretical-computer-science questions with uncertain tractability and little
connection to ESWA's applied scope.

Recommendation: do not authorise experiments on this direction for ESWA. SCOPE-R's verified engine, its positive
and negative results, the counterexamples of Phases 113 and 130, and all proofs remain preserved in this repository.
