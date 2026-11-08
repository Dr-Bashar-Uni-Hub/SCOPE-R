import math,random,time,csv,statistics
from functools import lru_cache

class Model:
 def __init__(self,n,m,seed):
  r=random.Random(seed);self.n=n;self.m=m;self.deadline=8
  self.actions=[1<<(i%4) for i in range(n)]
  self.outcomes=[[r.randrange(2) for _ in range(n)] for _ in range(m)]
  self.delay=[r.choice([1,2]) for _ in range(m)]
  self.wait=[[r.random()>.04 for _ in range(n)] for _ in range(m)]
  self.cost=[float(r.randint(0,10)) for _ in range(m)]

def graph(p):
 n=p.n; masks=[15]*(1<<n)
 for b in range(1,1<<n):
  bit=b&-b;masks[b]=masks[b^bit]&p.actions[bit.bit_length()-1]
 buckets=[];waits=[]
 for s in range(p.m):
  d={};wm=0
  for w,y in enumerate(p.outcomes[s]):d[y]=d.get(y,0)|(1<<w);wm|=int(p.wait[s][w])<<w
  buckets.append(tuple(d.values()));waits.append(wm)
 return masks,buckets,waits

def fresh(p):
 masks,buckets,waits=graph(p)
 @lru_cache(None)
 def f(b,t):
  if masks[b]:return 0.
  best=math.inf
  for s in range(p.m):
   if t+p.delay[s]>p.deadline or b&~waits[s]:continue
   children=[b&z for z in buckets[s]];children=[z for z in children if z]
   if len(children)<2:continue
   vals=[f(z,t+p.delay[s]) for z in children]
   q=p.cost[s]+sum(z.bit_count()/b.bit_count()*v for z,v in zip(children,vals)) if all(math.isfinite(v) for v in vals) else math.inf
   best=min(best,q)
  return best
 return f((1<<p.n)-1,0),f.cache_info().misses

class Repair:
 def __init__(self,p):
  self.p=p;self.nodes={};self.links={};self.by_sensor=[set() for _ in range(p.m)];self.last_cost=p.cost[:]
  masks,buckets,waits=graph(p)
  def visit(b,t):
   key=(b,t)
   if key in self.nodes:return self.nodes[key][0]
   if masks[b]:self.nodes[key]=[0.,{}];return 0.
   choices={}
   for s in range(p.m):
    if t+p.delay[s]>p.deadline or b&~waits[s]:continue
    children=[b&z for z in buckets[s]];children=[z for z in children if z]
    if len(children)<2:continue
    children=tuple((z,t+p.delay[s]) for z in children)
    # IMPORTANT: visit ALL children, including those following an infinite child.
    vals=[visit(*child) for child in children]
    q=p.cost[s]+sum(z.bit_count()/b.bit_count()*v for (z,_),v in zip(children,vals)) if all(math.isfinite(v) for v in vals) else math.inf
    choices[s]=[q,children]
    self.by_sensor[s].add(key)
    for child in children:self.links.setdefault(child,[]).append((key,s,child[0].bit_count()/b.bit_count()))
   best=min((q for q,_ in choices.values()),default=math.inf)
   self.nodes[key]=[best,choices];return best
  self.root=((1<<p.n)-1,0);self.value=visit(*self.root)
 def update_cost(self,s,new_cost):
  import heapq
  old_cost=self.last_cost[s];self.p.cost[s]=new_cost;self.last_cost[s]=new_cost
  delta=new_cost-old_cost
  pending=set(self.by_sensor[s]);heap=[(k[0].bit_count(),k) for k in pending];heapq.heapify(heap)
  for k in self.by_sensor[s]:
   q=self.nodes[k][1][s][0]
   if math.isfinite(q):self.nodes[k][1][s][0]=q+delta
  touched=0;changed=0
  while heap:
   _,k=heapq.heappop(heap)
   if k not in pending:continue
   pending.remove(k);node=self.nodes[k];old=node[0]
   new=min((x[0] for x in node[1].values()),default=math.inf)
   node[0]=new;touched+=1
   if new==old or (math.isfinite(new) and math.isfinite(old) and abs(new-old)<1e-11):continue
   changed+=1
   for parent,ss,weight in self.links.get(k,[]):
    q,children=self.nodes[parent][1][ss]
    if all(math.isfinite(x) for x in (q,new,old)):
     self.nodes[parent][1][ss][0]=q+weight*(new-old)
    else:
     vals=[self.nodes[ch][0] for ch in children]
     self.nodes[parent][1][ss][0]=self.p.cost[ss]+sum(ch[0].bit_count()/parent[0].bit_count()*v for ch,v in zip(children,vals)) if all(math.isfinite(v) for v in vals) else math.inf
    if parent not in pending:
     pending.add(parent);heapq.heappush(heap,(parent[0].bit_count(),parent))
  self.value=self.nodes[self.root][0]
  return touched,changed

def same(a,b):return a==b or (math.isfinite(a) and math.isfinite(b) and abs(a-b)<1e-8)

def run():
 r=random.Random(20261106);rows=[]
 for n,m,seeds,steps in [(8,10,12,30),(12,14,10,24),(14,16,5,20)]:
  for seed in range(seeds):
   p=Model(n,m,seed+n*1000);inc=Repair(p);assert same(inc.value,fresh(p)[0])
   for step in range(steps):
    s=r.randrange(m);new=float(r.randint(0,15))
    order=['fresh','repair'];r.shuffle(order)
    times={}
    for method in order:
     st=time.perf_counter_ns()
     if method=='repair':touched,changed=inc.update_cost(s,new);vi=inc.value
     else:p.cost[s]=new;vf,states=fresh(p)
     times[method]=time.perf_counter_ns()-st
    assert same(vi,vf),(n,seed,step,vi,vf)
    rows.append(dict(n=n,m=m,seed=seed,step=step,states=states,feasible=math.isfinite(vf),touched=touched,changed=changed,repair_ns=times['repair'],fresh_ns=times['fresh'],ratio=times['fresh']/times['repair']))
  print('done',n,len(rows),flush=True)
 with open('/mnt/data/scope_r_proof/results.csv','w',newline='') as f:
  w=csv.DictWriter(f,rows[0]);w.writeheader();w.writerows(rows)
 for n in [8,12,14]:
  a=[x for x in rows if x['n']==n];print(n,len(a),'feasible',sum(x['feasible'] for x in a),'median states',statistics.median(x['states'] for x in a),'speedup',round(statistics.median(x['ratio'] for x in a),3),'wins',sum(x['ratio']>1 for x in a))
 print('total',len(rows),'median speedup',statistics.median(x['ratio'] for x in rows))
if __name__=='__main__':run()
