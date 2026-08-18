# Draft reply on holodyne/slmsuite#206 (NOT posted, queued for 2026-08-17 evening)

---

thanks, both of those were worth checking.

on the API shape, agreed. `optimize(method="ot")` then `optimize(method="wgs")` fits
better than a third seed option, and it gets rid of the awkwardness of a "seed" that is
itself iterative. happy to build it that way. no cupy path yet and no GPU here to test
one, so I would want someone with hardware for that half.

on your question. I could not answer it honestly until the removal actually applied, and
on main it still does not when you use it as a callback, because the loop recomputes
`phase_ff` from the farfield right after the callback returns. fix and numbers in #208.
with that in, GS 50 iterations, 256 px SLM, 512 px farfield, removal every 10 iterations:

| target | arm | vortices | ripple | eff | time |
|---|---|---|---|---|---|
| flat-top | quadratic | 32 | 0.340 | 0.959 | 0.31 s |
| flat-top | quadratic + remove_vortices | 6 | 0.537 | 0.904 | 1.38 s |
| flat-top | transport | 0 | 0.169 | 0.981 | 0.70 s |
| flat-top | quadratic + rv, equal wall clock (61 iters) | 32 | 0.475 | 0.931 | 1.77 s |
| flat-top MRAF | quadratic | 24 | 0.253 | 0.815 | 0.22 s |
| flat-top MRAF | quadratic + remove_vortices | 6 | 0.458 | 0.736 | 1.30 s |
| flat-top MRAF | transport | 0 | 0.172 | 0.978 | 0.57 s |
| ring MRAF | quadratic | 8 | 0.367 | 0.823 | 0.21 s |
| ring MRAF | quadratic + remove_vortices | 4 | 0.639 | 0.752 | 0.63 s |
| ring MRAF | transport | 4 | 0.369 | 0.823 | 0.49 s |

on the flat tops the seed wins on all three numbers and still comes out faster, since
the removal runs about 0.2 s per call at this size and the seed is 0.38 s once. the
removal also trades ripple and efficiency away to get the vortex count down, which the
seed does not. on the ring the two are about even.

your point about the fraction of the farfield turned out to be the whole story. same SLM
and farfield, 50 iterations, sweeping the top-hat size:

| top hat as fraction of farfield | quadratic vortices | transport vortices | quadratic ripple | transport ripple |
|---|---|---|---|---|
| 0.6% | 0 | 0 | 0.371 | 0.378 |
| 2.4% | 4 | 0 | 0.400 | 0.284 |
| 9.8% | 32 | 0 | 0.340 | 0.169 |
| 22.0% | 182 | 0 | 0.331 | 0.143 |

at 0.6%, which is where the good experimental top hats live, quadratic is already
vortex-free and the seed buys nothing. ripple is even a hair worse. crossover is around
2%. so this is really about large-area targets rather than top hats in general, and I
should have said so in the first post.

WGS-Kim is the same story. at 0.6% it is fine and has the best ripple of the four
variants at 0.322. what I reported starts at 2.4% and gets worse with size, and Leonardo
and Nogrette hold up better there, like you said. so that part of #205 is a note about
running Kim outside what it was tuned for, not a bug.

| fraction | GS | WGS-Leonardo | WGS-Kim | WGS-Nogrette |
|---|---|---|---|---|
| 0.6% | 0 | 0 | 0 | 0 |
| 2.4% | 4 | 0 | 21 | 0 |
| 9.8% | 32 | 72 | 125 | 33 |
| 22.0% | 182 | 203 | 399 | 125 |

vortices inside the support, quadratic seed. transport is 0 in every cell of that grid
except one.

both tables come from
[`benchmark_callback.py`](https://github.com/steps-re/optical-lattice-extensions/blob/main/contrib/slmsuite/benchmark_callback.py)
and
[`benchmark_topsize.py`](https://github.com/steps-re/optical-lattice-extensions/blob/main/contrib/slmsuite/benchmark_topsize.py).

if the large-area case is worth carrying in 0.5.0 or 0.6.0 I will put up the
`method="ot"` version. if it is too narrow, that is a fine answer too and the code stays
in my repo for anyone who wants it.
