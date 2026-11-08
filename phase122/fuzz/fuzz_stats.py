# same generator as fuzz.py but biased toward feasible, nontrivial instances; reports value distribution
import sys,random,math,copy,os
sys.argv=[sys.argv[0]]
exec(open('fuzz.py').read().split("r=random.Random(122001)")[0])
def rand_model2(r,n,m):
    p=rand_model(r,n,m);p.deadline=r.randint(4,10)
    p.wait=[[r.random()>.03 for _ in range(n)] for _ in range(m)]
    p.actions=[(1<<(w%4))|((1<<r.randrange(4)) if r.random()<.3 else 0) for w in range(n)]
    p.delay=[r.choice([1,1,2,3,4,5]) for _ in range(m)]
    return p
r=random.Random(122002);checks=fin=nonzero=0;fails=0;kinds={}
for inst in range(400):
    n=r.randint(5,10);m=r.randint(5,11);p=rand_model2(r,n,m)
    lz=LazyEligibilityRepair(p);cl=ClosureRepair(p)
    for step in range(50):
        kind=r.choice(['cost','delay','outcome','wait','viability'])
        s,w=mutate(p,r,kind)
        if kind=='viability' and r.random()<.7: p.actions[w]=1<<r.randrange(4)  # mostly singleton to keep nontrivial
        lz.update(kind,s,w);cl.update(kind,s,w)
        o=ov(p);checks+=1;fin+=math.isfinite(o);nonzero+=(math.isfinite(o) and o>0)
        # boundary crossing tracking: was delay update crossing deadline relevance?
        if not(eq(lz.value,o) and eq(cl.value,o) and eq(fresh(p)[0],o)):
            fails+=1;print('FAIL',inst,step,kind,lz.value,cl.value,o);break
print('checks',checks,'finite',fin,'finite&>0',nonzero,'fails',fails)
