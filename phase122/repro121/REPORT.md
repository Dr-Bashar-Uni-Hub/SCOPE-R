# SCOPE-R Phase 121 — Matched-Representation Exact Replanning Audit

## Objective
Test whether SCOPE-R's cross-update repair, rather than a favorable representation or a slow posterior-vector comparator, provides a measurable advantage over independently implemented finite-horizon exact POMDP replanning.

## Experiment
- 24 deterministic random sequences; 384 sequential updates; 8, 10, 12 worlds; 10, 12, 14 binary sensors respectively.
- 12 balanced mixed sequences and 12 cost-dominated sequences, each with 16 updates.
- Synthetic robotic inspection scenario generator reused from Phase 120, with deadline, waiting safety and terminal action viability.
- Four solvers: independently coded matched-bitmask exact Bellman/POMDP (`matched_pomdp`), independently coded optimized fresh DP (`fresh`), SCOPE-R Phase 115 lazy eligibility repair, and ClosureRepair.
- Update categories: cost, delay, outcome, waiting safety, terminal action viability. Solver invocation order randomized per update. All amortized timings include initial construction and all updates.
- `matched_pomdp` deliberately discards its local cache after every update; this is a fresh exact POMDP baseline, **not** an optimized incremental POMDP solver.

## Results
- 384/384 updates exact-match across all four solvers; this is empirical testing, not proof of arbitrary-update correctness.
- Median sequence-level amortized speedups (matched POMDP time / solver time):
  - Balanced mixed: lazy 0.9594x, ClosureRepair 0.9537x.
  - Cost-dominated: lazy 1.4050x, ClosureRepair 1.2946x.
- Median sequence-level lazy versus ClosureRepair: balanced 1.0197x (7/12 wins), cost-dominated 1.0662x (9/12 wins).
- Median fresh/matched POMDP time ratio: 1.6330x, demonstrating the independent POMDP implementation is *faster* than the separate optimized fresh implementation on these instances. Results depend on code and workload; not a comparison against external POMDP packages.

## Scientific interpretation
- Representation matching removes the previous 5.7–6.6x comparison as evidence of a specialized algorithmic speedup.
- No overall balanced-mixed speed advantage is established. A cost-dominated advantage is observed against a strong independent *fresh* baseline.
- The observed incremental gain is modest compared with ClosureRepair. No novelty claim follows from the benchmark alone.
- The exact finite-horizon Bellman recurrence is equivalent to a constrained belief-state POMDP for the stated deterministic binary observation model. This is not a new POMDP solution principle.

## Limitations and next evidence needed
1. Compare against established incremental MDP/POMDP methods, not only a fresh exact POMDP solver; a literature and software baseline audit remains necessary.
2. Run substantially more sequences, larger feasible models, different priors and stochastic sensors; report paired uncertainty intervals and hardware details.
3. Use an externally sourced robotics or inspection dataset with measured observation costs/delays and calibrated safety constraints.
4. Formally prove the specific incremental update procedures correct for all update types, including newly admissible sensor alternatives and transitions between finite and infinite values.
5. Treat ESWA originality as **unproven**. A constrained-POMDP formulation, memoization, change propagation, and cost-gap stability conditions have precedents.

## Reproduction
`python benchmark.py` from this directory, with the bundled `baseline/` source files in their relative locations if using the portable package. The original script uses absolute historical paths for imports; `benchmark_portable.py` in the ZIP uses the bundled relative paths.
