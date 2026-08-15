# lz_sweep.py — run Hunter Swan's moving-lattice solver (lattice1D.py) through a
# Landau-Zener sweep and compare measured tunneling loss against the analytic
# LZ formula P = exp(-pi A^2 / (2 k g)) from the reconstruction of his
# unfinished "Shuttling and Landau-Zener tunnelling" section.
#
# Physics setup (all in his natural units hbar=1, 2m=1):
#   - Static 1D lattice (accel=0, vel=0), gravity g = gm*gSr drags quasimomentum:
#     Q(t) = g t / 2  (his HParams: p_g = grav*t/2)
#   - Lattice wavenumber k = k1 - k2 = 2. First zone-edge crossing at Q = k/2 = 1,
#     i.e. t_cross = 2/g.
#   - Lattice depth A = aa * Etyp^2/(2 dtn0) = aa * gSr  (his A(t) formula).
#   - Loss = 1 - (ground-band population after the crossing), measured by
#     projecting the evolved state onto static-lattice band eigenstates
#     via his SFrame(..., band=[0]).
import matplotlib
matplotlib.use('Agg')
import numpy as np
import time, json, sys
import lattice1D as l1

k = 2.0           # lattice wavenumber in his units (k1=1, k2=-1)
gSr = l1.gSr      # runtime value from his module

def run_one(aa, gm, n=6, nT=60, talk=False):
    """One gravity-driven sweep through the first zone edge. Returns loss."""
    g = gm * gSr
    t_cross = 2.0 / g          # Q(t_cross) = 1 = k/2
    t_end = 1.6 * t_cross      # comfortably past the crossing
    T = np.linspace(0.0, t_end, nT)
    c, p, h = l1.avUniform(accel=0., vel=0., grav=gSr, gm=gm, aa=aa,
                           T=T, n=n, init=0, ret='cph', plt='', talk=False)
    drift = l1.checkUnitarity(c)
    # Project final state onto band eigenstates (his SFrame with band arg)
    pops = l1.SFrame(c[-1], p[-1], h, T[-1], band=[0, 1, 2])
    loss = 1.0 - pops[0]
    return loss, pops, drift

def lz_analytic(aa, gm):
    A = aa * gSr
    g = gm * gSr
    return np.exp(-np.pi * A**2 / (2.0 * k * g))

if __name__ == '__main__':
    t0 = time.time()
    gms = [2.0, 4.0, 8.0]
    aas = np.arange(2.0, 26.0, 3.0)
    out = {'gms': gms, 'aas': aas.tolist(), 'loss': [], 'analytic': [], 'drift': []}
    for gm in gms:
        row_l, row_a, row_d = [], [], []
        for aa in aas:
            loss, pops, drift = run_one(aa, gm)
            row_l.append(float(loss)); row_a.append(float(lz_analytic(aa, gm)))
            row_d.append(float(drift))
            print(f"gm={gm:4.1f} aa={aa:5.1f}  loss={loss:8.5f}  LZ={row_a[-1]:8.5f}  "
                  f"pops={np.round(pops,4)}  drift={drift:.1e}", flush=True)
        out['loss'].append(row_l); out['analytic'].append(row_a); out['drift'].append(row_d)
    print(f"total {time.time()-t0:.1f}s")
    json.dump(out, open('lz_results.json', 'w'))
