import sys,random,math,copy,json,os,time
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path[:0]=[os.path.join(HERE,'../repro121/baseline/phase115')]
from benchmark import LazyEligibilityRepair
from repair import ClosureRepair
from verified import fresh
import oracle
class P: pass
def rand_model(r,n,m):
    p=P();p.n=n;p.m=m;p.deadline=r.randint(2,8)
    p.actions=[(1<<r.randrange(4))|((1<<r.randrange(4)) if r.random()<.4 else 0) for _ in range(n)]
    p.outcomes=[[r.randrange(2) for _ in range(n)] for _ in range(m)]
    p.delay=[r.randint(1,5) for _ in range(m)]
    p.wait=[[r.random()>.1 for _ in range(n)] for _ in range(m)]
    p.cost=[float(r.choice([0,0,1,2,3,5,8,13])) for _ in range(m)]
    return p
def mutate(p,r,kind):
    s=r.randrange(p.m);w=r.randrange(p.n)
    if kind=='cost':p.cost[s]=float(r.choice([0,1,2,3,5,8,13,21]))
    elif kind=='delay':p.delay[s]=r.randint(1,5)
    elif kind=='outcome':p.outcomes[s][w]^=1
    elif kind=='wait':p.wait[s][w]=not p.wait[s][w]
    else:
        a=r.randrange(1,16);p.actions[w]=a  # arbitrary nonempty viable-action subset
    return s,w
def ov(p):
    v=oracle.solve(p.n,p.m,tuple(p.actions),tuple(map(tuple,p.outcomes)),tuple(p.delay),tuple(map(tuple,p.wait)),tuple(int(c) for c in p.cost),p.deadline)
    return math.inf if v is None else float(v)
def eq(a,b):return a==b or (math.isfinite(a) and math.isfinite(b) and abs(a-b)<1e-7)
r=random.Random(122001);checks=0;fails=[];t0=time.time()
for inst in range(int(sys.argv[1]) if len(sys.argv)>1 else 300):
    n=r.randint(4,9);m=r.randint(3,9);p=rand_model(r,n,m)
    lz=LazyEligibilityRepair(p);cl=ClosureRepair(p)
    for step in range(40):
        kind=r.choice(['cost','delay','outcome','wait','viability'])
        snap=copy.deepcopy(p.__dict__);s,w=mutate(p,r,kind)
        lz.update(kind,s,w);cl.update(kind,s,w)
        o=ov(p);fv=fresh(p)[0];checks+=1
        res=dict(lazy=lz.value,closure=cl.value,fresh=fv,oracle=o)
        bad=[k for k,v in res.items() if not eq(v,o)]
        if bad:
            fails.append(dict(inst=inst,step=step,kind=kind,s=s,w=w,bad=bad,res=res,before=snap,after=copy.deepcopy(p.__dict__)))
            break
print('instances',inst+1,'checks',checks,'failures',len(fails),'secs',round(time.time()-t0,1))
json.dump(fails,open(os.path.join(HERE,'fuzz_failures.json'),'w'),indent=1,default=str)
for f in fails[:5]:print(f['inst'],f['step'],f['kind'],f['bad'],f['res'])
