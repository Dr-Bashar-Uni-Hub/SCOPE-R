"""Generates all manuscript figures deterministically from repository data and solvers.
Outputs PNG (300 dpi, for Word) and PDF (vector) to figures/out/.
  Fig. 1  illustrative instance and its optimal policy (solved by fig_instance.py; checked vs exhaustive DP)
  Fig. 2  update taxonomy and MBR replanning pipeline (conceptual diagram)
  Fig. 3  synthetic scaling (phase123/results/*/sequences.csv)
  Fig. 4  certificate isolation (phase129/results/lazy_*.csv)
  Fig. 5  case study: optimal expected test cost vs deadline (recomputed with phase124 + phase123 BnB)
Usage: python make_figures.py
"""
import os, sys, csv, glob, random, statistics as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H)
OUT = os.path.join(H, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path[:0] = [H, os.path.join(R, 'phase123'), os.path.join(R, 'phase124')]
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.linewidth': 0.8, 'savefig.dpi': 300})
C_EST, C_PROP, C_NEU = '#4C72B0', '#DD8452', '#7F7F7F'      # colour-blind-safe pair + grey
def save(fig, name):
    fig.savefig(os.path.join(OUT, name + '.png'), bbox_inches='tight'); fig.savefig(os.path.join(OUT, name + '.pdf'), bbox_inches='tight')
    plt.close(fig); print('written', name)
def boot(x, B=10000, seed=1):
    r = random.Random(seed); n = len(x); m = sorted(st.median([x[r.randrange(n)] for _ in range(n)]) for _ in range(B))
    return st.median(x), m[int(.025 * B)], m[int(.975 * B) - 1]
def box(ax, x, y, w, h, text, fc='white', ec='black', fs=8, lw=0.9, ls='-'):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle='round,pad=0.02,rounding_size=0.08', fc=fc, ec=ec, lw=lw, ls=ls))
    ax.text(x, y, text, ha='center', va='center', fontsize=fs, wrap=True)
def arrow(ax, x1, y1, x2, y2, text='', fs=7.5, color='black', off=(0.0, 0.0)):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>', mutation_scale=9, lw=0.9, color=color))
    if text: ax.text((x1 + x2) / 2 + off[0], (y1 + y2) / 2 + off[1], text, fontsize=fs, ha='center', va='center',
                     bbox=dict(fc='white', ec='none', pad=0.6))

# ---------------- Figure 1 ----------------
def fig1():
    import fig_instance as fi
    p = fi.model(3); V, term = fi.solve(p)
    assert abs(V(63, 0)[0] - 7.0) < 1e-12 and abs(fi.solve(fi.model(4))[0](63, 0)[0] - 3.5) < 1e-12
    fig, ax = plt.subplots(figsize=(7.2, 4.0)); ax.set_xlim(0, 10); ax.set_ylim(0.85, 6.25); ax.axis('off')
    tbl = ('Hypotheses and acceptable actions (D = discharge, M = monitor, T = treat)\n'
           'h1:{D}  h2:{D,M}  h3:{M}  h4:{M,T}  h5:{T}  h6:{T}\n'
           'Tests (cost, delay): history (1, 1)   blood (5, 3)   stress (8, 1; unsafe for h3)   imaging (12, 2);   deadline D = 3')
    ax.text(5, 5.85, tbl, ha='center', va='center', fontsize=7.6, bbox=dict(fc='#F2F2F2', ec='#BBBBBB', pad=4))
    box(ax, 5, 4.55, 3.4, 0.62, 'B = {h1,…,h6},  t = 0\nV = 7.0   →  test: history (cost 1)')
    box(ax, 2.75, 3.0, 4.3, 0.62, 'B = {h1,h2,h3},  t = 1\nV = 12.0   →  test: imaging (cost 12)')
    box(ax, 7.6, 3.0, 2.6, 0.62, 'B = {h4,h5,h6},  t = 1\nterminal: ⋂A = {T}', fc='#E3F1E3')
    box(ax, 0.95, 1.35, 1.8, 0.62, 'B = {h1},  t = 3\nterminal: {D}', fc='#E3F1E3')
    box(ax, 3.55, 1.35, 3.2, 0.62, 'B = {h2,h3},  t = 3\nterminal: {D,M} ∩ {M} = {M}', fc='#E3F1E3')
    arrow(ax, 4.4, 4.24, 3.0, 3.31, 'outcome 0', off=(-0.35, 0.05)); arrow(ax, 5.6, 4.24, 7.3, 3.31, 'outcome 1', off=(0.35, 0.05))
    arrow(ax, 2.2, 2.69, 1.1, 1.66, '0', off=(-0.15, 0)); arrow(ax, 3.2, 2.69, 3.55, 1.66, '1', off=(0.2, 0))
    ax.text(7.95, 1.6, 'Excluded at {h1,h2,h3}, t = 1:\n• blood (cost 5): 1 + 3 > D — deadline\n• stress (cost 8): unsafe for h3 — safety\n'
            'With D = 4, blood becomes admissible\nand V drops from 7.0 to 3.5.', fontsize=7.2, va='center', ha='center',
            bbox=dict(fc='#FFF4E5', ec=C_PROP, pad=4))
    save(fig, 'fig1_model_example')

# ---------------- Figure 2 ----------------
def fig2():
    fig, ax = plt.subplots(figsize=(7.2, 4.6)); ax.set_xlim(0, 10); ax.set_ylim(0.05, 6.75); ax.axis('off')
    box(ax, 1.55, 6.3, 2.5, 0.65, 'Model update\n(one element)', fc='#F2F2F2')
    box(ax, 4.95, 6.3, 2.9, 0.65, 'Classify the update\n(Table 1)', fc='#F2F2F2')
    arrow(ax, 2.8, 6.3, 3.5, 6.3)
    rows = [(5.05, 'World-local, w ∉ B', 'Keep exact values and bounds unchanged\n(Lemma 1, locality)', C_EST),
            (3.85, 'Tightening', 'Old values → lower bounds (Lemma 2)\nUntouched sub-policies remain exact (Lemma 3),\nchecked eagerly or lazily; structural cases proposed', C_PROP),
            (2.65, 'Cost decrease by δ', 'Old values − δ → lower bounds\n(Lemma 4)', C_EST),
            (1.55, 'Outcome change /\nother loosening', 'Discard affected entries\n(no general certificate exists: Section 5)', C_NEU)]
    xb, xc, xa, wc, wa = 0.35, 2.0, 6.45, 2.6, 5.0
    ax.plot([4.95, 4.95, xb, xb], [5.975, 5.65, 5.65, rows[-1][0]], color='black', lw=0.9)
    for y, lab, act, col in rows:
        arrow(ax, xb, y, xc - wc / 2, y)
        box(ax, xc, y, wc, 0.72, lab, fs=7.8)
        arrow(ax, xc + wc / 2, y, xa - wa / 2, y)
        box(ax, xa, y, wa, 0.92, act, fs=7.3, ec=col, lw=1.6)
    xr = 9.3
    for y, *_ in rows: ax.plot([xa + wa / 2, xr], [y, y], color='black', lw=0.9)
    ax.plot([xr, xr], [rows[0][0], 0.55], color='black', lw=0.9)
    box(ax, xa, 0.55, wa, 0.72, 'Replay old policy → root budget (Lemma 5)\nBounded search (Lemma 7) → exact new value V′', fc='#F2F2F2', fs=7.5)
    arrow(ax, xr, 0.55, xa + wa / 2, 0.55)
    ax.plot([0.5, 0.9], [0.75, 0.75], color=C_EST, lw=2.2); ax.text(1.0, 0.75, 'established', va='center', fontsize=7.4)
    ax.plot([0.5, 0.9], [0.5, 0.5], color=C_PROP, lw=2.2); ax.text(1.0, 0.5, 'contains the proposed element', va='center', fontsize=7.4)
    ax.plot([0.5, 0.9], [0.25, 0.25], color=C_NEU, lw=2.2); ax.text(1.0, 0.25, 'no certificate', va='center', fontsize=7.4)
    save(fig, 'fig2_mbr_pipeline')

# ---------------- Figure 3 ----------------
def fig3():
    tags = [('S', 12), ('M', 16), ('L', 20), ('XL', 24), ('XXL', 32), ('XXXL', 40)]
    series = {'bnb': ('fresh branch-and-bound', 'o', C_PROP), 'exh': ('exhaustive DP', 's', C_EST), 'closure': ('dependency repair (ClosureRepair)', '^', C_NEU)}
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    for key, (lab, mk, col) in series.items():
        xs, ms, los, his = [], [], [], []
        for tag, n in tags:
            S = list(csv.DictReader(open(os.path.join(R, 'phase123', 'results', tag, 'sequences.csv'))))
            if key + '_total_ns' not in S[0]: continue
            m, lo, hi = boot([int(s[key + '_total_ns']) / int(s['mbr_total_ns']) for s in S])
            xs.append(n); ms.append(m); los.append(m - lo); his.append(hi - m)
        ax.errorbar(xs, ms, yerr=[los, his], marker=mk, color=col, label=lab, capsize=3, lw=1.2, ms=5)
    ax.axhline(1, color='black', lw=0.7, ls=':')
    ax.set_yscale('log'); ax.set_xlabel('number of hypotheses n'); ax.set_ylabel('speed-up of MBR (median, 95% CI)')
    ax.set_xticks([12, 16, 20, 24, 32, 40]); ax.grid(True, which='both', alpha=0.25); ax.legend(frameon=False, fontsize=8)
    save(fig, 'fig3_synthetic_scaling')

# ---------------- Figure 4 ----------------
def fig4():
    order = [('syn20', 'Syn. 20/28'), ('syn24', 'Syn. 24/36'), ('syn32', 'Syn. 32/44'), ('heart12', 'Real, 6 h'), ('heart16', 'Real, 8 h')]
    kinds = [('delay', 'delay'), ('safety', 'safety'), ('region', 'region')]
    labels, lz, lzlo, lzhi, eg = [], [], [], [], []
    for ds, dname in order:
        for k, kname in kinds:
            Rr = []
            for f in sorted(glob.glob(os.path.join(R, 'phase129', 'results', f'lazy_{ds}_{k}_*.csv'))): Rr += list(csv.DictReader(open(f)))
            m, lo, hi = boot([float(r['nocert_ns']) / float(r['lazy_ns']) for r in Rr])
            labels.append(f'{dname} – {kname}'); lz.append(m); lzlo.append(m - lo); lzhi.append(hi - m)
            eg.append(st.median([float(r['nocert_ns']) / float(r['eager_ns']) for r in Rr]))
    y = list(range(len(labels)))[::-1]
    fig, ax = plt.subplots(figsize=(5.6, 4.6))
    ax.errorbar(lz, y, xerr=[lzlo, lzhi], fmt='o', color=C_PROP, capsize=3, ms=5, label='lazy certificate (median, 95% CI)')
    ax.plot(eg, y, 'x', color=C_EST, ms=6, mew=1.5, label='eager certificate (median)')
    ax.axvline(1, color='black', lw=0.8, ls='--')
    ax.axhspan(-0.5, 5.5, color='#EEEEEE', zorder=0)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=7.8); ax.set_xscale('log')
    ax.set_xticks([0.4, 0.6, 1, 1.5, 2, 3]); ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_xlabel('time without certificate ÷ time with certificate  (> 1: certificate helps)')
    ax.text(0.41, 2.5, 'real data', fontsize=7.5, rotation=90, va='center', color='#555555')
    ax.legend(frameon=False, fontsize=7.8, loc='lower right'); ax.grid(True, axis='x', alpha=0.25)
    save(fig, 'fig4_certificate_isolation')

# ---------------- Figure 5 ----------------
def fig5():
    from heart import load, consistent, HeartInstance
    from mbr import BnB, INF
    Ds = list(range(8, 41))
    res = {}
    for reg in ('overlap', 'binary'):
        rows, _ = consistent(load(), reg)
        res[reg] = [BnB(HeartInstance(rows, D, reg, safe_num=99)).value for D in Ds]
    check = dict(zip(Ds, res['overlap']))
    assert abs(check[12] - 102.11) < 0.01 and abs(check[16] - 85.13) < 0.01 and abs(check[20] - 76.17) < 0.01 and abs(check[40] - 68.50) < 0.01
    assert abs(dict(zip(Ds, res['binary']))[16] - 122.59) < 0.01
    fig, ax = plt.subplots(figsize=(5.2, 3.3))
    for reg, lab, col, mk in (('overlap', 'overlapping regions {D,M}/{M,T}/{T}', C_EST, 'o'), ('binary', 'binary regions {D}/{T}', C_PROP, 's')):
        xs = [D / 2 for D, v in zip(Ds, res[reg]) if v < INF]; vs = [v for v in res[reg] if v < INF]
        ax.plot(xs, vs, marker=mk, ms=3.5, color=col, lw=1.2, label=lab)
        first = xs[0]; ax.axvline(first, color=col, lw=0.6, ls=':')
    ax.axvspan(3.8, min(D / 2 for D, v in zip(Ds, res['overlap']) if v < INF) - 0.25, color='#F2D7D5', alpha=0.6, lw=0)
    ax.text(4.78, 127, 'infeasible\n(certified)', fontsize=6.6, ha='center', va='top', color='#8B1A1A', zorder=5)
    ax.set_xlabel('decision deadline (hours)'); ax.set_ylabel('optimal expected test cost (CAD, 1992)')
    ax.set_xlim(3.8, 20.2); ax.grid(True, alpha=0.25); ax.legend(frameon=False, fontsize=7.8)
    save(fig, 'fig5_price_of_deadline')
    with open(os.path.join(OUT, 'fig5_data.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['deadline_half_hour_units', 'deadline_hours', 'overlap_value', 'binary_value'])
        for D, a, b in zip(Ds, res['overlap'], res['binary']): w.writerow([D, D / 2, a, b])

if __name__ == '__main__':
    fig1(); fig2(); fig3(); fig4(); fig5()
