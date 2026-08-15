1. **FATAL — The “projection law” is tested only in an exactly separable cubic lattice, so the dimensional generalization is not tested.**  
   Exact quote: `lat = LatticeD(np.diag([2., 2., 2.]), {(1, 0, 0): A, (0, 1, 0): A, (0, 0, 1): A}, n=3)`  
   This Hamiltonian is exactly a Kronecker sum \(H_x+H_y+H_z\). Each Cartesian crossing is therefore an independent 1D Landau–Zener problem by construction. It cannot establish the stated general claim that “only that plane's own Fourier amplitude sets the gap.” In a nonseparable lattice, indirect coupling paths dress the gap, and at intersecting Bragg planes the relevant multilevel gap generally depends on several Fourier components. The campaign contains no nonorthogonal \(B\), mixed Fourier vector such as `(1,1,0)`, or genuinely coupled multidimensional crossing.

2. **ERROR — The reported “loss” for tilted single-plane sweeps includes excitation in all transverse directions, not just tunneling at the \(b_1\) plane.**  
   Exact quote: `loss = 1.0 - pops[0]`  
   For \(\theta>0\), \(Q_y\) also moves, and `pops[0]` is the overlap with the full multidimensional ground state. Thus  
   \[
   1-P_{\rm gs}^{(x)}P_{\rm gs}^{(y)}P_{\rm gs}^{(z)}
   \]
   is compared with an \(x\)-plane-only LZ probability. This is not a projection onto the \(b_1\) subsystem or a conditional \(b_1\) loss. The chosen endpoint can be especially contaminated:  
   Exact quote: `margin = min(1.6, 0.85 / max(np.tan(...)))`  
   At \(30^\circ\), the sweep ends at \(Q_y=0.85\), only \(0.15\) before the \(y\)-zone edge. A transverse reference run or factorized subsystem projection is required.

3. **FATAL — The “corner factorization” result is tautological for the chosen potential and does not adjudicate generic corner physics.**  
   Exact quote: `indep = 1.0 - (1.0 - P1) ** 2`  
   With diagonal \(B\) and only independent \(\cos 2x,\cos 2y,\cos 2z\) terms, the wavefunction evolution and instantaneous ground-state overlap factorize exactly, up to finite-cutoff and finite-time errors. Agreement with independent crossings is imposed by separability, not discovered. It cannot be generalized to a corner with mixed reciprocal couplings, nonorthogonal vectors, or nonseparable Fourier components.

4. **ERROR — The three-state “loss \(=P_1^2\)” interpretation is incompatible with the loss observable used in `lattice3D.py`.**  
   Exact quote: `(i) Gemini's 3-state Demkov-Osherov reduction (|b1+b2> ignored): collective sqrt(2) coupling -> loss = P1^2`  
   The lattice observable defines success as occupation of the post-crossing instantaneous ground state, which at the diagonal corner is carried into \(|b_1+b_2\rangle\). A model that omits this state has no successful output channel under that definition: all of its final population is outside the true ground state. `p3[0]` is only the probability to remain in the original diabatic state; it is not the total ground-band loss because populations in the one-recoil states are also loss. The claimed three-vs-four-state adjudication therefore compares different observables.

5. **ERROR — The reduced-model integrations do not reproduce the lattice protocol.**  
   Exact quotes: `s0, s1, nt = 0.0, 2.0, 400000`, `c[0] = 1.0`, and `4-state loss (1 - carried)`  
   `lattice3D.py` starts in the instantaneous ground eigenstate at \(s=0\) and, for the corner campaign, projects onto an instantaneous eigenstate at \(s=1.5\). `corner_probe.py` instead starts in a bare diabatic state and reads bare populations at \(s=2\). Finite-time LZ corrections and endpoint dressing are therefore different. These calculations cannot be directly compared to the hard-coded lattice number.

6. **ERROR — The asserted \(3\times10^{-4}\) agreement is contradicted by the displayed parameters and number.**  
   Exact quotes: `matched (ii) at 3e-4` and `loss = 0.68188 (A=0.3, g=0.12)`  
   For those parameters,
   \[
   P_1=\exp\!\left[-\frac{\pi(0.3)^2}{4(2)(0.12/\sqrt2)}\right]\approx0.4346,
   \quad
   2P_1-P_1^2\approx0.6803\text{–}0.6804.
   \]
   The discrepancy from `0.68188` is about \(1.5\times10^{-3}\), not \(3\times10^{-4}\). The measured value is also hard-coded rather than generated or loaded by `corner_probe.py`.

7. **ERROR — The LZ routine is sign-invalid for a general crossing direction.**  
   Exact quote: `slew = float(np.dot(b_vec, g_vec)) / 2.0`  
   The exponent requires the magnitude of the diabatic slope, hence \(|b\cdot\dot Q|\). A reverse crossing or the equivalent choice \(-b\) produces a negative denominator and an unphysical probability greater than one. Zero or tangential slew is likewise untreated. Use `abs(np.dot(...))` and explicitly reject zero slew.

8. **ERROR — `sweep_through_plane` claims a geometric angle it does not implement for general `B`.**  
   Exact quotes: `tilted by theta from the b1 normal (in the b1-b2 plane)` and `ghat[0] = np.cos(th); ghat[1] = np.sin(th)`  
   These are laboratory Cartesian axes, not normalized directions constructed from `lat.B[0]` and `lat.B[1]`. The angle and the `cot(theta)` crossing-order argument are valid only for the specific diagonal cubic matrices used here. This contradicts the advertised general \(d\)-dimensional solver and invalidates use on nonorthogonal reciprocal bases.

9. **ERROR — The finite-time campaign is compared directly with an asymptotic Landau–Zener formula without endpoint convergence.**  
   Exact quote: `t_end = margin * t_cross`  
   The evolution starts at finite detuning and ends only \(35\%-60\%\) beyond the crossing; the corner ends at `margin=1.5`. The largest gap, \(A=0.45\), is not parametrically negligible relative to these endpoint detunings. Instantaneous-eigenstate initialization/projection does not make the finite-time transition probability equal to the infinite-time LZ result. No margin extrapolation is performed, so percent-level agreement or disagreement cannot be assigned to the claimed law.

10. **ERROR — The “loss-optimal” and “122x” ramp claims are not supported by the optimization performed.**  
    Exact quotes: `loss-optimal shuttle ramps` and `for v_ratio in (0.5, 0.35, 0.25, 0.15): for w in (0.5, 0.8, 1.2):`  
    This is a 12-point scan inside one hand-selected two-parameter family for one \(A,T,N\). It neither establishes an optimum nor compares against general admissible controls. No maximum-speed, acceleration, bandwidth, or robustness constraint is imposed, so “optimal” and a general 122-fold advantage are overclaims. The ratio is merely the best in-sample ratio for this one scan.

11. **ERROR — The claimed \(0.28\%\) optimized loss lacks the numerical convergence needed for such a small residual.**  
    Exact quotes: `nt=6000`, `n=8`, and `BEST: loss=...`  
    There is no timestep refinement, cutoff refinement, trajectory-grid refinement, eigensolver-tolerance study, or norm/error report. The best point is selected by minimizing small differences over the same unconverged scan, making the minimum especially vulnerable to discretization error or coherent finite-time oscillations. A \(2.8\times10^{-3}\) result cannot support a 122x ratio without demonstrated absolute errors well below that scale.

12. **MINOR — The corner quantity is mislabeled in the source comment.**  
    Exact quote: `indep = 1.0 - (1.0 - P1) ** 2          # survival (1-P1) per plane, two planes`  
    The expression is total **loss**, while two-plane survival is \((1-P_1)^2\). The code compares it to `loss`, so the numerical expression is consistent, but the comment reverses the observable and contributes to the later three-state confusion.

**VERDICT: UNSOUND**