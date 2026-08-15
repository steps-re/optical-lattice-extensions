# fig9 — the nonseparable campaign (round-2 review response)
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np, json
SURF='#fcfcfb'; INK='#0b0b0b'; SEC='#52514e'; MUT='#898781'; GRID='#e1e0d9'; BASE='#c3c2b7'
S1='#2a78d6'; S2='#008300'; S3='#e87ba4'
plt.rcParams.update({'figure.facecolor':SURF,'axes.facecolor':SURF,'savefig.facecolor':SURF,
 'text.color':INK,'axes.labelcolor':SEC,'xtick.color':MUT,'ytick.color':MUT,
 'axes.edgecolor':BASE,'axes.grid':True,'grid.color':GRID,'grid.linewidth':0.7,
 'axes.spines.top':False,'axes.spines.right':False,'font.family':'sans-serif',
 'font.size':11,'axes.titlesize':12,'legend.frameon':False,'lines.linewidth':2.0})
r = json.load(open('lattice/nonseparable_results.json'))
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.4))
# left: relative excess loss vs theta for the nonseparable single-plane sweeps
for A, col in ((0.25, S1), (0.4, S2)):
    for g, mk in ((0.15, 'o'), (0.3, 's')):
        pts = [p for p in r['ns_proj'] if p['A'] == A and p['g'] == g]
        ax1.plot([p['th'] for p in pts], [100*(p['loss']-p['pred'])/p['pred'] for p in pts],
                 mk + '-', color=col, ms=7, mec=SURF, mew=1.0,
                 label=f"A={A}, g={g}")
ax1.axhline(0, color=BASE, lw=1)
ax1.set_xlabel('sweep tilt θ (deg)'); ax1.set_ylabel('excess loss over projection law (%)')
ax1.set_title('Minimal 3-laser lattice: the cross term dresses the crossing')
ax1.legend(fontsize=9)
# right: corner factorization deviation, separable vs nonseparable
labels = [f"A={c['A']}\ng={c['g']}" for c in r['ns_corner']]
x = np.arange(len(labels)); wdt = 0.38
ax2.bar(x - wdt/2, [c['dev'] for c in r['sep_corner']], wdt, color=S1, label='separable (reference)')
ax2.bar(x + wdt/2, [c['dev'] for c in r['ns_corner']], wdt, color=S3, label='nonseparable (minimal lasers)')
ax2.axhline(0, color=BASE, lw=1)
ax2.set_xticks(x); ax2.set_xticklabels(labels, fontsize=8.5)
ax2.set_ylabel('corner loss − factorized prediction')
ax2.set_title('Corner factorization: exact when separable, broken when not')
ax2.legend(fontsize=9)
fig.tight_layout(); fig.savefig('fig9_nonseparable.png', dpi=150); plt.close(fig)
print('fig9 written')
