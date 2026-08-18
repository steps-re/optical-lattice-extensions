# PR body for holodyne/slmsuite#208 (POSTED 2026-08-18, corrected same day)

Branch: `fix/remove-vortices-reaches-farfield` (in `~/code/_vendor/slmsuite`)
Base: `main` @ 42a9b4b
Title: **Make remove_vortices reach the farfield so the documented callback does something**

Corrections applied 2026-08-18 after adversarial review, see CORRECTION-208.md.

---

#207 fixed everything I reported in #205, including the unconditional `plot_farfield` in
point 2, which its description does not claim. Working on top of it I hit a separate
problem it does not cover, and which was not in #205: used as a `callback=` the way the
docstring shows, the removal still does not change the optimization.

the loop calls the callback right after `_nearfield2farfield`, and then
`_gs_farfield_routines` does

```python
self.phase_ff = cp.arctan2(self.farfield.imag, self.farfield.real, out=self.phase_ff)
```

later in the same iteration, unless `fixed_phase` is on. so whatever the callback wrote
into `phase_ff` gets overwritten from the farfield, which nobody touched, before anything
reads it.

on main at 42a9b4b, GS 50 iterations, 256 px SLM, 512 px farfield, quadratic seed,
callback every 10 iterations:

| target | no callback | callback on main |
|---|---|---|
| flat-top | 32 vortices, ripple 0.340, eff 0.959 | 32, 0.340, 0.959 |
| flat-top MRAF | 24, 0.253, 0.815 | 24, 0.253, 0.815 |
| ring MRAF | 8, 0.367, 0.823 | 8, 0.367, 0.823 |

identical to three decimals is what a no-op looks like. the removal itself works, it just
does not survive the iteration:

```
iter  9: vortices in phase_ff 102 -> 30
iter 19: 118 -> 26
iter 29: 122 -> 12
iter 39: 122 -> 14
iter 49: 128 -> 26
```

each call knocks the count down and the next one finds it back where it was or higher,
because the farfield the count is recomputed from was never touched.

## the patch in this PR is not the right fix

I am leaving it up as a draft because the problem above is real and reproducible, but the
change itself has two faults I found only after opening the PR. flagging both rather than
letting anyone review it as-is.

**it operates on a stale `phase_ff`.** `_nearfield2farfield` populates `self.farfield` but
does not refresh `phase_ff`. only `_gs_farfield_routines` does, at the end of the previous
iteration. the callback runs in between, so at that moment `phase_ff` describes the
previous farfield, measured max 3.14 rad and mean 0.24 rad out of sync with the current
one. writing it back therefore replaces this iteration's propagated phase with a
de-vortexed copy of the last one. that is not what my own description above says it does.

**once the callback actually does something, it hurts two of the four methods.** over 15
seeds, WGS-Leonardo goes from 189 vortices without the callback to 228 with it, and
WGS-Kim from 216 to 232. efficiency drops in every method and every seed, worst on MRAF at
about 14% relative. on stock the callback is a no-op for GS, Leonardo and Nogrette and a
net help for Kim, so this patch turns a harmless no-op into a regression on two of them.
nothing in the PR tests the WGS variants, which is why I did not see it.

so the direction needs to be: re-derive `phase_ff` from `self.farfield` before removing,
and work out what the feature should do for the WGS variants at all, rather than enabling
it everywhere. happy to rework it, or to close this and leave you the bug report, whichever
you prefer.

for what it is worth the mechanical parts of the patch do check out: amplitude preserved to
about 1.5 float32 ulp, dtype preserved, no NaN introduced, exact zeros stay zero, stats
untouched (they read `amp_ff`, cached before the callback), and the `fixed_phase` path is
byte-identical to stock.

`tests/holography` is 8 failed, 66 passed, 6 skipped, 11 errors on this branch against
8 failed, 65 passed, 6 skipped, 11 errors on 42a9b4b. only the new test differs. the
failures and errors are environment, not code: 11 errors from a missing `pytest-benchmark`
and 8 failures from a missing `imageio`.

repro: [`benchmark_callback.py`](https://github.com/steps-re/optical-lattice-extensions/blob/main/contrib/slmsuite/benchmark_callback.py),
run against stock main.

found with AI assistance, checked against the source and the numbers above. apologies for
the two corrections here, and for crediting #207 with only half of #205 in my first draft.
