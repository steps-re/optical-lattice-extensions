"""How much of the farfield does the top hat have to fill before the seed matters?

The maintainer's two objections on slmsuite #205/#206:

  (a) the best top-hat results are limited to a small fraction of the farfield,
      where there are fewer speckle degrees of freedom for the SLM to fight, so
      check that our top hat is a comparable fraction to whatever we compare to.
  (b) WGS-Kim's fixed-phase step is tuned for spot arrays, not image holograms,
      and may be hurting us. Try the other WGS variants.

Both are testable, so this sweeps the top-hat size across two decades of
farfield fraction and runs every variant at each size, quadratic vs transport.

Run: PYTHONPATH=/path/to/slmsuite@42a9b4b python benchmark_topsize.py
"""

import json

import matplotlib
matplotlib.use("Agg")
import numpy as np

from slmsuite.holography import analysis
from slmsuite.holography.algorithms import Hologram

from benchmark_seeds import (MAXITER, PAD, SLM, _floor, gaussian_amp, support_of)
from transport_seed import transport_phase

METHODS = ("GS", "WGS-Leonardo", "WGS-Kim", "WGS-Nogrette")
HALF_WIDTHS = (20, 40, 80, 120)


def flattop(half, edge=6.0):
    y, x = np.meshgrid(np.arange(PAD) - PAD / 2.0, np.arange(PAD) - PAD / 2.0,
                       indexing="ij")
    d = np.maximum(np.abs(x), np.abs(y)) - half
    return _floor(0.5 * (1 - np.tanh(d / edge)))


def metrics(holo, support):
    ff = np.asarray(holo.get_farfield(get=True))
    I = np.abs(ff) ** 2
    I = I / I.sum()
    winding = np.asarray(analysis.image_vortices(np.angle(ff)))
    inside = I[support]
    return {"vortices": int(np.count_nonzero(winding[support])),
            "ripple": float(inside.std() / inside.mean()),
            "efficiency": float(inside.sum())}


def main():
    amp = gaussian_amp()
    src2 = np.nan_to_num(amp.astype(float) ** 2, nan=0.0)

    print(f"top-hat area as a fraction of the {PAD}x{PAD} farfield, "
          f"SLM {SLM}x{SLM}, {MAXITER} iterations\n")
    header = f"{'half':>5}{'fraction':>10}  {'method':<14}"
    for s in ("quadratic", "transport"):
        header += f"{s + ' vort':>15}{'ripple':>9}{'eff':>8}"
    print(header)
    print("-" * len(header))

    out = []
    for half in HALF_WIDTHS:
        target = flattop(half)
        support = support_of(target)
        frac = (2 * half) ** 2 / PAD ** 2
        tgt2 = np.nan_to_num(target.astype(float) ** 2, nan=0.0)
        phi_t = transport_phase(src2, tgt2, farfield_shape=(PAD, PAD),
                                coarse=12, iters=40).astype(np.float32)

        for method in METHODS:
            row = {"half": half, "fraction": frac, "method": method}
            line = f"{half:>5}{frac:>9.1%}  {method:<14}"
            for seed in ("quadratic", "transport"):
                h = Hologram(target=target, amp=amp, slm_shape=(SLM, SLM))
                if seed == "quadratic":
                    h.reset_phase(quadratic_phase=True)
                else:
                    h.reset_phase(custom_phase=phi_t)
                h.optimize(method=method, maxiter=MAXITER, verbose=False)
                m = metrics(h, support)
                row[seed] = m
                line += (f"{m['vortices']:>15}{m['ripple']:>9.3f}"
                         f"{m['efficiency']:>8.3f}")
            out.append(row)
            print(line, flush=True)
        print()

    with open("benchmark_topsize.json", "w") as f:
        json.dump(out, f, indent=2)
    print("wrote benchmark_topsize.json")


if __name__ == "__main__":
    main()
