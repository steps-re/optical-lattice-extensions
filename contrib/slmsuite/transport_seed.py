"""
Optimal-transport initial phase for Gerchberg-Saxton-type hologram optimization.

The method is due to Swan, Torchylo, Van de Graaff, Rudolph and Hogan,
"High-fidelity holographic beam shaping with optimal transport and phase
diversity", Opt. Express 33, 6290 (2025), arXiv:2408.17025. This file is an
independent implementation of it, not their code.

Phase retrieval has to start somewhere. Random phase is the usual choice, and it
is a bad one: it scatters light into a speckle field whose zeros are optical
vortices, and a vortex is a topological defect. Iterations can move vortices and
can annihilate them in opposite-charge pairs, but in practice a speckled start
leaves residual defects the run never clears. slmsuite's quadratic preconditioner
exists for exactly this reason -- a smooth analytic phase seeds no vortices --
but it is only a lens and a blaze, so it can only match the target's centroid
and second moments.

Optimal transport extends that idea to an arbitrary target. Solve for the map T
carrying the source intensity onto the target intensity at minimum squared cost.
By Brenier's theorem the exact map is the gradient of a convex potential,
T = grad(psi), so taking phi = psi (suitably scaled) as the initial phase makes
the geometric-optics image of the beam the target.

Two things that claim does NOT establish. This implementation uses entropic
Sinkhorn on a coarse grid with thresholded measures, a barycentric projection and
an approximate integration, so the discrete map approximates the Brenier map
rather than being it. And curl-free constrains the SLM plane only: it does not
imply a vortex-free far field. An earlier version of this solver returned a
perfectly curl-free phase whose far field carried 519 vortices. Low far-field
vortex counts are an empirical result, not a theorem.

Method: entropic OT (log-domain Sinkhorn) on a coarse grid, barycentric
projection to get T, then a weighted least-squares fit to recover psi from
grad(psi) = T, then interpolation back to the full SLM grid.

The recovery step is the part worth reading. The obvious approach is a Neumann
Poisson solve by DCT, and it fails in two ways that both look like success: a
blaze has zero Laplacian, so a homogeneous-Neumann solve discards the beam
steering entirely, and a linear residual has constant divergence, which zero-flux
boundaries cannot represent at all. Weighted least squares over the illuminated
region has neither problem and needs no invented data outside the beam. Use
central differences there, not forward ones -- a forward difference estimates the
gradient at the face rather than the cell center, which biases every quadratic
term by (pi/N)*coarse^2. See test_transport_seed.py, which pins all of this
against translation and dilation, where the answer is known in closed form.

Depends only on numpy and scipy.
"""

import numpy as np
from scipy.interpolate import RectBivariateSpline

__all__ = ["transport_phase", "sinkhorn_log"]


def sinkhorn_log(mu, nu, C, eps_schedule=(0.05, 0.02, 0.008, 0.003, 0.001), iters=300):
    """
    Log-domain Sinkhorn with epsilon annealing.

    Log-domain because the naive kernel exp(-C/eps) underflows to zero for the
    small eps you need if you want the barycentric map to be sharp. Annealing
    because starting at small eps converges slowly; each stage warm-starts the
    next.

    Parameters
    ----------
    mu, nu : ndarray
        Source and target weights. Each must sum to 1.
    C : ndarray
        Cost matrix of shape ``(len(mu), len(nu))``, normalized to max 1 so that
        the eps schedule means the same thing regardless of grid units.
    eps_schedule : tuple of float
        Decreasing entropic regularization strengths.
    iters : int
        Sinkhorn iterations per stage. The default leaves the marginals about
        4e-4 off, which is convergence rather than an entropic floor: 1000
        reaches 2e-6 and 3000 reaches 7e-8. Ample for a seed that phase retrieval
        will refine, so the default buys speed. Raise it if you need the plan
        itself to be accurate.

    Returns
    -------
    P : ndarray
        Transport plan of shape ``(len(mu), len(nu))``.
    """
    f = np.zeros(len(mu))
    g = np.zeros(len(nu))
    lmu, lnu = np.log(mu), np.log(nu)

    for eps in eps_schedule:
        for _ in range(iters):
            f = -eps * np.logaddexp.reduce((g[None, :] - C) / eps + lnu[None, :], axis=1)
            g = -eps * np.logaddexp.reduce((f[:, None] - C) / eps + lmu[:, None], axis=0)

    eps = eps_schedule[-1]
    return np.exp((f[:, None] + g[None, :] - C) / eps + lmu[:, None] + lnu[None, :])


def transport_phase(
    source_intensity,
    target_intensity,
    farfield_shape=None,
    coarse=4,
    threshold=1e-3,
    eps_schedule=(0.05, 0.02, 0.008, 0.003, 0.001),
    iters=300,
):
    """
    Initial phase carrying ``source_intensity`` onto ``target_intensity``.

    The returned phase is a scalar potential, so its gradient is curl-free on the
    SLM plane. That does not by itself guarantee a vortex-free far field.

    Both intensities are treated as measures on a common pixel grid: the source
    on the SLM plane, the target on the farfield plane. They are matched by
    optimal transport, and the resulting map is integrated to a phase.

    Parameters
    ----------
    source_intensity : ndarray
        Nearfield (SLM-plane) intensity, shape ``(h, w)``. Need not be normalized.
    target_intensity : ndarray
        Farfield target intensity. May be larger than the source if the
        computational grid is padded. NaNs (slmsuite's MRAF noise region) are
        treated as zero.
    farfield_shape : (int, int) or None
        Shape of the padded FFT grid, which sets the mapping between a farfield
        pixel offset and the phase gradient that steers light there. Defaults to
        ``target_intensity.shape``. Pass this explicitly if the target you hand
        in has been cropped.
    coarse : int
        Downsampling factor for the transport problem. Sinkhorn is O(n*m) per
        iteration in the number of *active* pixels, so this is the main cost
        knob. 4 is a reasonable default; the recovered potential is smooth, so
        little is lost by solving it coarsely and interpolating.
    threshold : float
        Pixels below this fraction of the max are dropped from the transport
        problem. Keeps near-zero mass from dominating the log-domain updates.
    eps_schedule, iters
        Passed to :func:`sinkhorn_log`.

    Returns
    -------
    phase : ndarray
        Initial phase in radians, shape ``source_intensity.shape``, zero mean.
        Not wrapped: hand it to a hologram as a custom phase and let the caller
        wrap it.

    Notes
    -----
    The gradient convention follows the centered-FFT forward model
    ``E_ff[k] = sum_x E_nf[x] exp(-2 pi i k.x / N)``. Stationary phase gives
    ``k = (N / 2 pi) grad(phi)``, so light at SLM pixel ``x`` lands at farfield
    offset ``k`` when ``grad(phi)(x) = 2 pi k / N``. That is the field this
    routine integrates.
    """
    src_I = np.asarray(source_intensity, dtype=float)
    tgt_I = np.nan_to_num(np.asarray(target_intensity, dtype=float), nan=0.0)

    if src_I.ndim != 2 or tgt_I.ndim != 2:
        raise ValueError("source_intensity and target_intensity must both be 2D")
    if np.any(src_I < 0) or np.any(tgt_I < 0):
        raise ValueError("intensities must be nonnegative")
    if src_I.max() <= 0 or tgt_I.max() <= 0:
        raise ValueError("intensities must not be identically zero")

    N_ff = np.asarray(tgt_I.shape if farfield_shape is None else farfield_shape, dtype=float)

    # --- coarse grids -------------------------------------------------------
    # Crop to a multiple of `coarse` rather than padding, so no fictitious
    # zero-intensity border is introduced into the transport problem.
    def block_mean(a):
        h, w = (np.array(a.shape) // coarse) * coarse
        if h == 0 or w == 0:
            raise ValueError(f"coarse={coarse} is too large for shape {a.shape}")
        a = a[:h, :w]
        return a.reshape(h // coarse, coarse, w // coarse, coarse).mean(axis=(1, 3))

    src_c, tgt_c = block_mean(src_I), block_mean(tgt_I)

    def centers(n_coarse, n_full):
        """Coarse-block centers in full-grid pixels, measured from grid center."""
        return np.arange(n_coarse) * coarse + (coarse - 1) / 2.0 - n_full / 2.0

    ys = centers(src_c.shape[0], src_I.shape[0])
    xs_ = centers(src_c.shape[1], src_I.shape[1])
    yt = centers(tgt_c.shape[0], tgt_I.shape[0])
    xt = centers(tgt_c.shape[1], tgt_I.shape[1])

    Ys, Xs = np.meshgrid(ys, xs_, indexing="ij")
    Yt, Xt = np.meshgrid(yt, xt, indexing="ij")

    src_mask = src_c > src_c.max() * threshold
    tgt_mask = tgt_c > tgt_c.max() * threshold

    mu = src_c[src_mask].astype(float)
    nu = tgt_c[tgt_mask].astype(float)
    mu /= mu.sum()
    nu /= nu.sum()

    pts_s = np.stack([Ys[src_mask], Xs[src_mask]], axis=1)
    pts_t = np.stack([Yt[tgt_mask], Xt[tgt_mask]], axis=1)

    # --- transport ----------------------------------------------------------
    C = ((pts_s[:, None, :] - pts_t[None, :, :]) ** 2).sum(-1)
    C /= C.max()

    P = sinkhorn_log(mu, nu, C, eps_schedule=eps_schedule, iters=iters)
    T = (P @ pts_t) / P.sum(1, keepdims=True)  # barycentric projection

    # --- integrate grad(phi) = 2 pi T / N_ff --------------------------------
    gy = np.zeros(src_c.shape)
    gx = np.zeros(src_c.shape)
    gy[src_mask] = 2 * np.pi * T[:, 0] / N_ff[0]
    gx[src_mask] = 2 * np.pi * T[:, 1] / N_ff[1]

    # Integrate grad(psi) = g by WEIGHTED least squares over the illuminated
    # region: minimise sum_i w_i |grad(psi)_i - g_i|^2, with w the source
    # intensity. Zero weight outside the beam, so the undefined part of the
    # transport map contributes nothing and needs no invented fill.
    #
    # A plain Neumann Poisson solve is the obvious thing here and it is wrong.
    # Two ways it fails, both measured rather than guessed:
    #   - a blaze has zero Laplacian, so all of it lives in the boundary flux
    #     that a homogeneous-Neumann solve discards;
    #   - a linear residual field has CONSTANT divergence, which zero-flux
    #     boundaries cannot support at all, so the solver quietly splits the
    #     difference and returns a phase that under-deflects. On a pure
    #     translation of 10 px it delivered 6.
    # Least squares has neither problem: no boundary condition is imposed, and
    # the normal equations are consistent by construction.
    #
    # Work in radians per COARSE pixel to match the difference operators.
    gy_c, gx_c = gy * coarse, gx * coarse
    w = np.where(src_mask, src_c, 0.0).astype(float)
    if w.sum() <= 0:
        raise ValueError("no illuminated pixels survived thresholding")
    w = w / w.max()

    # Central differences, not forward. A forward difference estimates the
    # gradient at the FACE i+1/2, so pairing it with g sampled at cell centers
    # biases every quadratic term by (pi/N)*coarse^2 -- which on a 10 px
    # translation is most of the deflection. Central differences are centered
    # where g actually lives.
    def dy_f(a):
        out = np.zeros_like(a)
        out[1:-1] = 0.5 * (a[2:] - a[:-2])
        out[0] = a[1] - a[0]
        out[-1] = a[-1] - a[-2]
        return out

    def dx_f(a):
        out = np.zeros_like(a)
        out[:, 1:-1] = 0.5 * (a[:, 2:] - a[:, :-2])
        out[:, 0] = a[:, 1] - a[:, 0]
        out[:, -1] = a[:, -1] - a[:, -2]
        return out

    def dy_adj(r):
        out = np.zeros_like(r)
        out[2:] += 0.5 * r[1:-1]
        out[:-2] -= 0.5 * r[1:-1]
        out[1] += r[0]; out[0] -= r[0]
        out[-1] += r[-1]; out[-2] -= r[-1]
        return out

    def dx_adj(r):
        out = np.zeros_like(r)
        out[:, 2:] += 0.5 * r[:, 1:-1]
        out[:, :-2] -= 0.5 * r[:, 1:-1]
        out[:, 1] += r[:, 0]; out[:, 0] -= r[:, 0]
        out[:, -1] += r[:, -1]; out[:, -2] -= r[:, -1]
        return out

    def normal_op(psi):
        return dy_adj(w * dy_f(psi)) + dx_adj(w * dx_f(psi))

    rhs = dy_adj(w * gy_c) + dx_adj(w * gx_c)

    # Conjugate gradient on the normal equations. The operator's null space
    # includes the constant mode (the additive gauge), which we project out each
    # step. Weights are zero outside the illuminated region, so pixels far from
    # the beam are also unconstrained, and disconnected illuminated regions would
    # add further free modes. Those modes carry no light, so they do not affect
    # the delivered pattern, but the recovered phase there is arbitrary.
    def project(a):
        return a - a.mean()

    psi_c = np.zeros_like(src_c, dtype=float)
    r = project(rhs - normal_op(psi_c))
    p_dir = r.copy()
    rs = float((r * r).sum())
    rs0 = rs
    for _ in range(2000):
        Ap = project(normal_op(p_dir))
        denom = float((p_dir * Ap).sum())
        if denom <= 0:
            break
        alpha = rs / denom
        psi_c += alpha * p_dir
        r -= alpha * Ap
        rs_new = float((r * r).sum())
        if rs_new <= rs0 * 1e-14:
            break
        p_dir = r + (rs_new / rs) * p_dir
        rs = rs_new
    psi_c = project(psi_c)

    # --- back to the full SLM grid ------------------------------------------
    ky_full = np.arange(src_I.shape[0]) - src_I.shape[0] / 2.0
    kx_full = np.arange(src_I.shape[1]) - src_I.shape[1] / 2.0
    # Cubic needs 4 points per axis; fall back to linear on very small grids.
    deg = (min(3, len(ys) - 1), min(3, len(xs_) - 1))
    phase = RectBivariateSpline(ys, xs_, psi_c, kx=deg[0], ky=deg[1])(ky_full, kx_full)

    return phase - phase.mean()
