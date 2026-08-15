Here is the review of the updated numerical methods files. The previous fixes were implemented very well (the log-domain Sinkhorn and MRAF mixing are particularly clean), but the fix for the Z-module rank test introduced a subtle mathematical flaw that needs addressing.

1. **ERROR**: Flawed rational-subset rank test for Z-modules of rank > $d$.
   - **Quote**:
     ```python
             Bi = B[:, piv[:rk]]
             coef, res, *_ = np.linalg.lstsq(Bi, v, rcond=None)
             in_span = np.linalg.norm(Bi @ coef - v) < 1e-8
             rational = in_span and any(
                 np.allclose(coef * t, np.round(coef * t), atol=1e-6) for t in range(1, 65))
     ```
   - **Explanation**: The fix to avoid the min-norm solution of an underdetermined `lstsq` was to solve exactly on a real-basis subset `Bi` (of size $d$). However, this is mathematically flawed for quasicrystals. If the true Z-module rank exceeds the real dimension $d$, a new vector `v` might be a rational combination of the *full* set of already-added generators in `basis`, but NOT a rational combination of the chosen real-basis subset `Bi`. In such cases, `v` will be incorrectly flagged as irrational and added to `basis`, leading to an overestimation of the module's rank. While this happens to give the correct answer for the specific non-redundant difference sets tested in the script (`diffs5` and `ico`), it will fail for general redundant quasicrystal generators (e.g., if you appended `v3 + v4` to `diffs5`, it would incorrectly return rank 5 instead of 4). To fix this robustly without implementing LLL or PSLQ, you can check if `v` is an integer/rational combination of the full `basis` by setting up an integer linear programming query, or by using a lattice reduction heuristic on the full set.

SHIP-AFTER-FIXES