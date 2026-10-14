"""WGS-Kim fairness checks for benchmark_v050: hard-edged target, and fix_phase_iteration=30.

Rules out two excuses for Kim degrading on extended targets: the 1% tanh tail of the
smooth targets, and fixing the phase too early. Neither one is the cause.
"""
import os, sys
sys.path.insert(0, os.path.expanduser(os.environ.get("SLMSUITE_PATH", "~/code/_vendor/slmsuite-0.5.0"))); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, benchmark_v050 as b
from multiprocessing import Pool
def hard(cy, cx, half):
    y, x = b._grid(); return (np.maximum(np.abs(x-cx), np.abs(y-cy)) <= half).astype(np.float32)
orig = b.make_target
def mt(name, dy, dx):
    if name == "hard_offcenter": return hard(70+dy, -50+dx, 60)
    if name == "flattop_offcenter_fixphase30": return orig("flattop_offcenter", dy, dx)
    return orig(name, dy, dx)
b.make_target = mt
def job(j):
    if j["cfg"].endswith("fixphase30"):
        from slmsuite.holography.algorithms import _header
        _header.ALGORITHM_DEFAULTS["WGS-Kim"]["fix_phase_iteration"] = 30
    return b.run_arm(j)
J = [{"cfg": c, "seed": s, "method": "WGS-Kim", "arm": a, "iters": 100}
     for c in ("hard_offcenter", "flattop_offcenter_fixphase30") for s in range(2)
     for a in ("quadratic", "quadratic+rv", "ot")]
with Pool(8) as p:
    for r in p.imap(job, J):
        print(r["cfg"], r["seed"], r["arm"], "v", r["vortices"], "F %.3f rip %.3f" % (r["fidelity"], r["ripple"]), "F@10 %.3f F@30 %.3f" % (r["fid_trace"][10], r["fid_trace"][30]))
