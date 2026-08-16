# Draft reply on holodyne/slmsuite#206 (NOT posted)

---

thanks, both of those were worth checking.

**the API shape.** agreed, `optimize(method="ot")` then `optimize(method="wgs")` is a
better fit than a third seed option, and it drops the awkwardness of a "seed" that is
itself iterative. happy to build it that way. no cupy path yet and no GPU here to test
one, so I would want someone with hardware on that half.

**your question, is it better than quadratic + remove_vortices with the removal actually
applied.** I could not answer that honestly until the removal applied, and on main it
still does not when used as a callback: the loop recomputes `phase_ff` from the farfield
right after the callback returns. details and a fix in #NNN. with that in, GS 50
iterations, 256 px SLM, 512 px farfield, removal every 10 iterations:

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

so on the flat tops the seed wins on all three numbers and is still faster than the
removal callback, because the removal costs about 0.2 s per call at this size while the
seed costs 0.38 s once. the removal trades ripple and efficiency for the vortex count,
which the seed does not. on the ring the two are a wash.

**your point about the fraction of the farfield.** you were right, and it turns out to
be the whole story. sweeping the top-hat size at fixed SLM and farfield, 50 iterations:

| top hat as fraction of farfield | quadratic vortices | transport vortices | quadratic ripple | transport ripple |
|---|---|---|---|---|
| 0.6% | 0 | 0 | 0.371 | 0.378 |
| 2.4% | 4 | 0 | 0.400 | 0.284 |
| 9.8% | 32 | 0 | 0.340 | 0.169 |
| 22.0% | 182 | 0 | 0.331 | 0.143 |

at 0.6%, which is the regime the good experimental top hats live in, quadratic is
already vortex-free and the seed buys nothing (ripple is a hair worse). the crossover is
around 2%. so the honest scope for this is large-area targets, not top hats generally,
and I should have said that in the first post.

**WGS-Kim.** also fair. at 0.6% Kim is fine and actually has the best ripple of the four
variants (0.322). the blow-up I reported starts at 2.4% and gets worse with size, and
Leonardo and Nogrette hold up better there, exactly as you said. so treat that part of
#205 as a note about running Kim outside its intended regime rather than a bug. full
grid:

| fraction | GS | WGS-Leonardo | WGS-Kim | WGS-Nogrette |
|---|---|---|---|---|
| 0.6% | 0 | 0 | 0 | 0 |
| 2.4% | 4 | 0 | 21 | 0 |
| 9.8% | 32 | 72 | 125 | 33 |
| 22.0% | 182 | 203 | 399 | 125 |

(vortices inside the support, quadratic seed. transport is 0 in every cell except one.)

repro for both tables:
[`benchmark_callback.py`](https://github.com/steps-re/optical-lattice-extensions/blob/main/contrib/slmsuite/benchmark_callback.py)
and
[`benchmark_topsize.py`](https://github.com/steps-re/optical-lattice-extensions/blob/main/contrib/slmsuite/benchmark_topsize.py).

if the large-area case is interesting for 0.5.0 or 0.6.0 I will put up the
`method="ot"` version. if it is too narrow to carry, that is a fine answer too and I
will leave the code in my repo for anyone who wants it.
