# mraf.py — MRAF refinement (amplitude constrained only in the signal region)
# from the cached OT seed vs random init. Signal region = flat-top + margin.
import numpy as np
from numpy.fft import fft2, ifft2, fftshift, ifftshift
import json

d = np.load('ot_gs_results.npz')
I_T, supp, core, phi0 = d['I_T'], d['supp'], d['core'], d['phi0']
N = I_T.shape[0]
x = np.arange(N) - N/2
X, Y = np.meshgrid(x, x, indexing='ij')
a_in = np.exp(-(X**2 + Y**2) / 52.0**2)
S = I_T > I_T.max() * 1e-3                 # signal region (flat-top + skirt)
m = 0.45
rng = np.random.default_rng(7)

def farfield(phi):
    return fftshift(fft2(ifftshift(a_in * np.exp(1j * phi))))

def mraf(phi_init, n_iter=300):
    # NOTE: this is a RELAXED SIGNAL-REGION PROJECTION, not canonical MRAF
    # (canonical MRAF weights the noise region, not the signal region). We
    # report results under this name honestly; the m-mix inside S damps the
    # projection to avoid stagnation.
    phi = phi_init.copy(); errs = []
    sq = np.sqrt(I_T)
    def measure(p):
        If = np.abs(farfield(p))**2
        Ifs = If * (I_T[S].sum() / If[S].sum())
        return float(np.linalg.norm((Ifs - I_T)[supp]) / np.linalg.norm(I_T[supp]))
    for _ in range(n_iter):
        errs.append(measure(phi))
        Ef = farfield(phi)
        If = np.abs(Ef)**2
        sqn = sq * np.sqrt(If[S].sum() / I_T[S].sum())   # power-matched target amplitude
        mixed = m * sqn + (1 - m) * np.abs(Ef)           # relaxed signal projection
        out = np.where(S, mixed * np.exp(1j*np.angle(Ef)), Ef)
        E = fftshift(ifft2(ifftshift(out)))
        phi = np.angle(E)
    errs.append(measure(phi))                            # metric of the RETURNED phi
    return phi, np.array(errs)

def count_vortices(phi):
    th = np.angle(farfield(phi))
    wrap = lambda a: (a + np.pi) % (2*np.pi) - np.pi
    circ = (wrap(th[1:, :-1]-th[:-1, :-1]) + wrap(th[1:, 1:]-th[1:, :-1])
          + wrap(th[:-1, 1:]-th[1:, 1:]) + wrap(th[:-1, :-1]-th[:-1, 1:]))
    return int(((np.abs(circ) > np.pi) & core[:-1, :-1]).sum())

def ripple(phi):
    If = np.abs(farfield(phi))**2
    c = If[core]; return float(np.std(c)/np.mean(c))

phi_ot, err_ot = mraf(phi0)
# statistics over 5 independent random baselines (round-2 review finding)
rd_runs = [mraf(rng.uniform(-np.pi, np.pi, (N, N))) for _ in range(5)]
rd_errs = [float(r[1][-1]) for r in rd_runs]
med_i = int(np.argsort(rd_errs)[len(rd_errs) // 2])
phi_rd, err_rd = rd_runs[med_i]                      # median baseline for figures
print(f"random baselines (5 seeds), final errors: {sorted(round(e,4) for e in rd_errs)}")
eff = lambda phi: float((lambda If: If[supp].sum()/If.sum())(np.abs(farfield(phi))**2))
print(f"MRAF final error: OT {err_ot[-1]:.4f} vs random {err_rd[-1]:.4f}")
print(f"ripple: OT {ripple(phi_ot):.4f} vs random {ripple(phi_rd):.4f}")
print(f"vortices in core: OT {count_vortices(phi_ot)} vs random {count_vortices(phi_rd)}")
print(f"efficiency: OT {eff(phi_ot):.3f} vs random {eff(phi_rd):.3f}")
np.savez('mraf_results.npz', phi_ot=phi_ot, phi_rd=phi_rd, err_ot=err_ot, err_rd=err_rd,
         If_ot=np.abs(farfield(phi_ot))**2, If_rd=np.abs(farfield(phi_rd))**2)
json.dump({'err_ot': float(err_ot[-1]), 'err_rd': float(err_rd[-1]),
           'ripple_ot': ripple(phi_ot), 'ripple_rd': ripple(phi_rd),
           'nv_ot': count_vortices(phi_ot), 'nv_rd': count_vortices(phi_rd),
           'eff_ot': eff(phi_ot), 'eff_rd': eff(phi_rd)}, open('mraf_summary.json','w'))
