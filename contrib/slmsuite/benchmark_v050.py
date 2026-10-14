"""Transport seed vs quadratic + remove_vortices, against slmsuite 0.5.0 as released.

Answers the question on holodyne/slmsuite#206: is the optimal-transport seed better than
quadratic + remove_vortices with the removal actually applied, and does its compute time
pay for itself in faster convergence?

What "actually applied" means in 0.5.0. The released `Hologram.remove_vortices` docstring
says the removal only persists where the farfield phase is held fixed, as in WGS-Kim.
Every other GS-family method recomputes `phase_ff` from the farfield right after the
callback returns. So this script runs two refinement families:

  WGS-Kim       the removal is live (after the phase fixes at fix_phase_iteration=10)
  WGS-Leonardo  the removal is a documented no-op, kept as a control arm that must come
                out bit-identical to plain quadratic

Arms (same refinement method and the same iteration budget inside each family):
  random        seeded uniform phase passed as custom_phase
  quadratic     reset_phase(quadratic_phase=True), slmsuite's lens + blaze
  quadratic+rv  quadratic, plus the docstring's callback (remove_vortices every 10 its)
  ot            transport_phase() seed, then the same refinement
  ot+rv         transport seed plus the same callback (WGS-Kim only)

Metrics, all on the padded computational farfield:
  vortices    slmsuite.holography.analysis.image_vortices, counted inside the support
  fidelity    slmsuite's own computational "efficiency" stat: the normalized overlap
              (sum sqrt(I_target) sqrt(I))^2, NaN (MRAF) region excluded
  ripple      std/mean of I / I_target inside the support (50% of target max). The
              ratio, not raw intensity: raw std/mean also counts the target's own
              shape (a tanh edge, a Gaussian ring profile), which floors it near 0.2
              even for a perfect hologram
  in_support  fraction of total farfield power inside the support
Time is wall clock including the seed. Iterations- and seconds-to-threshold use a per-
iteration trace of fidelity and ripple from a second, untimed run of the same arm.

Run (pin the library explicitly, the script refuses anything but 0.5.0):
  SLMSUITE_PATH=~/code/_vendor/slmsuite-0.5.0 python benchmark_v050.py --workers 8
"""

import argparse
import json
import os
import sys
import time

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

_lib = os.environ.get("SLMSUITE_PATH")
if _lib:
    sys.path.insert(0, os.path.expanduser(_lib))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import numpy as np  # noqa: E402

import slmsuite  # noqa: E402
from slmsuite.holography import analysis  # noqa: E402
from slmsuite.holography.algorithms import Hologram  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transport_seed import transport_phase  # noqa: E402

SLM, PAD, WAIST = 256, 512, 60.0
COARSE, OT_ITERS = 12, 40  # cost-knob setting from the earlier sweep
RV_EVERY = 10
FID_THR, RIP_THR = 0.95, 0.20  # primary threshold, fixed before the full run (0.99/0.10 also derived from traces)


# ----------------------------------------------------------------------------- targets
def _grid():
    return np.meshgrid(np.arange(PAD) - PAD / 2.0, np.arange(PAD) - PAD / 2.0, indexing="ij")


def _floor(t, rel=0.01):
    """WGS divides by the target. A smooth tail of 1e-8 slips past slmsuite's zero guard."""
    return np.where(t < t.max() * rel, 0.0, t).astype(np.float32)


def flattop(cy, cx, half, edge=6.0):
    y, x = _grid()
    d = np.maximum(np.abs(x - cx), np.abs(y - cy)) - half
    return _floor(0.5 * (1 - np.tanh(d / edge)))


def ring(cy, cx, radius, width):
    y, x = _grid()
    return _floor(np.exp(-((np.hypot(x - cx, y - cy) - radius) ** 2) / width ** 2))


def twobars(cy, cx):
    """Two separated bars: a disconnected target, where a transport map is discontinuous."""
    y, x = _grid()
    a = np.maximum(np.abs(x - cx) - 70, np.abs(y - (cy - 45)) - 15)
    b = np.maximum(np.abs(x - cx) - 70, np.abs(y - (cy + 45)) - 15)
    return _floor(0.5 * (1 - np.tanh(np.minimum(a, b) / 4.0)))


def mraf(target, cy=0.0, cx=0.0, guard=130.0):
    """slmsuite's don't-care region: NaN outside a guard box around the pattern."""
    y, x = _grid()
    out = target.astype(np.float32).copy()
    out[np.maximum(np.abs(x - cx), np.abs(y - cy)) >= guard] = np.nan
    return out


def make_target(name, dy, dx):
    """dy, dx: per-seed jitter of the pattern center, so deterministic seeds still vary."""
    if name == "flattop_center":
        return flattop(dy, dx, 80)
    if name == "flattop_offcenter":
        return flattop(70 + dy, -50 + dx, 60)
    if name == "flattop_small_offcenter":
        return flattop(-80 + dy, 60 + dx, 30)
    if name == "ring_mraf_center":
        return mraf(ring(dy, dx, 90, 10), dy, dx)
    if name == "ring_offcenter":
        return ring(60 + dy, 60 + dx, 50, 8)
    if name == "twobars_offcenter":
        return twobars(-40 + dy, 30 + dx)
    raise KeyError(name)


CONFIGS = ("flattop_center", "flattop_offcenter", "flattop_small_offcenter",
           "ring_mraf_center", "ring_offcenter", "twobars_offcenter")


def gaussian_amp():
    y, x = np.meshgrid(np.arange(SLM) - SLM / 2.0, np.arange(SLM) - SLM / 2.0, indexing="ij")
    return np.exp(-(x ** 2 + y ** 2) / WAIST ** 2).astype(np.float32)


def support_of(target):
    return np.nan_to_num(target, nan=0.0) > np.nanmax(target) * 0.5


# ----------------------------------------------------------------------------- metrics
def field_metrics(ff, target, support):
    I = np.abs(ff) ** 2
    I = I / I.sum()
    T = np.nan_to_num(np.asarray(target, dtype=float), nan=0.0) ** 2
    valid = ~np.isnan(target)
    T = T / T.sum()
    fid = float(np.sum(np.sqrt(T[valid] * I[valid])) ** 2)  # slmsuite's normalization
    ratio = I[support] / T[support]
    return fid, float(ratio.std() / ratio.mean()), float(I[support].sum())


def final_metrics(holo, target, support):
    ff = np.asarray(holo.get_farfield(get=True))
    fid, rip, eff = field_metrics(ff, target, support)
    winding = np.asarray(analysis.image_vortices(np.angle(ff)))
    return {"vortices": int(np.count_nonzero(winding[support])),
            "fidelity": fid, "ripple": rip, "in_support": eff}


def rv_callback(holo):
    if holo.iter % RV_EVERY == RV_EVERY - 1:
        holo.remove_vortices()


# ----------------------------------------------------------------------------- one run
def run_arm(job):
    cfg, seed, method, arm, iters = job["cfg"], job["seed"], job["method"], job["arm"], job["iters"]
    rng = np.random.default_rng(1000 + seed)
    dy, dx = rng.uniform(-6, 6, 2)
    target = make_target(cfg, dy, dx)
    support = support_of(target)
    amp = gaussian_amp()

    # seed, timed
    t0 = time.perf_counter()
    if arm.startswith("ot"):
        src2 = amp.astype(float) ** 2
        tgt2 = np.nan_to_num(target.astype(float), nan=0.0) ** 2
        phi = transport_phase(src2, tgt2, farfield_shape=(PAD, PAD),
                              coarse=COARSE, iters=OT_ITERS).astype(np.float32)
    elif arm == "random":
        phi = np.random.default_rng(seed).uniform(-np.pi, np.pi, (SLM, SLM)).astype(np.float32)
    else:
        phi = None
    t_seed_compute = time.perf_counter() - t0

    use_rv = arm.endswith("+rv")

    def fresh():
        h = Hologram(target=target, amp=amp, slm_shape=(SLM, SLM))
        t = time.perf_counter()
        if phi is None:
            h.reset_phase(quadratic_phase=True)
        else:
            h.reset_phase(custom_phase=phi)
        return h, time.perf_counter() - t

    # timed run: only the arm's own callback plus a timestamp
    h, t_reset = fresh()
    stamps = []

    def timed_cb(holo):
        stamps.append(time.perf_counter())
        if use_rv:
            rv_callback(holo)

    t1 = time.perf_counter()
    h.optimize(method=method, maxiter=iters, verbose=False, callback=timed_cb, stat_groups=[])
    t_iters = time.perf_counter() - t1
    fin = final_metrics(h, target, support)
    final_phase = np.asarray(h.phase).copy()
    seed_time = t_seed_compute + t_reset
    cum = [s - t1 for s in stamps]  # cum[k] ~ time when the result of k updates is visible

    # traced run: same arm, per-iteration fidelity/ripple, not timed
    h2, _ = fresh()
    trace = []
    rv_effect = []

    def trace_cb(holo):
        trace.append(field_metrics(np.asarray(holo.farfield), target, support)[:2])
        if use_rv and holo.iter % RV_EVERY == RV_EVERY - 1 and holo.phase_ff is not None:
            mask = np.asarray(holo.target) > 0
            pre = int(np.count_nonzero(np.asarray(analysis.image_vortices(holo.phase_ff))[mask]))
            holo.remove_vortices()
            post = int(np.count_nonzero(np.asarray(analysis.image_vortices(holo.phase_ff))[mask]))
            rv_effect.append((holo.iter, pre, post, bool(holo.flags.get("fixed_phase", False))))

    h2.optimize(method=method, maxiter=iters, verbose=False, callback=trace_cb, stat_groups=[])
    deterministic = bool(np.array_equal(np.asarray(h2.phase), final_phase))
    trace.append(field_metrics(np.asarray(h2.get_farfield(get=True)), target, support)[:2])

    k_thr = next((k for k, (f, r) in enumerate(trace) if f >= FID_THR and r <= RIP_THR), None)
    if k_thr is None:
        t_thr = None
    elif k_thr < len(cum):
        t_thr = seed_time + cum[k_thr]
    else:
        t_thr = seed_time + t_iters

    return {**job, "jitter": [float(dy), float(dx)], **fin,
            "seed_s": seed_time, "iters_s": t_iters, "total_s": seed_time + t_iters,
            "iters_to_thr": k_thr, "s_to_thr": t_thr,
            "fid_trace": [round(f, 5) for f, _ in trace],
            "rip_trace": [round(r, 5) for _, r in trace],
            "rv_effect": rv_effect, "deterministic": deterministic,
            "final_phase_sha": __import__("hashlib").sha1(final_phase.tobytes()).hexdigest()}


def jobs(configs, seeds, iters):
    out = []
    for cfg in configs:
        for seed in range(seeds):
            for method, arms in (("WGS-Kim", ("random", "quadratic", "quadratic+rv", "ot", "ot+rv")),
                                 ("WGS-Leonardo", ("random", "quadratic", "quadratic+rv", "ot"))):
                for arm in arms:
                    out.append({"cfg": cfg, "seed": seed, "method": method,
                                "arm": arm, "iters": iters})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", default=",".join(CONFIGS))
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--iters", type=int, default=100)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--out", default="benchmark_v050.json")
    a = ap.parse_args()

    if slmsuite.__version__ != "0.5.0":
        sys.exit(f"refusing to run: slmsuite {slmsuite.__version__} at {slmsuite.__file__}")
    print(f"slmsuite {slmsuite.__version__} from {slmsuite.__file__}", flush=True)

    todo = jobs(a.configs.split(","), a.seeds, a.iters)
    t0 = time.time()
    results = []
    if a.workers > 1:
        from multiprocessing import Pool
        with Pool(a.workers) as pool:
            for i, r in enumerate(pool.imap_unordered(run_arm, todo), 1):
                results.append(r)
                print(f"[{i}/{len(todo)}] {r['cfg']} s{r['seed']} {r['method']} {r['arm']}: "
                      f"v={r['vortices']} F={r['fidelity']:.3f} rip={r['ripple']:.3f} "
                      f"t={r['total_s']:.1f}s", flush=True)
    else:
        for i, j in enumerate(todo, 1):
            r = run_arm(j)
            results.append(r)
            print(f"[{i}/{len(todo)}] {r['cfg']} s{r['seed']} {r['method']} {r['arm']}: "
                  f"v={r['vortices']} F={r['fidelity']:.3f} rip={r['ripple']:.3f} "
                  f"t={r['total_s']:.1f}s", flush=True)

    meta = {"slmsuite_version": slmsuite.__version__, "slmsuite_file": slmsuite.__file__,
            "numpy": np.__version__, "SLM": SLM, "PAD": PAD, "WAIST": WAIST,
            "coarse": COARSE, "ot_iters": OT_ITERS, "rv_every": RV_EVERY,
            "fid_thr": FID_THR, "rip_thr": RIP_THR, "iters": a.iters, "seeds": a.seeds,
            "workers": a.workers, "cpu_count": os.cpu_count(),
            "wall_s": time.time() - t0}
    with open(a.out, "w") as f:
        json.dump({"meta": meta, "results": results}, f)
    print(f"wrote {a.out} in {meta['wall_s']:.0f}s")


if __name__ == "__main__":
    main()
