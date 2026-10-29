no bench setup on my end. i came at this from the Swan et al. paper and wanted to see how the OT seed does inside slmsuite.

good call on CG, so i ran it on the same targets (0.5.0, 5 seeds each):

- the default lr=0.1 barely moves. from the quadratic seed the centered flat top sits at fidelity ~0.80 after 500 its. a sweep peaked around lr=30 (Adam, so steps are normalized) and 100 starts breaking things. 30 is still too hot for the centered MRAF ring, 10 is the safer pick.
- tuned, CG does beat WGS-Leonardo from the quadratic seed on flat tops: 0.96 vs 0.91 centered, 0.97 vs 0.93 off-center, and 0-14 vortices vs 10-64.
- from the OT seed both land ~0.998 with 0 vortices, WGS ending flatter (ripple 0.008 vs 0.04). on rings and the two-bar target WGS ties or wins.

that's scored on fidelity/ripple, not CG's own loss, so a loss built for top hats could change it. script and data: https://github.com/steps-re/optical-lattice-extensions/blob/main/contrib/slmsuite/benchmark_cg.py

(AI-assisted.)
