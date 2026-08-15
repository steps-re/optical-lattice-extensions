# phase_diversity.py — roadmap item 3: the solver his empty PhaseDiversity repo
# was named for. Recover the UNKNOWN complex input field E_in hitting the SLM
# from K far-field intensity images taken with known defocus probes.
#
# Truth: a Gaussian with smooth Zernike-like phase aberrations + amplitude
# nonuniformity. Probes: quadratic defocus phases of varying strength.
# Joint GS across all probes; metric = complex field fidelity.
import numpy as np, json
from numpy.fft import fft2, ifft2, fftshift, ifftshift

rng = np.random.default_rng(11)
root = '/private/tmp/claude-501/-Users-mike-Documents-Claude/325cb1ea-d772-429f-8fbb-7d3ef2b01dc0/scratchpad'
N = 256
x = np.arange(N) - N/2
X, Y = np.meshgrid(x, x, indexing='ij')
R2 = (X**2 + Y**2)
w0 = 52.0

# ---- ground truth input field (what a real lab beam looks like) ----
amp = np.exp(-R2 / w0**2) * (1 + 0.15 * np.exp(-((X-20)**2 + (Y+15)**2) / 40**2))
xr, yr = X / 80.0, Y / 80.0
aberr = (0.9 * (2*xr*yr)                        # astigmatism 45
         + 0.7 * (xr**2 - yr**2)                # astigmatism 0
         + 0.5 * (3*(xr**2+yr**2) - 2) * xr     # coma-x
         + 0.4 * np.sin(2.2*xr + 1.3))          # something non-Zernike
E_true = amp * np.exp(1j * aberr)

# ---- measurements: K defocus probes, far-field intensities ----
K = 6
probes = [c * R2 / 90.0**2 for c in np.linspace(-6, 6, K)]
def ff(E): return fftshift(fft2(ifftshift(E)))
def iff(E): return fftshift(ifft2(ifftshift(E)))
I_meas = [np.abs(ff(E_true * np.exp(1j*p)))**2 for p in probes]
# true Poisson shot noise: scale so the brightest pixel across probes has
# ~1e4 counts (a realistic camera well depth), then draw Poisson counts
PEAK = 1.0e4
scale = PEAK / max(I.max() for I in I_meas)
I_meas = [rng.poisson(I * scale).astype(float) for I in I_meas]

# ---- joint phase-diversity GS ----
def fidelity(E, F):
    return np.abs(np.vdot(E, F))**2 / (np.vdot(E, E).real * np.vdot(F, F).real)

E = np.exp(-R2 / w0**2).astype(complex)          # start: ideal Gaussian, flat phase
hist = []
for it in range(120):
    acc = np.zeros_like(E)
    for p, I in zip(probes, I_meas):
        Ef = ff(E * np.exp(1j*p))
        Ef = np.sqrt(I) * np.exp(1j * np.angle(Ef))   # enforce this image
        acc += iff(Ef) * np.exp(-1j*p)                # back out the probe
    E = acc / K
    hist.append(float(fidelity(E, E_true)))

F = fidelity(E, E_true)
# amplitude & phase errors within the beam (where amp > 5% max)
mask = amp > 0.05 * amp.max()
# remove global phase AND global scale before comparing (the Poisson-count
# reconstruction carries the camera's count scale, not the field's units)
E_al = E * np.exp(-1j * np.angle(np.vdot(E_true, E)))
E_al = E_al * (np.vdot(E_al, E_true).real / np.vdot(E_al, E_al).real)
amp_err = float(np.linalg.norm((np.abs(E_al)-amp)[mask]) / np.linalg.norm(amp[mask]))
ph_err = float(np.std(np.angle(E_al * np.conj(E_true))[mask]))
print(f"phase-diversity recovery: fidelity |<E|E_true>|^2 = {F:.5f}")
print(f"  amplitude error {amp_err*100:.2f}%   residual phase RMS {ph_err*1000:.1f} mrad")
np.savez(f'{root}/phase_diversity.npz', E_true=E_true, E_rec=E_al, amp=amp,
         aberr=aberr, hist=np.array(hist), mask=mask)
json.dump(dict(fidelity=F, amp_err=amp_err, phase_rms_mrad=ph_err*1000, K=K),
          open(f'{root}/phase_diversity.json', 'w'))
