"""Ablation: deterministic node-expansion counts (hardware-independent) + time, identical streams.
Every variant checked against fresh BnB value each update (and BnB against exhaustive at init)."""
import sys,os,random,math,csv,time,gc
H=os.path.dirname(os.path.abspath(__file__));sys.path[:0]=[H,os.path.join(H,'../phase122/repro121')]
from mbr import MBR,BnB,exhaustive
from gen_hard import Inst
from benchmark_portable import change
V={'full':{},'only_L1_locality':dict(L2=False,L3=False,L4=False,use_ub=False),'only_L2L3_monotone':dict(L1=False,L4=False,use_ub=False),'only_L4_singleuse':dict(L1=False,L2=False,L3=False,use_ub=False),'only_L5_replay':dict(L1=False,L2=False,L3=False,L4=False),'none(reuse off)':dict(L1=False,L2=False,L3=False,L4=False,use_ub=False)}
tag,n,m,seeds,steps=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5])
rows=[]
for regime in ('balanced','cost_dominated'):
  for seed in range(seeds):
    base=123000+n*100+seed+(regime=='balanced')*50000
    p=Inst(n,m,base,deadline=10);r=random.Random(base+7)
    obj={k:MBR(p,**kw) for k,kw in V.items()};obj['bnb']=BnB(p)
    exp={k:0 for k in obj};tm={k:0 for k in obj}
    for step in range(steps):
      kind=r.choice(['cost']*7+['delay','outcome','wait','viability']) if regime=='cost_dominated' else r.choice(['cost','delay','outcome','wait','viability'])
      s,w=change(p,r,kind)
      for k,o in obj.items():
        e0=o.expanded;gc.collect();gc.disable();t=time.perf_counter_ns();o.update(kind,s,w);tm[k]+=time.perf_counter_ns()-t;gc.enable();exp[k]+=o.expanded-e0
      ref=obj['bnb'].value
      for k,o in obj.items():
        assert o.value==ref or abs(o.value-ref)<=1e-7*max(1,abs(ref)),(k,step,o.value,ref)
    for k in obj:rows.append(dict(tag=tag,regime=regime,seed=seed,variant=k,expansions=exp[k],update_ms=tm[k]/1e6))
os.makedirs('results/ablation',exist_ok=True)
with open(f'results/ablation/{tag}_only.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
import statistics as st
for k in list(V)+['bnb']:
    a=[x for x in rows if x['variant']==k];b={(x['regime'],x['seed']):x for x in rows if x['variant']=='full'}
    print(tag,k.ljust(18),'total expansions',sum(x['expansions'] for x in a),'| median exp ratio vs full %.2f'%st.median((x['expansions']+1)/(b[(x['regime'],x['seed'])]['expansions']+1) for x in a),'| update ms total %.0f'%sum(x['update_ms'] for x in a))
