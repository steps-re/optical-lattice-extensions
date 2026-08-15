# cloud_survival.py — roadmap item 2: OT-shaped lattice light -> uniform LZ loss.
#
# The lattice depth is proportional to local beam intensity: A(r) ~ I(r).
# Under Gaussian illumination the cloud edge sits in a shallower lattice and
# tunnels out catastrophically faster (loss ~ exp(-const * I(r)^2)).
# Under the OT flat-top (from mraf_results.npz — the ACTUAL simulated beam,
# same total power) the depth is uniform, so the whole cloud survives alike.
#
# Survival per atom after N crossings: (1 - exp(-pi A(r)^2 / 2 k g))^N.
import numpy as np, json
from numpy.fft import fft2, fftshift, ifftshift

root = '/private/tmp/claude-501/-Users-mike-Documents-Claude/325cb1ea-d772-429f-8fbb-7d3ef2b01dc0/scratchpad'
m = np.load(f'{root}/mraf_results.npz')
d = np.load(f'{root}/ot_gs_results.npz')

N = 256
x = np.arange(N) - N/2
X, Y = np.meshgrid(x, x, indexing='ij')

# Two candidate lattice-illumination profiles, EQUAL POWER INTO THE CLOUD
# REGION r<40 (not equal total power — see normalization note below):
I_flat = m['If_ot'].astype(float)                  # the OT+GS flat-top we made
I_gauss_raw = np.exp(-2 * (X**2 + Y**2) / 60.0**2) # a lattice beam waist 60 px
# Normalize to equal power DELIVERED INTO the cloud region (r<40), isolating
# the uniformity physics from this reconstruction's shaper efficiency (the
# paper's production shaper delivers far more of the total into the signal).
_inside = (X**2 + Y**2) < 40.0**2
I_gauss = I_gauss_raw * (I_flat[_inside].sum() / I_gauss_raw[_inside].sum())

# Atom cloud: Gaussian density, sigma chosen to fill the flat-top (45 px half-width)
sigma_cloud = 18.0
rho = np.exp(-(X**2 + Y**2) / (2 * sigma_cloud**2)); rho /= rho.sum()

# Depth calibration: the FLAT-TOP PLATEAU depth = A0 (the design point); the
# equal-in-region-power Gaussian is then hotter at center, shallower at edge.
# Depth convention: A = coefficient of cos(kx) -> coupling A/2 ->
# P = exp(-pi A^2/2kg), the convention VALIDATED against the full solver in
# lz_sweep.py (24/24 points).
A0, k, g, Ncross = 0.50, 2.0, 0.0295 * 2, 3
I_ref = np.median(I_flat[d['core']])     # calibrate: plateau depth = A0

def survival(I_map):
    A = A0 * I_map / I_ref
    P = np.exp(-np.pi * A**2 / (2 * k * g))        # loss per crossing
    return (1 - P) ** Ncross                       # survival after N crossings

S_gauss = survival(I_gauss)
S_flat = survival(I_flat)
avg_gauss = float((rho * S_gauss).sum())
avg_flat = float((rho * S_flat).sum())

# Radial survival profiles for the figure
r = np.sqrt(X**2 + Y**2).ravel()
order = np.argsort(r)
def radial(Smap, nbin=60):
    rr = r[order]; ss = Smap.ravel()[order]
    bins = np.linspace(0, 80, nbin)
    idx = np.digitize(rr, bins)
    prof = [ss[idx == i].mean() if (idx == i).any() else np.nan for i in range(1, nbin)]
    return bins[1:], np.array(prof)

rb, prof_g = radial(S_gauss)
_, prof_f = radial(S_flat)
np.savez(f'{root}/cloud_survival.npz', rb=rb, prof_g=prof_g, prof_f=prof_f,
         S_gauss=S_gauss, S_flat=S_flat, rho=rho,
         avg_gauss=avg_gauss, avg_flat=avg_flat)
print(f"cloud-averaged shuttle survival ({Ncross} crossings, equal power into cloud region r<40):")
print(f"  Gaussian illumination: {avg_gauss:.3f}")
print(f"  OT flat-top          : {avg_flat:.3f}   ({avg_flat/avg_gauss:.2f}x)")
# Uniformity + worst-atom metrics (the flat-top's actual job)
inside = np.sqrt(X**2 + Y**2) < 40
def depth_cv(I_map):
    Avals = (A0 * I_map / I_ref)[inside]
    return float(np.std(Avals) / np.mean(Avals))
def worst_atom(Smap, pct=5):
    w = rho[inside]; s = Smap[inside]
    order = np.argsort(s); cw = np.cumsum(w[order]) / w.sum()
    return float(s[order][np.searchsorted(cw, pct / 100)])
print(f"  depth CV across cloud region: gauss {depth_cv(I_gauss)*100:.1f}% vs flat {depth_cv(I_flat)*100:.1f}%")
print(f"  worst-atom (5th pctile) survival: gauss {worst_atom(S_gauss):.3f} vs flat {worst_atom(S_flat):.3f}")
json.dump(dict(avg_gauss=avg_gauss, avg_flat=avg_flat, A0=A0, g=g, N=Ncross),
          open(f'{root}/cloud_survival.json', 'w'))
