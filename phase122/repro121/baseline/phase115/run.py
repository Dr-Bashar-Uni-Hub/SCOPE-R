import sys,math,random,time,csv,statistics,heapq,collections,os
sys.path.insert(0,os.path.dirname(__file__))
from verified import Model,fresh,same,graph
from mutate import mutate
class Unified:
 def __init__(self,p):
  self.p=p;self.root=((1<<p.n)-1,0);self.nodes={};self.parents=collections.defaultdict(set);self.by_sensor=[set() for _ in range(p.m)];self.by_world=[set() for _ in range(p.n)];self.last_cost=p.cost[:];self.value=self.eval(self.root)
 def eval(self,k):
  if k in self.nodes:return self.nodes[k][0]
  b,t=k;p=self.p;common=15
  for w in range(p.n):
   if b>>w&1:common &=p.actions[w]
  if common:
   for w in range(p.n):
    if b>>w&1:self.by_world[w].add(k)
   self.nodes[k]=[0.,{}];return 0.
  choices={}
  for s in range(p.m):
   if t+p.delay[s]>p.deadline or any(not p.wait[s][w] for w in range(p.n) if b>>w&1):continue
   c0=c1=0
   for w in range(p.n):
    if b>>w&1:
     if p.outcomes[s][w]:c1|=1<<w
     else:c0|=1<<w
   if not c0 or not c1:continue
   children=((c0,t+p.delay[s]),(c1,t+p.delay[s]))
   vals=[self.eval(ch) for ch in children]
   q=p.cost[s]+sum(ch[0].bit_count()/b.bit_count()*v for ch,v in zip(children,vals)) if all(map(math.isfinite,vals)) else math.inf
   choices[s]=[q,children]
   for ch in children:self.parents[ch].add((k,s))
   self.by_sensor[s].add(k)
  for w in range(p.n):
   if b>>w&1:self.by_world[w].add(k)
  val=min((x[0] for x in choices.values()),default=math.inf)
  self.nodes[k]=[val,choices];return val
 def is_terminal(self,k):
  b,_=k;mask=15
  for w in range(self.p.n):
   if b>>w&1:mask &= self.p.actions[w]
  return bool(mask)
 def is_informative(self,k,s):
  b,_=k;seen=set()
  for w in range(self.p.n):
   if b>>w&1:seen.add(self.p.outcomes[s][w])
  return len(seen)>1
 def structural(self,kind,s,w):
  # All affected local Bellman states, including descendants that become newly reachable,
  # are repaired on demand; parents are invalidated transitively.
  if kind in ('viability','outcome','wait'):direct=set(self.by_world[w])
  elif kind=='delay':direct={k for k,node in self.nodes.items() if not self.is_terminal(k) and self.is_informative(k,s)}
  else:direct=set(self.by_sensor[s])
  affected=set(direct);stack=list(direct)
  while stack:
   for parent,_ in tuple(self.parents.get(stack.pop(),())):
    if parent not in affected:affected.add(parent);stack.append(parent)
  for k in affected:
   node=self.nodes.pop(k,None)
   if node is None:continue
   for ss,(q,children) in node[1].items():
    self.by_sensor[ss].discard(k)
    for ch in children:self.parents[ch].discard((k,ss))
   b,_=k
   for w0 in range(self.p.n):
    if b>>w0&1:self.by_world[w0].discard(k)
  self.value=self.eval(self.root)
  return len(affected)
 def cost(self,s):
  delta=self.p.cost[s]-self.last_cost[s];self.last_cost[s]=self.p.cost[s]
  pending=set(self.by_sensor[s]);heap=[(k[0].bit_count(),k) for k in pending];heapq.heapify(heap)
  for k in pending:
   q=self.nodes[k][1][s][0]
   if math.isfinite(q):self.nodes[k][1][s][0]=q+delta
  touched=0
  while heap:
   _,k=heapq.heappop(heap)
   if k not in pending:continue
   pending.remove(k);touched+=1
   node=self.nodes[k];old=node[0];new=min((x[0] for x in node[1].values()),default=math.inf);node[0]=new
   if same(old,new):continue
   for parent,ss in tuple(self.parents.get(k,())):
    if parent not in self.nodes:continue
    choice=self.nodes[parent][1][ss];q,children=choice
    if all(map(math.isfinite,(q,old,new))):choice[0]=q+(k[0].bit_count()/parent[0].bit_count())*(new-old)
    else:
     vals=[self.nodes[ch][0] for ch in children]
     choice[0]=self.p.cost[ss]+sum(ch[0].bit_count()/parent[0].bit_count()*v for ch,v in zip(children,vals)) if all(map(math.isfinite,vals)) else math.inf
    if parent not in pending:pending.add(parent);heapq.heappush(heap,(parent[0].bit_count(),parent))
  self.value=self.nodes[self.root][0];return touched
 def update(self,kind,s,w):return self.cost(s) if kind=='cost' else self.structural(kind,s,w)
def run():
 rows=[];seq=[]
 for n,m,seeds,steps in [(8,10,5,24),(12,14,4,20),(14,16,2,16)]:
  for pattern in ('mixed','mostly_cost'):
   for seed in range(seeds):
    r=random.Random(108000+n*100+seed);p=Model(n,m,seed+1234+n*999)
    t=time.perf_counter_ns();inc=Unified(p);ti=time.perf_counter_ns()-t
    t=time.perf_counter_ns();vf,_=fresh(p);tf=time.perf_counter_ns()-t
    assert same(inc.value,vf)
    for step in range(steps):
     kind=r.choice(['cost']*7+['outcome','delay','wait','viability']) if pattern=='mostly_cost' else r.choice(['cost','outcome','delay','wait','viability'])
     s,w=mutate(p,r,kind);order=['inc','fresh'];r.shuffle(order);times={}
     for method in order:
      t=time.perf_counter_ns()
      if method=='inc':touched=inc.update(kind,s,w);v=inc.value
      else:vf,states=fresh(p)
      times[method]=time.perf_counter_ns()-t
     assert same(v,vf),(n,pattern,seed,step,kind,v,vf)
     ti+=times['inc'];tf+=times['fresh']
     rows.append(dict(n=n,pattern=pattern,seed=seed,step=step,kind=kind,feasible=math.isfinite(vf),states=states,touched=touched,inc_ns=times['inc'],fresh_ns=times['fresh'],ratio=times['fresh']/times['inc'],amortized=tf/ti))
    seq.append(dict(n=n,pattern=pattern,seed=seed,steps=steps,amortized=tf/ti,win=tf>ti))
  print('finished',n,flush=True)
 for name,data in [('updates.csv',rows),('sequences.csv',seq)]:
  with open(os.path.join(os.path.dirname(__file__),name),'w',newline='') as f:
   writer=csv.DictWriter(f,fieldnames=data[0].keys());writer.writeheader();writer.writerows(data)
 print('total',len(rows),'faster',sum(x['ratio']>1 for x in rows))
 for pattern in ('mixed','mostly_cost'):
  a=[x for x in seq if x['pattern']==pattern];print(pattern,'median amortized',statistics.median(x['amortized'] for x in a),'wins',sum(x['win'] for x in a),'/',len(a))
 for kind in ['cost','outcome','delay','wait','viability']:
  a=[x for x in rows if x['kind']==kind];print(kind,len(a),statistics.median(x['ratio'] for x in a))
if __name__=='__main__':run()
