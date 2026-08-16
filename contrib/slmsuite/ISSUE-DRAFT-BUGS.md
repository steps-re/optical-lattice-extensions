# POSTED as [slmsuite#205](https://github.com/slmsuite/slmsuite/issues/205) on 2026-08-16.

Title: `_remove_vortices` plots instead of removing, and its documented callback raises AttributeError

---

Three problems in the vortex-removal path, all in `_hologram.py`. I found them while
benchmarking something else and they compound, so the documented feature does not work as
written.

**1. The removal is inside the debug-plot branch.** In `_remove_vortices`, at current main:

```python
if self.phase_ff is not None:
    limits = self.plot_farfield(self.target)        # line 990, always runs

    if plot:                                        # line 992
        ...
        analysis.image_remove_vortices(self.phase_ff, self.target > 0)   # line 998
```

`plot_farfield` sits outside the branch and the removal sits inside it, so the default call
`_remove_vortices()` renders a figure and removes nothing. Only `_remove_vortices(plot=True)`
actually removes vortices, along with seven figures.

Measured on a 256 px flat-top with GS at 50 iterations, running your documented callback
every 10 iterations against not running it at all:

| target | without callback | with callback |
|---|---|---|
| flat-top | 299 vortices, ripple 0.350, eff 0.926 | 299 vortices, ripple 0.350, eff 0.926 |
| flat-top MRAF | 24 vortices, ripple 0.253, eff 0.815 | 24 vortices, ripple 0.253, eff 0.815 |
| ring MRAF | 8 vortices, ripple 0.367, eff 0.823 | 8 vortices, ripple 0.367, eff 0.823 |

Identical to three decimals, which is what a no-op produces.

**2. The unconditional plot is the entire cost.** The docstring says the method is "slightly
expensive, so calling every loop is not advised". Timed on the same setup: 34.2 ms per call
as shipped, unmeasurably small with `plot_farfield` stubbed out, against 6.4 ms for a GS
iteration. The expense is the figure, not the work. Moving line 990 inside `if plot:` fixes
both this and problem 1.

**3. The documented example calls a method that does not exist.** The docstring example is:

```python
def remove_vortices_callback(holo):
    if holo.iter % 10 == 9:
        holo.remove_vortices()
```

`Hologram` defines `_remove_vortices` only. `remove_vortices` exists on `_multiplane` and
`_spots`, but not on the base class the example is written against, so copying the snippet
raises `AttributeError`. `hasattr(Hologram(...), "remove_vortices")` is `False`.

**Separately, `WGS-Kim` freezes a poor phase on continuous targets.** Possibly intended, but
worth a look. Ripple with efficiency in brackets, flat-top, 50 iterations:

| target | seed | default | `fix_phase_iteration` beyond maxiter |
|---|---|---|---|
| flat-top | random | 5.012 (0.842) | 0.508 (0.874) |
| flat-top | quadratic | 7.230 (0.859) | 0.480 (0.888) |
| flat-top MRAF | random | 7.331 (0.065) | 0.497 (0.396) |
| flat-top MRAF | quadratic | 1.127 (0.122) | 0.286 (0.572) |

Freezing at iteration 10 locks in whatever ten iterations produced, and on a continuous
target that is not enough to recover from a poor start. Efficiency of 0.065 under MRAF,
where the other WGS variants on the same target sit near 0.72 to 0.79. I have not tested
the spot-array case the flag is presumably tuned for, so this may be correct behaviour
outside its intended use, and may only need documenting.

Environment: slmsuite 0.4.1, numpy 2.5.2, scipy 1.18.0, Python 3.14, macOS arm64, numpy
backend. Repro script attached. Found with AI assistance, verified by reading the source
and by the measurements above.
