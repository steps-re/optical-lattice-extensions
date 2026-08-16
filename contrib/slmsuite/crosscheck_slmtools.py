"""Compare SLMTools' otPhase output against our transport_phase on identical inputs.

Conversion between conventions, derived from their source: natural-lattice
coordinates are pixels/sqrt(n) and phase is in cycles, so phi_rad = 2*pi*Phi and
per-pixel gradients compare directly.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transport_seed import transport_phase

n = 64
s = np.sqrt(n)
coords = np.arange(-np.floor(n / 2), np.floor((n - 1) / 2) + 1) / s
X, Y = np.meshgrid(coords, coords, indexing="ij")

wnat = 15 / s
U = np.exp(-2 * (X**2 + Y**2) / wnat**2)
hw, ed = 20 / s, 2 / s
V = 0.5 * (1 - np.tanh((np.maximum(np.abs(X), np.abs(Y)) - hw) / ed))
V[V < V.max() * 0.01] = 0

Uj = np.loadtxt("cc_U.csv", delimiter=",")
Vj = np.loadtxt("cc_V.csv", delimiter=",")
print(f"input replication: |dU|max={np.abs(U-Uj).max():.2e} |dV|max={np.abs(V-Vj).max():.2e}")

phi_j = 2 * np.pi * np.loadtxt("cc_phi.csv", delimiter=",")       # theirs, radians
phi_o = transport_phase(U, V, farfield_shape=(n, n), coarse=2)     # ours, radians
amp = np.sqrt(U)
support = V > V.max() * 0.5
core = U > U.max() * 0.5

def farfield(phi):
    E = np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(amp * np.exp(1j * phi))))
    I = np.abs(E) ** 2
    return E, I / I.sum()

def vortices(E):
    """Winding count INSIDE the target support, matching the main benchmark.
    Whole-plane counts are dominated by phase noise in dark regions and mean
    nothing."""
    th = np.angle(E)
    def w(a): return (a + np.pi) % (2 * np.pi) - np.pi
    c = (w(th[1:, :-1] - th[:-1, :-1]) + w(th[1:, 1:] - th[1:, :-1])
         + w(th[:-1, 1:] - th[1:, 1:]) + w(th[:-1, :-1] - th[:-1, 1:]))
    return int(((np.abs(c) > np.pi) & support[:-1, :-1]).sum())

def gs(phi, it=100):
    ph = phi.copy()
    sV = np.sqrt(V)
    for _ in range(it):
        E = np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(amp * np.exp(1j * ph))))
        E = sV * np.exp(1j * np.angle(E))
        ph = np.angle(np.fft.fftshift(np.fft.ifft2(np.fft.ifftshift(E))))
    return ph

print("\nseed-only (no iterations):")
for name, ph in (("SLMTools otPhase", phi_j), ("ours transport_phase", phi_o)):
    E, I = farfield(ph)
    inside = I[support]
    print(f"  {name:<22} efficiency {inside.sum():.3f}  ripple {inside.std()/inside.mean():.3f}  vortices(in support) {vortices(E)}")

print("\nagreement in the illuminated core:")
gy_j, gx_j = np.gradient(phi_j)
gy_o, gx_o = np.gradient(phi_o)
gdiff = np.hypot(gy_j - gy_o, gx_j - gx_o)[core]
gmag = np.hypot(gy_o, gx_o)[core]
d = (phi_j - phi_o)[core]
print(f"  gradient RMS diff / RMS magnitude: {np.sqrt((gdiff**2).mean()):.4f} / {np.sqrt((gmag**2).mean()):.4f}"
      f" = {np.sqrt((gdiff**2).mean())/np.sqrt((gmag**2).mean()):.1%}")
print(f"  phase std after piston removal: {(d - d.mean()).std():.3f} rad")

print("\ntranslation control (8 px shift), theirs:")
phi2 = 2 * np.pi * np.loadtxt("cc_phi_shift.csv", delimiter=",")
# The shift is along the FIRST index in the CSV layout (Julia comprehension
# order), so the blaze lives on axis 0.
slope = np.gradient(phi2, axis=0)[core].mean()
print(f"  measured blaze {slope:.4f} rad/px, expected {2*np.pi*8/n:.4f}, ratio {slope/(2*np.pi*8/n):.3f}")

print("\nafter 100 GS iterations (our loop, both seeds):")
for name, ph in (("from SLMTools seed", phi_j), ("from our seed", phi_o)):
    E, I = farfield(gs(ph))
    inside = I[support]
    print(f"  {name:<22} efficiency {inside.sum():.3f}  ripple {inside.std()/inside.mean():.3f}  vortices {vortices(E)}")

print("\ntheir own gs(100) output, propagated by us:")
phg = np.loadtxt("cc_phigs.csv", delimiter=",")
E, I = farfield(phg)
print(f"  efficiency {I[support].sum():.3f}  vortices {vortices(E)}")
