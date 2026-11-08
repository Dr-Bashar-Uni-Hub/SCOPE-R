"""Harder synthetic inspection instances (Phase 123). 4 terminal actions (so frozen
ClosureRepair/Phase-115 code runs unchanged), random + structured binary sensors."""
import random
class Inst:
    def __init__(self,n,m,seed,deadline=10,two_action=.3,unsafe=.03):
        r=random.Random(seed);self.n=n;self.m=m;self.deadline=deadline
        self.actions=[]
        for w in range(n):
            a=1<<r.randrange(4)
            if r.random()<two_action:a|=1<<r.randrange(4)
            self.actions.append(a)
        self.outcomes=[]
        for s in range(m):
            if s%4==0:  # sensor correlated with one action region (noisy)
                z=r.randrange(4);sig=[int(bool(self.actions[w]>>z&1)) ^ int(r.random()<.25) for w in range(n)]
            else:
                q=r.uniform(.25,.75);sig=[int(r.random()<q) for _ in range(n)]
            self.outcomes.append(sig)
        self.delay=[r.choice([1,1,2,3]) for _ in range(m)]
        self.wait=[[r.random()>unsafe for _ in range(n)] for _ in range(m)]
        self.cost=[float(r.choice([1,2,3,4,6,8,10])) for _ in range(m)]
