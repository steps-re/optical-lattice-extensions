1. **ERROR — internally contradictory numerical-accuracy claim.**  
   Exact quote: “the simulated loss matches eq. (\ref{LZloss}) to three decimal places, with the largest deviations ($\sim 10^{-2}$...)”  
   An absolute deviation of \(10^{-2}\) is incompatible with agreement to three decimal places, which requires errors below roughly \(5\times10^{-4}\). The claimed validation accuracy must be restated quantitatively, with a defined error metric.

2. **ERROR — stated exponent range is numerically wrong.**  
   Exact quote: “the dimensionless exponent $\pi A^2/2kg$ spans $[10^{-3}, 6]$”  
   Using the stated \(A=aa\,g_0\), \(aa_{\min}=2\), \(g_{\max}=8g_0\), \(g_0=0.0295\), and the code convention apparently used later, \(k=2\), the minimum is
   \[
   \frac{\pi(2g_0)^2}{2(2)(8g_0)}\simeq 1.16\times10^{-2},
   \]
   not \(10^{-3}\). This is a factor-of-ten error in the reported validation domain.

3. **ERROR — the alleged approach to the breakdown regime does not occur for the reported parameters.**  
   Exact quote: “the largest deviations ... consistent in magnitude with ... the approach of $A$ toward $k^2$”  
   The largest stated depth is \(A=23g_0=0.6785\). For \(k=2\), \(k^2=4\), so \(A/k^2\simeq0.17\), not \(A\sim k^2\). No evidence is supplied that the deviations are caused by multiband breakdown rather than finite endpoints, basis projection, truncation, or integration error.

4. **ERROR — the numerical projection is underspecified and may be the wrong observable.**  
   Exact quote: “then projects the final state onto static-lattice band eigenstates to measure the ground-band survival.”  
   The evolved Hamiltonian is \(H_{Q_f}=(p-Q_f)^2+V\). Its band eigenstates correspond to the appropriate shifted quasimomentum/gauge sector, not generically to eigenstates of \(H_0=p^2+V\) in the original sector. The text must specify the gauge transformation, final quasimomentum, and which instantaneous eigenvectors are used. A naive projection onto unshifted “static-lattice” eigenstates gives a spurious loss.

5. **ERROR — the claimed three-decimal/full-lattice validation lacks the convergence information needed to distinguish physics from numerics.**  
   Exact quote: “integrates the full $(2n+1)$-state Schrödinger equation with no two-level reduction”  
   A finite \((2n+1)\)-state calculation is not the full infinite-level problem. No \(n\)-convergence, time-step/tolerance convergence, start/end detunings, or boundary-population check is reported. This is especially consequential where claimed discrepancies are \(10^{-2}\) and are assigned a physical explanation.

6. **ERROR — “loss” is not implied by a diabatic transition in the closed Hamiltonian being simulated.**  
   Exact quote: “for a shuttle that keeps accelerating this is loss, because the excited branch is never recaptured”  
   In a coherent periodic lattice under sustained forcing, excited-band amplitude can encounter later avoided crossings and undergo Bloch–Zener/Stückelberg dynamics. “Never recaptured” requires an explicit open-system mechanism, spatial wave-packet separation with quantified overlap loss, removal from the lattice, or a measurement. It does not follow from the band label alone.

7. **ERROR — geometric compounding is not justified by the stated condition.**  
   Exact quote: “true when the excited branch disperses away before the next crossing.”  
   Momentum-space plane-wave integration has no automatic absorbing branch, and coherent amplitudes do not become probabilities merely because their phases evolve. Independent geometric loss requires decoherence, an absorber, ensemble phase averaging, or demonstrable spatial separation. Without one of these, the correct calculation is coherent amplitude propagation, not \((1-P)^N\).

8. **MINOR — the band-gap identification is overgeneralized.**  
   Exact quote: “which is the band gap between the two lowest bands at the zone edge”  
   This is true for the first weak-lattice zone-edge crossing. The preceding derivation is written for arbitrary \(n\); crossings in an extended-zone description need not correspond to the two lowest bands.

9. **ERROR — the proposed optimization problem is mathematically ill-posed under the stated constraints.**  
   Exact quote: “Fix total transported momentum $Nk$ and total time $T$... so the optimal profile is bang-bang”  
   Fixed displacement and time alone do not define a finite optimum when velocity and acceleration are unbounded. One can concentrate time arbitrarily near crossings and make arbitrarily fast changes elsewhere. Conversely, abrupt changes of \(Q(t)\) can themselves excite the system. Bounds or penalties on \(\dot Q\), \(\ddot Q\), bandwidth, jerk, or available force are required before an “optimal” bang-bang trajectory can be claimed.

10. **ERROR — the Landau–Zener formula does not establish the asserted finite window or interior optimum.**  
    Exact quote: “loss is paid only inside windows of width $w \sim \mathcal{O}(A/k)$”  
    Exact quote: “an interior optimum in $(v_s/v_f,\, w)$ exists rather than unbounded improvement.”  
    \(A/k\) estimates where the instantaneous diabatic detuning is comparable to the coupling, but the finite-time LZ transition scale also depends on sweep rate, roughly through \(\sqrt{\alpha}\), and on endpoint phases. The existence of an interior optimum does not follow from the asymptotic LZ expression and is neither derived nor demonstrated by the reported scan.

11. **ERROR — the reported bang-bang result is inconsistent with the manuscript’s own piecewise-constant estimate.**  
    Exact quote: “$v_s/v_f = 0.15$, $w = 0.5$ achieves $0.28\%$ loss”  
    Taking the preceding definitions literally, the total slow distance is \(Nw=1.5\), the fast distance is \(Nk-Nw=4.5\), and
    \[
    T=\frac{1.5}{v_s}+\frac{4.5}{v_f},
    \qquad v_s/v_f=0.15,
    \]
    gives \(v_s\simeq0.00856\). For \(A=0.35\), \(k=2\),
    \[
    P\simeq\exp\!\left[-\frac{\pi A^2}{4kv_s}\right]\simeq3.6\times10^{-3},
    \]
    so three independent crossings lose about \(1.1\%\), not \(0.28\%\). The definition of \(w\), actual crossing velocity, or reported result is inconsistent.

12. **ERROR — a single tuned coherent trajectory does not establish “loss optimality.”**  
    Exact quote: “a tanh-smoothed bang-bang profile ... achieves $0.28\%$ loss — a \textbf{122$\times$ reduction}”  
    No global optimization, robustness analysis, phase averaging, or comparison against other admissible controls is reported. With three coherent crossings, a selected trajectory can exploit Stückelberg cancellation rather than robustly reduce independent LZ loss. Calling it “loss-optimal” and quoting a \(122\times\) improvement is unsupported and potentially cherry-picked.

13. **ERROR — the stated trade-off invokes a quantity fixed by the problem.**  
    Exact quote: “the optimal schedule set by a trade-off between the LZ exponent and the number of Bloch periods consumed.”  
    For fixed total momentum transfer \(Nk\), the number of zone-edge crossings/Bloch periods is fixed. Changing the schedule redistributes time; it does not trade against the number of periods unless reversals or extra crossings are allowed.

14. **ERROR — the corner discussion labels an incomplete three-state quantity as total loss.**  
    Exact quote: “A three-state truncation predicts a collective $\sqrt2$-enhanced coupling and loss $P_1^2$”  
    \(P_1^2\) can describe the diabatic survival probability of the initially occupied state in the corresponding bow-tie reduction. It is not automatically the total loss from the desired carried state, which is absent from the three-state truncation. The observable and state mapping must be specified.

15. **ERROR — “quasicrystal” is overclaimed from the rank test alone.**  
    Exact quote: “$r > e$ gives a quasicrystal with an $r$-dimensional superspace description.”  
    The rank condition establishes quasiperiodicity/nonexistence of a full-rank period lattice for the Fourier module. It does not by itself establish that the physical ground state or atomic structure is a quasicrystal, nor properties such as long-range order, pure-point diffraction, or stability. The conclusion should be “quasiperiodic potential” unless those additional properties are shown.

16. **ERROR — the universal verification statement is unsupported by the evidence described.**  
    Exact quote: “Every quantitative claim was verified against full momentum-space Schrödinger integration”  
    Rank classification is not verified by Schrödinger integration; the shuttle “optimality” is not established by one selected ramp; the illumination and phase-diversity claims concern different numerical models; and all momentum grids are finite rather than “full.” This blanket statement materially overstates validation.

**VERDICT: UNSOUND**