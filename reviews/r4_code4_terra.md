1. **ERROR — MRAF’s reported “final error” is one iteration stale relative to the returned/output field.**  
   Exact quote:
   > `errs.append(np.linalg.norm((Ifs - I_T)[supp]) / np.linalg.norm(I_T[supp]))`  
   > `...`  
   > `phi = np.angle(E)`  
   > `return phi, np.array(errs)`

   Each error is measured before its iteration’s MRAF update, but `phi` is returned after the last update. Thus `err_ot[-1]`, `err_rd[-1]`, the random-run median selection, and the JSON “final errors” refer to the penultimate field, whereas ripple/vortex/efficiency metrics refer to the returned final field. Append a post-loop metric (or measure after each update) so all reported final metrics describe the same field.

2. **ERROR — `rank_over_Z` is not a valid general rational-rank test because it declares rational dependence only for denominators ≤64.**  
   Exact quote:
   > `rational = in_span and any(`  
   > `    np.allclose(coef * t, np.round(coef * t), atol=1e-6) for t in range(1, 65))`

   A genuine rational relation with denominator greater than 64 is classified as irrational and spuriously increases the reported module rank. Conversely, with floating trigonometric inputs and `atol=1e-6`, this is only a heuristic for the displayed examples, not a numerical demonstration of the stated integer-module criterion. For the constructed algebraic examples, use exact/symbolic algebraic-number representations or state explicitly that this is a bounded-denominator heuristic rather than a rank test.

3. **WINCE — The cloud-survival setup does not implement its stated equal-total-power comparison.**  
   Exact quotes:
   > `# two candidate lattice-illumination profiles, EQUAL TOTAL POWER:`  
   > `I_gauss = I_gauss_raw * (I_flat[_inside].sum() / I_gauss_raw[_inside].sum())`

   This normalizes the Gaussian to equal power *inside* \(r<40\), not equal total power. The later comment correctly describes the actual protocol, but the header and introductory claim remain false. This matters because total power and shaping efficiency are physically relevant resources; either normalize total powers equally, or consistently present this as an equal-delivered-cloud-power comparison.

SHIP-AFTER-FIXES