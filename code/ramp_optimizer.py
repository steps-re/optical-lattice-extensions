# ramp_optimizer.py — loss-optimal shuttle ramps (roadmap item 1).
#
# Task: transfer the lattice frame momentum from Q=0 to Q=N*k (N zone-edge
# crossings at Q = k/2, 3k/2, ...) in FIXED total time T. The LZ formula says
# loss is paid only near crossings, at rate exp(-pi A^2/(4 k Qdot)); so the
# optimal profile slows to Qdot=v_s inside a window of width w around each
# crossing and sprints at v_f elsewhere ("bang-bang"), tanh-smoothed.
#
# We grid-search (v_s fraction, w) at fixed T and compare against the linear
# ramp, integrating the full Schrodinger equation with LatticeD (d=1).
import numpy as np, json, time
from lattice3D import LatticeD

k = 2.0
A = 0.35
N_CROSS = 3                    # sweep Q: 0 -> 3k, crossings at .5k, 1.5k, 2.5k
Q_END = N_CROSS * k
edges = (np.arange(N_CROSS) + 0.5) * k

def build_traj(T, v_ratio, w, n_grid=40000):
    """Speed profile v(Q): v_s in windows of width w around each edge, v_f
    elsewhere, tanh-smoothed; scaled so total time is exactly T.
    v_ratio = v_s / v_f. Returns Q_of_t callable."""
    Q = np.linspace(0, Q_END, n_grid)
    s = np.ones_like(Q)                     # relative speed, f=1 fast
    sm = w / 6.0
    for e in edges:
        s += (v_ratio - 1.0) * 0.5 * (np.tanh((Q - (e - w/2)) / sm)
                                      - np.tanh((Q - (e + w/2)) / sm))
    t_of_Q = np.concatenate([[0.0], np.cumsum(np.diff(Q) / s[:-1])])
    t_of_Q *= T / t_of_Q[-1]                # normalize duration to T
    def Q_of_t(t):
        return np.array([np.interp(t, t_of_Q, Q)])
    v_slow = (Q[1] - Q[0]) / np.diff(t_of_Q).min()  # not used, diagnostic
    return Q_of_t, t_of_Q

def run_traj(Q_of_t, T, nt=6000):
    lat = LatticeD([[k]], {(1,): A}, n=8)
    q = np.zeros(1)
    c = lat.evolve(q, None, T, nt=nt, Q_of_t=Q_of_t)
    pops = lat.band_populations(c, q, Q=Q_of_t(T), nbands=3)
    return 1.0 - pops[0], pops

if __name__ == '__main__':
    t0 = time.time()
    # Choose T so the linear ramp hurts: linear Qdot = Q_END/T; pick loss ~ 30%
    # exp(-pi A^2/(4 k Qdot)) per crossing.
    Qdot_lin = np.pi * A**2 / (4 * k * (-np.log(0.13)))       # 13% loss/crossing
    T = Q_END / Qdot_lin
    print(f"T = {T:.1f}  (linear Qdot = {Qdot_lin:.4f}), A={A}, {N_CROSS} crossings")

    lin_Q = lambda t: np.array([Q_END * t / T])
    loss_lin, pops = run_traj(lin_Q, T)
    per_cross = np.exp(-np.pi * A**2 / (4 * k * Qdot_lin))
    pred_lin = 1 - (1 - per_cross) ** N_CROSS
    print(f"linear ramp: loss={loss_lin:.5f}  (independent-LZ pred {pred_lin:.5f})", flush=True)

    results = dict(T=float(T), A=A, k=k, N=N_CROSS,
                   loss_linear=float(loss_lin), pred_linear=float(pred_lin), scan=[])
    best = None
    for v_ratio in (0.5, 0.35, 0.25, 0.15):
        for w in (0.5, 0.8, 1.2):
            Q_of_t, tq = build_traj(T, v_ratio, w)
            loss, pops = run_traj(Q_of_t, T)
            # analytic prediction for this profile
            v_s_eff = None
            row = dict(v_ratio=v_ratio, w=w, loss=float(loss))
            results['scan'].append(row)
            tag = ''
            if best is None or loss < best[0]:
                best = (loss, v_ratio, w); tag = '  <-- best'
            print(f"bang-bang v_s/v_f={v_ratio:4.2f} w={w:3.1f}: loss={loss:.5f}{tag}", flush=True)
    results['best'] = dict(loss=float(best[0]), v_ratio=best[1], w=best[2],
                           improvement=float(results['loss_linear'] / best[0]))
    print(f"\nBEST: loss={best[0]:.5f} vs linear {loss_lin:.5f} "
          f"-> {loss_lin/best[0]:.1f}x lower loss at equal time  ({time.time()-t0:.0f}s)")
    json.dump(results, open('ramp_results.json', 'w'))
