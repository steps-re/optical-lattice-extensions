# corner_probe.py — adjudicate the dual-model review dispute over the 45-degree
# corner. Three candidate theories for the diagonal sweep loss:
#   (i)  Gemini's 3-state Demkov-Osherov reduction (|b1+b2> ignored):
#        collective sqrt(2) coupling -> loss = P1^2
#   (ii) independent-crossings factorization: loss = 1-(1-P1)^2
#   (iii) the full lattice answer (lattice3D.py measured): matched (ii) at 3e-4
# Probe: integrate BOTH reduced models exactly (dense few-level, linear-in-s
# diabatic energies taken from the true lattice geometry) and compare.
import numpy as np
from scipy.linalg import expm

A = 0.30; g = 0.12
alpha_s = g / (2 * np.sqrt(2))         # sdot: Q=(s,s), s = g t cos45 / 2
V = A / 2.0
# per-plane single-crossing LZ (the building block P1), slew d(dE)/dt = 4*sdot
P1 = np.exp(-2 * np.pi * V**2 / (4 * alpha_s))
print(f"P1 (per-plane) = {P1:.5f}")
print(f"theory (i)  3-state collective: loss = P1^2        = {P1**2:.5f}")
print(f"theory (ii) factorized:         loss = 2P1 - P1^2  = {2*P1-P1**2:.5f}")
print(f"lattice3D measured (run_3d.py): loss = 0.68188 (A=0.3, g=0.12)")

def run_model(nlev):
    """Integrate the reduced model with diabatic energies from the true
    geometry: E0=2s^2, E1=E2=(2-s)^2+s^2, E3=2(2-s)^2; couplings V on
    0-1, 0-2 and (if nlev==4) 1-3, 2-3. Start in level 0 well before s=1."""
    s0, s1, nt = 0.0, 2.0, 400000
    ss = np.linspace(s0, s1, nt + 1)
    dt = (ss[1] - ss[0]) / alpha_s
    c = np.zeros(nlev, complex); c[0] = 1.0
    for i in range(nt):
        s = ss[i] + (ss[1]-ss[0])/2
        E = [2*s**2, (2-s)**2 + s**2, (2-s)**2 + s**2, 2*(2-s)**2][:nlev]
        H = np.diag(E).astype(complex)
        H[0,1] = H[1,0] = V; H[0,2] = H[2,0] = V
        if nlev == 4:
            H[1,3] = H[3,1] = V; H[2,3] = H[3,2] = V
        c = expm(-1j * H * dt) @ c
    return np.abs(c)**2

p3 = run_model(3)
p4 = run_model(4)
print(f"\n3-state integration: pops={p3.round(5)}  -> stay-in-|0> = {p3[0]:.5f} (Gemini predicts P1^2={P1**2:.5f})")
print(f"4-state integration: pops={p4.round(5)}")
print(f"  4-state carried-through (|b1+b2>) = {p4[3]:.5f}; factorized (1-P1)^2 = {(1-P1)**2:.5f}")
print(f"  4-state loss (1 - carried) = {1-p4[3]:.5f} vs measured lattice 0.68188 vs 2P1-P1^2 = {2*P1-P1**2:.5f}")
