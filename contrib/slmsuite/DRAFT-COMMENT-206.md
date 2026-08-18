# Draft reply on holodyne/slmsuite#206 (NOT posted)

HELD until #208 is resolved. This cites #208, which is now a draft with a known defect.
Corrected 2026-08-18 after adversarial review: removed the non-reproducible equal-wall-clock
row, dropped single-run wall-clock precision, and fixed three overstated claims.

---

thanks, both of those were worth checking.

on the API shape, agreed. `optimize(method="ot")` then `optimize(method="wgs")` fits
better than a third seed option, and it gets rid of the awkwardness of a "seed" that is
itself iterative. happy to build it that way. no cupy path yet and no GPU here to test
one, so I would want someone with hardware for that half.

on your question. I could not answer it honestly until the removal actually applied, and
on main it still does not when you use it as a callback, because the loop recomputes
`phase_ff` from the farfield right after the callback returns. I opened #208 for that but
have since moved it to draft, since the patch there operates on a stale `phase_ff` and
makes WGS-Leonardo and WGS-Kim worse than no callback at all. so read the numbers below as
"quadratic plus a removal that is genuinely applied under GS", not as an endorsement of
that patch.

GS 50 iterations, 256 px SLM, 512 px farfield, removal every 10 iterations in the
`+ remove_vortices` arms:

| target | arm | vortices | ripple | eff |
|---|---|---|---|---|
| flat-top | quadratic | 32 | 0.340 | 0.959 |
| flat-top | quadratic + remove_vortices | 6 | 0.537 | 0.904 |
| flat-top | transport | 0 | 0.169 | 0.981 |
| flat-top MRAF | quadratic | 24 | 0.253 | 0.815 |
| flat-top MRAF | quadratic + remove_vortices | 6 | 0.458 | 0.736 |
| flat-top MRAF | transport | 0 | 0.172 | 0.978 |
| ring MRAF | quadratic | 8 | 0.367 | 0.823 |
| ring MRAF | quadratic + remove_vortices | 4 | 0.639 | 0.752 |
| ring MRAF | transport | 4 | 0.369 | 0.823 |

on the flat tops the seed wins on all three numbers. the removal trades ripple and
efficiency away to get the vortex count down, which the seed does not. on the ring the two
are about even.

I dropped the timings I had in here. they were single runs on a laptop and they moved by
about a factor of two when I re-ran them, so the seconds were not worth the digits I gave
them. the ratios were stable: the removal costs roughly three to five times a bare GS run
of the same length, and the seed costs roughly one bare run. I also had an "equal wall
clock" row, which was the direct answer to your cost question, and I have taken it out. the
iteration budget was set by an inline timing probe, so it drifts with machine load, and
sweeping the budget by hand gives ripple anywhere from 0.34 at 59 iterations to 0.56 at 70,
with the 61 I happened to publish sitting at 0.475. that is noise I presented as a result,
and it was the row most flattering to my own method. I cannot separate the two on cost with
what I have.

your point about the fraction of the farfield turned out to be the whole story. same SLM
and farfield, 50 iterations, sweeping the top-hat size:

| top hat as fraction of farfield | quadratic vortices | transport vortices | quadratic ripple | transport ripple |
|---|---|---|---|---|
| 0.6% | 0 | 0 | 0.371 | 0.378 |
| 2.4% | 4 | 0 | 0.400 | 0.284 |
| 9.8% | 32 | 0 | 0.340 | 0.169 |
| 22.0% | 182 | 0 | 0.331 | 0.143 |

at the smallest size I swept, 0.6% of the farfield, quadratic is already vortex-free and
the seed buys nothing. ripple is even a hair worse. the crossover is somewhere between
0.6% and 2.4% and I did not sample inside that gap. so this is really about large-area
targets rather than top hats in general, and I should have said so in the first post.

WGS-Kim is a similar story, though I overstated it before. the ripple blow-up I reported
appears at 2.4% and is present at every larger size I tried, but it does not grow
monotonically: 0.322, 7.390, 7.230, 3.289 across the four sizes. the vortex count does grow
monotonically. so that part of #205 is a note about running Kim outside what it was tuned
for, not a bug.

| fraction | GS | WGS-Leonardo | WGS-Kim | WGS-Nogrette |
|---|---|---|---|---|
| 0.6% | 0 | 0 | 0 | 0 |
| 2.4% | 4 | 0 | 21 | 0 |
| 9.8% | 32 | 72 | 125 | 33 |
| 22.0% | 182 | 203 | 399 | 125 |

vortices inside the support, quadratic seed. transport is 0 in 15 of the 16 cells, the
exception being WGS-Nogrette at 0.6% with 4.

on "consider using one of the other WGS variants", you were right that Kim is the problem,
but I should be precise about the rest: Nogrette holds up best of the four, and Leonardo is
better than Kim but worse than plain GS at 9.8% and above. so it is really Nogrette rather
than both.

both tables come from
[`benchmark_callback.py`](https://github.com/steps-re/optical-lattice-extensions/blob/main/contrib/slmsuite/benchmark_callback.py)
and
[`benchmark_topsize.py`](https://github.com/steps-re/optical-lattice-extensions/blob/main/contrib/slmsuite/benchmark_topsize.py).

if the large-area case is worth carrying in 0.5.0 or 0.6.0 I will put up the
`method="ot"` version. if it is too narrow, that is a fine answer too and the code stays
in my repo for anyone who wants it.
