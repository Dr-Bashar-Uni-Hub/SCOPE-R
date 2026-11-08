# Proposition H — formal statement and proof (overlapping acceptable-action sets)

Status: **proved** (hand proof, below) and **empirically checked**: 488,362 states including every subset of
hypotheses with heavily overlapping action sets (phase128/propH_audit.py), 78,795 reachable states
(phase123/test_heuristic.py); implementation of L(B) equals the defining minimum on 4,000 weight vectors
(phase129/test_huffman_definition.py).

## 1. Setting

* W finite set of hypotheses; 𝒜 finite set of terminal actions; for each w ∈ W a nonempty set A(w) ⊆ 𝒜.
* Tests s ∈ S: outcome sets pos_s ⊆ W, integer delays τ_s ≥ 1, safe sets Safe_s ⊆ W, costs c_s ≥ 0; deadline D.
* State (B, t), ∅ ≠ B ⊆ W, t ∈ {0, …, D}; uniform distribution on B.
* B is **terminal** iff ⋂_{w∈B} A(w) ≠ ∅.
* s is **admissible** at (B, t) iff t + τ_s ≤ D, B ⊆ Safe_s, and both B ∩ pos_s and B ∖ pos_s are nonempty.
* A **policy** π from (B, t) is a finite rooted binary tree. Each internal node ν carries a state (B_ν, t_ν) and
  a test s_ν admissible at (B_ν, t_ν); its two children carry (B_ν ∩ pos_{s_ν}, t_ν + τ_{s_ν}) and
  (B_ν ∖ pos_{s_ν}, t_ν + τ_{s_ν}). The root carries (B, t). Every leaf carries a terminal belief.
  Each w ∈ B reaches exactly one leaf ℓ(w); its **depth** d(w) is the number of internal nodes on that path.
* Cost: J(π) = Σ_ν (|B_ν| / |B|) · c_{s_ν} = (1/|B|) Σ_{w∈B} Σ_{ν on the path of w} c_{s_ν}.
* V(B, t) = min_π J(π) over policies from (B, t) (+∞ if none exists); this equals the Bellman value (Theorem 0).

## 2. Definitions used by the bound

* **Single-action classes:** for k ∈ 𝒜, S_k(B) = { w ∈ B : A(w) = {k} }.
* **Excluded hypotheses:** X(B) = { w ∈ B : |A(w)| ≥ 2 }. B is the disjoint union of X(B) and the S_k(B).
* K(B) = { k : S_k(B) ≠ ∅ }, n_k = |S_k(B)|.
* **Kraft-constrained depth cost:** L(B) = min { Σ_{k∈K(B)} n_k ℓ_k : ℓ_k ∈ ℕ, Σ_{k∈K(B)} 2^{−ℓ_k} ≤ 1 },
  with L(B) = 0 if |K(B)| ≤ 1 (take ℓ_k = 0).
* **Cheapest schedulable test:** c_min(t) = min { c_s : t + τ_s ≤ D } (= +∞ if the set is empty).
* **Bound:** h(B, t) = 0 if B is terminal; otherwise h(B, t) = c_min(t) · max(1, L(B)/|B|), with the conventions
  +∞ · x = +∞ for x > 0 and h = 0 whenever c_min(t) = 0.

## 3. Proposition H

For every state (B, t): h(B, t) ≤ V(B, t).

## 4. Proof

If B is terminal, h = 0 ≤ V. Assume B nonterminal. If V(B, t) = +∞ there is nothing to prove; if
c_min(t) = 0 then h = 0. If c_min(t) = +∞, no test is schedulable from t, so no policy from (B, t) has an
internal node; since B is nonterminal no policy exists and V = +∞ ≥ h. Assume now V < ∞, 0 < c_min(t) < ∞, and
fix any policy π from (B, t).

**Step 1 (every query costs at least c_min(t)).** Times are nondecreasing along paths, so every internal node ν
has t_ν ≥ t, and admissibility gives t_ν + τ_{s_ν} ≤ D, hence t + τ_{s_ν} ≤ D and c_{s_ν} ≥ c_min(t). Therefore
J(π) ≥ c_min(t) · (1/|B|) Σ_{w∈B} d(w).

**Step 2 (at least one query).** B is nonterminal, so the root is an internal node and d(w) ≥ 1 for every w ∈ B:
(1/|B|) Σ_w d(w) ≥ 1.

**Step 3 (Lemma A: a terminal leaf meets at most one single-action class).** Suppose a leaf belief B_ℓ contains
w ∈ S_j and w′ ∈ S_k with j ≠ k. Then ⋂_{u∈B_ℓ} A(u) ⊆ A(w) ∩ A(w′) = {j} ∩ {k} = ∅, so B_ℓ is not terminal —
a contradiction. Hypotheses in X(B) are unconstrained by this lemma; the proof never needs to locate them.

**Step 4 (Kraft argument on the single-action classes).** For k ∈ K(B) choose a leaf ℓ_k* of minimum depth
δ_k among the leaves containing some element of S_k(B). By Lemma A the leaves ℓ_k* (k ∈ K(B)) are pairwise
distinct. In any binary tree the leaves satisfy Σ_{leaves λ} 2^{−depth(λ)} ≤ 1 (Kraft's inequality), so the
distinct subset satisfies Σ_{k∈K(B)} 2^{−δ_k} ≤ 1; hence (δ_k) is feasible in the definition of L(B). Each
w ∈ S_k(B) reaches a leaf containing an element of S_k(B), so d(w) ≥ δ_k. Since d(w) ≥ 0 for w ∈ X(B),
Σ_{w∈B} d(w) ≥ Σ_{k∈K(B)} Σ_{w∈S_k(B)} d(w) ≥ Σ_{k∈K(B)} n_k δ_k ≥ L(B).
If |K(B)| ≤ 1 the inequality Σ_w d(w) ≥ 0 = L(B) is trivial.

**Step 5.** Steps 1, 2 and 4 give J(π) ≥ c_min(t) · max(1, L(B)/|B|) = h(B, t). Minimising over π gives V(B, t) ≥ h(B, t). ∎

## 5. Remarks

1. **Treatment of overlapping sets.** Hypotheses with |A(w)| ≥ 2 form X(B) and are excluded from the classes;
   they contribute only through the |B| in the normaliser and through Step 2. Overlap therefore cannot make the
   bound invalid, only weaker. If K(B) = ∅ or |K(B)| = 1 (e.g. every hypothesis has an overlapping set), the
   bound reduces to c_min(t).
2. **Why the shallowest leaf.** A class may be split over several leaves; taking the shallowest one gives a
   valid per-class depth δ_k while keeping the chosen leaves distinct.
3. **Computing L(B).** By the Kraft–McMillan theorem, integer vectors with Σ 2^{−ℓ_k} ≤ 1 are exactly the
   codeword-length vectors of binary prefix codes, and Huffman's algorithm minimises Σ n_k ℓ_k over prefix codes;
   hence L(B) is the Huffman cost, computed in phase123/mbr.py (CompiledH.h) by repeated merging of the two
   smallest weights. Verified against the defining minimum (phase129/test_huffman_definition.py).
4. **Implementation correspondence.** CompiledH.h returns 0 for terminal B, c_min(t) when c_min(t) ∈ {0, +∞}
   or |K(B)| < 2, and otherwise max(c, c·L/|B|) = c·max(1, L/|B|).
5. **Tightness.** h = V occurs (maximum observed ratio 1.0 in phase128/propH_audit.py).
6. **Nonuniform prior.** Replace |B_ν|/|B| by prior mass and n_k by the mass of S_k(B); the proof is unchanged.
7. **Attribution.** The Huffman/entropy idea is due to Pattipati & Alexandridis (1990) for test sequencing with
   single faults; the contribution here is only the adaptation to overlapping decision regions (Lemma A and the
   exclusion of X(B)).
