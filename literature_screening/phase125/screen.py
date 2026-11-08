"""Stage-1 screening: transparent concept-group scoring over title+abstract+keywords.
G1 problem class, G2 replanning/reuse, G3 exact/bounded optimisation. Inclusion for Stage 2:
G1>=1 and (G2>=1 or G3>=1) with score>=4, or any 'strong' phrase."""
import pandas as pd, re
u = pd.read_csv('merged_dedup.csv').fillna('')
G1 = ['test sequencing', 'test sequence', 'sequential diagnosis', 'sequential fault diagnosis', 'fault diagnosis strateg',
      'diagnostic strateg', 'test strateg', 'troubleshoot', 'decision tree', 'and/or graph', 'and-or graph', 'and/or search',
      'ao*', 'ao star', 'pomdp', 'partially observable', 'active learning', 'decision region', 'feature acquisition',
      'test selection', 'optimal testing', 'sequential testing', 'adaptive sensing', 'information acquisition',
      'value of information', 'identification problem', 'binary identification']
G2 = ['incremental', 'replan', 're-plan', 'warm start', 'warm-start', 'reuse', 're-use', 'model change', 'changing model',
      'lifelong', 'adaptive a*', 'reoptimi', 're-optimi', 'sensitivity analysis', 'dynamic update', 'update the strategy',
      'cost change', 'changes in cost', 'online update', 'dynamic environment']
G3 = ['optimal', 'exact', 'branch and bound', 'branch-and-bound', 'dynamic programming', 'lower bound', 'admissible',
      'heuristic search', 'bound']
STRONG = ['incremental ao', 'adaptive a*', 'test sequencing', 'decision region determination', 'and/or graph',
          'optimal decision tree', 'sequential fault diagnosis', 'sequential diagnosis']
def cnt(text, terms): return sum(1 for t in terms if t in text)
rows = []
for _, r in u.iterrows():
    tx = (r.title + ' ' + r.abstract + ' ' + r.keywords).lower()
    g1, g2, g3, st = cnt(tx, G1), cnt(tx, G2), cnt(tx, G3), cnt(tx, STRONG)
    tt = r.title.lower()
    score = 2 * g1 + 2 * g2 + g3 + 3 * st + 2 * (cnt(tt, G1) + cnt(tt, G2))
    rows.append((g1, g2, g3, st, score))
u[['g1', 'g2', 'g3', 'strong', 'score']] = pd.DataFrame(rows, index=u.index)
u['stage2'] = ((u.g1 >= 1) & ((u.g2 >= 1) | (u.g3 >= 1)) & (u.score >= 4)) | (u.strong >= 1)
print('Stage-1 included for abstract reading:', u.stage2.sum(), 'of', len(u))
print('  G1 hits', (u.g1 >= 1).sum(), '| G1&G2', ((u.g1 >= 1) & (u.g2 >= 1)).sum(), '| strong phrase', (u.strong >= 1).sum())
u.sort_values('score', ascending=False).to_csv('screened.csv', index=False)
s = u[u.stage2].sort_values('score', ascending=False)
s[['score', 'g1', 'g2', 'g3', 'strong', 'year', 'title', 'venue', 'doi', 'sources']].to_csv('stage2_candidates.csv', index=False)
for _, r in s.head(70).iterrows(): print(f"{r.score:3d} {int(r.year) if r.year else ''} {r.title[:105]}")
