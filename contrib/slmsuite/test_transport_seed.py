"""Analytic checks for the transport seed.

Two cases where the right answer is known in closed form:

  translation  OT map is a rigid shift  -> phi is a blaze, dphi/dx = 2 pi s / N
  dilation     OT map is T(x) = a x     -> phi is a lens,  dphi/dx = 2 pi a x / N

Run with pytest, or directly (exits non-zero on failure).

Gradients are measured with a CENTRAL difference because that is what the solver
uses. An earlier version of this file measured with a forward difference and
described it as "the solver's convention", which stopped being true when the
solver moved to central differences.
"""

import sys

import numpy as np
import pytest

from transport_seed import transport_phase

N = 256
COARSE = 8


def gauss(cy, cx, w, n=N):
    y, x = np.meshgrid(np.arange(n) - n / 2.0, np.arange(n) - n / 2.0, indexing="ij")
    return np.exp(-(((y - cy) ** 2 + (x - cx) ** 2) / w ** 2))


def d_dx(a):
    """Central difference along x, matching the solver."""
    out = np.zeros_like(a)
    out[:, 1:-1] = 0.5 * (a[:, 2:] - a[:, :-2])
    out[:, 0] = a[:, 1] - a[:, 0]
    out[:, -1] = a[:, -1] - a[:, -2]
    return out


@pytest.mark.parametrize("shift", [10.0, 25.0, 40.0])
def test_translation_is_a_blaze(shift):
    """A shifted target of equal width must produce mean dphi/dx = 2 pi shift / N."""
    src, tgt = gauss(0, 0, 30.0), gauss(0, shift, 30.0)
    phi = transport_phase(src, tgt, farfield_shape=(N, N), coarse=COARSE)
    core = src > src.max() * 0.5
    want = 2 * np.pi * shift / N
    got = d_dx(phi)[core].mean()
    assert abs(got / want - 1) < 0.10, f"shift {shift}: want {want:.5f}, got {got:.5f}"


@pytest.mark.parametrize("scale", [1.6, 2.2])
def test_dilation_is_a_lens(scale):
    """A widened target must produce dphi/dx with slope 2 pi a / N against x."""
    src, tgt = gauss(0, 0, 30.0), gauss(0, 0, 30.0 * scale)
    phi = transport_phase(src, tgt, farfield_shape=(N, N), coarse=COARSE)
    core = src > src.max() * 0.5
    _, x = np.meshgrid(np.arange(N) - N / 2.0, np.arange(N) - N / 2.0, indexing="ij")
    want = 2 * np.pi * scale / N
    got = np.polyfit(x[core], d_dx(phi)[core], 1)[0]
    assert abs(got / want - 1) < 0.12, f"scale {scale}: want {want:.6f}, got {got:.6f}"


def _marginal_error(P, mu, nu):
    return float(np.abs(P.sum(1) - mu).sum() + np.abs(P.sum(0) - nu).sum())


def test_pushforward_lands_on_the_target():
    """The end-to-end property: light must actually arrive where the map says.

    This is the test that matters. A curl-free check is nearly tautological, since
    any numerically differentiated scalar array has negligible discrete curl. This
    one propagates the seed and asks how much power lands inside the target region.

    It is also the test that would have caught the real bug in this solver: an
    earlier version delivered a ring at radius 63 when the target sat at 90, for
    0.6 percent efficiency, while still being perfectly curl-free.
    """
    y, x = np.meshgrid(np.arange(N) - N / 2.0, np.arange(N) - N / 2.0, indexing="ij")
    r = np.hypot(x, y)
    src = np.exp(-(r ** 2) / 30.0 ** 2)
    tgt = np.exp(-((r - 70.0) ** 2) / 8.0 ** 2)          # annulus, nonconvex support

    phi = transport_phase(src, tgt, farfield_shape=(N, N), coarse=COARSE)
    field = np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(np.sqrt(src) * np.exp(1j * phi))))
    I = np.abs(field) ** 2
    I = I / I.sum()

    support = tgt > tgt.max() * 0.5
    efficiency = I[support].sum()
    assert efficiency > 0.45, f"only {efficiency:.3f} of the light landed on the ring"


def test_sinkhorn_marginals_converge():
    """The plan must push the source marginal onto the target, and tighten with iterations.

    The default iters=300 per epsilon stage leaves the marginals about 4e-4 off.
    That is convergence, not an entropic floor: 1000 iterations reaches 2e-6 and
    3000 reaches 7e-8. For a seed that later gets refined by phase retrieval, 4e-4
    is ample, so the default trades marginal accuracy for speed on purpose.
    """
    from transport_seed import sinkhorn_log

    rng = np.random.default_rng(0)
    mu = rng.random(40) + 0.05
    nu = rng.random(35) + 0.05
    mu /= mu.sum()
    nu /= nu.sum()
    xs = rng.random((40, 2))
    ut = rng.random((35, 2))
    C = ((xs[:, None, :] - ut[None, :, :]) ** 2).sum(-1)
    C /= C.max()

    err_default = _marginal_error(sinkhorn_log(mu, nu, C), mu, nu)
    err_long = _marginal_error(sinkhorn_log(mu, nu, C, iters=1000), mu, nu)
    assert err_default < 1e-3, f"default marginal error {err_default:.2e}"
    assert err_long < err_default / 10, (
        f"more iterations did not tighten the marginals: "
        f"{err_default:.2e} -> {err_long:.2e}")


def _main():
    failures = []
    for shift in (10.0, 25.0, 40.0):
        try:
            test_translation_is_a_blaze(shift)
            print(f"  translation {shift:5.1f}  ok")
        except AssertionError as e:
            failures.append(str(e))
            print(f"  translation {shift:5.1f}  FAIL {e}")
    for scale in (1.6, 2.2):
        try:
            test_dilation_is_a_lens(scale)
            print(f"  dilation    {scale:5.1f}  ok")
        except AssertionError as e:
            failures.append(str(e))
            print(f"  dilation    {scale:5.1f}  FAIL {e}")
    for fn, label in ((test_pushforward_lands_on_the_target, "pushforward"),
                      (test_sinkhorn_marginals_converge, "sinkhorn marginals")):
        try:
            fn()
            print(f"  {label:<18} ok")
        except AssertionError as e:
            failures.append(str(e))
            print(f"  {label:<18} FAIL {e}")

    print(f"\n{len(failures)} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_main())
