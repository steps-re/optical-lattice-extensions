# lattice3D.py — d-dimensional generalization of Hunter Swan's lattice1D.py.
# Same conventions: natural units hbar = 1, 2m = 1, kinetic energy = |p|^2.
#
# A minimal d-dimensional lattice (d+1 lasers) gives a potential
#   V(x) = sum_c A_c cos(b_c . x)
# over a set of reciprocal vectors b_c (integer combinations of a basis B).
# We evolve a state on the momentum lattice { q + m . B : m in Z^d } through a
# uniformly accelerated frame Q(t) = g_vec * t / 2 (gravity-driven sweep, as in
# his HParams p_g = grav*t/2), and measure ground-band survival by projecting
# onto instantaneous band eigenstates — the d-dimensional SFrame.
#
# The claim under test (the "projection law", generalizing his 1D story):
# crossing the Bragg plane of reciprocal vector b costs
#   P_tunnel = exp( - 2 pi (A_b/2)^2 / (2 b . Qdot) ) = exp( - pi A_b^2 / (4 b . Qdot) )
# i.e. only the component of the sweep normal to the Bragg plane matters,
# and only that plane's own Fourier amplitude sets the gap.
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import eigsh, expm_multiply


class LatticeD:
    """Momentum-space d-dimensional lattice with cutoff n (grid (2n+1)^d)."""

    def __init__(self, B, couplings, n):
        """B: (d,d) reciprocal basis, rows are b_i.
        couplings: dict {integer tuple m: amplitude} meaning A cos((m.B).x).
        n: momentum cutoff per axis."""
        self.B = np.asarray(B, float)
        self.d = self.B.shape[0]
        self.n = n
        self.shape = (2 * n + 1,) * self.d
        self.N = np.prod(self.shape)
        # integer coordinates of every momentum lattice site
        grids = np.meshgrid(*[np.arange(-n, n + 1)] * self.d, indexing='ij')
        self.m = np.stack([g.ravel() for g in grids], axis=1)      # (N, d)
        self.couplings = {tuple(k): v for k, v in couplings.items()}

    def momenta(self, q):
        return q[None, :] + self.m @ self.B                        # (N, d)

    def _shift_pairs(self):
        """For each coupling vector, the (row, col) index pairs it connects."""
        idx = np.arange(self.N).reshape(self.shape)
        pairs = []
        for mv, amp in self.couplings.items():
            src = idx
            dst = idx
            sl_src = tuple(slice(max(0, -s), (2*self.n+1) + min(0, -s)) for s in mv)
            sl_dst = tuple(slice(max(0, s), (2*self.n+1) + min(0, s)) for s in mv)
            pairs.append((amp / 2.0, src[sl_src].ravel(), dst[sl_dst].ravel()))
        return pairs

    def hamiltonian(self, q, Q=None):
        """Sparse H at quasimomentum q in frame momentum offset Q."""
        P = self.momenta(q)
        if Q is not None:
            P = P - Q[None, :]
        dia = np.einsum('ij,ij->i', P, P)
        rows, cols, vals = [np.arange(self.N)], [np.arange(self.N)], [dia]
        for amp2, s, t in self._shift_pairs():
            rows += [s, t]; cols += [t, s]; vals += [np.full(len(s), amp2)] * 2
        H = sparse.csr_matrix((np.concatenate(vals),
                               (np.concatenate(rows), np.concatenate(cols))),
                              shape=(self.N, self.N))
        return H

    def ground_state(self, q, Q=None, nbands=1):
        H = self.hamiltonian(q, Q)
        vals, vecs = eigsh(H, k=max(nbands, 2), which='SA')
        order = np.argsort(vals)
        return vals[order][:nbands], vecs[:, order][:, :nbands]

    def evolve(self, q, g_vec, t_end, nt=2000, c0=None, Q_of_t=None):
        """Integrate i dc/dt = H(t) c via short-time Krylov exponentials
        (expm_multiply) on the piecewise-frozen H, midpoint-evaluated
        (2nd-order accurate). Default frame trajectory is the gravity sweep
        Q(t) = g_vec t / 2; pass Q_of_t(t) -> (d,) array for arbitrary ramps."""
        if Q_of_t is None:
            g_vec = np.asarray(g_vec, float)
            Q_of_t = lambda t: g_vec * t / 2.0
        if c0 is None:
            _, v = self.ground_state(q, Q=Q_of_t(0.0))
            c = v[:, 0].astype(complex)
        else:
            c = c0.astype(complex)
        ts = np.linspace(0.0, t_end, nt + 1)
        dt = ts[1] - ts[0]
        for i in range(nt):
            H = self.hamiltonian(q, Q=Q_of_t(ts[i] + dt / 2.0))
            c = expm_multiply(-1j * H * dt, c)
        return c

    def band_populations(self, c, q, Q, nbands=3):
        """Project c onto instantaneous band eigenstates at frame offset Q."""
        H = self.hamiltonian(q, Q=Q)
        vals, vecs = eigsh(H, k=nbands + 2, which='SA')
        order = np.argsort(vals)
        vecs = vecs[:, order]
        return np.array([np.abs(vecs[:, b].conj() @ c) ** 2 for b in range(nbands)])


def bragg_projection_law(A, b_vec, g_vec):
    """P_tunnel = exp(-pi A^2 / (4 b . Qdot)), Qdot = g_vec/2."""
    slew = abs(float(np.dot(b_vec, g_vec))) / 2.0
    if slew == 0.0:
        raise ValueError("sweep is tangential to the Bragg plane: no crossing")
    return np.exp(-np.pi * A ** 2 / (4.0 * slew))


def sweep_through_plane(lat, A, g, theta_deg, n_t=2400, margin=1.35):
    """3D gravity sweep tilted by theta from the b1 normal (in the b1-b2 plane).
    Ends after the b1 Bragg-plane crossing; returns measured loss + prediction."""
    th = np.radians(theta_deg)
    ghat = np.zeros(lat.d)
    ghat[0] = np.cos(th)
    if lat.d > 1:
        ghat[1] = np.sin(th)
    g_vec = g * ghat
    b1 = lat.B[0]
    # crossing when Q . b1hat = |b1|/2, Q = g_vec t/2
    t_cross = (np.linalg.norm(b1) / 2.0) / (np.dot(g_vec, b1) / np.linalg.norm(b1) / 2.0)
    t_end = margin * t_cross
    q = np.zeros(lat.d)
    c = lat.evolve(q, g_vec, t_end, nt=n_t)
    pops = lat.band_populations(c, q, Q=g_vec * t_end / 2.0, nbands=3)
    loss = 1.0 - pops[0]
    pred = bragg_projection_law(A, b1, g_vec)
    return float(loss), float(pred), pops
