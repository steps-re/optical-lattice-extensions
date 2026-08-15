# DRAFT: slmsuite issue. NOT POSTED. Mike posts.

Title: Optimal-transport initial phase (Swan et al. 2025) as an alternative to `quadratic_phase`

---

Swan, Torchylo, Van de Graaff, Rudolph and Hogan, "High-fidelity holographic beam shaping
with optimal transport and phase diversity", Opt. Express 33, 6290 (2025),
arXiv:2408.17025, show that optimal transport produces excellent initializations for
iterative phase retrieval. The method is theirs. What follows is an implementation against
your API, a benchmark, and the tests.

`reset_phase()` currently offers random phase, or a lens-and-blaze fit to the target's
first and second moments. Your docstring is candid that the quadratic option exists
because a smooth analytic phase seeds fewer vortices than noise does, but a lens and a
blaze can only match a centroid and a width.

Optimal transport approximates the whole distribution. Solve for the map carrying the
source intensity onto the target intensity at minimum squared cost. By Brenier's theorem
the exact map is the gradient of a convex potential, so taking that potential as the
initial phase makes the geometric-optics image of the beam the target itself.

Two caveats, because the implementation is not the idealisation. The solver uses entropic
Sinkhorn on a coarse grid with thresholded measures, a barycentric projection and a
least-squares integration, so the discrete map approximates the Brenier map rather than
being it. And curl-free constrains the SLM plane only. It does not by itself imply a
vortex-free far field: an earlier version of this solver returned a perfectly curl-free
phase whose far field carried 519 vortices, because the map it encoded was wrong. The zero
counts below are measured, not derived.

**Method.** 256 px SLM padded to 512, Gaussian illumination, 50 iterations, six algorithms
against a flat-top and a ring, each plain and as MRAF with a `nan` noise region: 24
configurations. `vortices` is your `analysis.image_vortices` winding map counted inside the
signal region. `ripple` is std/mean of far-field intensity in that region and `efficiency`
is the power fraction inside it, both my definitions. Ripple has a floor, because
the targets are not flat: scored against itself the flat-top gives 0.175 and the
ring 0.357. Read the ripple numbers against those floors. The random column is the mean of five
seeded draws, generated here and passed as `custom_phase`, because `_get_random_phase`
builds a fresh unseeded `default_rng` on the numpy path and does not respond to a global
seed.

| config | method | random (n=5) | quadratic | transport |
|---|---|---|---|---|
| flat-top | GS | 300 / 0.347 / 0.927 | 32 / 0.340 / 0.959 | **0 / 0.178 / 0.981** |
| flat-top | WGS-Leonardo | 110 / 0.523 / 0.874 | 72 / 0.480 / 0.888 | **0 / 0.174 / 0.980** |
| flat-top | WGS-Nogrette | 222 / 0.362 / 0.913 | 33 / 0.249 / 0.942 | **0 / 0.174 / 0.981** |
| flat-top MRAF | GS | 344 / 0.288 / 0.787 | 24 / 0.253 / 0.815 | **0 / 0.178 / 0.980** |
| flat-top MRAF | WGS-Leonardo | 139 / 0.578 / 0.387 | 42 / 0.286 / 0.572 | **0 / 0.174 / 0.979** |
| ring | GS | 102 / 0.429 / 0.787 | 0 / 0.376 / 0.895 | 0 / 0.373 / 0.894 |
| ring MRAF | GS | 121 / 0.416 / 0.679 | 8 / 0.367 / 0.823 | **0 / 0.365 / 0.886** |
| ring MRAF | WGS-Nogrette | 73 / 0.435 / 0.638 | 0 / 0.358 / 0.820 | **0 / 0.358 / 0.880** |

Transport gives zero counted vortices in all 24 configurations, and efficiency never below
0.855.

On the flat-top the ripple result is the substantive one: the floor is 0.175 and transport
reaches 0.178, so it is essentially at the best the target admits, while quadratic sits at
0.340, roughly twice the distance from the floor.

On the ring, ripple cannot tell the two apart. The floor is 0.357, transport gives 0.373
and quadratic 0.376, both within 0.02 of a metric floor, so that comparison is
uninformative and I am not going to read anything into it. What does separate on the ring
is vortex count under MRAF and efficiency, roughly 0.88 against 0.82.

Full per-configuration results are in the attached `benchmark_seeds.json`, including the
min and max of the five random draws.

**Cost.** The tables above use `coarse=8` with 300 Sinkhorn iterations per epsilon stage,
which costs 12 to 24 s. That is not the useful setting. Sweeping it on the flat-top:

| coarse | Sinkhorn iters | seed | vortices | ripple | efficiency |
|---|---|---|---|---|---|
| 8 | 300 | 12.4 s | 0 | 0.178 | 0.981 |
| 8 | 40 | 1.7 s | 0 | 0.177 | 0.981 |
| 12 | 300 | 2.4 s | 0 | 0.170 | 0.981 |
| **12** | **40** | **0.3 s** | **0** | **0.169** | **0.981** |
| 16 | 40 | 0.1 s | 14 | 0.212 | 0.977 |

At `coarse=12, iters=40` the seed costs **0.3 s** and is slightly better than the expensive
setting, 0.169 ripple against 0.178, still zero vortices. Quality falls off at 16, so 12 is
the knee. The defaults in the attached code were chosen for transport accuracy the seed does
not need.

**Equal wall clock** at the expensive setting, since a fixed iteration count would otherwise
flatter it. I measured the seed, converted it into the extra iterations it could have bought,
and re-ran the cheap seeds with that budget: 1,168 to 2,908 iterations.

| config | method | quadratic @50 | quadratic @equal time | transport @50 |
|---|---|---|---|---|
| flat-top | GS | 32 / 0.340 / 0.959 | 4 / 0.207 / 0.979 | **0 / 0.178 / 0.981** |
| flat-top | WGS-tanh | 32 / 0.338 / 0.959 | 2 / 0.250 / 0.981 | **0 / 0.179 / 0.981** |
| flat-top MRAF | GS | 24 / 0.253 / 0.815 | 6 / 0.181 / 0.924 | **0 / 0.178 / 0.980** |
| flat-top MRAF | WGS-Leonardo | 42 / 0.286 / 0.572 | 6 / 0.202 / 0.801 | **0 / 0.174 / 0.979** |

The extra iterations do help, which is why the control is worth running: quadratic goes
from 32 vortices to 4 on the first row. It does not catch up. Counting a configuration for
transport when it has no more vortices and no worse ripple within 2 percent, transport at
50 iterations holds in 23 of 24. The exception is ring MRAF under WGS-Kim, where quadratic
reaches slightly lower ripple at much lower efficiency.

The iteration budget is extrapolated from a per-iteration time measured on one
50-iteration run, so I checked it: the long runs actually take 0.97 to 0.99 times the
transport path's total wall clock across four spot checks, both roughly 24 s. The budget is
equal within 3 percent.

**Against your existing remedy.** `_remove_vortices` addresses the same problem, so it is
the control that matters. Running your documented callback every 10 iterations changes
nothing at all: 299 vortices with and without on the flat-top, 24 with and without on
flat-top MRAF, 8 with and without on ring MRAF, identical to three decimals. That is because
the removal call sits inside the method's `if plot:` branch while the plotting sits outside
it, so the default invocation plots and does not remove. I have written that up separately
as a bug, and it is worth fixing regardless of what you decide here.

**Threshold sensitivity**, since the signal region is defined as target above half maximum
and that is arbitrary. Sweeping it from 0.05 to 0.9 on the flat-top, transport gives zero
vortices at every threshold while quadratic ranges from 16 to 74 and random from 244 to 397.
The conclusion does not depend on the cut.

Implementation is ~300 lines of numpy and scipy, no new dependencies. Dense Sinkhorn is the
memory cost and the coarse-grid factor controls it. There is no CuPy path yet, though at
0.3 s on CPU that matters less than I expected when I started. On the API, a third boolean
beside `random_phase` and `quadratic_phase` would create
ambiguous combinations, so an initializer callable or an enum may suit you better than the
flags pattern. Happy to open a PR in whichever shape you prefer, or to leave this here.

Environment: slmsuite 0.4.1, numpy 2.5.2, scipy 1.18.0, Python 3.14, macOS arm64, numpy
backend (no CuPy).

Built with AI assistance. The two benchmark scripts, their results JSONs and the tests are
attached: `benchmark_seeds.py` for the main tables and `benchmark_extras.py` for the cost
sweep, the `_remove_vortices` control and the threshold sweep. The tests assert against
pure translation and pure dilation, where the answer is known in closed form, plus an
end-to-end check that the seed's light lands on a ring target, and exit non-zero on
failure.
