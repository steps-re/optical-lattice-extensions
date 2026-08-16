# optical-lattice-extensions

Independent work building on Hunter Swan's public optical-lattice notes and beam-shaping paper (Opt. Express 33, 6290, 2025). Not affiliated with Swan, Stanford, or the Hogan Lab, and not endorsed by them.

I read the paper, wandered into the GitHub, and found two loose threads: the manuscript leaves the Landau-Zener section empty, and the code predates Python 3. This repo pulls on both, and on a third that turned out to matter more than either.

Corrections are the reason this is public. If something here is wrong, open an issue.

## The short version

The paper's optimal-transport beam shaping, reimplemented properly, is a better way to start Gerchberg-Saxton than anything the standard holography package currently ships. Against `slmsuite`'s own analytic preconditioner, on `slmsuite`'s own code, scored with its own vortex counter. Random is the mean of five seeded draws. 50 GS iterations, 256 px SLM padded to 512:

| target | | random | quadratic | transport |
|---|---|---|---|---|
| flat-top | vortices | 300 | 32 | **0** |
| | ripple | 0.347 | 0.340 | **0.178** |
| | efficiency | 0.927 | 0.959 | **0.981** |
| ring | vortices | 102 | 0 | **0** |
| | ripple | 0.429 | 0.376 | 0.373 |
| | efficiency | 0.787 | 0.895 | 0.894 |

Ripple has a floor because the targets are not flat: the flat-top scores 0.175 against itself. Transport reaches 0.178, essentially the best the target admits, while quadratic sits at twice the distance from the floor. On the ring the two tie, and the quadratic seed already reaches zero vortices there on its own. I am not going to dress that up.

The zero vortex counts are measured, not derived. Brenier's theorem makes the exact transport map the gradient of a convex potential, but the implementation is entropic Sinkhorn on a coarse grid, and a curl-free SLM phase does not by itself guarantee a vortex-free far field. An earlier version of this solver was perfectly curl-free and put 519 vortices in the far field, because the map it encoded was wrong.

The seed costs 0.3 s at practical settings (`coarse=12`, 40 Sinkhorn iterations per stage), against 0.3 s for the 50 GS iterations themselves. The accuracy-tuned defaults cost 12 to 24 s and buy nothing a seed needs.

Code, benchmarks and tests are in `contrib/slmsuite/`. Upstream: the bug report is [slmsuite#205](https://github.com/slmsuite/slmsuite/issues/205) and the feature proposal is [slmsuite#206](https://github.com/slmsuite/slmsuite/issues/206).

## How it is verified

The seed is pinned against cases with closed-form answers rather than against
plausibility. A pure translation must produce a blaze of exactly `2*pi*shift/N`, a pure
dilation a lens of exactly `2*pi*a*x/N`, and an end-to-end check propagates the seed and
requires the light to actually land on a ring target. That last test is the one that
would have caught the worst bug this code ever had. `contrib/slmsuite/test_transport_seed.py`
holds all seven and is the thing to run first if you doubt any number here.

The advantage is insensitive to what runs afterwards. Across six Gerchberg-Saxton variants,
two targets, and plain and noise-region variants of each, the transport seed gives zero
vortices in all 24 configurations with efficiency never below 0.855. It is also insensitive
to the measurement: sweeping the signal-region threshold from 0.05 to 0.9 leaves transport
at zero vortices everywhere while quadratic ranges from 16 to 74. And it survives the fair
fight: given the seed's seconds as 1,200 to 2,900 extra iterations instead, the quadratic
seed improves and still does not catch up, in 23 of 24 configurations.

## What fell out along the way

Benchmarking inside `slmsuite` surfaced three bugs in its own vortex-removal path, written
up in `contrib/slmsuite/ISSUE-DRAFT-BUGS.md`. The removal call in `_remove_vortices` sits
inside the debug-plot branch while its plotting sits outside it, so the default call plots
and removes nothing. The docstring's "slightly expensive" warning is measuring that stray
plot, 34 ms against microseconds of real work. And the documented callback example calls a
method that does not exist on `Hologram`. Also `WGS-Kim`'s `fix_phase_iteration: 10` freezes whatever
phase exists at iteration 10, which on a continuous target locks in a poor start.

## What else is here

**tex/** A standalone addendum on shuttling and Landau-Zener tunnelling, in the manuscript's notation. It is a proposed continuation, not part of Swan's manuscript. `Extensions.pdf` carries the higher-dimensional results.

**code/**

- `lattice3D.py`: a d-dimensional solver written from scratch against the same conventions as `lattice1D.py`.
- `run_3d.py`, `run_nonseparable.py`: tests of the per-crossing loss formula P = exp(-pi A^2 / 4|b.Qdot|). It holds at all 30 tested points in separable 2D and 3D lattices. In a minimal 3-laser lattice it is leading-order only, and zone-corner factorization breaks by up to 0.18 in absolute loss where the separable reference stays within 0.004.
- `ramp_optimizer.py`: on the one benchmark tested, a shaped shuttle ramp cut loss from 34.1% to 0.28% at equal transport time, stable under doubled resolution.
- `ot_gs2.py`, `mraf.py`, `phase_diversity.py`: standalone studies of the paper's beam shaping and a phase-diversity solver, on their own fixed geometry. For the shaper itself use `contrib/slmsuite/transport_seed.py`, which is the general implementation and the one the numbers above come from.
- `quasicrystal.py`: when a set of lasers makes a lattice and when it makes a quasicrystal.

**results/** the JSON behind every number. **figs/** nine figures. **reviews/** adversarial review transcripts and the fixes they forced.

## Reproducing

```
pip install numpy scipy matplotlib
python code/run_3d.py
python code/run_nonseparable.py
python code/ramp_optimizer.py

cd contrib/slmsuite
pip install slmsuite
python test_transport_seed.py     # 7 checks, exits non-zero on failure
python benchmark_seeds.py         # the main tables
python benchmark_extras.py        # cost sweep, remedy control, threshold sweep
```

`code/lz_sweep.py` is the exception. It drives Swan's own `lattice1D.py` and `bands.py`, which are not redistributed here, so it needs his repo checked out alongside.

## Provenance and limits

The coding and derivations were done by AI agents under my direction. I am an engineer, not a physicist, and no physicist has reviewed this. Every claim is a simulation at finite cutoff and finite resolution, checked against analytic limits and by adversarial review across five rounds. None of it is experimental.

Treat everything here as a reproducible claim rather than an authority. The tests are there so you do not have to take my word for it.

## Relation to Swan's repositories

The two Python 3 fixes to `lattice1D.py` went upstream as [orswan/lattice#1](https://github.com/orswan/lattice/pull/1), still open. None of his code, text or figures is redistributed here. His personal repositories carry no license, which is also why the compiled manuscript that exists locally stays local.

His lab is another matter: [hoganphysics/SLMTools](https://github.com/hoganphysics/SLMTools) is an actively maintained, MIT-licensed Julia implementation of the paper's beam-shaping methods. `contrib/slmsuite/transport_seed.py` was written independently from the paper before I knew SLMTools existed, and has since been cross-checked against it on identical inputs: phase gradients agree to 15 percent RMS, both seeds give zero in-support vortices, both converge to identical results after refinement, and a translation control on their output in our convention measures 0.999 of the expected blaze. The harness is `contrib/slmsuite/crosscheck_slmtools.jl` and `.py`.

## License

MIT for code, CC BY 4.0 for documents and figures. See `LICENSE`.

Mike German
