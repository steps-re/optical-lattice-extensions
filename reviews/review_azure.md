1. **ERROR — Document 1:** “\(\left|\frac{d\,\Delta E}{dt}\right| = 2k\,\dot Q\)” and “\(\exp[-\pi A^2/(4k\dot Q)]\).”  
   The absolute value was dropped. The rate is \(2k|\dot Q|\), and the denominator must contain \(|\dot Q|\). As written, a reverse shuttle gives \(P_{\rm tunnel}>1\).

2. **ERROR — Document 1:** “A diabatic transition here means … the atom has slipped out of the lattice.”  
   In an infinite periodic lattice this is excitation to another band/diabatic momentum branch, not physical escape from the lattice. Calling it loss is justified only if excited-band atoms are subsequently removed or never recaptured. The manuscript itself later discusses coherent recoupling, contradicting the literal identification.

3. **ERROR — Document 1:** “if the crossings are well separated the losses compound geometrically: … \((1-P_{\text{tunnel}})^N\).”  
   Separation alone is insufficient. One must also neglect all return paths from excited bands or impose an absorbing-loss/dephasing model. Dephasing removes Stückelberg interference but does not prevent incoherent repopulation of the ground band at later avoided crossings.

4. **MINOR — Document 1:** “Across lattice depths \(A/g\in[2,23]\).”  
   \(A/g\) is not dimensionless in these units: \(A\sim k^2\), whereas \(g=2\dot Q\sim k^3\). Numerical ranges require a stated momentum scale, e.g. \(A/k^2\) and \(g/k^3\), or an explicit choice of \(k\).

5. **MINOR — Document 1:** “deviations … in the direction expected from the finite duration of the sweep and the breakdown of \(A\ll k^2\).”  
   Neither correction has a universal sign. Finite-time Landau–Zener corrections are generally oscillatory, and multiband corrections can raise or lower the measured ground-band survival.

6. **ERROR — Document 2:** “\(\displaystyle P_{\text{tunnel}}=\exp\!\left(-\frac{\pi A_b^2}{4\,b\cdot\dot Q}\right)\).”  
   The denominator must be \(4|b\!\cdot\!\dot Q|\). The stated expression is unphysical for crossing the same Bragg plane in the opposite direction. It also does not apply at \(b\!\cdot\!\dot Q=0\), where no crossing is traversed.

7. **FATAL — Document 2:** “crosses two Bragg planes at the same instant — a three-state ‘bow-tie’ crossing.”  
   At a corner of a separable square/cubic Brillouin zone, four states are degenerate:  
   \[
   |q\rangle,\quad |q+b_x\rangle,\quad |q+b_y\rangle,\quad
   |q+b_x+b_y\rangle .
   \]
   The fourth state is coupled to the two intermediate states and cannot be discarded in a nonperturbative LZ event. This is not the claimed three-state bow-tie model.

8. **ERROR — Document 2:** “consistent with the exact solvability of bow-tie models, whose transition probabilities are products of pairwise LZ factors. Corners … therefore … decompose plane-by-plane.”  
   General bow-tie scattering probabilities are not simply arbitrary products of independent pairwise LZ probabilities. For the stated cubic cosine lattice, factorization can occur because the Hamiltonian is separable, \(H=H_x+H_y(+H_z)\), not because of a universal bow-tie theorem. Additional reciprocal vectors, nonorthogonal planes, or Fourier components coupling the degenerate states invalidate the plane-by-plane conclusion.

9. **FATAL — Document 2:** “loss is paid only inside windows of width \(w\sim\mathcal O(A/k)\) … so the optimal profile is bang-bang” and “narrower windows and harder speed contrast monotonically win.”  
   Landau–Zener dynamics does not define a sweep-independent compact loss window. Besides the adiabatic scale \(\delta Q\sim A/k\), the nonadiabatic transition region contains a sweep-rate-dependent scale \(\delta\Delta E\sim\sqrt{\alpha}\). Moreover, the LZ formula assumes sufficiently asymptotic initial and final detunings. Taking \(w\to0\) while \(v_s=Nw/T\to0\) would spuriously predict unlimited improvement although the state never traverses enough detuning to execute the adiabatic momentum transfer. Thus the claimed monotonic optimization does not follow from the LZ formula; velocity/acceleration bounds and finite-time dynamics are essential.

10. **FATAL — Document 2:** “The potential is periodic iff \(\operatorname{rank}_{\mathbb Z}M=d\).”  
    Rank alone is not sufficient without requiring that the Fourier module have real span \(d\). For example, in \(d=2\),
    \[
    V(x,y)=\cos x+\cos(\sqrt2\,x)
    \]
    has \(\operatorname{rank}_{\mathbb Z}M=2=d\) but is quasiperiodic in \(x\), not a two-dimensional periodic potential. Conversely, \(V(x,y)=\cos x\) has rank \(1<d\) yet admits a full-rank set of translation periods because it is invariant in \(y\). The relevant comparison is between the \(\mathbb Z\)-rank and the real dimension of the span of the actual nonzero Fourier support, together with discreteness of that module.