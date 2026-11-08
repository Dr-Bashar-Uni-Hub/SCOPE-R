import csv,glob,sys,os
for tag in sys.argv[1:]:
    for fn in ('updates.csv','sequences.csv'):
        rows=[]
        for f in sorted(glob.glob(f'results/{tag}/chunk_*/{fn}')):rows+=list(csv.DictReader(open(f)))
        rows.sort(key=lambda r:(r['regime'],int(r['seed']),int(r.get('step',0))))
        with open(f'results/{tag}/{fn}','w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        print(tag,fn,len(rows))
