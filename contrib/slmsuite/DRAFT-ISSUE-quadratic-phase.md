# Draft issue for holodyne/slmsuite (NOT posted, queued for 2026-08-19 evening)

Title: **`reset_phase(quadratic_phase=True)` raises ValueError whenever `amp` was not given**

Every claim below was re-run against stock main @42a9b4b on 2026-08-18.

---

`Hologram.__init__` stores a scalar when no amplitude is passed:

```python
self.amp = 1 / np.sqrt(np.prod(self.slm_shape))    # _hologram.py:402
```

and `_get_quadratic_initial_phase` hands that straight to an image moment:

```python
std_amp = np.sqrt(analysis.image_variances(self.amp)[:2, 0])    # _hologram.py:509
```

`image_variances` unpacks `images.shape` into three values, so a 0-d scalar raises. on
main at 42a9b4b:

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
raises the same way. `optimize(..., quadratic_phase=True)` on a fresh `Hologram` does
not raise, so the entry point matters and I have not traced why.

passing a uniform array of the same value instead of leaving `amp` unset works and gives
a good seed. on the target above after 20 GS iterations, 0 vortices in the support on
3 of 3 runs, against 71 to 82 over 5 runs of the default random seed. so it is only the
scalar path.

which means the analytic seed is unreachable through `reset_phase` for any hologram built
without an explicit `amp`, and that is the default, including in most of the tests.

could be fixed either by materialising the uniform amplitude before the moment call or by
short-circuiting to the analytic value for a uniform aperture. happy to put up a PR if you
have a preference.

found with AI assistance, repro above run against 42a9b4b.
