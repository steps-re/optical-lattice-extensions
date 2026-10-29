"""slmsuite's gradient method ("CG", torch Adam) on the benchmark_v050 targets.

Answers the follow-up on holodyne/slmsuite#206: Ian pointed out that conjugate-gradient
optimization often beats WGS on top hats. This reuses benchmark_v050's targets, metrics,
seeds and jitter unchanged, and swaps the refinement method for slmsuite's own "CG"
(default loss ComplexMSELoss, optimizer Adam) at a few learning rates.

Arms: random, quadratic, ot (same seeds as benchmark_v050). Method strings carry the
learning rate, e.g. "CG@0.1" runs method="CG" with optimizer_kwargs={"lr": 0.1}.

Run:
  SLMSUITE_PATH=~/code/_vendor/slmsuite-0.5.0 python benchmark_cg.py --workers 8
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import benchmark_v050 as b  # noqa: E402  (sets thread env vars and SLMSUITE_PATH first)


class LrHologram(b.Hologram):
    """Lets a job's method string carry the CG learning rate through run_arm unchanged."""

    def optimize(self, method="GS", **kw):
        if method.startswith("CG@"):
            kw["optimizer_kwargs"] = {"lr": float(method[3:])}
            method = "CG"
        return super().optimize(method=method, **kw)


b.Hologram = LrHologram


def jobs(configs, seeds, iters, lrs, arms):
    return [{"cfg": cfg, "seed": seed, "method": f"CG@{lr}", "arm": arm, "iters": iters}
            for cfg in configs for seed in range(seeds) for lr in lrs for arm in arms]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", default=",".join(b.CONFIGS))
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--iters", type=int, default=300)
    ap.add_argument("--lrs", default="0.03,0.1,0.3")
    ap.add_argument("--arms", default="random,quadratic,ot")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--out", default="benchmark_cg.json")
    a = ap.parse_args()

    if b.slmsuite.__version__ != "0.5.0":
        sys.exit(f"refusing to run: slmsuite {b.slmsuite.__version__} at {b.slmsuite.__file__}")
    import torch
    print(f"slmsuite {b.slmsuite.__version__} from {b.slmsuite.__file__}, torch {torch.__version__}",
          flush=True)

    todo = jobs(a.configs.split(","), a.seeds, a.iters, a.lrs.split(","), a.arms.split(","))
    t0 = time.time()
    results = []

    def report(i, r):
        results.append(r)
        print(f"[{i}/{len(todo)}] {r['cfg']} s{r['seed']} {r['method']} {r['arm']}: "
              f"v={r['vortices']} F={r['fidelity']:.3f} rip={r['ripple']:.3f} "
              f"t={r['total_s']:.1f}s", flush=True)

    if a.workers > 1:
        from multiprocessing import Pool
        with Pool(a.workers) as pool:
            for i, r in enumerate(pool.imap_unordered(b.run_arm, todo), 1):
                report(i, r)
    else:
        for i, j in enumerate(todo, 1):
            report(i, b.run_arm(j))

    meta = {"slmsuite_version": b.slmsuite.__version__, "slmsuite_file": b.slmsuite.__file__,
            "torch": torch.__version__, "numpy": b.np.__version__, "SLM": b.SLM, "PAD": b.PAD,
            "WAIST": b.WAIST, "coarse": b.COARSE, "ot_iters": b.OT_ITERS, "iters": a.iters,
            "seeds": a.seeds, "lrs": a.lrs, "workers": a.workers, "cpu_count": os.cpu_count(),
            "wall_s": time.time() - t0}
    with open(a.out, "w") as f:
        json.dump({"meta": meta, "results": results}, f)
    print(f"wrote {a.out} in {meta['wall_s']:.0f}s")


if __name__ == "__main__":
    main()
