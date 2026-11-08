"""Sequence-level statistics: median speedup of each solver vs MBR (total time incl. init),
percentile bootstrap 95% CI (10,000 resamples, seed fixed), wins, and expansion ratios."""
import csv,sys,os,random,statistics as st,glob,json
REF=os.environ.get('REF','mbr');FB=os.environ.get('FB','bnb')
def boot(xs,B=10000,seed=1):
    r=random.Random(seed);n=len(xs);meds=sorted(st.median(r.choice(xs) for _ in range(n)) for _ in range(B))
    return meds[int(.025*B)],meds[int(.975*B)-1]
out=[]
for tag in sys.argv[1:]:
    seqs=list(csv.DictReader(open(f'results/{tag}/sequences.csv')))
    ups=list(csv.DictReader(open(f'results/{tag}/updates.csv')))
    names=[k[:-9] for k in seqs[0] if k.endswith('_total_ns')]
    for regime in ('balanced','cost_dominated','all'):
        S=[s for s in seqs if regime=='all' or s['regime']==regime]
        U=[u for u in ups if regime=='all' or u['regime']==regime]
        if not S:continue
        for nm in names:
            if nm==REF:continue
            ratios=[int(s[nm+'_total_ns'])/int(s[REF+'_total_ns']) for s in S]
            lo,hi=boot(ratios)
            out.append(dict(tag=tag,regime=regime,baseline=nm,sequences=len(S),median_speedup_of_MBR=round(st.median(ratios),3),ci_lo=round(lo,3),ci_hi=round(hi,3),MBR_wins=sum(x>1 for x in ratios)))
        ex=[(int(u[FB+'_expanded'])+1)/(int(u[REF+'_expanded'])+1) for u in U]
        zero=sum(int(u[REF+'_expanded'])==0 for u in U)
        tot_b=sum(int(u[FB+'_expanded']) for u in U);tot_m=sum(int(u[REF+'_expanded']) for u in U)
        out.append(dict(tag=tag,regime=regime,baseline=FB+'_expansions(update-level)',sequences=len(U),median_speedup_of_MBR=round(st.median(ex),3),ci_lo='',ci_hi='',MBR_wins=f'aggregate ratio {tot_b/max(tot_m,1):.2f}; zero-expansion updates {zero}/{len(U)}'))
for r in out:print(r['tag'],r['regime'].ljust(14),r['baseline'].ljust(28),r['median_speedup_of_MBR'],f"[{r['ci_lo']},{r['ci_hi']}]",r['MBR_wins'],'/',r['sequences'])
fn='results/summary_'+REF+'_'+'_'.join(sys.argv[1:])+'.csv'
with open(fn,'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
