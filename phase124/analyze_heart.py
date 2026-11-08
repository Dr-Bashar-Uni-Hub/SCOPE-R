"""Merge chunks and report per-stream speedups of MBR (median, bootstrap 95% CI, wins) + expansions."""
import csv, glob, sys, random, statistics as st, os
def boot(x, B=10000, seed=1):
    r = random.Random(seed); m = sorted(st.median(r.choice(x) for _ in x) for _ in range(B)); return m[int(.025*B)], m[int(.975*B)-1]
for tag in sys.argv[1:]:
    d = f'results/{tag}'
    for fn in ('sequences.csv', 'updates.csv'):
        rows = []
        for f in sorted(glob.glob(f'{d}/chunk_*/{fn}')): rows += list(csv.DictReader(open(f)))
        if rows:
            rows.sort(key=lambda r: (int(r['stream']), int(r.get('step', 0))))
            with open(f'{d}/{fn}', 'w', newline='') as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    S = list(csv.DictReader(open(f'{d}/sequences.csv'))); U = list(csv.DictReader(open(f'{d}/updates.csv')))
    names = [k[:-9] for k in S[0] if k.endswith('_total_ns')]
    print(f'{tag}: streams {len(S)}, exact checks {len(U)}')
    for nm in names:
        if nm == 'mbr': continue
        x = [int(s[nm+'_total_ns'])/int(s['mbr_total_ns']) for s in S]; lo, hi = boot(x)
        print(f'  MBR vs {nm:8s} median {st.median(x):6.2f}x  CI [{lo:.2f}, {hi:.2f}]  wins {sum(v>1 for v in x)}/{len(x)}')
    tb = sum(int(u['bnb_expanded']) for u in U); tm = sum(int(u['mbr_expanded']) for u in U)
    print(f'  expansions BnB/MBR aggregate {tb/max(tm,1):.2f}; zero-expansion MBR updates {sum(int(u["mbr_expanded"])==0 for u in U)}/{len(U)}')
    print('  median ms per update:', {nm: round(st.median(int(u[nm+'_ns']) for u in U)/1e6, 2) for nm in names})
