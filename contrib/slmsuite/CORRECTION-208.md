correcting myself, and apologies for the noise.

I ran a proper adversarial pass over this after opening it and found two things wrong, so
I have moved it to draft and rewritten the description.

**the patch operates on a stale `phase_ff`.** `_nearfield2farfield` populates
`self.farfield` but does not refresh `phase_ff`. only `_gs_farfield_routines` does, at the
end of the previous iteration, and the callback runs in between. measured max 3.14 rad,
mean 0.24 rad out of sync with the current farfield. so writing `phase_ff` back replaces
the current iteration's propagated phase with a de-vortexed copy of the previous one,
which is not what I said it does.

**once the callback is actually live it hurts two of the four methods.** over 15 seeds,
WGS-Leonardo 189 vortices without it against 228 with it, WGS-Kim 216 against 232, and
efficiency down in every method and seed. I tested only GS. that was the gap.

the underlying report still holds: used as the docstring shows, the removal is discarded
by the `arctan2` recompute in the same iteration, and the three-row table is unchanged.
but the fix needs to re-derive `phase_ff` from the farfield first, and needs an answer for
what the feature should do under WGS at all. I would rather not guess at that in a PR.

also, I got the credit wrong at the top. I wrote that #207 fixed "half" of #205. it fixed
all three points, including the unconditional `plot_farfield` in point 2, which its own
description does not claim. the callback problem was never in #205, it is separate. sorry
to @SAY-5 for understating that.

happy to rework this, or close it and leave you the report, whichever is less work for you.
