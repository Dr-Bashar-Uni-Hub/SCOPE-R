# Novelty matrix (sources opened and verified 7 Nov 2026)

| Element | Closest verified prior art | Overlap | Defensible claim |
|---|---|---|---|
| Terminal-action viability A(w), stop when ∩A ≠ ∅ | Javdani, Chen, Karbasi, Krause, Bagnell, Srinivasa, *Near Optimal Bayesian Active Learning for Decision Making*, AISTATS 2014 (PMLR 33:430–438) — Decision Region Determination | **Identical concept** | None; cite as DRD |
| Waiting safety (sensor allowed only if safe for all worlds in belief support) | Junges, Jansen, Seshia, *Enforcing Almost-Sure Reachability in POMDPs*, CAV 2021 (arXiv 2007.00085) — belief-support MDP, shielding | Same mechanism (support-based action masking) | None alone |
| Minimise expected cost s.t. reaching goal surely | Chatterjee, Chmelík, Gupta, Kanodia, *Artificial Intelligence* 234 (2016) 26–48 | General case of our objective | Ours is a finite-horizon deterministic-observation special case |
| Deadline / time-limited test strategies | Raghavan, Shakeri, Pattipati, IEEE SMC-A 29(1) 1999 (precedence/setup); time-constrained online TSG, *Sensors* 26 (2026) 6997 | High | None alone |
| Exact AND/OR search with admissible (Huffman/entropy) bounds | Pattipati & Alexandridis, IEEE SMC 20(4) 1990, 872–887 | **High** — the fresh BnB and Prop. H are this idea | Adaptation of the Huffman bound to overlapping decision regions (minor) |
| Exact DP for decision trees with constraints | van der Linden, de Weerdt, Demirović, STreeD, NeurIPS 2023; MurTree (JMLR 2022) | Medium (learning setting, not acquisition policies) | — |
| Dependency-graph change propagation (ClosureRepair) | Ramalingam & Reps, J. Algorithms 1996 (incremental grammar/hypergraph problem, heterogeneous modifications) | **High** | None |
| Reusing previous values as admissible heuristics after cost **increases** | Koenig & Likhachev, *Adaptive A\**, AAMAS 2005; Sun, Koenig, Yeoh, GAA\*, AAMAS 2008 (decreases); LPA\*/D\* Lite; Lim et al. L-GLS, IJRR 2024 | **High in principle** (OR-graphs, edge costs only) | Extension to AND/OR expected-cost search and to **constraint** updates |
| Policy reuse after POMDP model change | Kurniawati & Patrikalakis PBPT (2013); Kurniawati & Yadav ABT (2016); Novitsky et al. IR-PFT (2024/25) | Medium | Those are approximate/sampling-based without certified optimality; MBR is exact |
| Active feature acquisition as POMDP | Aronsson, Rahbar, Haghir Chehreghani, IJCAI 2026 survey (doi 10.24963/ijcai.2026/860) | Context | — |

## Candidate contribution (narrow, falsifiable)

**C1. Update-monotonicity taxonomy for exact constrained information acquisition.** Each of five
model-update kinds (cost, delay, sensor outcome, waiting safety, decision-region viability) is
classified as tightening / loosening / non-monotone / world-local, and for each class we prove which
parts of the previous exact solution remain *exact* (Lemmas 1, 3), *lower bounds* (Lemmas 2, 4),
or *upper bounds* (Lemma 5), plus temporal dominance across deadline levels (Lemma 6).

**C2. MBR**, an exact branch-and-bound replanner that consumes those certificates, with a proof of
exactness and state-level empirical verification.

**C3. Evidence**: 1.9–2.8× median speedup over the same search run fresh (CIs exclude 1 at all six
sizes), 2.9–3.7× fewer expansions, robust to a stronger heuristic; 8–138× over exhaustive DP,
ClosureRepair, Phase 115 and the matched Phase 121 POMDP planner.

## What is NOT claimed
Not new: the problem class, Bellman recursion, bounded AND/OR search, Huffman bounds, change
propagation, the single-use cost-gap bound (Phase 117), or the general principle that old values are
admissible after monotone cost increases (Adaptive A*). C1 is an extension of that principle to a
setting (AND/OR expected cost, constraint updates, decision regions, deadlines) where we found no
published treatment — after two targeted searches; an exhaustive search (Scopus/WoS, incl.
"incremental AO*", "LAO* replanning", "dynamic test sequencing") is still required before submission.

## Phase 127 corrections
- **Minimax LPA*** (Likhachev & Koenig, NIPS 2002, pp. 1595–1602) is an incremental heuristic search algorithm for nondeterministic (minimax, AND/OR) domains. The earlier statement that the AND/OR extension of incremental heuristic search "was not developed" is withdrawn. Distinction: Minimax LPA* repairs worst-case values by propagating edge-cost changes; SCOPE-R targets expected-cost optimal policies, and its proposed element is a retained-exactness certificate for structural/constraint tightening used within exact bounded re-search.
- Final narrowed claim: see THEORY.md §5 ("proposed" row only).

## Phase 128 — final, evidence-based novelty statement
The algorithmic novelty is modest. The structural certificate (Lemma 3, cases 2–4) is correct, not found stated in prior work by the documented screening, but elementary: it follows immediately from Bellman optimality and relaxation monotonicity, which are established (Adaptive A*, Koenig & Likhachev 2006; MurTree; DynamicHS), and incremental AND/OR search itself is established (Minimax LPA*). In a controlled ablation it reduced node expansions but did not deliver a reliable runtime benefit (1.37–1.46× only for delay increases on synthetic instances; 0.37–0.92× elsewhere). MBR's speed-ups come from established components. The defensible contribution is an exact, verified what-if replanning engine for constrained diagnostic test selection, evidence on which components matter (including this negative result), and the case-study findings.

## Phase 129 — lazy certificate
Lazy, demand-driven validation is established (Adapton, Hammer et al., PLDI 2014; LPA*/D* Lite; DynamicHS's
lazy update policy; lazy edge evaluation). The lazy structural certificate is that pattern applied to Lemma 3.
It beats the no-certificate baseline on synthetic instances but not on the real case study (0.90–0.95×), so
it does not provide a defensible algorithmic contribution. See phase129/README.md.

## Phase 130 — minimal recomputation regions after non-monotone updates
No defensible gap: answered by established theory or provably impossible in the required generality (docs/PHASE130_FEASIBILITY.md).
