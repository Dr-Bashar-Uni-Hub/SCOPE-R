# Clinical review checklist (independent clinician validation REQUIRED — not yet performed)

Status: **No clinical validation has been performed.** All items below are modelling assumptions made by the
authors for a computational case study. The case study is not clinical decision support.

Reviewer: ______________________  Specialty / role: ______________________  Date: ____________

For each item: mark **Accept / Modify (state value) / Reject**, and add a reference where possible.

## A. Data interpretation
- [ ] A1. Diagnosis variable `num`: UCI documents 0 = <50% diameter narrowing and >50% narrowing as disease; values 1–4 are **not** documented as vessel counts or severity grades. We treat `num` as an ordinal severity scale. Is this acceptable? If not, how should 1–4 be interpreted?
- [ ] A2. Population: 297 complete Cleveland Clinic records (1980s referral population, ~46% disease prevalence). Acceptable as an illustrative population only?
- [ ] A3. Exclusion of 6 records with missing `ca`/`thal` and 1 irreducibly ambiguous record (overlapping regions).

## B. Test cut-points (one binary threshold per test; file `phase124/heart.py`, function `cut`)
- [ ] B1. Age ≥ 55 years
- [ ] B2. Sex: male = positive
- [ ] B3. Chest pain: asymptomatic (type 4) = positive
- [ ] B4. Resting systolic BP ≥ 140 mmHg
- [ ] B5. Serum cholesterol ≥ 240 mg/dl
- [ ] B6. Fasting blood sugar > 120 mg/dl (as coded in data)
- [ ] B7. Resting ECG abnormal (any non-normal code)
- [ ] B8. Maximum heart rate < 85% of age-predicted maximum (220 − age)
- [ ] B9. Exercise-induced angina = positive
- [ ] B10. Exercise ST depression ≥ 1.0 mm
- [ ] B11. ST slope flat or downsloping = positive
- [ ] B12. ≥ 1 major vessel coloured by fluoroscopy
- [ ] B13. Thallium scan: fixed or reversible defect = positive
- [ ] B14. Is a single binary cut per test acceptable for this illustration, given information loss?

## C. Decision regions (acceptable final actions per patient)
- [ ] C1. `num = 0` → {discharge, monitor}
- [ ] C2. `num = 1` → {monitor, treat}  (depends on A1)
- [ ] C3. `num ≥ 2` → {treat}
- [ ] C4. Are "discharge / monitor / treat" meaningful action categories? Should invasive angiography or referral be an explicit action?
- [ ] C5. Binary alternative (`num = 0` → discharge; `num > 0` → treat) as sensitivity scenario.

## D. Waiting-safety rule
- [ ] D1. Stress-test-based measurements (max heart rate, exercise angina, ST depression, ST slope, thallium) are inadmissible while any still-possible patient has `num ≥ 3` (also tested: ≥ 2, ≥ 4). Clinically meaningful? (In the model this makes complete diagnosis infeasible.)
- [ ] D2. Is fluoroscopy (`ca`) correctly treated as not exercise-dependent?
- [ ] D3. Should safety be probabilistic (risk threshold) rather than "safe for every still-possible patient"?

## E. Costs, delays and deadlines
- [ ] E1. Test costs from Turney (1995): Ontario fee schedule (1992, CAD), full first-in-group cost (no shared-blood-draw discount). Acceptable as relative costs?
- [ ] E2. Delays from Sheng & Ling (2006), hours; discretised to 30-min slots with a minimum of one slot; tests performed one at a time (no batching).
- [ ] E3. Deadlines of 4, 6, 8, 10 h: plausible decision horizons for the clinical setting?

## F. Overall
- [ ] F1. Wording of clinical limitations in the manuscript (Section 7) is adequate.
- [ ] F2. Any statement in the manuscript that could be read as a clinical recommendation must be removed or rephrased.
