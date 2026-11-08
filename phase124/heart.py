"""Phase 124 real-data case study: Cleveland heart-disease diagnosis.

Data   : UCI processed.cleveland.data (303 rows; 6 with missing values removed -> 297).
Costs  : Turney (1995, JAIR 2:369-409), Table 17, full (first-in-group) cost, i.e. the
         no-group-discount setting Turney used in his Section 4.2.2.
Delays : Sheng & Ling (ICML 2006), Table 1, hours. Converted to integer half-hour units,
         minimum 1 unit (assumption: every test occupies at least one scheduling slot).
Binarisation: one clinically standard cut-point per test (assumption, documented below).
Decision regions (assumption): num=0 -> {discharge, monitor}; num=1 -> {monitor, treat};
         num>=2 -> {treat}.  Alternative 'binary' regions: num=0 -> {discharge}, num>0 -> {treat}.
Waiting safety (assumption): exercise-based tests are not admissible while the belief still
         contains a patient with num >= SAFE_NUM (exercise testing contraindicated in high-risk CAD).
"""
import math, os, random
H = os.path.dirname(os.path.abspath(__file__))
COLS = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang',
        'oldpeak', 'slope', 'ca', 'thal', 'num']
COST = {'age': 1.00, 'sex': 1.00, 'cp': 1.00, 'trestbps': 1.00, 'chol': 7.27, 'fbs': 5.20,
        'restecg': 15.50, 'thalach': 102.90, 'exang': 87.30, 'oldpeak': 87.30, 'slope': 87.30,
        'ca': 100.90, 'thal': 102.90}                    # Turney 1995 Table 17 (CAD $)
DELAY_H = {'age': 0.001, 'sex': 0.001, 'cp': 0.001, 'trestbps': 0.01, 'chol': 4, 'fbs': 4,
           'restecg': 0.5, 'thalach': 1, 'exang': 1, 'oldpeak': 1, 'slope': 1, 'ca': 1,
           'thal': 1}                                     # Sheng & Ling 2006 Table 1 (hours)
EXERCISE = {'thalach', 'exang', 'oldpeak', 'slope', 'thal'}  # stress-test based measurements
TESTS = COLS[:-1]


def cut(r, t):
    """Clinically standard binary cut-points (assumption; one per test)."""
    if t == 'age': return int(r['age'] >= 55)
    if t == 'sex': return int(r['sex'] == 1)
    if t == 'cp': return int(r['cp'] == 4)                 # asymptomatic chest pain
    if t == 'trestbps': return int(r['trestbps'] >= 140)   # hypertension threshold
    if t == 'chol': return int(r['chol'] >= 240)           # 'high' total cholesterol
    if t == 'fbs': return int(r['fbs'] == 1)               # fasting glucose > 120 (given)
    if t == 'restecg': return int(r['restecg'] != 0)       # abnormal resting ECG
    if t == 'thalach': return int(r['thalach'] < 0.85 * (220 - r['age']))  # <85% age-predicted max HR
    if t == 'exang': return int(r['exang'] == 1)
    if t == 'oldpeak': return int(r['oldpeak'] >= 1.0)     # >=1 mm ST depression
    if t == 'slope': return int(r['slope'] != 1)           # flat or downsloping
    if t == 'ca': return int(r['ca'] >= 1)
    if t == 'thal': return int(r['thal'] != 3)             # fixed or reversible defect
    raise KeyError(t)


def load():
    rows = []
    for line in open(os.path.join(H, 'data', 'processed.cleveland.data')):
        v = line.strip().split(',')
        if len(v) != 14 or '?' in v:
            continue
        rows.append({c: float(x) for c, x in zip(COLS, v)})
    return rows


REGIONS = {
    'overlap': lambda num: 0b011 if num == 0 else (0b110 if num == 1 else 0b100),
    'binary': lambda num: 0b001 if num == 0 else 0b100,
}


class HeartInstance:
    """SCOPE-R model interface (n, m, deadline, actions, outcomes, delay, wait, cost)."""

    def __init__(self, patients, deadline, regions='overlap', safe_num=3, unit_h=0.5):
        self.patients = patients
        self.n, self.m, self.deadline = len(patients), len(TESTS), deadline
        self.tests = list(TESTS)
        self.actions = [REGIONS[regions](int(p['num'])) for p in patients]
        self.outcomes = [[cut(p, t) for p in patients] for t in TESTS]
        self.delay = [max(1, math.ceil(DELAY_H[t] / unit_h - 1e-9)) for t in TESTS]
        self.wait = [[not (t in EXERCISE and p['num'] >= safe_num) for p in patients] for t in TESTS]
        self.cost = [COST[t] for t in TESTS]


def consistent(rows, regions='overlap'):
    """Drop patients whose test profile coincides with another patient's profile while their
    viable-action sets are disjoint (irreducible ambiguity: no test sequence can ever separate
    them). Returns kept rows and the number dropped."""
    f = REGIONS[regions]
    prof = {}
    for r in rows:
        prof.setdefault(tuple(cut(r, t) for t in TESTS), []).append(r)
    keep, drop = [], 0
    for k, grp in prof.items():
        inter = 0b111
        for r in grp:
            inter &= f(int(r['num']))
        if inter:
            keep += grp
        else:
            # keep the patients sharing the action viable for the most group members
            # (so the kept group has a common viable action); drop the rest (documented)
            best_a = max((1 << a for a in range(3)),
                         key=lambda m: sum(bool(f(int(r['num'])) & m) for r in grp))
            for r in grp:
                if f(int(r['num'])) & best_a:
                    keep.append(r)
                else:
                    drop += 1
    return keep, drop
