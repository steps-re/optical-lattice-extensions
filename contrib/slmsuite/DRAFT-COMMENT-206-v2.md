# Draft reply on holodyne/slmsuite#206 (NOT posted)

Replaces DRAFT-COMMENT-206.md, which was written against 42a9b4b and cited #208 (closed
2026-10-05). Numbers below come from benchmark_v050.md, run against the v0.5.0 tag.
Paste everything below the line.

---

reran this against 0.5.0 to answer your question properly.

one thing first. per the new docstring the removal only sticks where the phase is fixed, and that's what I see: under WGS-Leonardo the callback leaves the final phase bit-identical in 30/30 runs and just adds time (2.8 s to 6.8 s per 100 iterations, median). so "actually applied" means WGS-Kim here.

setup: 256 px SLM, 512 px farfield, 100 iterations, 6 targets (several off-center, one disconnected), 5 seeds each, single CPU core, time includes the seed.

on the large-area targets (two flat tops at 6 and 10% of the farfield, and two bars) the OT seed plus Leonardo gives 0 vortices and fidelity 0.97 to 1.00. quadratic plus Leonardo gives 8 to 45 vortices and 0.90 to 0.93. quadratic + remove_vortices under Kim gives 23 to 94 and 0.66 to 0.74, mostly because Kim drifts on extended targets once the phase is fixed. I checked that with hard-edged targets and with fix_phase_iteration=30 and it doesn't go away.

on cost, the seed takes 0.4 s, about 14 Leonardo iterations. OT reaches fidelity 0.99 within 2 iterations on the two big flat tops (0.5 to 0.7 s total) and 0.95 in 31 on the two bars. quadratic doesn't reach 0.95 within 100 on any of the three, with or without the removal. so yes, it pays for itself there.

where it doesn't help: rings. quadratic is already vortex-free, the off-center ring is a tie (0.972 vs 0.971, and quadratic gets there sooner) and quadratic wins the centered MRAF ring (0.944 vs 0.865). on a small off-center flat top (1.4% of the farfield) both are close, 0.999 vs 0.981. and stacking remove_vortices on top of the OT seed lowered fidelity in all 6 configs.

agree on `optimize(method="ot")` then `method="wgs"`. the solver is plain array ops so a cupy path should be easy, and I'm happy to write it. I have no GPU here though, so someone would need to run it on hardware.

script and full table: [benchmark_v050.py](https://github.com/steps-re/optical-lattice-extensions/blob/main/contrib/slmsuite/benchmark_v050.py), [benchmark_v050.md](https://github.com/steps-re/optical-lattice-extensions/blob/main/contrib/slmsuite/benchmark_v050.md)

(AI-assisted. numbers are straight from the linked script.)
