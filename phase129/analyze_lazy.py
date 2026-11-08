"""Phase 129 analysis. PRIMARY contrast (pre-registered): no-certificate / lazy time ratio per trial;
median, percentile bootstrap 95% CI (10,000 resamples, seed 1). Criterion for a 'reliable improvement':
CI > 1 in a majority of settings AND no setting with CI entirely < 1."""
import csv, glob, os, random, statistics as st
H = os.path.dirname(os.path.abspath(__file__))
def boot(x, B=10000, seed=1):
    r = random.Random(seed); n = len(x); m = sorted(st.median([x[r.randrange(n)] for _ in range(n)]) for _ in range(B))
    return m[int(.025 * B)], m[int(.975 * B) - 1]
def ci(x): lo, hi = boot(x); return st.median(x), lo, hi
out = []
for ds in ['syn20', 'syn24', 'syn32', 'heart12', 'heart16']:
    for k in ['delay', 'safety', 'region']:
        R = []
        for f in sorted(glob.glob(os.path.join(H, 'results', f'lazy_{ds}_{k}_*.csv'))): R += list(csv.DictReader(open(f)))
        if not R: continue
        f = lambda c: [float(r[c]) for r in R]
        prim = [float(r['nocert_ns']) / float(r['lazy_ns']) for r in R]
        el = [float(r['eager_ns']) / float(r['lazy_ns']) for r in R]
        ne = [float(r['nocert_ns']) / float(r['eager_ns']) for r in R]
        fl = [float(r['fresh_ns']) / float(r['lazy_ns']) for r in R]
        m, lo, hi = ci(prim)
        zero = {v: sum(int(r[f'{v}_exp']) == 0 for r in R) for v in ['nocert', 'eager', 'lazy', 'fresh']}
        row = dict(dataset=ds, kind=k, trials=len(R),
                   oracle_exhaustive=sum(r['oracle'] == 'exhaustive' for r in R), replay_failed=sum(r['replay_failed'] == 'True' for r in R),
                   infeasible=sum(r['feasible'] == 'False' for r in R),
                   prim_median=round(m, 3), prim_lo=round(lo, 3), prim_hi=round(hi, 3), prim_wins=sum(x > 1 for x in prim),
                   eager_over_lazy=round(st.median(el), 3), nocert_over_eager=round(st.median(ne), 3), fresh_over_lazy=round(st.median(fl), 3),
                   ms_nocert=round(st.median(f('nocert_ns')) / 1e6, 3), ms_eager=round(st.median(f('eager_ns')) / 1e6, 3),
                   ms_lazy=round(st.median(f('lazy_ns')) / 1e6, 3), ms_fresh=round(st.median(f('fresh_ns')) / 1e6, 3),
                   cert_ms_eager=round(st.median(f('eager_cert_ns')) / 1e6, 3), cert_ms_lazy=round(st.median(f('lazy_cert_ns')) / 1e6, 3),
                   cert_share_eager=f"{100*st.median([float(r['eager_cert_ns'])/float(r['eager_ns']) for r in R]):.0f}%",
                   cert_share_lazy=f"{100*st.median([float(r['lazy_cert_ns'])/float(r['lazy_ns']) for r in R]):.0f}%",
                   cert_nodes_eager=st.median(f('eager_cert_nodes')), cert_nodes_lazy=st.median(f('lazy_cert_nodes')),
                   retained_eager=st.median(f('eager_kept_L3')), promoted_lazy=st.median(f('lazy_promoted')),
                   exp_nocert=int(sum(f('nocert_exp'))), exp_eager=int(sum(f('eager_exp'))), exp_lazy=int(sum(f('lazy_exp'))), exp_fresh=int(sum(f('fresh_exp'))),
                   zero_nocert=zero['nocert'], zero_eager=zero['eager'], zero_lazy=zero['lazy'],
                   kb_nocert=round(st.median(f('nocert_peak_bytes')) / 1024, 1), kb_eager=round(st.median(f('eager_peak_bytes')) / 1024, 1),
                   kb_lazy=round(st.median(f('lazy_peak_bytes')) / 1024, 1), kb_fresh=round(st.median(f('fresh_peak_bytes')) / 1024, 1),
                   cacheE_lazy=st.median(f('lazy_cacheE')), cacheE_nocert=st.median(f('nocert_cacheE')))
        out.append(row)
with open(os.path.join(H, 'results', 'lazy_summary.csv'), 'w', newline='') as fo:
    w = csv.DictWriter(fo, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
above = sum(r['prim_lo'] > 1 for r in out); below = sum(r['prim_hi'] < 1 for r in out); amb = len(out) - above - below
for r in out:
    print(f"{r['dataset']:7s} {r['kind']:6s} n={r['trials']:2d} | NOCERT/LAZY {r['prim_median']:.2f} [{r['prim_lo']:.2f},{r['prim_hi']:.2f}] wins {r['prim_wins']:2d}/{r['trials']} | eager/lazy {r['eager_over_lazy']:.2f} | nocert/eager {r['nocert_over_eager']:.2f} | fresh/lazy {r['fresh_over_lazy']:.1f}")
    print(f"        ms nc/eg/lz/fr {r['ms_nocert']}/{r['ms_eager']}/{r['ms_lazy']}/{r['ms_fresh']} | cert ms eg/lz {r['cert_ms_eager']}/{r['cert_ms_lazy']} ({r['cert_share_eager']}/{r['cert_share_lazy']}) nodes {r['cert_nodes_eager']:.0f}/{r['cert_nodes_lazy']:.0f} | ret eg {r['retained_eager']:.0f} prom lz {r['promoted_lazy']:.0f} | exp nc/eg/lz {r['exp_nocert']}/{r['exp_eager']}/{r['exp_lazy']} | zero-search nc/eg/lz {r['zero_nocert']}/{r['zero_eager']}/{r['zero_lazy']} | peak KB nc/eg/lz {r['kb_nocert']}/{r['kb_eager']}/{r['kb_lazy']} | replayfail {r['replay_failed']} infeas {r['infeasible']} exh {r['oracle_exhaustive']}")
print(f"\nPRE-REGISTERED CRITERION: settings with CI>1: {above}/{len(out)}; CI<1: {below}; ambiguous: {amb}  ->  "
      + ('RELIABLE IMPROVEMENT' if above > len(out) / 2 and below == 0 else 'NOT a reliable improvement'))
