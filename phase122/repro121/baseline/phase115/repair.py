import math,heapq
from run import Unified
from verified import same
class ClosureRepair(Unified):
 def structural(self,kind,s,w):
  p=self.p
  direct=set(self.by_world[w]) if kind in ('viability','outcome','wait') else set(self.nodes)
  pending=set(direct);heap=[(k[0].bit_count(),k[1],k) for k in direct];heapq.heapify(heap)
  touched=changed=0
  while heap:
   _,__,k=heapq.heappop(heap)
   if k not in pending:continue
   pending.remove(k)
   if k not in self.nodes:continue
   touched+=1
   b,t=k;node=self.nodes[k];old=node[0];choices=node[1]
   common=15
   for ww in range(p.n):
    if b>>ww&1:common &=p.actions[ww]
   if common:
    for ss,(q,children) in list(choices.items()):
     self.by_sensor[ss].discard(k)
     for ch in children:self.parents[ch].discard((k,ss))
    choices.clear();new=0.
   else:
    # On directly affected nodes, refresh the changed alternative, or all alternatives
    # if viability changes terminal status. New descendants are built recursively.
    if kind=='viability' and k in direct and not choices:
     for ss in range(p.m):self._replace(k,ss)
    elif k in direct and kind!='viability':self._replace(k,s)
    new=min((v[0] for v in choices.values()),default=math.inf)
   node[0]=new
   if same(old,new):continue
   changed+=1
   for parent,ss in tuple(self.parents.get(k,())):
    if parent not in self.nodes or ss not in self.nodes[parent][1]:continue
    q,children=self.nodes[parent][1][ss]
    vals=[self.nodes[ch][0] for ch in children]
    self.nodes[parent][1][ss][0]=p.cost[ss]+sum(ch[0].bit_count()/parent[0].bit_count()*v for ch,v in zip(children,vals)) if all(map(math.isfinite,vals)) else math.inf
    if parent not in pending:
     pending.add(parent);heapq.heappush(heap,(parent[0].bit_count(),parent[1],parent))
  self.value=self.nodes[self.root][0]
  return touched,changed
 def _replace(self,k,s):
  b,t=k;p=self.p;choices=self.nodes[k][1]
  if s in choices:
   for ch in choices[s][1]:self.parents[ch].discard((k,s))
   del choices[s];self.by_sensor[s].discard(k)
  if t+p.delay[s]>p.deadline or any(not p.wait[s][w] for w in range(p.n) if b>>w&1):return
  c0=c1=0
  for w in range(p.n):
   if b>>w&1:
    if p.outcomes[s][w]:c1|=1<<w
    else:c0|=1<<w
  if not c0 or not c1:return
  children=((c0,t+p.delay[s]),(c1,t+p.delay[s]))
  vals=[self.eval(ch) for ch in children]
  q=p.cost[s]+sum(ch[0].bit_count()/b.bit_count()*v for ch,v in zip(children,vals)) if all(map(math.isfinite,vals)) else math.inf
  choices[s]=[q,children];self.by_sensor[s].add(k)
  for ch in children:self.parents[ch].add((k,s))
 def update(self,kind,s,w):return self.cost(s) if kind=='cost' else self.structural(kind,s,w)
