# POSTED 2026-08-27 as holodyne/slmsuite#209
# https://github.com/holodyne/slmsuite/issues/209
#
# All three claims re-verified against stock main @42a9b4b immediately before posting
# (upstream had not moved since 8/18). reset_phase(quadratic_phase=True) and the
# flags route both raise ValueError; optimize(quadratic_phase=True) stores the flag
# and leaves the phase untouched.

Title: **the analytic quadratic seed is unreachable on a default `Hologram`: `reset_phase` raises, `optimize` silently ignores it**

Every claim below re-run against stock main @42a9b4b on 2026-08-18. Corrected the same day
after review: the unpack is in `image_moment` not `image_variances`, `optimize` is a silent
no-op rather than merely "not raising", and the random-arm range is over 20 draws not 5.

---

`Hologram.__init__` stores a scalar when no amplitude is passed:

```python
self.amp = 1 / np.sqrt(np.prod(self.slm_shape))    # _hologram.py:402
```

and `_get_quadratic_initial_phase` hands that straight to an image moment:

```python
std_amp = np.sqrt(analysis.image_variances(self.amp)[:2, 0])    # _hologram.py:509
```

`image_variances` normalizes through `image_moment`, which unpacks `images.shape` into
three values (`analysis/__init__.py:497`), so a 0-d scalar raises. on main at 42a9b4b:

```python
import numpy as np
from slmsuite.holography.algorithms import Hologram

target = np.zeros((128, 128), dtype=np.float32)
target[48:80, 48:80] = 1
holo = Hologram(target=target, slm_shape=(64, 64))
holo.reset_phase(quadratic_phase=True)
# ValueError: not enough values to unpack (expected 3, got 0)
```

setting `flags["quadratic_phase"] = True` and calling `reset_phase()` with no arguments
raises the same way.

the other entry point fails differently and more quietly. `optimize(...,
quadratic_phase=True)` does not raise, but only because `optimize` never calls
`reset_phase` at all. it stores the flag and leaves the phase as the random one from
construction:

```python
h = Hologram(target=target, slm_shape=(64, 64))
before = np.array(h.phase, copy=True)
h.optimize(method="GS", maxiter=0, verbose=False, quadratic_phase=True)
h.flags["quadratic_phase"]          # True
np.allclose(before, h.phase)        # True - the seed was never applied
```

so on a default `Hologram` the analytic seed is not reachable from either route: one
raises, the other accepts the argument and ignores it.

passing a uniform array of the same value instead of leaving `amp` unset works and gives a
good seed. on the target above after 20 GS iterations, 0 vortices in the support. the
quadratic seed is deterministic so that is one run, not a sample. the default random seed
gives 63 to 95 vortices over 20 unseeded draws.

`amp` is left unset in all 6 `Hologram(` constructions in `tests/`, so nothing in the suite
exercises the working path.

could be fixed either by materialising the uniform amplitude before the moment call or by
short-circuiting to the analytic value for a uniform aperture, and separately by having
`optimize` honour the flag instead of storing it. happy to put up a PR if you have a
preference.

found with AI assistance, repro above run against 42a9b4b.
