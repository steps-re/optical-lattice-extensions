"""Is slmsuite's vortex-removal callback doing anything, and how does it compare?

Background. Issue #205 reported that `_remove_vortices` ran its removal inside
the `if plot:` branch, so the default call plotted and removed nothing. PR #207
(merged 2026-08-16, 42a9b4b) fixed that and made the method public. This script
checks what the fix bought when the method is used the way its docstring
documents it, as a `callback=` during a GS loop, and then runs the comparison
the maintainer asked for on #206.

Result, measured here: the callback is still a no-op in a plain GS loop. The
loop calls the callback right after nearfield -> farfield, then
`_gs_farfield_routines` recomputes `phase_ff` from the untouched farfield later
in the same iteration, which discards the correction. Writing the corrected
phase back into the farfield is enough to make it stick.

Requires slmsuite at or after 42a9b4b (public `remove_vortices`). Nothing here
patches the library, and it has to run against STOCK main for section 1 to mean
anything, since a patched library would make the "as shipped" row work too.

Run: PYTHONPATH=/path/to/slmsuite@42a9b4b python benchmark_callback.py
"""

import json
import time

import matplotlib
matplotlib.use("Agg")
import numpy as np

from slmsuite.holography import analysis
from slmsuite.holography.algorithms import Hologram

from benchmark_seeds import (MAXITER, PAD, SLM, gaussian_amp, support_of,
                             target_flattop, target_ring, to_mraf)
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


def plain_callback(holo):
    """slmsuite's documented snippet, verbatim."""
    if holo.iter % 10 == 9:
        holo.remove_vortices()


def writeback_callback(holo):
    """The same, plus the one line that makes the correction survive the loop."""
    if holo.iter % 10 == 9:
        holo.remove_vortices()
        if holo.phase_ff is not None:
            ff = holo.farfield
            np.multiply(np.abs(ff), np.exp(1j * holo.phase_ff), out=ff)


def trace_callback(holo, log):
    """Records what the removal did, and whether it was still there next time."""
    if holo.iter % 10 == 9:
        mask = np.asarray(holo.target) > 0
        before = np.array(holo.phase_ff, copy=True) if holo.phase_ff is not None else None
        holo.remove_vortices()
        if before is None:
            log.append((holo.iter, None, None))
            return
        after = np.array(holo.phase_ff, copy=True)
        count = lambda p: int(np.count_nonzero(np.asarray(analysis.image_vortices(p))[mask]))
        log.append((holo.iter, count(before), count(after)))


def main():
    amp = gaussian_amp()
    src2 = np.nan_to_num(amp.astype(float) ** 2, nan=0.0)
    configs = (("flattop", target_flattop()),
               ("flattop/MRAF", to_mraf(target_flattop())),
               ("ring/MRAF", to_mraf(target_ring())))
    out = {}

    # ------------- 1: does the documented callback change anything? ----------
    print("1. GS 50 iterations, quadratic seed, callback every 10 iterations\n")
    print(f"{'config':<16}{'callback':<20}{'vort':>6}{'ripple':>9}{'eff':>9}")
    one = {}
    for name, target in configs:
        support = support_of(target)
        one[name] = {}
        for label, cb in (("none", None),
                          ("as shipped", plain_callback),
                          ("+ farfield write-back", writeback_callback)):
            h = Hologram(target=target, amp=amp, slm_shape=(SLM, SLM))
            h.reset_phase(quadratic_phase=True)
            h.optimize(method="GS", maxiter=MAXITER, verbose=False, callback=cb)
            m = metrics(h, support)
            one[name][label] = m
            print(f"{name:<16}{label:<20}{m['vortices']:>6}{m['ripple']:>9.3f}"
                  f"{m['efficiency']:>9.3f}", flush=True)
        print()
    out["callback_effect"] = one

    # ------------- 2: the removal happens, it just does not survive ----------
    print("\n2. what each invocation does to phase_ff (flat-top, as shipped)\n")
    log = []
    h = Hologram(target=target_flattop(), amp=amp, slm_shape=(SLM, SLM))
    h.reset_phase(quadratic_phase=True)
    h.optimize(method="GS", maxiter=MAXITER, verbose=False,
               callback=lambda holo: trace_callback(holo, log))
    for it, before, after in log:
        if before is None:
            print(f"   iter {it:>3}: phase_ff was None, removal skipped")
        else:
            print(f"   iter {it:>3}: vortices in phase_ff {before} -> {after}, "
                  f"and back to ~{before} by the next call")
    out["trace"] = [{"iter": i, "before": b, "after": a} for i, b, a in log]

    # ------------- 3: the comparison asked for on #206 -----------------------
    print("\n\n3. transport seed vs quadratic + a removal that actually applies\n")
    print(f"{'config':<16}{'arm':<34}{'iters':>6}{'vort':>6}{'ripple':>9}"
          f"{'eff':>9}{'time':>9}")
    three = {}
    for name, target in configs:
        support = support_of(target)
        tgt2 = np.nan_to_num(target.astype(float) ** 2, nan=0.0)
        t0 = time.time()
        phi_t = transport_phase(src2, tgt2, farfield_shape=(PAD, PAD),
                                coarse=12, iters=40).astype(np.float32)
        t_seed = time.time() - t0
        three[name] = {}

        for label, seed, cb in (("quadratic", "quad", None),
                                ("quadratic + remove_vortices", "quad", writeback_callback),
                                ("transport seed", "ot", None),
                                ("transport + remove_vortices", "ot", writeback_callback)):
            h = Hologram(target=target, amp=amp, slm_shape=(SLM, SLM))
            if seed == "quad":
                h.reset_phase(quadratic_phase=True)
            else:
                h.reset_phase(custom_phase=phi_t)
            t1 = time.time()
            h.optimize(method="GS", maxiter=MAXITER, verbose=False, callback=cb)
            dt = time.time() - t1 + (t_seed if seed == "ot" else 0.0)
            m = metrics(h, support)
            three[name][label] = {**m, "time_s": round(dt, 2), "iters": MAXITER}
            print(f"{name:<16}{label:<34}{MAXITER:>6}{m['vortices']:>6}"
                  f"{m['ripple']:>9.3f}{m['efficiency']:>9.3f}{dt:>8.2f}s", flush=True)

        # the seed's cost, spent on extra iterations of the cheap arm instead
        h = Hologram(target=target, amp=amp, slm_shape=(SLM, SLM))
        h.reset_phase(quadratic_phase=True)
        probe = time.time()
        h.optimize(method="GS", maxiter=MAXITER, verbose=False, callback=writeback_callback)
        per_iter = (time.time() - probe) / MAXITER
        eq = int(MAXITER + t_seed / per_iter)
        h = Hologram(target=target, amp=amp, slm_shape=(SLM, SLM))
        h.reset_phase(quadratic_phase=True)
        t1 = time.time()
        h.optimize(method="GS", maxiter=eq, verbose=False, callback=writeback_callback)
        dt = time.time() - t1
        m = metrics(h, support)
        three[name]["quadratic + rv, equal wall clock"] = {**m, "time_s": round(dt, 2),
                                                           "iters": eq}
        print(f"{name:<16}{'quadratic + rv, equal wall clock':<34}{eq:>6}"
              f"{m['vortices']:>6}{m['ripple']:>9.3f}{m['efficiency']:>9.3f}"
              f"{dt:>8.2f}s\n", flush=True)
    out["head_to_head"] = three

    with open("benchmark_callback.json", "w") as f:
        json.dump(out, f, indent=2)
    print("wrote benchmark_callback.json")


if __name__ == "__main__":
    main()
