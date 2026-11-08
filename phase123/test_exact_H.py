"""Exactness tests for Phase 123 solvers against (a) independent exhaustive DP,
(b) frozen SCOPE-R verified.fresh, (c) Phase 122 exact-rational oracle."""
import sys,os,random,math,copy,time
H=os.path.dirname(os.path.abspath(__file__))
sys.path[:0]=[H,os.path.join(H,'../phase122/fuzz'),os.path.join(H,'../phase122/repro121/baseline/phase115')]
from mbr import exhaustive,BnB,MBR,BnBH,MBRH
from verified import fresh
import oracle
class P: pass
def gen(r,n,m,K=4):
    p=P();p.n=n;p.m=m;p.deadline=r.randint(3,9)
    p.actions=[(1<<r.randrange(K))|((1<<r.randrange(K)) if r.random()<.3 else 0) for _ in range(n)]
    p.outcomes=[[r.randrange(2) for _ in range(n)] for _ in range(m)]
    p.delay=[r.choice([1,1,2,3,4,5]) for _ in range(m)]
    p.wait=[[r.random()>.06 for _ in range(n)] for _ in range(m)]
    p.cost=[float(r.choice([0,1,2,3,5,8,13])) for _ in range(m)]
    return p
def mutate(p,r,kind):
    s=r.randrange(p.m);w=r.randrange(p.n)
    if kind=='cost':p.cost[s]=float(r.choice([0,1,2,3,5,8,13,21]))
    elif kind=='delay':p.delay[s]=r.randint(1,5)
    elif kind=='outcome':p.outcomes[s][w]^=1
    elif kind=='wait':p.wait[s][w]=not p.wait[s][w]
    else:
        p.actions[w]=r.randrange(1,16) if r.random()<.3 else 1<<r.randrange(4)
    return s,w
def eq(a,b):return a==b or (math.isfinite(a) and math.isfinite(b) and abs(a-b)<=1e-7*max(1,abs(b)))
def ov(p):
    v=oracle.solve(p.n,p.m,tuple(p.actions),tuple(map(tuple,p.outcomes)),tuple(p.delay),tuple(map(tuple,p.wait)),tuple(int(c) for c in p.cost),p.deadline)
    return math.inf if v is None else float(v)
r=random.Random(int(sys.argv[1]) if len(sys.argv)>1 else 123001)
N=int(sys.argv[2]) if len(sys.argv)>2 else 300
checks=fin=ora=0;t0=time.time()
for inst in range(N):
    n=r.randint(4,11);m=r.randint(3,12);p=gen(r,n,m)
    mb=MBRH(p);mb2=MBR(p,temporal=False,use_ub=False,L1=False);bb=BnBH(p)
    v0=exhaustive(p)[0];assert eq(mb.value,v0) and eq(bb.value,v0) and eq(mb2.value,v0),(inst,'init',mb.value,bb.value,v0)
    for step in range(40):
        kind=r.choice(['cost','delay','outcome','wait','viability'])
        s,w=mutate(p,r,kind)
        mb.update(kind,s,w);mb2.update(kind,s,w);bb.update(kind,s,w)
        ve=exhaustive(p)[0];vf=fresh(p)[0];checks+=1;fin+=math.isfinite(ve)
        if not(eq(ve,vf)):raise SystemExit(('ORACLE DISAGREE',inst,step,ve,vf))
        if n<=8 and step%4==0:
            o=ov(p);ora+=1
            assert eq(o,ve),('rational',inst,step,o,ve)
        for name,val in [('MBR',mb.value),('MBR-noT-noUB',mb2.value),('BnB',bb.value)]:
            if not eq(val,ve):
                raise SystemExit(('MISMATCH',name,inst,step,kind,s,w,val,ve,mb.stats))
print('instances',N,'checks',checks,'finite',fin,'rational-oracle checks',ora,'secs',round(time.time()-t0,1),'ALL EXACT')
