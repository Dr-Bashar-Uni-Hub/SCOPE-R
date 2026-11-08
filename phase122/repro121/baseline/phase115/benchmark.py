import sys,os,random,time,math,csv,statistics,heapq
ROOT='/mnt/data/scope_r_phase114';sys.path.append(ROOT)
from verified import Model,fresh,same
from repair import ClosureRepair
from mutate import mutate

class LazyEligibilityRepair(ClosureRepair):
    """Candidate eligibility cached by belief mask, never by time-state.
    On delay updates, query only cached nodes with a nonterminal belief
    and an informative partition for that sensor. Avoid persistent per-sensor
    state-set maintenance; cache partition tests by (belief,sensor,version).
    """
    def __init__(self,p):
        self.partition_version=[0]*p.m
        self.informative_cache={}
        super().__init__(p)
    def informative(self,b,s):
        key=(b,s,self.partition_version[s])
        ans=self.informative_cache.get(key)
        if ans is None:
            z=0
            for w in range(self.p.n):
                if b>>w&1:z|=1<<self.p.outcomes[s][w]
            ans=(z==3)
            self.informative_cache[key]=ans
        return ans
    def structural(self,kind,s,w):
        if kind=='outcome':
            self.partition_version[s]+=1
            # Drop stale sensor partitions periodically; not per-update.
            if len(self.informative_cache)>100000:self.informative_cache.clear()
        if kind!='delay':return super().structural(kind,s,w)
        # Unlike the eager index, no maintenance on graph insertions/deletions.
        direct={k for k in self.nodes if not self.is_terminal(k) and self.informative(k[0],s)}
        return self.repair_delay(s,direct)
    def repair_delay(self,s,direct):
        p=self.p
        pending=set(direct)
        heap=[(k[0].bit_count(),k[1],k) for k in direct]
        heapq.heapify(heap)
        touched=0;changed=0
        while heap:
            _,__,k=heapq.heappop(heap)
            if k not in pending:continue
            pending.remove(k)
            if k not in self.nodes:continue
            touched+=1
            node=self.nodes[k];old=node[0]
            if k in direct:self._replace(k,s)
            new=min((q for q,_ in node[1].values()),default=math.inf)
            node[0]=new
            if same(old,new):continue
            changed+=1
            for parent,ss in tuple(self.parents.get(k,())):
                if parent not in self.nodes or ss not in self.nodes[parent][1]:continue
                q,children=self.nodes[parent][1][ss]
                vals=[self.nodes[ch][0] for ch in children]
                self.nodes[parent][1][ss][0]=(p.cost[ss]+sum(ch[0].bit_count()/parent[0].bit_count()*v for ch,v in zip(children,vals))) if all(map(math.isfinite,vals)) else math.inf
                if parent not in pending:
                    pending.add(parent);heapq.heappush(heap,(parent[0].bit_count(),parent[1],parent))
        self.value=self.nodes[self.root][0]
        return touched,changed

def run():
    rows=[];seq=[]
    for n,m,seeds,steps in [(8,10,5,22),(12,14,5,20),(14,16,3,18),(16,18,2,14)]:
        for pattern in ('mixed','mostly_cost'):
            for seed in range(seeds):
                r=random.Random(115000+n*1000+seed+(pattern=='mixed')*20000)
                p=Model(n,m,seed+87000+n*77)
                t=time.perf_counter_ns();lazy=LazyEligibilityRepair(p);lt=time.perf_counter_ns()-t
                t=time.perf_counter_ns();closure=ClosureRepair(p);ct=time.perf_counter_ns()-t
                t=time.perf_counter_ns();v,states=fresh(p);ft=time.perf_counter_ns()-t
                assert same(lazy.value,v) and same(closure.value,v)
                for step in range(steps):
                    kind=r.choice(['cost']*7+['outcome','delay','wait','viability']) if pattern=='mostly_cost' else r.choice(['cost','outcome','delay','wait','viability'])
                    s,w=mutate(p,r,kind)
                    order=['lazy','closure','fresh'];r.shuffle(order);times={}
                    for name in order:
                        t=time.perf_counter_ns()
                        if name=='lazy':lazy.update(kind,s,w)
                        elif name=='closure':closure.update(kind,s,w)
                        else:v,states=fresh(p)
                        times[name]=time.perf_counter_ns()-t
                    if not same(lazy.value,v) or not same(closure.value,v):raise AssertionError((n,pattern,seed,step,kind,lazy.value,closure.value,v))
                    lt+=times['lazy'];ct+=times['closure'];ft+=times['fresh']
                    rows.append(dict(n=n,pattern=pattern,seed=seed,step=step,kind=kind,feasible=math.isfinite(v),states=states,**{k+'_ns':v for k,v in times.items()}))
                seq.append(dict(n=n,pattern=pattern,seed=seed,steps=steps,lazy_vs_fresh=ft/lt,closure_vs_fresh=ft/ct,lazy_vs_closure=ct/lt))
        print('finished',n,flush=True)
    for filename,data in [('updates.csv',rows),('sequences.csv',seq)]:
        with open('/mnt/data/scope_r_phase115/'+filename,'w',newline='') as f:
            writer=csv.DictWriter(f,data[0].keys());writer.writeheader();writer.writerows(data)
    print('EXACT',len(rows),'sequences',len(seq))
    for pattern in ('mixed','mostly_cost'):
        a=[x for x in seq if x['pattern']==pattern]
        print(pattern,'lazy',statistics.median(x['lazy_vs_fresh'] for x in a),'closure',statistics.median(x['closure_vs_fresh'] for x in a),'lazy beats closure',sum(x['lazy_vs_closure']>1 for x in a),'/',len(a))
    for kind in ['cost','outcome','delay','wait','viability']:
        a=[x for x in rows if x['kind']==kind]
        print(kind,len(a),'median lazy/closure speed',statistics.median(x['closure_ns']/x['lazy_ns'] for x in a))
if __name__=='__main__':run()
