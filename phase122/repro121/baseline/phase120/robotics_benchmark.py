"""Synthetic robotic safe-action identification; no claim of physical validation.
Run: python robotics_benchmark.py
"""
import sys,random,math,csv,statistics
from functools import lru_cache
sys.path.insert(0,__import__('os').path.dirname(__file__))
from verified import fresh

class Scenario:
 def __init__(self,n,m,seed):
  r=random.Random(seed);self.n=n;self.m=m;self.deadline=7
  # Latent obstacle configurations: each world admits a subset of four actions.
  self.actions=[]
  for w in range(n):
   a=(1<<(w%4))
   if r.random()<.35:a|=1<<r.randrange(4)
   self.actions.append(a)
  # Binary inspection sensors: each reads a synthetic geometric zone.
  self.outcomes=[];self.delay=[];self.wait=[];self.cost=[]
  for s in range(m):
   z=r.randrange(4); signature=[int(bool(self.actions[w]&(1<<z))) for w in range(n)]
   if s%3==0:signature=[int((w//(1+s%4))%2==1) for w in range(n)]
   if s%5==0:signature=[int((w>>((s//5)%4))&1) for w in range(n)]
   self.outcomes.append(signature)
   self.delay.append(r.choice([1,1,2,3]))
   # Some observations unsafe to wait for in some latent configurations.
   self.wait.append([r.random()>(.02 if s%3 else .12) for _ in range(n)])
   self.cost.append(float(r.choice([1,2,3,4,6,8])))

def greedy(p):
 """Myopic entropy-per-cost policy; infeasible continuation returns inf."""
 @lru_cache(None)
 def rec(b,t):
  common=15
  for w in range(p.n):
   if b>>w&1:common &=p.actions[w]
  if common:return 0.
  options=[]
  for s in range(p.m):
   if t+p.delay[s]>p.deadline or any((b>>w&1) and not p.wait[s][w] for w in range(p.n)):continue
   a=c=0
   for w in range(p.n):
    if b>>w&1:
     if p.outcomes[s][w]:a|=1<<w
     else:c|=1<<w
   if not a or not c:continue
   N=b.bit_count();h=-(a.bit_count()/N)*math.log2(a.bit_count()/N)-(c.bit_count()/N)*math.log2(c.bit_count()/N)
   options.append((-(h/(p.cost[s]+.5*p.delay[s])),s,a,c))
  if not options:return math.inf
  _,s,a,c=min(options)
  x,y=rec(a,t+p.delay[s]),rec(c,t+p.delay[s])
  return p.cost[s]+(a.bit_count()*x+c.bit_count()*y)/b.bit_count() if math.isfinite(x) and math.isfinite(y) else math.inf
 return rec((1<<p.n)-1,0)

def main():
 rows=[]
 for n,m,k in [(8,10,100),(10,12,100),(12,14,80)]:
  for seed in range(k):
   p=Scenario(n,m,118000+seed+100*n)
   v,states=fresh(p);g=greedy(p)
   rows.append(dict(worlds=n,sensors=m,seed=seed,exact=v,greedy=g,exact_feasible=math.isfinite(v),greedy_feasible=math.isfinite(g),states=states))
  print('completed',n,flush=True)
 with open('/mnt/data/scope_r_phase118/robotics_results.csv','w',newline='') as f:
  w=csv.DictWriter(f,rows[0]);w.writeheader();w.writerows(rows)
 for n in [8,10,12]:
  a=[r for r in rows if r['worlds']==n];feas=[r for r in a if r['exact_feasible']];both=[r for r in feas if r['greedy_feasible']]
  print(n,'total',len(a),'exact feasible',len(feas),'greedy feasible among exact',len(both),'median greedy/exact',round(statistics.median(r['greedy']/r['exact'] for r in both),3) if both else None,'median states',statistics.median(r['states'] for r in a))
if __name__=='__main__':main()
