# make_figs2.py — figures 5-8 for the scaled program. Same palette as make_figs.py.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
import numpy as np, json

SURF='#fcfcfb'; INK='#0b0b0b'; SEC='#52514e'; MUT='#898781'; GRID='#e1e0d9'; BASE='#c3c2b7'
S1='#2a78d6'; S2='#008300'; S3='#e87ba4'; S4='#eda100'
seq = LinearSegmentedColormap.from_list('seqblue',
    [SURF,'#cde2fb','#9ec5f4','#6da7ec','#3987e5','#256abf','#184f95','#0d366b'])
div = LinearSegmentedColormap.from_list('divbr',
    ['#104281','#5598e7','#f0efec','#e88a89','#a02a2a'])
plt.rcParams.update({
    'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF,
    'text.color': INK, 'axes.labelcolor': SEC, 'xtick.color': MUT, 'ytick.color': MUT,
    'axes.edgecolor': BASE, 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.7,
    'axes.spines.top': False, 'axes.spines.right': False,
    'font.family': 'sans-serif', 'font.size': 11, 'axes.titlesize': 12,
    'legend.frameon': False, 'lines.linewidth': 2.0,
})
root = '/private/tmp/claude-501/-Users-mike-Documents-Claude/325cb1ea-d772-429f-8fbb-7d3ef2b01dc0/scratchpad'

# ---------- Fig 5: projection law parity + theta collapse ----------
r3 = json.load(open(f'{root}/lattice/results_3d.json'))
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.6))
pts3 = r3['proj3d']; pts2 = r3['proj2d']; corner = r3['corner']
ax1.plot([1e-3, 1], [1e-3, 1], color=BASE, lw=1, zorder=1)
ax1.loglog([p['pred'] for p in pts3], [p['loss'] for p in pts3], 'o', color=S1,
           ms=7, mec=SURF, mew=1.0, label='3D tilted sweeps (24)', zorder=3)
ax1.loglog([p['pred'] for p in pts2], [p['loss'] for p in pts2], 's', color=S2,
           ms=7, mec=SURF, mew=1.0, label='2D tilted sweeps (6)', zorder=3)
ax1.loglog([c['indep'] for c in corner], [c['loss'] for c in corner], 'D', color=S3,
           ms=8, mec=SURF, mew=1.0, label='45° corner vs factorized (6)', zorder=3)
ax1.set_xlabel('predicted loss  exp(−πA²/4|b·Q̇|)  (corner: 1−(1−P₁)²)')
ax1.set_ylabel('measured loss (full solver)')
ax1.set_title('The projection law holds in every dimension')
ax1.legend(loc='upper left', fontsize=9.5)
# right: theta collapse for A=0.3 g=0.12
th = np.linspace(0, 32, 100)
sel = [p for p in pts3 if p['A'] == 0.3 and p['g'] == 0.12]
pred = np.exp(-np.pi * 0.3**2 / (4 * (0.12 * np.cos(np.radians(th)))))
ax2.plot(th, pred, color=S1)
ax2.plot([p['th'] for p in sel], [p['loss'] for p in sel], 'o', color=S1,
         ms=8, mec=SURF, mew=1.2)
ax2.annotate('only the normal\ncomponent b·Q̇ matters', xy=(20, 0.536), xytext=(2, 0.515),
             color=SEC, fontsize=10, arrowprops=dict(arrowstyle='->', color=MUT))
ax2.set_xlabel('sweep tilt θ from Bragg-plane normal (deg)')
ax2.set_ylabel('loss')
ax2.set_title('Oblique shuttles pay only cos θ  (A=0.3, g=0.12)')
fig.tight_layout(); fig.savefig(f'{root}/fig5_projection.png', dpi=150); plt.close(fig)

# ---------- Fig 6: 3D band structure ----------
fig, ax = plt.subplots(figsize=(7.6, 4.6))
ramp = ['#86b6ef', '#3987e5', '#104281']
for i, (Astr, Es) in enumerate(r3['bands'].items()):
    E = np.array(Es)
    xs = np.arange(len(E))
    for b in range(E.shape[1]):
        ax.plot(xs, E[:, b], color=ramp[i], lw=1.6,
                label=f'A = {Astr}' if b == 0 else None)
npts = (len(E) - 1) // 4
for j, lbl in zip(range(0, len(E), npts), ['Γ', 'X', 'M', 'R', 'Γ']):
    ax.axvline(j, color=GRID, lw=1, zorder=0)
    ax.text(j, ax.get_ylim()[0], lbl, color=SEC, ha='center', va='bottom', fontsize=11)
ax.set_xticks([])
ax.set_ylabel('band energy (natural units)')
ax.set_title('3D cubic-lattice bands along Γ–X–M–R–Γ (lattice3D.py)')
ax.legend(loc='upper left')
fig.tight_layout(); fig.savefig(f'{root}/fig6_bands3d.png', dpi=150); plt.close(fig)

# ---------- Fig 7: optimal ramps ----------
rr = json.load(open(f'{root}/lattice/ramp_results.json'))
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.4), gridspec_kw={'width_ratios': [1.4, 1]})
# rebuild best profile for display
T = rr['T']; Q_END = 6.0; edges = [1.0, 3.0, 5.0]
def profile(v_ratio, w, n=4000):
    Q = np.linspace(0, Q_END, n); s = np.ones_like(Q); sm = w / 6
    for e in edges:
        s += (v_ratio - 1) * 0.5 * (np.tanh((Q-(e-w/2))/sm) - np.tanh((Q-(e+w/2))/sm))
    t = np.concatenate([[0], np.cumsum(np.diff(Q)/s[:-1])]); t *= T/t[-1]
    return t, Q
t_bb, Q_bb = profile(rr['best']['v_ratio'], rr['best']['w'])
ax1.plot([0, T], [0, Q_END], color=S2)
ax1.plot(t_bb, Q_bb, color=S1)
for e in edges:
    ax1.axhline(e, color=GRID, lw=1, zorder=0)
ax1.annotate('linear', xy=(T*0.62, Q_END*0.62), color=S2, fontweight='bold',
             xytext=(8, -14), textcoords='offset points')
ax1.annotate('bang-bang:\nease through crossings,\nsprint between', xy=(T*0.35, Q_bb[len(Q_bb)//3]),
             xytext=(T*0.42, 1.0), color=S1, fontsize=10,
             arrowprops=dict(arrowstyle='->', color=MUT))
ax1.set_xlabel('time'); ax1.set_ylabel('frame momentum Q  (zone edges marked)')
ax1.set_title('Same start, same end, same total time')
scan = rr['scan']
losses = [rr['loss_linear']] + [s['loss'] for s in scan]
labels = ['linear'] + [f"{s['v_ratio']:.2f}/{s['w']:.1f}" for s in scan]
colors = [S2] + [S1] * len(scan)
best_i = int(np.argmin(losses))
ax2.bar(range(len(losses)), losses, color=colors, width=0.7)
ax2.set_yscale('log')
ax2.set_xticks(range(len(losses)))
ax2.set_xticklabels(labels, rotation=60, fontsize=7.5)
ax2.set_ylabel('total loss (log)')
ax2.set_title(f"Best bang-bang: {rr['best']['loss']*100:.2f}% vs linear "
              f"{rr['loss_linear']*100:.1f}%  ({rr['best']['improvement']:.0f}×)")
fig.tight_layout(); fig.savefig(f'{root}/fig7_ramps.png', dpi=150); plt.close(fig)

# ---------- Fig 8: gallery — quasicrystals, phase diversity, cloud survival ----------
qc = np.load(f'{root}/quasicrystal.npz')
pd_ = np.load(f'{root}/phase_diversity.npz')
cs = np.load(f'{root}/cloud_survival.npz')
fig, axes = plt.subplots(2, 3, figsize=(11.5, 7.4))
panels = [
    ('Pentagonal 5-beam: quasicrystal (r=4>e=2)', qc['V5'][200:700, 200:700], seq),
    ('Icosahedral slice: quasicrystal (r=6>e=3)', qc['Vico'][100:600, 100:600], seq),
    ('Redundant 4th beam on the integer lattice:\nstill periodic (his countable family)', qc['V4'], seq),
    ('True aberration phase (radians)', np.where(pd_['mask'], pd_['aberr'], np.nan), div),
    ('Recovered by phase diversity (fid. 0.99998)',
     np.where(pd_['mask'], np.angle(pd_['E_rec'] * np.exp(-1j*0)), np.nan), div),
    (None, None, None),
]
for ax, (title, img, cmap) in zip(axes.flat, panels):
    if title is None:
        # cloud survival radial profile
        ax.plot(cs['rb'], cs['prof_g'], color=S2)
        ax.plot(cs['rb'], cs['prof_f'], color=S1)
        ax.annotate('Gaussian beam', xy=(55, 0.42), color=S2, fontweight='bold', fontsize=9.5)
        ax.annotate('OT flat-top', xy=(8, 0.93), color=S1, fontweight='bold', fontsize=9.5)
        ax.set_xlabel('radius (px)'); ax.set_ylabel('shuttle survival')
        ax.set_title('Uniform depth rescues the cloud edge', fontsize=10.5)
        ax.set_xlim(0, 70); ax.set_ylim(0, 1.05)
        continue
    im = ax.imshow(img, cmap=cmap, interpolation='bilinear')
    ax.set_title(title, fontsize=10)
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for s_ in ax.spines.values(): s_.set_visible(False)
fig.suptitle('Roadmap items: quasicrystals by rank criterion · phase diversity · shaped-light shuttling', y=0.995)
fig.tight_layout(); fig.savefig(f'{root}/fig8_gallery.png', dpi=150); plt.close(fig)
print('figs 5-8 written')
