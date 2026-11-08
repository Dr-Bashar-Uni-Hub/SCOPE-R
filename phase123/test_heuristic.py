"""Direct admissibility check of the Huffman bound (Prop. H): h(B,t) <= V(B,t) at every reachable state."""
import random
from mbr import CompiledH,INF
from gen_hard import Inst
viol=chk=tight=0
for seed in range(60):
  rr=random.Random(seed);n,m=rr.choice([(10,14),(12,16),(14,20)]);p=Inst(n,m,9000+seed,deadline=random.Random(seed).choice([6,8,10]),two_action=.3)
  c=CompiledH(p);memo={}
  def V(b,t):
    k=(b,t)
    if k in memo:return memo[k]
    if c.terminal(b):memo[k]=0.;return 0.
    best=INF
    for s in range(m):
      t2=t+c.delay[s]
      if t2>c.D or b&~c.safe[s]:continue
      x=b&c.pos[s];y=b^x
      if not x or not y:continue
      vx,vy=V(x,t2),V(y,t2)
      if vx<INF and vy<INF:best=min(best,c.cost[s]+(x.bit_count()*vx+y.bit_count()*vy)/b.bit_count())
    memo[k]=best;return best
  V((1<<n)-1,0)
  for (b,t),v in memo.items():
    h=c.h(b,t);chk+=1
    if h>v+1e-9:viol+=1
    if v<INF and v>0 and h>c.cmin_t[t]+1e-9:tight+=1
print('states checked',chk,'violations',viol,'states where Huffman bound beats cmin',tight)
