# make_figs.py — figures for the Swan work package. Palette: dataviz reference
# (light mode): surface #fcfcfb, ink #0b0b0b, secondary #52514e, muted #898781,
# grid #e1e0d9, series blue #2a78d6 / green #008300 / magenta #e87ba4,
# sequential blue ramp #cde2fb -> #0d366b.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import json, sys

SURF='#fcfcfb'; INK='#0b0b0b'; SEC='#52514e'; MUT='#898781'; GRID='#e1e0d9'; BASE='#c3c2b7'
S1='#2a78d6'; S2='#008300'; S3='#e87ba4'
seq = LinearSegmentedColormap.from_list('seqblue',
    [SURF,'#cde2fb','#9ec5f4','#6da7ec','#3987e5','#256abf','#184f95','#0d366b'])

plt.rcParams.update({
    'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF,
    'text.color': INK, 'axes.labelcolor': SEC, 'xtick.color': MUT, 'ytick.color': MUT,
    'axes.edgecolor': BASE, 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.7,
    'axes.spines.top': False, 'axes.spines.right': False,
    'font.family': 'sans-serif', 'font.size': 11, 'axes.titlesize': 12,
    'legend.frameon': False, 'lines.linewidth': 2.0,
})

root = '/private/tmp/claude-501/-Users-mike-Documents-Claude/325cb1ea-d772-429f-8fbb-7d3ef2b01dc0/scratchpad'

# ---------- Fig 1: LZ loss, his solver vs analytic ----------
lz = json.load(open(f'{root}/lattice/lz_results.json'))
aas = np.array(lz['aas']); gms = lz['gms']
colors = [S1, S2, S3]
fig, ax = plt.subplots(figsize=(7.2, 4.6))
aa_fine = np.linspace(aas[0], aas[-1], 200)
gSr = 0.029503  # runtime value from his module
for i, gm in enumerate(gms):
    ana = np.exp(-np.pi * (aa_fine*gSr)**2 / (2*2*gm*gSr))
    ax.plot(aa_fine, ana, color=colors[i], zorder=2)
    ax.plot(aas, lz['loss'][i], 'o', color=colors[i], ms=7, mec=SURF, mew=1.2, zorder=3)
    # direct label at the right end of each curve
    ax.annotate(f'a = {gm:.0f} g', xy=(aas[-1], lz['loss'][i][-1]),
                xytext=(6, 0), textcoords='offset points', color=colors[i],
                fontsize=10.5, fontweight='bold', va='center')
ax.set_yscale('log'); ax.set_ylim(1e-3, 1.3); ax.set_xlim(1, 28.5)
ax.set_xlabel('lattice depth  aa  (units of his default depth gSr)')
ax.set_ylabel('tunneling loss  1 − P(ground band)')
ax.set_title('Landau-Zener loss: Swan\'s psolver (dots) vs the reconstructed formula (lines)')
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([],[],color=SEC,marker='o',ls='',mec=SURF,label='his lattice1D.py solver'),
                   Line2D([],[],color=SEC,label='exp(−πA²/2kg)')], loc='lower left')
fig.tight_layout(); fig.savefig(f'{root}/fig1_lz.png', dpi=150); plt.close(fig)

# ---------- Fig 2: band structure & the avoided crossing ----------
sys.path.insert(0, f'{root}/lattice')
import bands
fig, ax = plt.subplots(figsize=(7.2, 4.6))
qs = np.linspace(-2, 2, 301)
depths = [5, 14, 23]
ramp = ['#86b6ef', '#3987e5', '#104281']   # ordinal steps 250/400/650
for d_i, aa in enumerate(depths):
    A = aa * gSr
    E = bands.eigeng1(qs, 2.0, A, 2, n=8)
    for b in range(2):
        ax.plot(qs, E[:, b], color=ramp[d_i],
                label=f'aa = {aa}' if b == 0 else None)
ax.axvline(1.0, color=GRID, lw=1, zorder=0)
ax.annotate('zone edge:\nLZ crossing', xy=(1.0, 1.05), xytext=(1.25, 0.45),
            color=SEC, fontsize=10, arrowprops=dict(arrowstyle='->', color=MUT))
ax.set_xlabel('quasimomentum q  (his units, k = 2)')
ax.set_ylabel('band energy  (natural units, ħ = 1, 2m = 1)')
ax.set_title('Two lowest bands from his bands.py — the gap at the zone edge is A')
ax.legend(loc='upper center', ncols=3)
ax.set_xlim(-2, 2); ax.set_ylim(-0.4, 4.2)
fig.tight_layout(); fig.savefig(f'{root}/fig2_bands.png', dpi=150); plt.close(fig)

# ---------- Fig 3: beam shaping gallery ----------
d = np.load(f'{root}/ot_gs_results.npz')
m = np.load(f'{root}/mraf_results.npz')
sl = slice(64, 192)  # crop to central 128 px for display
panels = [
    ('Target: flat-top square', d['I_T']),
    ('OT seed alone (no GS yet)', d['If_seed']),
    ('SLM phase: OT seed (smooth lens)', None),  # phase panel
    ('Random init + GS refine', m['If_rd']),
    ('OT seed + GS refine', m['If_ot']),
    ('SLM phase: random-init result', None),
]
fig, axes = plt.subplots(2, 3, figsize=(10.5, 7.0))
for ax, (title, img) in zip(axes.flat, panels):
    if img is None:
        ph = d['phi0'] if 'OT' in title else m['phi_rd']
        ax.imshow(np.mod(ph, 2*np.pi), cmap='gray', interpolation='nearest')
    else:
        im = img[sl, sl].astype(float)
        im = np.clip(im / np.percentile(im, 99.5), 0, 1)
        ax.imshow(im ** 0.7, cmap=seq, interpolation='nearest')
    ax.set_title(title, fontsize=10.5, color=INK)
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for s_ in ax.spines.values(): s_.set_visible(False)
fig.suptitle('Gaussian → flat-top with a phase-only SLM (Swan et al. arXiv:2408.17025 method)', y=0.99)
fig.tight_layout(); fig.savefig(f'{root}/fig3_beams.png', dpi=150); plt.close(fig)

# ---------- Fig 4: convergence + vortex maps ----------
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12.6, 4.2),
                                    gridspec_kw={'width_ratios': [1.5, 1, 1]})
it = np.arange(len(m['err_ot']))
ax1.plot(it, m['err_rd'], color=S2)
ax1.plot(it, m['err_ot'], color=S1)
ax1.annotate('random init', xy=(it[-1], m['err_rd'][-1]), xytext=(-8, 10),
             textcoords='offset points', ha='right', color=S2, fontweight='bold')
ax1.annotate('OT seed', xy=(it[-1], m['err_ot'][-1]), xytext=(-8, -14),
             textcoords='offset points', ha='right', color=S1, fontweight='bold')
ax1.set_yscale('log'); ax1.set_xlabel('GS iteration'); ax1.set_ylabel('relative L2 error (flat-top)')
ax1.set_title('Convergence')
summ = json.load(open(f'{root}/mraf_summary.json'))
for ax, key, ttl, col in ((ax2, 'If_ot', f"OT seed: {summ['nv_ot']} vortices", S1),
                          (ax3, 'If_rd', f"random: {summ['nv_rd']} vortices", S2)):
    If = m[key]; If = If / If.max()
    ax.imshow(If[sl, sl] ** 0.7, cmap=seq, interpolation='nearest')
    # overlay vortices recomputed from phase
    ph = np.angle(np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(
        np.exp(-(np.add.outer((np.arange(256)-128)**2,(np.arange(256)-128)**2))/52.0**2)
        * np.exp(1j * (m['phi_ot'] if key=='If_ot' else m['phi_rd']))))))
    wrap = lambda a: (a + np.pi) % (2*np.pi) - np.pi
    circ = (wrap(ph[1:, :-1]-ph[:-1, :-1]) + wrap(ph[1:, 1:]-ph[1:, :-1])
          + wrap(ph[:-1, 1:]-ph[1:, 1:]) + wrap(ph[:-1, :-1]-ph[:-1, 1:]))
    core = d['core']
    vy, vx = np.where((np.abs(circ) > np.pi) & core[:-1, :-1])
    keep = (vy >= sl.start) & (vy < sl.stop) & (vx >= sl.start) & (vx < sl.stop)
    ax.plot(vx[keep]-sl.start, vy[keep]-sl.start, 'o', ms=4, mfc='none', mec='#e34948', mew=1.1)
    ax.set_title(ttl, fontsize=11)
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for s_ in ax.spines.values(): s_.set_visible(False)
fig.tight_layout(); fig.savefig(f'{root}/fig4_convergence.png', dpi=150); plt.close(fig)
print('figures written')
