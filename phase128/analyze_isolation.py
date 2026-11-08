"""Summarise the isolation ablation: certificate-specific effect (noL3s vs full), Lemma-2 effect
(L1only vs noL3s), and overall (fresh vs full). Paired per-trial time ratios; median with percentile
bootstrap 95% CI (10,000 resamples, seed 1); expansions and retained-entry counts."""
import csv, glob, random, statistics as st, os
H = os.path.dirname(os.path.abspath(__file__))
def boot(x, B=10000, seed=1):
    r = random.Random(seed); n = len(x); m = sorted(st.median([x[r.randrange(n)] for _ in range(n)]) for _ in range(B))
    return m[int(.025 * B)], m[int(.975 * B) - 1]
def fmt(x): lo, hi = boot(x); return f'{st.median(x):.2f}x [{lo:.2f}, {hi:.2f}]'
out = []
order = ['syn20', 'syn24', 'heart12', 'heart16']; kinds = ['delay', 'safety', 'region']
for ds in order:
    for k in kinds:
        R = []
        for f in sorted(glob.glob(os.path.join(H, 'results', f'isolation_{ds}_{k}_*.csv'))): R += list(csv.DictReader(open(f)))
        if not R: continue
        g = lambda c: [float(r[c]) for r in R]
        cert = [float(r['noL3s_ns']) / float(r['full_ns']) for r in R]
        l2 = [float(r['L1only_ns']) / float(r['noL3s_ns']) for r in R]
        tot = [float(r['fresh_ns']) / float(r['full_ns']) for r in R]
        keptfrac = [float(r['kept_L3']) / max(1, float(r['old_entries'])) for r in R]
        touched = [r for r in R if r['root_retained_by_L3'] == 'False']
        row = dict(dataset=ds, kind=k, trials=len(R),
                   value_changed=sum(r['value_changed'] == 'True' for r in R),
                   root_retained_by_cert=sum(r['root_retained_by_L3'] == 'True' for r in R),
                   kept_L3_median_entries=st.median(g('kept_L3')), kept_L3_median_share=f'{100*st.median(keptfrac):.0f}%',
                   exp_full=int(sum(g('full_exp'))), exp_noL3s=int(sum(g('noL3s_exp'))), exp_L1only=int(sum(g('L1only_exp'))), exp_fresh=int(sum(g('fresh_exp'))),
                   ms_full_median=round(st.median(g('full_ns')) / 1e6, 3), ms_noL3s_median=round(st.median(g('noL3s_ns')) / 1e6, 3),
                   ms_fresh_median=round(st.median(g('fresh_ns')) / 1e6, 3),
                   speedup_certificate=fmt(cert), cert_wins=sum(c > 1 for c in cert),
                   speedup_lemma2=fmt(l2), speedup_full_vs_fresh=fmt(tot),
                   touched_trials=len(touched),
                   cert_speedup_touched=fmt([float(r['noL3s_ns']) / float(r['full_ns']) for r in touched]) if len(touched) >= 3 else 'n<3')
        out.append(row)
with open(os.path.join(H, 'results', 'isolation_summary.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
for r in out:
    print(f"{r['dataset']:8s} {r['kind']:7s} n={r['trials']:3d} chg={r['value_changed']:2d} rootByCert={r['root_retained_by_cert']:2d} "
          f"keptL3={r['kept_L3_median_entries']:.0f} ({r['kept_L3_median_share']}) exp full/noL3s/L1/fresh={r['exp_full']}/{r['exp_noL3s']}/{r['exp_L1only']}/{r['exp_fresh']} "
          f"ms full/noL3s/fresh={r['ms_full_median']}/{r['ms_noL3s_median']}/{r['ms_fresh_median']}\n"
          f"          CERT {r['speedup_certificate']} wins {r['cert_wins']}/{r['trials']} | L2 {r['speedup_lemma2']} | full-vs-fresh {r['speedup_full_vs_fresh']} | touched {r['touched_trials']}: cert {r['cert_speedup_touched']}")
