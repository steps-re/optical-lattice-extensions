# run_nonseparable.py — round-2 review response. The cubic campaign was
# separable (factorization by construction), so here: a TRUE minimal 2D
# lattice — 3 lasers, couplings cos(b1.x), cos(b2.x) AND the cross term
# cos((b1-b2).x) — which is NOT a Kronecker sum.
# (a) single-plane projection law under nonseparability: does the gap stay
#     set by the plane's own amplitude?
# (b) the zone corner: does plane-by-plane factorization survive?
# (c) margin (endpoint) convergence spot-check.
# (d) best bang-bang ramp: resolution + endpoint convergence.
import numpy as np, json, time
from lattice3D import LatticeD, sweep_through_plane, bragg_projection_law

t0 = time.time()
out = {}

def make_lat(A, n=6):
    # minimal 3-laser 2D lattice: equal amplitudes on b1, b2, b1-b2
    return LatticeD(np.diag([2., 2.]), {(1, 0): A, (0, 1): A, (1, -1): A}, n=n)

# ---------- (a) projection law, nonseparable ----------
res = []
for A in (0.25, 0.40):
    for g in (0.15, 0.30):
        lat = make_lat(A)
        for th in (0., 15., 30.):
            margin = min(1.6, 0.85 / max(np.tan(np.radians(th)), 1e-9))
            loss, pred, pops = sweep_through_plane(lat, A, g, th, n_t=2400, margin=margin)
            res.append(dict(A=A, g=g, th=th, loss=float(loss), pred=float(pred)))
            print(f"NS A={A} g={g} th={th:4.1f}  loss={loss:.5f} pred={pred:.5f} "
                  f"rel={(loss-pred)/pred:+.3f}", flush=True)
out['ns_proj'] = res

# ---------- (b) corner, nonseparable ----------
corner = []
for A in (0.25, 0.40):
    for g in (0.15, 0.30):
        lat = make_lat(A)
        loss, _, pops = sweep_through_plane(lat, A, g, 45.0, n_t=3000, margin=1.5)
        gv = g * np.array([np.cos(np.pi/4), np.sin(np.pi/4)])
        P1 = bragg_projection_law(A, lat.B[0], gv)
        fact = 1.0 - (1.0 - P1) ** 2
        corner.append(dict(A=A, g=g, loss=float(loss), fact=float(fact),
                           dev=float(loss - fact)))
        print(f"NS-corner A={A} g={g}  loss={loss:.5f} factorized={fact:.5f} "
              f"deviation={loss-fact:+.5f}", flush=True)
out['ns_corner'] = corner

# separable reference corners at the same params (same protocol, no cross term)
sep = []
for A in (0.25, 0.40):
    for g in (0.15, 0.30):
        lat = LatticeD(np.diag([2., 2.]), {(1, 0): A, (0, 1): A}, n=6)
        loss, _, pops = sweep_through_plane(lat, A, g, 45.0, n_t=3000, margin=1.5)
        gv = g * np.array([np.cos(np.pi/4), np.sin(np.pi/4)])
        P1 = bragg_projection_law(A, lat.B[0], gv)
        fact = 1.0 - (1.0 - P1) ** 2
        sep.append(dict(A=A, g=g, loss=float(loss), fact=float(fact),
                        dev=float(loss - fact)))
        print(f"SEP-corner A={A} g={g}  loss={loss:.5f} factorized={fact:.5f} "
              f"deviation={loss-fact:+.5f}", flush=True)
out['sep_corner'] = sep

# ---------- (c) margin convergence ----------
mconv = []
lat = make_lat(0.40)
for margin in (1.35, 1.6, 2.0, 2.6):
    loss, pred, _ = sweep_through_plane(lat, 0.40, 0.15, 0.0, n_t=3000, margin=margin)
    mconv.append(dict(margin=margin, loss=float(loss), pred=float(pred)))
    print(f"margin={margin}: loss={loss:.5f} (pred {pred:.5f})", flush=True)
out['margin_conv'] = mconv

# ---------- (d) ramp convergence + robustness ----------
import ramp_optimizer as ro
Q_END = ro.Q_END
best_v, best_w = 0.15, 0.5
rows = []
for nt, n in ((6000, 8), (12000, 12)):
    Q_of_t, _ = ro.build_traj(ro.Q_END / (np.pi * ro.A**2 / (4 * ro.k * (-np.log(0.13)))) , best_v, best_w)
    # rebuild with the same T as the campaign:
    Qdot_lin = np.pi * ro.A**2 / (4 * ro.k * (-np.log(0.13)))
    T = Q_END / Qdot_lin
    Q_of_t, _ = ro.build_traj(T, best_v, best_w)
    lat1 = LatticeD([[ro.k]], {(1,): ro.A}, n=n)
    c = lat1.evolve(np.zeros(1), None, T, nt=nt, Q_of_t=Q_of_t)
    pops = lat1.band_populations(c, np.zeros(1), Q=Q_of_t(T), nbands=3)
    rows.append(dict(nt=nt, n=n, loss=float(1 - pops[0])))
    print(f"ramp best (nt={nt}, n={n}): loss={1-pops[0]:.5f}", flush=True)
# independent-LZ estimate for the same profile (review finding: quote alongside)
v_s = None
# slow speed from the profile: measure minimum Qdot near an edge
Q_of_t, tq = ro.build_traj(T, best_v, best_w)
ts = np.linspace(0, T, 20000)
Qs = np.array([Q_of_t(t)[0] for t in ts])
dQdt = np.gradient(Qs, ts)
edgemask = np.abs((Qs % 2.0) - 1.0) < 0.05          # near zone edges Q=1,3,5
v_s = float(np.median(dQdt[edgemask]))
P_est = np.exp(-np.pi * ro.A**2 / (4 * ro.k * v_s))
indep = 1 - (1 - P_est) ** 3
rows.append(dict(v_s=v_s, indep_estimate=float(indep)))
print(f"independent-LZ estimate at measured crossing speed v_s={v_s:.5f}: {indep:.5f}", flush=True)
out['ramp_check'] = rows
json.dump(out, open('nonseparable_results.json', 'w'))
print(f"total {time.time()-t0:.0f}s")
