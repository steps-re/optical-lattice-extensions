1. **ERROR — The implemented update is a relaxed signal-region projection, not the standard MRAF constraint.**  
   Exact quote:  
   > `mixed = m * sqn + (1 - m) * np.abs(Ef)           # TRUE MRAF amplitude mixing`  
   > `out = np.where(S, mixed * np.exp(1j*np.angle(Ef)), Ef)`  
   
   Standard MRAF assigns the target amplitude in the signal region and retains the current field—with the complementary weight—in the noise region, e.g. `m*sqn` inside and `(1-m)*Ef` outside (or square-root weights, depending on parameter convention). Here the current amplitude is instead mixed into the **signal** region while the noise region is unweighted. That changes the fixed point and makes the claimed MRAF comparison methodologically inaccurate.

2. **WINCE — MRAF still reports the metric from one iterate before the returned phase.**  
   Exact quote:  
   > `errs.append(np.linalg.norm((Ifs - I_T)[supp]) / np.linalg.norm(I_T[supp]))`  
   > `...`  
   > `phi = np.angle(E)`  
   > `return phi, np.array(errs)`  
   
   After the final error is recorded, `phi` is updated once more and returned without measurement. Thus `err_ot[-1]` and `err_rd[-1]` are not metrics of the saved/output phases. Append one final measurement after the loop, as was done in `ot_gs2.py`.

3. **ERROR — The revised rational-rank test still discards necessary rational-basis vectors.**  
   Exact quote:  
   > `Bi = B[:, piv[:rk]]`  
   > `coef, res, *_ = np.linalg.lstsq(Bi, v, rcond=None)`  
   > `...`  
   > `if rational:`  
   > `    continue`  
   
   Once the module rank exceeds the real dimension, testing rational membership against only a maximal **real-linearly independent** subset is insufficient. A vector can be a rational combination of the full existing module basis while having irrational coefficients relative to every selected real basis. For example, in order  
   \[
   (1,0),\ (0,1),\ (\sqrt2,0),\ (1+\sqrt2,0),
   \]
   the true \(\mathbb Q\)-rank is 3 because the fourth vector is the first plus the third; this routine reports 4. The supplied showcase cases may happen to classify correctly, but the advertised general rank criterion is not implemented reliably. Rational dependence must be tested against the full accumulated basis, not a real-independent subset; bounded denominator search also needs to be explicitly characterized as heuristic.

**SHIP-AFTER-FIXES**