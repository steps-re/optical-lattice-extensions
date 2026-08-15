1. **ERROR — sign/absolute-value inconsistency in both LZ derivations.**  
   Exact quotes: “with $\alpha = 2k\dot Q$” and “$P_{\text{tunnel}}=\exp\left(-\frac{\pi A^2}{4k\dot Q}\right)$”; Document 2 similarly writes “$|d\,\Delta E/dt| = 2\, b \cdot \dot Q$.”  
   The sweep rate must be positive: $\alpha=2k|\dot Q|$ and $|d\Delta E/dt|=2|b\cdot\dot Q|$. The final exponents need absolute values unless the sweep direction is explicitly restricted.

2. **ERROR — the repeated-crossing discussion invokes Stückelberg interference where this monotonic nearest-neighbor sweep does not generically provide a recombination path.**  
   Exact quote: “if the sweep is hard enough that the amplitude lost at one crossing has not dephased before the next, the amplitudes interfere and one obtains Landau-Zener-Stückelberg oscillations.”  
   For a monotonic sweep of the 1D cosine lattice, successive avoided crossings involve different momentum pairs; amplitude left behind at one crossing does not meet the transported branch again. Geometric ground-band survival can follow from distinct outgoing channels without physical dephasing. Stückelberg oscillations require an actual closed/recombining path—e.g. sweep reversal, additional couplings, or a specified multiband loop—not merely closely spaced crossings.

3. **ERROR — the preceding “never recaptured” statement directly conflicts with the later Stückelberg claim.**  
   Exact quotes: “the excited branch is never recaptured” and “the amplitude lost at one crossing has not dephased before the next, the amplitudes interfere.”  
   Either the outgoing branch does not rejoin, in which case dephasing is irrelevant, or a concrete recapture path must be identified.

4. **ERROR — the shuttle-optimization conclusion is asserted more strongly than the analysis supports.**  
   Exact quote: “the optimal profile is bang-bang.”  
   The LZ estimate motivates slowing near crossings, but it does not prove global optimality. The answer depends on admissible acceleration/jerk, endpoint conditions, coherence, and whether arbitrary changes in $\dot Q$ are permitted. This should be “suggests a bang-bang-like profile” or restricted explicitly to the scanned control family.

5. **ERROR — the claimed existence of an interior optimum does not follow from the stated argument.**  
   Exact quote: “so an interior optimum in $(v_s/v_f,\,w)$ exists rather than unbounded improvement.”  
   Failure of the asymptotic LZ formula for narrow windows does not by itself establish an interior optimum of the exact dynamics. Narrow-window protocols can enter finite-time/Rabi or coherent-control regimes; existence requires either a numerical result with stated bounds or an optimization argument.

6. **ERROR — the three-state corner result is mislabeled or insufficiently defined.**  
   Exact quote: “A three-state truncation predicts a collective $\sqrt2$-enhanced coupling and loss $P_1^2$.”  
   If $P_1$ is the single-plane tunnelling/loss probability defined earlier, $P_1^2$ is the probability of remaining on the original diabatic product branch in the independent-crossing picture, not plainly the total loss. Moreover, a three-state model omitting $|q+b_1+b_2\rangle$ cannot define survival in the true post-corner ground band. State exactly which population is $P_1^2$.

7. **WINCE — the flat-top statistics are sufficiently counterintuitive that they need reconciliation before circulation.**  
   Exact quote: “cloud-averaged 3-crossing survival $0.863$ … and worst-atom (5th percentile) survival $0.882$.”  
   A mean below the fifth percentile is mathematically possible only through a severe sub-5% tail or differing weighting conventions. Either circumstance matters directly to the claim that the flat top “rescues the tail.” Define the averaging and percentile measures and explain the residual low-survival population. Also, “5th percentile” is not “worst atom.”

8. **ERROR — numerical computation cannot by itself verify the exact $\mathbb Z$-rank claims.**  
   Exact quote: “Numerically verified on four configurations.”  
   Integer rank and irrational commensurability are exact algebraic properties and are unstable under floating-point representation. Use symbolic coordinates/exact number fields or call the numerics diffraction illustrations rather than verification of the rank criterion.

9. **WINCE — the frequency-offset wording is physically ambiguous.**  
   Exact quote: “six independent standing waves require frequency-offset pairs so cross-interference terms time-average away.”  
   Counterpropagating beams within each standing-wave pair must ordinarily share a frequency; the offsets should be **between different standing-wave pairs**. As written, “frequency-offset pairs” can mean offsetting the two beams within a pair, which produces a moving rather than stationary standing wave.

10. **WINCE — Document 1 opens with manuscript-sales language rather than a neutral continuation.**  
    Exact quote: “We now make good on the promise … The payoff will be … the central design constraint for moving atoms with optical lattices.”  
    “We now derive…” is enough. “The payoff” and “central design constraint” overstate what is a weak-lattice, isolated-crossing estimate.

11. **NITPICK — conversational flourish that does not match the surrounding manuscript register.**  
    Exact quote: “the standard derivation proceeds via parabolic cylinder functions, or more slickly via a contour argument.”  
    “More slickly” reads like generated exposition and contributes nothing; omit the parenthesis or cite a standard reference.

12. **WINCE — “honest test” is performative and needlessly disparages the preceding check.**  
    Exact quote: “The honest test is a true minimal 2D lattice.”  
    Use “A nonseparable test is…” Likewise, “true minimal 2D lattice” should be defined geometrically rather than used rhetorically.

13. **WINCE — the bold headline ratio overmarkets a coarse in-family search.**  
    Exact quote: “a \textbf{122$\times$ reduction at equal total time}.”  
    The same paragraph says this is the best of a 12-point scan and that the phase-robust estimate supports only $\sim90\times$. Lead with the robust figure or report both without boldface.

14. **WINCE — explicit AI-review provenance will reduce rather than increase confidence.**  
    Exact quote: “reimplemented here with corrections from a two-model adversarial code review.”  
    This is an obvious AI tell and is not a reproducibility method. State the actual corrections, tests, and comparison benchmarks.

15. **ERROR — shot-to-shot reproducibility is not established by the reported static spatial simulation.**  
    Exact quote: “Uniform illumination does not primarily raise the average—it rescues the tail, and with it shot-to-shot reproducibility.”  
    Tail survival may plausibly reduce sensitivity to cloud-position or size fluctuations, but no fluctuating-cloud ensemble or shot model is reported. Replace with a conditional statement or add that simulation.

16. **WINCE — the final phase-diversity result reads like an unrelated precision dump.**  
    Exact quote: “recovers a simulated aberrated input beam from 6 defocus probes at fidelity $0.99972$ (0.79\% amplitude error, 28.5~mrad residual phase RMS) under true Poisson shot noise.”  
    “True Poisson” is promotional, “fidelity” is undefined, and the result is disconnected from the note’s argument. Define the metric and relevance or remove it.

17. **NITPICK — malformed numerical notation.**  
    Exact quote: “agrees to $|{\le}0.004|$.”  
    Write “agrees within $0.004$” or “has absolute deviation $\le 0.004$.”

**SHARE-AFTER-FIXES**