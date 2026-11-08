# Changelog

## 1.5.0-IJAR (8 Nov 2026) — figures
- New `figures/`: deterministic scripts for Figures 1–5 (model example solved by an independent exhaustive solver;
  update-step diagram; synthetic scaling; certificate isolation; case-study cost vs deadline). The script asserts
  agreement with Table 5 and with the Figure 1 policy values. Replaces ChatGPT-generated images, which Elsevier does
  not permit and whose Figure 3 contradicted Tables 2, 4 and 6.

## 1.4.0-IJAR (8 Nov 2026) — submission version for the International Journal of Approximate Reasoning
- Manuscript reframed for IJAR (certificates and limits after model updates); Section 5 from Phase 130; Table 4 from
  Phase 129; Appendix A (formal Proposition H). README and reproducibility map updated to the IJAR numbering.
- Corrected the Phase 129 sequence-level slowdown to 2.5–5.4% (time ratio 0.949–0.976).

## 1.3.0-research (Phase 130, 8 Nov 2026) — feasibility of minimal recomputation regions (no implementation)
- Literature map (Ramalingam–Reps boundedness, Minimax LPA*, Adapton, prioritized sweeping, AO* / Mahanti–Bagchi,
  Saks–Wigderson AND/OR evaluation, reoptimization hardness, MurTree similarity bounds).
- Verified counterexamples CE1–CE4 and Lemma D (phase130/counterexamples.py); reoptimization-hardness corollary.
- Verdict: no defensible ESWA-level gap for this question (docs/PHASE130_FEASIBILITY.md). Manuscript unchanged.

## 1.2.0-research (Phase 129, 8 Nov 2026) — lazy structural certificate
- New `phase129/`: lazy (on-demand) evaluation of the structural certificate, four-variant paired benchmark
  (no-cert / eager / lazy / fresh) on 5 datasets × 3 update kinds (630 trials), sequence-level real-data check,
  state-level correctness tests (11,550 updates), Huffman-definition check.
- Result: pre-registered criterion NOT met — lazy beats no-cert on synthetic instances (7/9 settings) but is
  slower on all 6 real-data settings (0.90–0.95×) and on all 7 Table-6 streams (2.5–5.4% slower). The certificate can
  remove at most 0.4–4.4% of no-cert expansions on the real instance.
- New `docs/PROPOSITION_H.md`: formal definition and proof for overlapping acceptable-action sets.
- Manuscript intentionally not revised in this phase.

## 1.1.0-submission (Phase 128, 8 Nov 2026) — final audit
- Proposition H re-audited under overlapping action sets: admissible (488,362 states, 0 violations); proof clarified.
- Exactness theorem strengthened (failed replay, +∞ budget, infeasible updates); 40,000 edge-case updates exact; safety net never fired.
- New controlled isolation of the structural certificate: correct, reduces expansions, net runtime benefit only for synthetic delay increases. Novelty claim downgraded accordingly.
- Reliability: independent recomputation of all medians/CIs; deterministic expansion counts reproduced; ±10% run-to-run timing noise documented.
- Manuscript data-availability text no longer claims an existing v1.0.0 release (repository was empty at audit time).
- AI disclosure made consistent between Section 6.1 and the declaration.

## 1.0.0-submission (Phase 127, 8 Nov 2026)
- Assembled repository from the Phase 122–126 working directories (directory names kept so relative imports work unchanged).
- Moved THEORY.md, NOVELTY.md, RESULTS_AND_DECISION.md from phase123/ to docs/.
- Fixed `phase123/test_lemmas.py`: removed a dead line that looked for a counterexample file outside the repository (it could crash when that sandbox path existed; the actual regression uses the bundled `phase123/phase113_counterexample.json`). Results unchanged.
- Removed a 14-byte failed-download stub (`phase124/data/cleve.tsv.gz`).
- Added README, LICENSE (MIT, holder to be confirmed), CITATION.cff, requirements.txt, scripts/, and docs/ (reproducibility map, reference verification, clinical checklist, AI declaration draft).
- Documentation corrections: Minimax LPA* (Likhachev & Koenig, NIPS 2002) added as prior incremental AND/OR (minimax) search; UCI `num` values 1–4 are not documented as vessel counts — region assignment restated as an unvalidated ordinal-severity assumption; UCI dataset year corrected to 1989.

## Phases 122–126 (research record)
- 122: independent audit of frozen Phase 121; exact-rational oracle; fuzzing of frozen solvers.
- 123: MBR method, proofs, synthetic benchmarks (GC-controlled), ablations, heuristic control.
- 124: Cleveland heart-disease case study with published costs/delays.
- 125–126: novelty screening of Scopus, Web of Science and Google Scholar exports supplied by the authors.
