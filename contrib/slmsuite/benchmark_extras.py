"""
The three controls a maintainer would ask for next.

  A  vs _remove_vortices   slmsuite's existing remedy for the same problem. If
                           their callback fixes vortices at lower cost, the seed
                           is not worth adding, so this is the decisive control.
  B  cost frontier         The seed costs 17-24 s, which is the main objection.
                           Sinkhorn dominates it, and the defaults were chosen for
                           accuracy we do not need in a seed. Find the cheap end.
  C  threshold sensitivity Vortex counts and efficiency are measured inside
                           target > half max. That threshold is arbitrary, so
                           check the conclusion does not depend on it.

Run: python benchmark_extras.py
"""

import json
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from slmsuite.holography import analysis
from slmsuite.holography.algorithms import Hologram

from benchmark_seeds import (COARSE, MAXITER, PAD, SLM, gaussian_amp,
                             seeded_random_phase, support_of, target_flattop,
                             target_ring, to_mraf)
from transport_seed import transport_phase


def metrics(holo, support):
    ff = np.asarray(holo.get_farfield(get=True))
    I = np.abs(ff) ** 2
    I = I / I.sum()
    winding = np.asarray(analysis.image_vortices(np.angle(ff)))
    inside = I[support]
    return {"vortices": int(np.count_nonzero(winding[support])),
            "ripple": float(inside.std() / inside.mean()),
            "efficiency": float(inside.sum())}


def seed_phase(kind, holo, phi_t, seed=0):
    if kind == "random":
        holo.reset_phase(custom_phase=seeded_random_phase(seed))
    elif kind == "quadratic":
        holo.reset_phase(quadratic_phase=True)
    else:
        holo.reset_phase(custom_phase=phi_t)


# _remove_vortices calls plot_farfield unconditionally, outside its `if plot:`
# block, so every invocation renders a figure. Measured: 34.2 ms per call as
# shipped versus unmeasurably small with the plot suppressed, against 6.4 ms for
# a GS iteration. Benchmarking their remedy at its shipped cost would be unfair
# to them, since a one-line fix removes it, so we neutralise the plotting and
# compare against the callback at its true cost.
_ORIG_PLOT = Hologram.plot_farfield
Hologram.plot_farfield = lambda self, *a, **k: None


def devortex_callback(holo):
    """slmsuite's own documented pattern, every 10 iterations.

    Their docstring example calls holo.remove_vortices(), which does not exist on
    Hologram (only the private _remove_vortices does), so the documented snippet
    raises AttributeError as written. We call the private method.
    """
    if holo.iter % 10 == 9:
        holo._remove_vortices()
        plt.close("all")


def main():
    amp = gaussian_amp()
    out = {}

    # ---------------- A: against their existing remedy --------------------
    print("A. transport seed vs slmsuite's _remove_vortices callback\n")
    print(f"{'config':<16}{'seed':<11}{'callback':<10}{'iters':>6}{'vort':>6}"
          f"{'ripple':>9}{'eff':>8}{'time':>8}")
    A = {}
    for cfg, target in (("flattop", target_flattop()),
                        ("flattop/MRAF", to_mraf(target_flattop())),
                        ("ring/MRAF", to_mraf(target_ring()))):
        support = support_of(target)
        t0 = time.time()
        phi_t = transport_phase(
            np.nan_to_num(amp.astype(float) ** 2, nan=0.0),
            np.nan_to_num(target.astype(float) ** 2, nan=0.0),
            farfield_shape=(PAD, PAD), coarse=COARSE).astype(np.float32)
        t_seed = time.time() - t0
        A[cfg] = {}

        for kind in ("random", "quadratic", "transport"):
            for cb in (False, True):
                if kind == "transport" and cb:
                    continue
                h = Hologram(target=target, amp=amp, slm_shape=(SLM, SLM))
                seed_phase(kind, h, phi_t)
                t1 = time.time()
                h.optimize(method="GS", maxiter=MAXITER, verbose=False,
                           callback=devortex_callback if cb else None)
                dt = time.time() - t1 + (t_seed if kind == "transport" else 0.0)
                m = metrics(h, support)
                A[cfg][f"{kind}{'+devortex' if cb else ''}"] = {**m, "time_s": round(dt, 2)}
                print(f"{cfg:<16}{kind:<11}{'yes' if cb else 'no':<10}{MAXITER:>6}"
                      f"{m['vortices']:>6}{m['ripple']:>9.3f}{m['efficiency']:>8.3f}"
                      f"{dt:>7.1f}s", flush=True)

        # and their remedy given the seed's whole time budget
        h = Hologram(target=target, amp=amp, slm_shape=(SLM, SLM))
        seed_phase("quadratic", h, phi_t)
        probe = time.time()
        h.optimize(method="GS", maxiter=MAXITER, verbose=False, callback=devortex_callback)
        per_iter = (time.time() - probe) / MAXITER
        eq = int(MAXITER + t_seed / per_iter)
        h = Hologram(target=target, amp=amp, slm_shape=(SLM, SLM))
        seed_phase("quadratic", h, phi_t)
        t1 = time.time()
        h.optimize(method="GS", maxiter=eq, verbose=False, callback=devortex_callback)
        dt = time.time() - t1
        m = metrics(h, support)
        A[cfg]["quadratic+devortex_equal_time"] = {**m, "time_s": round(dt, 2), "iters": eq}
        print(f"{cfg:<16}{'quadratic':<11}{'yes':<10}{eq:>6}{m['vortices']:>6}"
              f"{m['ripple']:>9.3f}{m['efficiency']:>8.3f}{dt:>7.1f}s   <- equal time\n",
              flush=True)
    out["vs_remove_vortices"] = A

    # ---------------- B: how cheap can the seed get? -----------------------
    print("\nB. seed cost frontier (flat-top, GS 50 iters)\n")
    print(f"{'coarse':>7}{'sink_iters':>12}{'seed_s':>9}{'vort':>6}{'ripple':>9}{'eff':>8}")
    B = []
    target = target_flattop()
    support = support_of(target)
    src2 = amp.astype(float) ** 2
    tgt2 = target.astype(float) ** 2
    for coarse in (8, 12, 16):
        for iters in (300, 100, 40):
            t0 = time.time()
            phi = transport_phase(src2, tgt2, farfield_shape=(PAD, PAD),
                                  coarse=coarse, iters=iters).astype(np.float32)
            ts = time.time() - t0
            h = Hologram(target=target, amp=amp, slm_shape=(SLM, SLM))
            h.reset_phase(custom_phase=phi)
            h.optimize(method="GS", maxiter=MAXITER, verbose=False)
            m = metrics(h, support)
            B.append({"coarse": coarse, "iters": iters, "seed_s": round(ts, 2), **m})
            print(f"{coarse:>7}{iters:>12}{ts:>8.1f}s{m['vortices']:>6}"
                  f"{m['ripple']:>9.3f}{m['efficiency']:>8.3f}", flush=True)
    out["cost_frontier"] = B

    # ---------------- C: does the threshold change the story? --------------
    print("\nC. support-threshold sensitivity (flat-top, GS 50 iters)\n")
    print(f"{'thresh':>8}{'random v':>10}{'quad v':>9}{'transport v':>13}"
          f"{'quad eff':>10}{'tran eff':>10}")
    C = []
    t0 = time.time()
    phi_t = transport_phase(src2, tgt2, farfield_shape=(PAD, PAD),
                            coarse=COARSE).astype(np.float32)
    holos = {}
    for kind in ("random", "quadratic", "transport"):
        h = Hologram(target=target, amp=amp, slm_shape=(SLM, SLM))
        seed_phase(kind, h, phi_t)
        h.optimize(method="GS", maxiter=MAXITER, verbose=False)
        holos[kind] = h
    for th in (0.05, 0.1, 0.25, 0.5, 0.75, 0.9):
        sup = np.nan_to_num(target, nan=0.0) > np.nanmax(target) * th
        row = {"threshold": th}
        for kind, h in holos.items():
            row[kind] = metrics(h, sup)
        C.append(row)
        print(f"{th:>8}{row['random']['vortices']:>10}{row['quadratic']['vortices']:>9}"
              f"{row['transport']['vortices']:>13}{row['quadratic']['efficiency']:>10.3f}"
              f"{row['transport']['efficiency']:>10.3f}", flush=True)
    out["threshold_sensitivity"] = C

    with open("benchmark_extras.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote benchmark_extras.json")


if __name__ == "__main__":
    main()
