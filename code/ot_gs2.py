# ot_gs.py — Optimal-transport-seeded Gerchberg-Saxton beam shaping,
# implementing the algorithm of Swan et al., Opt. Express 33, 6290 (2025)
# (arXiv:2408.17025) from the paper's description, and demonstrating it against
# a random-initialization GS baseline on a ring target.
#
# Pipeline:
#   1. Coarse-grid entropic OT (log-domain Sinkhorn) between the input Gaussian
#      intensity and the target far-field intensity, cost |x-u|^2.
#   2. Barycentric transport map -> curl-free potential psi via a Poisson solve
#      (DCT / Neumann), phi0 = scaled psi  (vortex-free by construction:
#      Brenier's theorem, T = grad(convex psi)).
#   3. GS refinement at full resolution from phi0 vs from random phase.
#   4. Metrics: relative L2 intensity error on the target support, efficiency,
#      and vortex count (2pi phase windings on plaquettes inside the support).
import numpy as np
from numpy.fft import fft2, ifft2, fftshift, ifftshift
from scipy.fft import dctn, idctn
from scipy.interpolate import RectBivariateSpline
import json, time

rng = np.random.default_rng(7)

# ---------------- geometry ----------------
N = 256          # fine grid (SLM and far field)
s = 4            # coarse factor
Nc = N // s      # coarse grid for OT
w_in = 52.0      # input Gaussian 1/e^2-ish waist in SLM pixels

xf = np.arange(N) - N/2
Xf, Yf = np.meshgrid(xf, xf, indexing='ij')
a_in = np.exp(-(Xf**2 + Yf**2) / w_in**2)                 # input amplitude
I_in_f = a_in**2

# Target: smoothed flat-top square, half-width 45 px, 5 px edge (atom-trap beam)
dist = np.maximum(np.abs(Xf), np.abs(Yf)) - 45.0
I_T = 0.5 * (1 - np.tanh(dist / 5.0))
I_T /= I_T.sum()
supp = I_T > I_T.max() * 0.5                               # the flat-top itself
core = I_T > I_T.max() * 0.8                               # bright core (vortex metric)

def farfield(phi):
    """Forward model, matching hologram.jl's `ft`: centered FFT of a_in e^{i phi}."""
    E = a_in * np.exp(1j * phi)
    return fftshift(fft2(ifftshift(E)))

# ---------------- 1. Sinkhorn OT on the coarse grid ----------------
def downsample(a):
    return a.reshape(Nc, s, Nc, s).mean(axis=(1, 3))

I_in_c = downsample(I_in_f)
I_T_c = downsample(I_T)
xc = np.arange(Nc) * s + (s - 1) / 2.0 - N/2               # true block centers in fine px
Xc, Yc = np.meshgrid(xc, xc, indexing='ij')

src = I_in_c > I_in_c.max() * 1e-3
tgt = I_T_c > I_T_c.max() * 1e-3
mu = I_in_c[src]; mu /= mu.sum()                           # source weights
nu = I_T_c[tgt]; nu /= nu.sum()                            # target weights
xs = np.stack([Xc[src], Yc[src]], 1)                       # source points (fine-px units)
ut = np.stack([Xc[tgt], Yc[tgt]], 1)                       # target points (fine-px units)
print(f"OT problem: {len(mu)} source x {len(nu)} target points", flush=True)

C = ((xs[:, None, :] - ut[None, :, :])**2).sum(-1)         # squared distance cost
C /= C.max()

def sinkhorn_log(mu, nu, C, eps_list=(0.05, 0.02, 0.008, 0.003, 0.001), iters=300):
    f = np.zeros(len(mu)); g = np.zeros(len(nu))
    lmu = np.log(mu); lnu = np.log(nu)
    for eps in eps_list:
        for _ in range(iters):
            # f-update: f = -eps*logsumexp((g - C)/eps + lnu)
            M = (g[None, :] - C) / eps + lnu[None, :]
            f = -eps * (np.logaddexp.reduce(M, axis=1))
            M = (f[:, None] - C) / eps + lmu[:, None]
            g = -eps * (np.logaddexp.reduce(M, axis=0))
    # transport plan (dense, coarse -> fine barycentric map)
    P = np.exp((f[:, None] + g[None, :] - C) / eps_list[-1] + lmu[:, None] + lnu[None, :])
    return P

t0 = time.time()
P = sinkhorn_log(mu, nu, C)
row = P.sum(1, keepdims=True)
T_map = (P @ ut) / row                                     # barycentric map: source pt -> far-field px
err_marg = np.abs(P.sum(1) - mu).sum()
print(f"Sinkhorn {time.time()-t0:.1f}s, marginal err {err_marg:.2e}", flush=True)

# ---------------- 2. Curl-free potential via Poisson solve ----------------
# Required gradient on the fine grid: dphi/dx_fine = 2*pi*u_fine/N.
# Build the (masked) target-displacement field on the coarse grid, fill outside
# the source mask by nearest neighbor, take divergence, solve Neumann Poisson via DCT.
gx = np.zeros((Nc, Nc)); gy = np.zeros((Nc, Nc))
gx[src] = 2*np.pi * T_map[:, 0] / N                        # gradient per FINE pixel
gy[src] = 2*np.pi * T_map[:, 1] / N
# nearest-neighbor fill outside the source mask
from scipy.ndimage import distance_transform_edt
idx = distance_transform_edt(~src, return_distances=False, return_indices=True)
gx = gx[tuple(idx)]; gy = gy[tuple(idx)]

# divergence (per coarse px step = s fine px)
div = (np.gradient(gx, axis=0) + np.gradient(gy, axis=1)) * s
# Neumann Poisson: laplacian(psi) = div, via DCT-II
d = dctn(div, type=2, norm='ortho')
kxc = np.pi * np.arange(Nc) / Nc
lam = (2*np.cos(kxc)[:, None] - 2) + (2*np.cos(kxc)[None, :] - 2)
lam[0, 0] = 1.0
psi_c = idctn(np.where(lam != 0, d / lam, 0.0), type=2, norm='ortho')  # d already carries s^2 (index-Laplacian)
psi_c -= psi_c.mean()

# interpolate to the fine grid
sp = RectBivariateSpline(xc, xc, psi_c)
phi0 = sp(xf, xf)
print("OT seed phase built", flush=True)

# ---------------- 3. GS refinement ----------------
def gs(phi_init, n_iter=200):
    phi = phi_init.copy()
    errs, effs = [], []
    sqrt_IT = np.sqrt(I_T)
    def measure(p):
        If_n = np.abs(farfield(p))**2
        If_n = If_n / If_n.sum()
        return (np.linalg.norm((If_n - I_T)[supp]) / np.linalg.norm(I_T[supp]),
                If_n[supp].sum())
    for _ in range(n_iter):
        e_, f_ = measure(phi); errs.append(e_); effs.append(f_)
        Ef = farfield(phi)
        Ef = sqrt_IT * np.exp(1j * np.angle(Ef))           # target-plane constraint
        E = fftshift(ifft2(ifftshift(Ef)))
        phi = np.angle(E)                                  # SLM-plane constraint
    e_, f_ = measure(phi); errs.append(e_); effs.append(f_)  # metrics of the RETURNED phi
    return phi, np.array(errs), np.array(effs)

def count_vortices(phi):
    """2pi windings on plaquettes of the far-field phase inside the support."""
    Ef = farfield(phi)
    th = np.angle(Ef)
    def wrap(a):
        return (a + np.pi) % (2*np.pi) - np.pi
    circ = (wrap(th[1:, :-1] - th[:-1, :-1]) + wrap(th[1:, 1:] - th[1:, :-1])
            + wrap(th[:-1, 1:] - th[1:, 1:]) + wrap(th[:-1, :-1] - th[:-1, 1:]))
    v = np.abs(circ) > np.pi
    m = core[:-1, :-1]
    return int((v & m).sum()), v & m

t0 = time.time()
phi_ot, err_ot, eff_ot = gs(phi0)
phi_rd, err_rd, eff_rd = gs(rng.uniform(-np.pi, np.pi, (N, N)))
print(f"GS x2 {time.time()-t0:.1f}s", flush=True)

nv_ot, vmap_ot = count_vortices(phi_ot)
nv_rd, vmap_rd = count_vortices(phi_rd)
nv_seed, _ = count_vortices(phi0)
def ripple(phi):
    If = np.abs(farfield(phi))**2; If /= If.sum()
    c = If[core]; return float(np.std(c) / np.mean(c))
reached = np.nonzero(err_ot <= err_rd[-1])[0]
it_cross = int(reached[0]) if len(reached) else -1         # -1 = never reached
print(f"seed-only error {err_ot[0]:.4f} | final: OT {err_ot[-1]:.4f} vs random {err_rd[-1]:.4f}")
print(f"OT-seeded run reaches random's FINAL error at iteration {it_cross} of 200")
print(f"flat-top ripple (RMS/mean): OT {ripple(phi_ot):.3f} vs random {ripple(phi_rd):.3f}")
print(f"efficiency (power on target support): OT {eff_ot[-1]:.3f} vs random {eff_rd[-1]:.3f}")
print(f"vortices in support: OT-seed(before GS) {nv_seed}, OT-seeded {nv_ot}, random {nv_rd}")

np.savez('ot_gs_results.npz',
         I_T=I_T, supp=supp, core=core, phi0=phi0, phi_ot=phi_ot, phi_rd=phi_rd,
         If_ot=np.abs(farfield(phi_ot))**2, If_rd=np.abs(farfield(phi_rd))**2,
         If_seed=np.abs(farfield(phi0))**2,
         err_ot=err_ot, err_rd=err_rd, eff_ot=eff_ot, eff_rd=eff_rd,
         vmap_ot=vmap_ot, vmap_rd=vmap_rd, nv=[nv_seed, nv_ot, nv_rd])
json.dump({'err_ot': float(err_ot[-1]), 'err_rd': float(err_rd[-1]),
           'eff_ot': float(eff_ot[-1]), 'eff_rd': float(eff_rd[-1]),
           'ripple_ot': ripple(phi_ot), 'ripple_rd': ripple(phi_rd), 'it_cross': it_cross, 'nv_seed': nv_seed, 'nv_ot': nv_ot, 'nv_rd': nv_rd},
          open('ot_gs_summary.json', 'w'))
