"""Matched-representation repeated-replanning audit; synthetic robotics only."""
import sys,random,time,math,csv,statistics,copy,os
from pathlib import Path
from functools import lru_cache
HERE=Path(__file__).resolve().parent
sys.path[:0]=['/mnt/data/scope_r_phase115','/mnt/data/scope_r_phase120']
from robotics_benchmark import Scenario
from verified import fresh,same
from benchmark import LazyEligibilityRepair
from repair import ClosureRepair

# Independently coded POMDP Bellman solver using the SAME bitmask state representation.
# Cache is rebuilt after any model update; unlike SCOPE-R, no cross-update repair.
def matched_pomdp(p):
    n=p.n; full=(1<<n)-1
    allowed=[0]*(1<<n)
    for b in range(1,1<<n):
        bit=b&-b;allowed[b]=allowed[b^bit]&p.actions[bit.bit_length()-1] if b^bit else p.actions[bit.bit_length()-1]
    obs=[]; safe=[]
    for s in range(p.m):
        pos=sum((1<<w) for w in range(n) if p.outcomes[s][w]);obs.append(pos)
        safe.append(sum((1<<w) for w in range(n) if p.wait[s][w]))
    @lru_cache(None)
    def solve(b,t):
        if allowed[b]:return 0.
        v=math.inf
        for s in range(p.m):
            if t+p.delay[s]>p.deadline or (b&~safe[s]):continue
            x=b&obs[s];y=b&~obs[s]
            if not x or not y:continue
            a=solve(x,t+p.delay[s]);z=solve(y,t+p.delay[s])
            if math.isfinite(a) and math.isfinite(z):
                q=p.cost[s]+(x.bit_count()*a+y.bit_count()*z)/b.bit_count()
                if q<v:v=q
        return v
    return solve(full,0),solve.cache_info().misses

def change(p,r,kind):
    s=r.randrange(p.m);w=r.randrange(p.n)
    if kind=='cost':p.cost[s]=float(r.randrange(1,10))
    elif kind=='delay':p.delay[s]=r.choice([1,2,3,4])
    elif kind=='outcome':p.outcomes[s][w]^=1
    elif kind=='wait':p.wait[s][w]=not p.wait[s][w]
    else:
        p.actions[w]=1<<r.randrange(4)
        if r.random()<.3:p.actions[w]|=1<<r.randrange(4)
    return s,w

def run():
    rows=[];sequences=[];mismatch=[]
    for n,m,count,steps in [(8,10,4,16),(10,12,4,16),(12,14,4,16)]:
      for regime in ('balanced','cost_dominated'):
       for seed in range(count):
        p=Scenario(n,m,121000+n*100+seed+(regime=='balanced')*10000)
        r=random.Random(181000+n*100+seed+(regime=='balanced')*10000)
        timings={}
        for name,constructor in [('lazy',LazyEligibilityRepair),('closure',ClosureRepair)]:
            t=time.perf_counter_ns();obj=constructor(p);timings[name]=time.perf_counter_ns()-t
            if name=='lazy':lazy=obj
            else:closure=obj
        t=time.perf_counter_ns();v,states=matched_pomdp(p);timings['matched']=time.perf_counter_ns()-t
        t=time.perf_counter_ns();vf,_=fresh(p);timings['fresh']=time.perf_counter_ns()-t
        assert all(same(x,v) for x in [lazy.value,closure.value,vf])
        for step in range(steps):
            kind=r.choice(['cost']*7+['delay','outcome','wait','viability']) if regime=='cost_dominated' else r.choice(['cost','delay','outcome','wait','viability'])
            s,w=change(p,r,kind)
            order=['lazy','closure','matched','fresh'];r.shuffle(order);elapsed={};vals={}
            for name in order:
                t=time.perf_counter_ns()
                if name=='lazy':lazy.update(kind,s,w);val=lazy.value
                elif name=='closure':closure.update(kind,s,w);val=closure.value
                elif name=='matched':val,_=matched_pomdp(p)
                else:val,_=fresh(p)
                elapsed[name]=time.perf_counter_ns()-t;vals[name]=val
            if not all(same(vals[x],vals['matched']) for x in vals):
                mismatch.append((n,regime,seed,step,kind,vals))
                raise AssertionError(mismatch[-1])
            for name in timings:timings[name]+=elapsed[name]
            rows.append(dict(n=n,regime=regime,seed=seed,step=step,kind=kind,feasible=math.isfinite(vals['matched']),**{x+'_ns':elapsed[x] for x in elapsed}))
        sequences.append(dict(n=n,regime=regime,seed=seed,steps=steps,**{x+'_total_ns':timings[x] for x in timings},lazy_vs_matched=timings['matched']/timings['lazy'],closure_vs_matched=timings['matched']/timings['closure'],lazy_vs_closure=timings['closure']/timings['lazy'],matched_vs_fresh=timings['fresh']/timings['matched']))
      print('completed',n,flush=True)
    for filename,data in [('updates.csv',rows),('sequences.csv',sequences)]:
        with open(HERE/filename,'w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
    print('checks',len(rows),'sequences',len(sequences))
    for regime in ['balanced','cost_dominated']:
        group=[x for x in sequences if x['regime']==regime]
        print(regime,'median lazy vs matched',statistics.median(x['lazy_vs_matched'] for x in group),'closure vs matched',statistics.median(x['closure_vs_matched'] for x in group),'lazy vs closure',statistics.median(x['lazy_vs_closure'] for x in group),'lazy wins closure',sum(x['lazy_vs_closure']>1 for x in group),'/',len(group))
    print('matched vs fresh',statistics.median(x['matched_vs_fresh'] for x in sequences))
if __name__=='__main__':run()
