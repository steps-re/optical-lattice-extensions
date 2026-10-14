"""Summarize benchmark_v050.json into the tables quoted on #206.

Run: python summarize_v050.py benchmark_v050.json > benchmark_v050.md
"""

import json
import sys
from collections import defaultdict

import numpy as np

d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "benchmark_v050.json"))
meta, R = d["meta"], d["results"]
it_max = meta["iters"]


def first(trace_f, trace_r, f_thr, r_thr):
    return next((k for k, (f, r) in enumerate(zip(trace_f, trace_r))
                 if f >= f_thr and r <= r_thr), None)


groups = defaultdict(list)
for r in R:
    groups[(r["cfg"], r["method"], r["arm"])].append(r)

# --- controls ---------------------------------------------------------------
print("# slmsuite 0.5.0: transport seed vs quadratic + remove_vortices\n")
print(f"slmsuite {meta['slmsuite_version']} ({meta['slmsuite_file']}), numpy {meta['numpy']}, "
      f"SLM {meta['SLM']}px, farfield {meta['PAD']}px, {it_max} iterations, "
      f"{meta['seeds']} seeds per config (target center jittered +-6 px, random phase reseeded), "
      f"{meta['workers']} single-threaded workers on {meta['cpu_count']} vCPU. "
      f"remove_vortices every {meta['rv_every']} iterations via the docstring callback.\n")

print("## controls\n")
nd = sum(not r["deterministic"] for r in R)
print(f"- runs whose timed and traced repeats disagreed: {nd} of {len(R)}")
same = diff = 0
for (cfg, m, arm), rs in groups.items():
    if m == "WGS-Leonardo" and arm == "quadratic+rv":
        base = {r["seed"]: r["final_phase_sha"] for r in groups[(cfg, m, "quadratic")]}
        for r in rs:
            same += base[r["seed"]] == r["final_phase_sha"]
            diff += base[r["seed"]] != r["final_phase_sha"]
print(f"- WGS-Leonardo quadratic+rv final phase bit-identical to quadratic: {same} of {same + diff}")
kd = sum(1 for (c, m, a), rs in groups.items() if m == "WGS-Kim" and a == "quadratic+rv"
         for r in rs if r["final_phase_sha"] != {x["seed"]: x["final_phase_sha"]
                                                 for x in groups[(c, m, "quadratic")]}[r["seed"]])
print(f"- WGS-Kim quadratic+rv final phase differs from quadratic: {kd} of "
      f"{sum(len(rs) for (c, m, a), rs in groups.items() if m == 'WGS-Kim' and a == 'quadratic+rv')}")
red = [(pre, post) for r in R if r["method"] == "WGS-Kim" and r["arm"] == "quadratic+rv"
       for (_, pre, post, fixed) in r["rv_effect"] if fixed]
if red:
    print(f"- WGS-Kim, phase fixed: vortices in stored phase_ff (target>0 mask) per removal call, "
          f"median {np.median([p for p, _ in red]):.0f} -> {np.median([q for _, q in red]):.0f}")
print()

# --- main table ---------------------------------------------------------------
THR = [(0.95, 0.20), (0.99, 0.10)]
print("## results (median over seeds, [min-max] for vortices)\n")
print("fidelity = slmsuite's computational overlap stat. ripple = std/mean of I/I_target in the "
      "50% support. time = seed + all iterations. to-threshold columns: iterations (and seconds "
      "incl. seed) until fidelity >= F and ripple <= r, `-` = not reached in "
      f"{it_max} its in any seed, `k/n` = reached in k of n seeds (median over those).\n")
hdr = ("| target | method | arm | vortices | fidelity | ripple | time s | "
       "its/s to F.95 r.20 | its/s to F.99 r.10 |")
print(hdr)
print("|" + "---|" * 9)
cfgs = list(dict.fromkeys(r["cfg"] for r in R))
order = ["random", "quadratic", "quadratic+rv", "ot", "ot+rv"]
for cfg in cfgs:
    for m in ("WGS-Leonardo", "WGS-Kim"):
        for arm in order:
            rs = groups.get((cfg, m, arm))
            if not rs:
                continue
            v = [r["vortices"] for r in rs]
            cells = []
            for f_thr, r_thr in THR:
                ks, ts = [], []
                for r in rs:
                    k = first(r["fid_trace"], r["rip_trace"], f_thr, r_thr)
                    if k is not None:
                        ks.append(k)
                        ts.append(r["seed_s"] + r["iters_s"] * min(k, it_max) / it_max)
                if not ks:
                    cells.append("-")
                else:
                    tag = "" if len(ks) == len(rs) else f" ({len(ks)}/{len(rs)})"
                    cells.append(f"{np.median(ks):.0f} / {np.median(ts):.1f}{tag}")
            print(f"| {cfg} | {m} | {arm} | {np.median(v):.0f} [{min(v)}-{max(v)}] | "
                  f"{np.median([r['fidelity'] for r in rs]):.3f} | "
                  f"{np.median([r['ripple'] for r in rs]):.3f} | "
                  f"{np.median([r['total_s'] for r in rs]):.1f} | {cells[0]} | {cells[1]} |")

# --- cost lines ---------------------------------------------------------------
print("\n## cost\n")
for arm, m in (("ot", "WGS-Leonardo"), ("quadratic", "WGS-Leonardo"),
               ("quadratic+rv", "WGS-Leonardo"), ("quadratic+rv", "WGS-Kim")):
    rs = [r for r in R if r["arm"] == arm and r["method"] == m]
    print(f"- {m} {arm}: seed {np.median([r['seed_s'] for r in rs]):.2f} s, "
          f"{it_max} iterations {np.median([r['iters_s'] for r in rs]):.2f} s (median)")
