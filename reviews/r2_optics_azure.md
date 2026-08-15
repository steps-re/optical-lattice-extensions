1. **FATAL — The OT phase reconstruction has an erroneous extra factor \(s^2=16\).**  
   Exact quote:
   ```python
   div = (np.gradient(gx, axis=0) + np.gradient(gy, axis=1)) * s
   ...
   psi_c = idctn(np.where(lam != 0, d * (s**2) / lam, 0.0), ...)
   ```
   Here `gx,gy` are gradients per fine-grid pixel, while one coarse-index step is \(s\) fine pixels. The first multiplication by `s` already converts the divergence for a discrete coarse-index Poisson equation. Multiplying the Poisson solution by another `s**2` scales the phase by 16. Thus `phi0` is not the potential whose gradient implements `T_map`; any claimed benefit cannot be attributed to the stated OT ray map.

2. **ERROR — The claimed Brenier/OT construction is not what the code computes.**  
   Exact quote:
   ```python
   # ... vortex-free by construction:
   # Brenier's theorem, T = grad(convex psi).
   ```
   followed by
   ```python
   gx = gx[tuple(idx)]; gy = gy[tuple(idx)]
   ...
   # Neumann Poisson: laplacian(psi) = div
   ```
   An entropically regularized barycentric map, thresholded support, nearest-neighbor extension, and Helmholtz projection via Poisson solve is not the exact Brenier map. The projection guarantees at most a curl-free least-squares field; it does not preserve convexity or exact mass transport. The “Brenier” and “vortex-free by construction” justification is therefore invalid.

3. **ERROR — The coarse-grid coordinates are shifted by half a fine pixel.**  
   Exact quote:
   ```python
   xc = (np.arange(Nc) - Nc/2 + 0.5) * s
   ```
   For blocks formed by
   ```python
   a.reshape(Nc, s, Nc, s).mean(...)
   ```
   from fine coordinates `np.arange(N)-N/2`, the block centers are
   \[
   x_c=is+(s-1)/2-N/2,
   \]
   which for `s=4` gives `-126.5, -122.5, ...`, not `-126, -122, ...`. Because the phase gradient uses the absolute target coordinate, this introduces a spurious half-pixel far-field tilt/shift.

4. **ERROR — The advertised “0.93% error” is a restricted-support metric, not total target error.**  
   Exact quote:
   ```python
   supp = I_T > I_T.max() * 0.5
   ...
   errs.append(np.linalg.norm((If_n - I_T)[supp]) /
               np.linalg.norm(I_T[supp]))
   ```
   All errors in the edge skirt and outside the half-maximum square are discarded. Consequently the headline “0.93% vs 3.3% error” cannot be presented as an overall intensity-reconstruction error without explicitly qualifying it as a half-maximum-support error.

5. **ERROR — One fixed random initialization is not a statistically valid GS/MRAF baseline.**  
   Exact quote:
   ```python
   phi_rd, err_rd, eff_rd = gs(rng.uniform(-np.pi, np.pi, (N, N)))
   ```
   and
   ```python
   phi_rd, err_rd = mraf(rng.uniform(-np.pi, np.pi, (N, N)))
   ```
   GS outcomes have substantial initialization dependence. Comparing the OT seed against one random draw cannot support claims such as “0.93% vs 3.3%” or “50 vs 316 vortices.” Multiple independent random starts, distributions/confidence intervals, and preferably comparison against the best or median baseline are required.

6. **ERROR — Reported final metrics do not correspond to the returned final phase.**  
   Exact quote:
   ```python
   errs.append(...)
   effs.append(...)
   ...
   phi = np.angle(E)
   return phi, np.array(errs), np.array(effs)
   ```
   The metric is recorded before each update, but `phi` is returned after the update. Thus `err_ot[-1]` and `eff_ot[-1]` describe the penultimate field, whereas ripple, vortices, and saved intensities describe the final field. The same off-by-one mismatch occurs in `mraf()`.

7. **ERROR — The crossing-iteration calculation silently reports zero if the target is never reached.**  
   Exact quote:
   ```python
   it_cross = int(np.argmax(err_ot <= err_rd[-1]))
   ```
   `np.argmax` returns `0` when the condition is false everywhere. The code would then falsely claim that the OT run reached the random final error at iteration zero. It also reports a zero-based index as an iteration count.

8. **ERROR — `mraf.py` is not implementing its declared MRAF mixing.**  
   Exact quote:
   ```python
   m = 0.45
   ```
   and
   ```python
   out = np.where(S, sqn * np.exp(1j*np.angle(Ef)), Ef)
   ```
   The declared mixing parameter is never used. This is a signal-region amplitude-projection GS variant, not the stated MRAF algorithm with the specified mixing factor. Results may be reported for this algorithm, but not as results for `m=0.45` MRAF.

9. **ERROR — The phase-diversity “shot-like noise” model is physically wrong and makes the fidelity claim unrealistically easy.**  
   Exact quote:
   ```python
   # add 1% shot-like noise (realism)
   I_meas = [I * (1 + 0.01 * rng.standard_normal(I.shape)) for I in I_meas]
   ```
   Shot-noise variance scales as intensity and requires a photon-count calibration; its relative noise grows in dim pixels. This model instead imposes approximately constant 1% relative Gaussian noise and essentially no absolute noise in dark pixels. Therefore “fidelity 0.99998 with 1% noise” is only a result for this synthetic multiplicative-noise model, not for 1% shot noise or a realistic camera measurement.

10. **FATAL — The cloud comparison is explicitly not at equal total beam power, despite being labeled that way.**  
    Exact quote:
    ```python
    # The two candidate lattice-illumination profiles, EQUAL TOTAL POWER:
    ```
    followed by
    ```python
    I_gauss = I_gauss_raw * (
        I_flat[_inside].sum() / I_gauss_raw[_inside].sum())
    ```
    This equalizes power only inside `r<40`, not total power. Yet the output says:
    ```python
    print(f"cloud-averaged shuttle survival (..., equal beam power):")
    ```
    The normalization deliberately removes shaper efficiency and is not an equal-input-power or equal-total-output-power comparison. The quoted survival advantage therefore does not establish the claimed same-power advantage.

11. **FATAL — The stated depth calibration contradicts the implemented calibration.**  
    Exact quote:
    ```python
    # Depth calibration: cloud-center depth under the GAUSSIAN beam = A0.
    ```
    but the code uses
    ```python
    I_ref = np.median(I_flat[d['core']])  # calibrate: plateau depth = A0
    A = A0 * I_map / I_ref
    ```
    This sets the flat-top plateau depth to `A0`, not the Gaussian center depth. Those are different experimental comparisons and produce different survival ratios. The reported `0.885 vs 0.565` is therefore not generated under the calibration described in the text.

12. **FATAL — The Landau–Zener exponent is unsupported because \(A\), \(g\), and the crossing Hamiltonian are never defined consistently.**  
    Exact quote:
    ```python
    # Survival per atom after N crossings:
    # (1 - exp(-pi A(r)^2 / 2 k g))^N.
    ```
    and
    ```python
    A0, k, g, Ncross = 0.50, 2.0, 0.0295 * 2, 3
    ```
    A “lattice depth” is not generally the diabatic coupling or the full avoided-crossing gap. For a conventional \(V_0\sin^2(kx)\) lattice, Fourier coupling, full gap, and lattice depth differ by factors of two or four, which become factors of four or sixteen in the exponent. The sweep slope also depends on whether `g` denotes force, acceleration, or quasimomentum rate in the stated \(2m=1\) units. No Hamiltonian derivation is supplied. Moreover, `(1-P)**Ncross` assumes independent incoherent crossings and excludes Stückelberg interference. The numerical survival values are therefore not physically established.

13. **FATAL — `rank_over_Z` does not compute rank over \(\mathbb Z\) or \(\mathbb Q\).**  
    Exact quote:
    ```python
    coef, *_ = np.linalg.lstsq(B, v, rcond=None)
    if ... and np.allclose(coef, np.round(coef), ...):
        continue
    ```
    Module rank is determined by integer/rational relations among all generators, not by whether each new vector is an integer combination of a greedily selected floating-point basis. For example, generators \(v\) and \(v/2\) have module rank one because \(2(v/2)-v=0\), but this routine reports rank two because the coefficient `0.5` is not an integer. Once more than \(d\) vectors have been added, the underdetermined least-squares solution is basis-dependent and has no number-theoretic meaning. Therefore all rank-criterion verdicts are unsupported even when the curated examples happen to receive expected labels.

14. **ERROR — The alleged physical four-laser lattice configuration violates the equal-wave-number constraint.**  
    Exact quote:
    ```python
    v0 = np.array([0.35, 0.8])
    k4 = [v0, v0+b1, v0+b2, v0+b1+2*b2]
    ```
    These vectors have different magnitudes. Coherent monochromatic free-space laser beams must have the same \(|\mathbf k|\). Thus this is an abstract Fourier construction, not the claimed non-minimal laser configuration.

15. **ERROR — The 3D “laser” rank test is not applied to the difference-vector module used in the stated criterion.**  
    Exact quote:
    ```python
    # ... rank criterion ... difference vectors {k_1l}
    ```
    but the 3D case does
    ```python
    r_real, r_mod = rank_over_Z(list(ico))
    ```
    rather than constructing laser wavevectors and passing their differences. Its displayed potential likewise uses
    ```python
    for k in ico:
        Vico += np.cos(k[0]*X + k[1]*Y)
    ```
    not the pair-interference potential used by `potential_2d`. It therefore does not demonstrate the stated laser-difference-vector criterion.

16. **ERROR — One symmetric pentagonal example does not demonstrate the claimed “general-position” theorem.**  
    Exact quote:
    ```python
    # numerically demonstrate his conjecture that
    # non-minimal lasers in general position give quasicrystals
    ```
    The code tests one specially symmetric regular pentagon and uses an invalid numerical module-rank routine. This neither samples general position nor establishes the generic/countable-exception claim.

**VERDICT: UNSOUND**