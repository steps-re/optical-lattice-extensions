# run_3d.py — the 3D campaign.
# (a) Projection law: tilted sweeps theta in [0,30deg], loss vs exp(-pi A^2/(4 b.Qdot))
# (b) 2D points with the same protocol (d=2)
# (c) The 45-degree corner: simultaneous double crossing vs independent-crossings
# (d) 3D band structure along Gamma-X-M-R-Gamma
import numpy as np, json, time
from lattice3D import LatticeD, sweep_through_plane, bragg_projection_law
from scipy.sparse.linalg import eigsh

t00 = time.time()
out = {}

# ---------------- (a) 3D projection law ----------------
res = []
for A in (0.20, 0.30, 0.45):
    for g in (0.12, 0.24):
        lat = LatticeD(np.diag([2., 2., 2.]),
                       {(1, 0, 0): A, (0, 1, 0): A, (0, 0, 1): A}, n=3)
        for th in (0., 10., 20., 30.):
            # end before the b2 plane: t_b2/t_b1 = cot(theta)
            margin = min(1.6, 0.85 / max(np.tan(np.radians(th)), 1e-9))
            loss, pred, pops = sweep_through_plane(lat, A, g, th, n_t=1800, margin=margin)
            res.append(dict(d=3, A=A, g=g, th=th, loss=loss, pred=pred,
                            slew=float(2 * (g / 2) * np.cos(np.radians(th)))))
            print(f"3D A={A} g={g} th={th:4.1f}  loss={loss:.5f} pred={pred:.5f}", flush=True)
out['proj3d'] = res

# ---------------- (b) 2D points ----------------
res2 = []
for A in (0.25, 0.40):
    g = 0.15
    lat = LatticeD(np.diag([2., 2.]), {(1, 0): A, (0, 1): A}, n=5)
    for th in (0., 15., 30.):
        margin = min(1.6, 0.85 / max(np.tan(np.radians(th)), 1e-9))
        loss, pred, pops = sweep_through_plane(lat, A, g, th, n_t=2000, margin=margin)
        res2.append(dict(d=2, A=A, g=g, th=th, loss=loss, pred=pred,
                         slew=float(2 * (g / 2) * np.cos(np.radians(th)))))
        print(f"2D A={A} g={g} th={th:4.1f}  loss={loss:.5f} pred={pred:.5f}", flush=True)
out['proj2d'] = res2

# ---------------- (c) the 45-degree corner ----------------
corner = []
for A in (0.20, 0.30, 0.45):
    for g in (0.12, 0.24):
        lat = LatticeD(np.diag([2., 2., 2.]),
                       {(1, 0, 0): A, (0, 1, 0): A, (0, 0, 1): A}, n=3)
        loss, pred_single, pops = sweep_through_plane(lat, A, g, 45.0, n_t=2400, margin=1.5)
        # independent-crossings prediction: survive both planes independently
        P1 = bragg_projection_law(A, lat.B[0], g * np.array([np.cos(np.pi/4), np.sin(np.pi/4), 0]))
        indep = 1.0 - (1.0 - P1) ** 2          # survival (1-P1) per plane, two planes
        corner.append(dict(A=A, g=g, loss=loss, indep=float(indep), P1=float(P1)))
        print(f"corner A={A} g={g}  loss={loss:.5f} indep={indep:.5f}", flush=True)
out['corner'] = corner

# ---------------- (d) 3D band structure ----------------
def bands_path(A, n=3, npts=40, nb=4):
    lat = LatticeD(np.diag([2., 2., 2.]),
                   {(1, 0, 0): A, (0, 1, 0): A, (0, 0, 1): A}, n=n)
    G = np.zeros(3); X = np.array([1., 0., 0.]); M = np.array([1., 1., 0.]); R = np.array([1., 1., 1.])
    path = []
    for a, b in ((G, X), (X, M), (M, R), (R, G)):
        for s in np.linspace(0, 1, npts, endpoint=False):
            path.append(a + s * (b - a))
    path.append(G)
    Es = []
    for q in path:
        H = lat.hamiltonian(np.asarray(q))
        v = np.sort(eigsh(H, k=nb + 2, which='SA')[0])[:nb]
        Es.append(v.tolist())
    return Es

out['bands'] = {str(A): bands_path(A) for A in (0.15, 0.45, 0.90)}
print(f"total {time.time()-t00:.0f}s")
json.dump(out, open('results_3d.json', 'w'))
