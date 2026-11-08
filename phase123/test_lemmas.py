"""State-level verification of Lemmas 1-6: after each update, EVERY retained exact entry of MBR
equals the true optimum of that state, and EVERY stored lower bound is <= the true optimum.
Also runs the Phase 113 delay counterexample as a regression."""
import sys,os,json,math,random
H=os.path.dirname(os.path.abspath(__file__));sys.path[:0]=[H]
from mbr import MBR,MBRH,Compiled,INF,exhaustive
exec(open(os.path.join(H,'test_exact.py')).read().split('r=random.Random')[0].split('from verified')[0].replace('from mbr import exhaustive,BnB,MBR',''))
exec('\n'.join(l for l in open(os.path.join(H,'test_exact.py')).read().split('\n') if l.startswith(('def gen','    ','def mutate','class P'))).split('def eq')[0])
def truth(p):
    c=Compiled(p);memo={}
    def V(b,t):
        k=(b,t)
        if k in memo:return memo[k]
        if c.terminal(b):memo[k]=0.;return 0.
        best=INF
        for s in range(c.m):
            t2=t+c.delay[s]
            if t2>c.D or b&~c.safe[s]:continue
            x=b&c.pos[s];y=b^x
            if not x or not y:continue
            vx,vy=V(x,t2),V(y,t2)
            if vx<INF and vy<INF:best=min(best,c.cost[s]+(x.bit_count()*vx+y.bit_count()*vy)/b.bit_count())
        memo[k]=best;return best
    return V
r=random.Random(123077);E=L=bad=0
for inst in range(250):
    n=r.randint(5,11);m=r.randint(4,12);p=gen(r,n,m);M=MBR(p) if inst%2 else MBRH(p)
    for step in range(30):
        kind=r.choice(['cost','delay','outcome','wait','viability']);s,w=mutate(p,r,kind);M.update(kind,s,w);V=truth(p)
        for (b,t),(v,_) in M.E.items():
            E+=1;tv=V(b,t)
            if not(v==tv or (v<INF and tv<INF and abs(v-tv)<=1e-7*max(1,tv))):bad+=1;print('EXACT VIOLATION',inst,step,kind,b,t,v,tv)
        for (b,t),v in M.L.items():
            L+=1
            if v>V(b,t)+1e-7*max(1,abs(v) if v<INF else 1):bad+=1;print('LB VIOLATION',inst,step,kind,b,t,v,V(b,t))
print('retained/stored exact entries checked',E,'lower bounds checked',L,'violations',bad)
# Phase 113 counterexample regression: build pre-update model, apply the delay update in steps.
cx=json.load(open(os.path.join(H,'phase113_counterexample.json')))
class Q:pass
q=Q();q.n,q.m,q.deadline=cx['n'],cx['m'],cx['deadline'];q.actions=cx['actions'];q.outcomes=cx['outcomes'];q.wait=cx['wait'];q.cost=cx['cost']
final=list(cx['delay']);ok=True
for d0 in range(1,6):           # every possible previous delay of the changed sensor
    q.delay=list(final);q.delay[cx['sensor']]=d0;M=MBR(q)
    q.delay[cx['sensor']]=final[cx['sensor']];M.update('delay',cx['sensor'],0)
    ok&=abs(M.value-cx['fresh'])<1e-9 and abs(exhaustive(q)[0]-cx['fresh'])<1e-9
print('Phase 113 counterexample regression (all 5 predecessor delays): value',M.value,'expected',cx['fresh'],'PASS' if ok else 'FAIL')
