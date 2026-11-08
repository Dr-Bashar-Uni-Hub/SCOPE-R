"""Phase 125: merge Scopus + WoS exports, deduplicate (DOI, then normalised title+year)."""
import pandas as pd, glob, re, os
rows = []
for f in sorted(glob.glob('raw/scopus/Scopus/*.csv')):
    d = pd.read_csv(f)
    for _, r in d.iterrows():
        rows.append(dict(src='Scopus', file=os.path.basename(f)[7:15], title=str(r['Title']), year=r['Year'],
                         venue=str(r['Source title']), doi=str(r['DOI']) if pd.notna(r['DOI']) else '',
                         abstract=str(r['Abstract']) if pd.notna(r['Abstract']) else '',
                         keywords=' '.join(str(r[k]) for k in ('Author Keywords', 'Index Keywords') if pd.notna(r[k])),
                         authors=str(r['Authors']), cited=r['Cited by'], doctype=str(r['Document Type'])))
for f in sorted(glob.glob('raw/wos/*/*.xls')):
    d = pd.read_excel(f)
    for _, r in d.iterrows():
        rows.append(dict(src='WoS', file=os.path.basename(f), title=str(r['Article Title']), year=r['Publication Year'],
                         venue=str(r['Source Title']), doi=str(r['DOI']) if pd.notna(r['DOI']) else '',
                         abstract=str(r['Abstract']) if pd.notna(r['Abstract']) else '',
                         keywords=' '.join(str(r[k]) for k in ('Author Keywords', 'Keywords Plus') if pd.notna(r[k])),
                         authors=str(r['Authors']), cited=r['Times Cited, All Databases'], doctype=str(r['Document Type'])))
df = pd.DataFrame(rows)
print('raw records', len(df), df.src.value_counts().to_dict())
df['doi_n'] = df.doi.str.lower().str.strip().str.replace(r'^https?://(dx\.)?doi\.org/', '', regex=True)
df['title_n'] = df.title.str.lower().str.replace(r'[^a-z0-9]+', ' ', regex=True).str.strip()
df['key'] = df.apply(lambda r: 'doi:' + r.doi_n if r.doi_n else 't:' + r.title_n, axis=1)
# merge records sharing DOI or normalised title
groups, key_of = {}, {}
for i, r in df.iterrows():
    k = key_of.get('doi:' + r.doi_n) if r.doi_n else None
    k = k or key_of.get('t:' + r.title_n)
    if k is None: k = len(groups); groups[k] = []
    groups[k].append(i)
    if r.doi_n: key_of['doi:' + r.doi_n] = k
    key_of['t:' + r.title_n] = k
out = []
for k, idx in groups.items():
    g = df.loc[idx]
    best = g.loc[g.abstract.str.len().idxmax()].to_dict()
    best['sources'] = '+'.join(sorted(set(g.src))); best['n_dup'] = len(idx)
    best['doi'] = next((d for d in g.doi if d), '')
    out.append(best)
u = pd.DataFrame(out)
print('unique records', len(u), u.sources.value_counts().to_dict(), 'with abstract', (u.abstract.str.len() > 50).sum())
u.to_csv('merged_dedup.csv', index=False)
