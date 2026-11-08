import random
def mutate(p,r,kind):
 s=r.randrange(p.m);w=r.randrange(p.n)
 if kind=='cost':p.cost[s]=float(r.randint(0,15))
 elif kind=='delay':p.delay[s]=1 if p.delay[s]==2 else 2
 elif kind=='outcome':p.outcomes[s][w]^=1
 elif kind=='wait':p.wait[s][w]=not p.wait[s][w]
 else:p.actions[w]=1<<r.randrange(4)
 return s,w

