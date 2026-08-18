# Draft PR to holodyne/slmsuite (NOT posted, queued for 2026-08-17 evening)

Branch: `fix/remove-vortices-reaches-farfield` (local, in `~/code/_vendor/slmsuite`)
Base: `main` @ 42a9b4b
Title: **Make remove_vortices reach the farfield so the documented callback does something**

---

#207 fixed the half of #205 I reported. the removal runs now and the figures only show
up with `plot=True`. but used as a `callback=` the way the docstring shows, it still
does nothing.

the loop calls the callback right after `_nearfield2farfield`, and then
`_gs_farfield_routines` does

```python
self.phase_ff = cp.arctan2(self.farfield.imag, self.farfield.real, out=self.phase_ff)
```

later in the same iteration, unless `fixed_phase` is on. so the corrected `phase_ff`
gets overwritten from the farfield, which nobody touched, before anything reads it.

on main at 42a9b4b, GS 50 iterations, 256 px SLM, 512 px farfield, quadratic seed,
callback every 10 iterations:

| target | no callback | callback on main | callback on this branch |
|---|---|---|---|
| flat-top | 32 vortices, ripple 0.340, eff 0.959 | 32, 0.340, 0.959 | 6, 0.537, 0.904 |
| flat-top MRAF | 24, 0.253, 0.815 | 24, 0.253, 0.815 | 6, 0.458, 0.736 |
| ring MRAF | 8, 0.367, 0.823 | 8, 0.367, 0.823 | 4, 0.639, 0.752 |

identical to three decimals is what a no-op looks like. the removal itself is fine, it
just does not survive the iteration:

```
iter  9: vortices in phase_ff 102 -> 30, back to ~102 by the next call
iter 19: vortices in phase_ff 118 -> 26, back to ~118 by the next call
iter 29: vortices in phase_ff 122 -> 12, back to ~122 by the next call
```

so this writes the corrected phase back into the farfield, where the `arctan2` will pick
it up instead of throwing it away. amplitude is preserved. with `fixed_phase` on
(WGS-Kim after the freeze) the callback already worked, since that path skips the
`arctan2`, and this leaves that alone.

the test from #207 passes either way because it calls `remove_vortices()` after
`optimize()` has finished. I added one that runs it as a callback and checks the GS
result changes.

one caveat: fewer vortices is not free here. ripple goes up and efficiency goes down in
all three rows above. the callback does what it says now, but it is a trade, and that
might be worth a line in the docstring.

`tests/holography` is 8 failed, 66 passed, 6 skipped, 11 errors on this branch against
8 failed, 65 passed, 6 skipped, 11 errors on 42a9b4b. only the new test differs. the
failures and errors are pre-existing on my machine, mostly missing `pytest-benchmark`
and hardware fixtures.

repro: [`benchmark_callback.py`](https://github.com/steps-re/optical-lattice-extensions/blob/main/contrib/slmsuite/benchmark_callback.py),
run against stock main.

found with AI assistance, checked against the source and the numbers above.

---

## Companion comment on #205 (closed)

> #207 got the plotting half of this. the callback half is still there: the loop
> recomputes `phase_ff` from the farfield in `_gs_farfield_routines` after the callback
> returns, so the removal is thrown away in the same iteration and the GS result does
> not move. one-line fix and a test in #208.
