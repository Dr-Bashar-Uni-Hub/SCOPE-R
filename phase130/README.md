# Phase 130 — feasibility investigation (no method implemented)
`counterexamples.py` verifies, by brute force against the exhaustive solver: CE1 unbounded value change after one
outcome flip (factor M, finite→∞); CE2 insufficiency of old-policy-local information; CE3 touched region 2^(n−1)
vs value-affected 0–6 states with unchanged root; CE4 two disjoint minimal certificates with the real Proposition H
bound (first failed attempt documented); Lemma D deletion/similarity bound on 587,659 pairs.
Run: `python counterexamples.py`. Report: `../docs/PHASE130_FEASIBILITY.md`.
