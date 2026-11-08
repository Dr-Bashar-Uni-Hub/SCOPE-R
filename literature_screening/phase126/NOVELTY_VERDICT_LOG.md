# Phase 126 — Targeted search + full-text novelty assessment (8 Nov 2026)
Inputs: Q1 (1 rec), Q2 (1), Q3 (95), Q4 (100), Q5 (1); forward citations: Adaptive A* (2), DynamicHS 2023 (7), MurTree 2022 (96).
Total 303 records; all titles read; 17 abstracts read; 3 full texts read (Rodler 2023; Liu & Shachter 2015; Nielsen & Jensen 2003).
Noise: Q3 ~90% clinical cost-effectiveness; Q4 ~90% generic troubleshooting/industry.
Caveat: Scopus indexes few AAMAS/ICAPS/SoCS papers (Adaptive A*: 2 citing records), so forward-citation coverage of the incremental-search line is incomplete.

New relevant records (beyond Phase 125):
- Koenig & Likhachev et al., "A new principle for incremental heuristic search: Theoretical results", ICAPS 2006 — heuristic updating across a series of similar searches (OR-graph A*). Precedent for Lemma 2's reuse principle.
- Kurniawati & Yadav 2016 (ABT), doi 10.1007/978-3-319-28872-7_35 — approximate online POMDP under model change (already known).
- Kaminski et al. 2018, CEJOR doi 10.1007/s10100-017-0479-6 — sensitivity of optimal decision-tree strategies to probabilities.
- Interval-valued influence diagrams, IJAR 2017 doi 10.1016/j.ijar.2016.05.004 — sensitivity to parameter perturbations.
- Branches (AO* for optimal sparse DTs), PMLR 2025 — static.
- DYNFRS (machine unlearning in random forests), ICLR 2025 — data-update reuse, approximate ensembles, different problem.
No record found that certifies retained exactness of an expected-cost-optimal policy after structural/constraint updates.

Full-text findings:
- Nielsen & Jensen 2003 (IEEE SMC-A 33(1):223-234, doi 10.1109/TSMCA.2003.811116): exact admissible domains for utility parameters (linear), probability parameters (quotients of linear functions), n-way safe balls; reduced strategies ignore zero-probability configurations. Explicit restriction: probability parameters must stay in (0,1); "Theorem 1 does not hold if probability parameters are allowed to attain extreme values". Test costs are utility parameters (separable value model), so cost-update certification is fully covered -> SCOPE-R Lemma 3 (cost case) and Lemma 4 are special cases of established results.
- Bhattacharjya & Shachter 2008: same scope via decision circuits; inactive max nodes = untouched sub-strategies (tight/weak interval bounds).
- Liu & Shachter 2015 (UAI): exact test sequencing via decision circuits with recursive coalescence (state = set of observed results; same as SCOPE-R belief-set memo); lower bound Omega(n(c+1)^(n-1)) for algorithms examining the entire policy space (bounded search escapes it by pruning). Static; mentions sensitivity on probabilities/costs; no structural updates, deadlines or safety.
- Rodler 2023 (Inf. Sci. 627:251-279, doi 10.1016/j.ins.2022.08.029): stateful reuse of the HS-tree across measurement additions; Property 1 (diagnoses only grow, conflicts only shrink) is a monotone-update retention argument; consistent minimal diagnoses retained without reasoning; Theorem 1 soundness/completeness/best-first. Objective = diagnosis enumeration, measurement choice myopic; one update type (knowledge addition).

Classification:
ESTABLISHED: exact test sequencing (DP/AO*/decision circuits); belief-set coalescence; bounded search; Huffman bounds; parametric sensitivity incl. costs (admissible domains, safe balls, inactive nodes); monotone-update reuse principle (Adaptive A*, ICAPS 2006 principle, MurTree, DynamicHS Property 1); subproblem locality (folklore DP).
POTENTIALLY ORIGINAL (no precedent found): retained-exactness certificate for expected-cost-optimal sub-policies under STRUCTURAL tightening — delay increase under a hard deadline, removal of support-based waiting safety, shrinking decision regions (zero/one-probability structure changes excluded by parametric sensitivity frameworks); combined taxonomy across five update kinds with exact bounded re-search; real-data deadline/safety case study.
UNRESOLVED: forward citations of incremental-search papers outside Scopus; MDP/SSP exact incremental replanning under model change (Q2 returned only ABT).
