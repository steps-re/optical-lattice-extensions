1. ERROR
Quote: "projects the final state onto static-lattice band eigenstates" (DOC 1, Sec 1.3) vs. "The projection observable is the instantaneous ground band of the \emph{swept} Hamiltonian $H_{Q_f} = (p-Q_f)^2 + V$ ... not the eigenstates of the unshifted $H_0$." (DOC 1, Sec 1.3)
Explanation: Direct contradiction within the same paragraph. The first quote claims the projection is onto the static-lattice band eigenstates, while the second explicitly (and correctly, for measuring survival in a transported lattice) states it is onto the swept Hamiltonian's eigenstates and *not* the unshifted $H_0$. 

2. ERROR
Quote: "overlap $|\langle E_{\rm rec}|E_{\rm true}\rangle|^2 = 0.9997$ (0.8\% amplitude error, 29~mrad residual phase RMS)" (DOC 2, Sec VI)
Explanation: This is mathematically impossible. Assuming standard intensity-weighted errors, a residual phase RMS of 29 mrad ($\sigma_\phi = 0.029$) alone limits the maximum possible overlap (fidelity) to $F \approx 1 - \sigma_\phi^2 = 1 - 0.000841 = 0.999159$. Combined with a 0.8% amplitude error ($\sigma_A = 0.008$), the overlap must be approximately $1 - 0.029^2 - 0.008^2 \approx 0.9991$. An overlap of 0.9997 would require the total variance to be $\approx 0.0003$, which is nearly three times smaller than the phase variance alone.

3. WINCE
Quote: "with the optimal schedule set by a trade-off between the LZ exponent and the number of Bloch periods consumed." (DOC 1, Sec 1.4)
Explanation: For a fixed total momentum transfer, the number of crossings (and thus the number of Bloch periods traversed) is strictly fixed. The actual trade-off for the schedule optimization is between the LZ exponent (which prefers slow crossings) and the total time consumed (or the maximum acceleration $v_f$ required between crossings to meet a fixed time budget).

4. NITPICK
Quote: "the independent-LZ estimate at the measured minimum crossing speed ($v_s = 0.0072$) is 0.37%" (DOC 2, Sec III)
Explanation: The independent-LZ estimate for 3 crossings at $v_s = 0.0072$ with $A=0.35$ and $k=2$ evaluates to $1 - (1 - \exp(-\pi \times 0.35^2 / (8 \times 0.0072)))^3 \approx 0.3757\%$, which rounds to 0.38%, not 0.37% (looks like a truncation rather than a rounding).

SHIP-AFTER-FIXES