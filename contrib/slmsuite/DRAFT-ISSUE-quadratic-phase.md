# Draft issue for holodyne/slmsuite (NOT posted, queued for 2026-08-17 evening)

Title: **`reset_phase(quadratic_phase=True)` raises ValueError whenever `amp` was not given**

---

`Hologram.__init__` stores a scalar when no amplitude is passed:

```python
self.amp = 1 / np.sqrt(np.prod(self.slm_shape))    # _hologram.py:402
```

and `_get_quadratic_initial_phase` hands that straight to an image moment:

```python
std_amp = np.sqrt(analysis.image_variances(self.amp)[:2, 0])    # _hologram.py:508
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

same thing through `flags["quadratic_phase"]` and through
`optimize(..., quadratic_phase=True)`. passing a uniform array of the same value instead
works and gives a good seed (0 vortices, eff 0.959 on the target above after 20 GS
iterations), so it is only the scalar path.

which means the analytic seed is unreachable for any hologram built without an explicit
`amp`, and that is the default, including in most of the tests.

could be fixed either by materialising the uniform amplitude before the moment call or
by short-circuiting to the analytic value for a uniform aperture. happy to put up a PR
if you have a preference.

found with AI assistance, repro above run against 42a9b4b.
