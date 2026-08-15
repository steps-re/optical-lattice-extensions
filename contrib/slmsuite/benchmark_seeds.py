"""
Compare initial phases for Gerchberg-Saxton in slmsuite: random, quadratic, transport.

Everything runs through slmsuite's own Hologram and is scored with slmsuite's own
analysis.image_vortices, so the vortex numbers are not graded on a curve of my
choosing. Ripple and efficiency are my definitions and are stated below.

Answers the objections a maintainer would raise:

  equal wall clock   The transport seed costs seconds and the iterations cost
                     milliseconds, so a fixed iteration count flatters it. We
                     measure the seed, convert it to the number of extra
                     iterations it could have bought, and re-run the cheap seeds
                     with that budget.
  random baseline    slmsuite's _get_random_phase builds a fresh unseeded
                     default_rng on the numpy path, so a global seed does not
                     reach it. We generate random phase ourselves from a seeded
                     RNG and pass it as custom_phase, which makes it both
                     reproducible and repeatable over several draws.
  MRAF               Constructed here rather than in a side script.
  WGS-Kim control    fix_phase_iteration is the suspected cause of the WGS-Kim
                     behaviour, so we run it disabled as a control before
                     calling anything a bug.

Run: python benchmark_seeds.py
"""

import json
import time

import numpy as np

from slmsuite.holography import analysis
from slmsuite.holography.algorithms import Hologram

from transport_seed import transport_phase

SLM = 256
PAD = 512
WAIST = 60.0
MAXITER = 50
COARSE = 8
N_RANDOM_DRAWS = 5


def gaussian_amp():
    y, x = np.meshgrid(np.arange(SLM) - SLM / 2.0, np.arange(SLM) - SLM / 2.0, indexing="ij")
    return np.exp(-(x ** 2 + y ** 2) / WAIST ** 2).astype(np.float32)


def _floor(t, rel=0.01):
    """Clamp the tail to exactly zero.

    WGS divides by the target amplitude. slmsuite guards target == 0 and inf, but
    a smooth tail is tiny and NONZERO, and values around 1e-8 slip past both
    guards to become weights of order 1e8.
    """
    return np.where(t < t.max() * rel, 0.0, t).astype(np.float32)


def target_flattop(half=80.0, edge=6.0):
    y, x = np.meshgrid(np.arange(PAD) - PAD / 2.0, np.arange(PAD) - PAD / 2.0, indexing="ij")
    d = np.maximum(np.abs(x), np.abs(y)) - half
    return _floor(0.5 * (1 - np.tanh(d / edge)))


def target_ring(radius=90.0, width=10.0):
    y, x = np.meshgrid(np.arange(PAD) - PAD / 2.0, np.arange(PAD) - PAD / 2.0, indexing="ij")
    r = np.hypot(x, y)
    return _floor(np.exp(-((r - radius) ** 2) / width ** 2))


def to_mraf(target, guard=130.0):
    """slmsuite's documented don't-care region: NaN outside a guard box."""
    y, x = np.meshgrid(np.arange(PAD) - PAD / 2.0, np.arange(PAD) - PAD / 2.0, indexing="ij")
    out = target.astype(np.float32).copy()
    out[np.maximum(np.abs(x), np.abs(y)) >= guard] = np.nan
    return out


def support_of(target):
    """Signal region. Computed with nan-aware max so MRAF targets work."""
    m = np.nanmax(target)
    return np.nan_to_num(target, nan=0.0) > m * 0.5


def metrics(holo, support):
    """vortices: slmsuite's winding-number map, counted inside the support.
    ripple:    std/mean of farfield intensity inside the support (uniformity).
    efficiency: fraction of total farfield power inside the support.
    """
    ff = np.asarray(holo.get_farfield(get=True))
    I = np.abs(ff) ** 2
    I = I / I.sum()
    winding = np.asarray(analysis.image_vortices(np.angle(ff)))
    inside = I[support]
    return {
        "vortices": int(np.count_nonzero(winding[support])),
        "ripple": float(inside.std() / inside.mean()),
        "efficiency": float(inside.sum()),
    }


def seeded_random_phase(seed):
    """Reproducible random phase. slmsuite's own is unseeded on the numpy path."""
    rng = np.random.default_rng(seed)
    return rng.uniform(-np.pi, np.pi, (SLM, SLM)).astype(np.float32)


def run(target, seed_kind, method, maxiter, amp, phi_t=None, seed=0, flags=None):
    holo = Hologram(target=target, amp=amp, slm_shape=(SLM, SLM))
    if seed_kind == "random":
        holo.reset_phase(custom_phase=seeded_random_phase(seed))
    elif seed_kind == "quadratic":
        holo.reset_phase(quadratic_phase=True)
    else:
        holo.reset_phase(custom_phase=phi_t)
    if flags:
        holo.flags.update(flags)
    t0 = time.time()
    holo.optimize(method=method, maxiter=maxiter, verbose=False)
    return holo, time.time() - t0


def main():
    amp = gaussian_amp()
    results = {}

    for tname, base in (("flattop", target_flattop()), ("ring", target_ring())):
        for variant in ("plain", "MRAF"):
            target = base if variant == "plain" else to_mraf(base)
            support = support_of(target)
            key = f"{tname}/{variant}"
            results[key] = {}

            t0 = time.time()
            phi_t = transport_phase(
                np.nan_to_num(amp.astype(float) ** 2, nan=0.0),
                np.nan_to_num(target.astype(float) ** 2, nan=0.0),
                farfield_shape=(PAD, PAD), coarse=COARSE).astype(np.float32)
            t_seed = time.time() - t0

            for method in ("GS", "WGS-Leonardo", "WGS-Nogrette", "WGS-Wu",
                           "WGS-tanh", "WGS-Kim"):
                row = {}

                # random, several seeded draws
                draws = []
                for s in range(N_RANDOM_DRAWS):
                    h, dt = run(target, "random", method, MAXITER, amp, seed=s)
                    draws.append(metrics(h, support))
                row["random"] = {
                    k: {"mean": float(np.mean([d[k] for d in draws])),
                        "min": float(np.min([d[k] for d in draws])),
                        "max": float(np.max([d[k] for d in draws]))}
                    for k in ("vortices", "ripple", "efficiency")}

                h, dt_q = run(target, "quadratic", method, MAXITER, amp)
                row["quadratic"] = metrics(h, support)

                h, dt_t = run(target, "transport", method, MAXITER, amp, phi_t=phi_t)
                row["transport"] = metrics(h, support)
                row["t_seed_s"] = round(t_seed, 2)
                row["t_opt_s"] = round(dt_t, 3)

                # Equal wall clock: spend the seed's seconds on more iterations.
                per_iter = dt_q / MAXITER if dt_q > 0 else 1e-3
                eq_iter = int(MAXITER + t_seed / per_iter)
                row["equal_time_iters"] = eq_iter
                for kind in ("random", "quadratic"):
                    h, _ = run(target, kind, method, eq_iter, amp, seed=0)
                    row[f"{kind}_equal_time"] = metrics(h, support)

                # WGS-Kim control: is fix_phase_iteration the cause?
                if method == "WGS-Kim":
                    for kind in ("random", "quadratic", "transport"):
                        h, _ = run(target, kind, method, MAXITER, amp, phi_t=phi_t,
                                   flags={"fix_phase_iteration": 10 ** 6})
                        row[f"{kind}_nofixphase"] = metrics(h, support)

                results[key][method] = row
                r, q, t = row["random"], row["quadratic"], row["transport"]
                print(f"{key:<14} {method:<13} "
                      f"rand v{r['vortices']['mean']:6.1f} r{r['ripple']['mean']:7.3f} "
                      f"e{r['efficiency']['mean']:.3f} | "
                      f"quad v{q['vortices']:4d} r{q['ripple']:7.3f} e{q['efficiency']:.3f} | "
                      f"tran v{t['vortices']:4d} r{t['ripple']:7.3f} e{t['efficiency']:.3f} | "
                      f"eqT {eq_iter} it", flush=True)

    with open("benchmark_seeds.json", "w") as f:
        json.dump({"config": {"slm": SLM, "pad": PAD, "waist": WAIST,
                              "maxiter": MAXITER, "coarse": COARSE,
                              "random_draws": N_RANDOM_DRAWS},
                   "results": results}, f, indent=2)
    print("wrote benchmark_seeds.json")


if __name__ == "__main__":
    main()
