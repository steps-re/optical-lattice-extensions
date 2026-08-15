# Round-5 review: Claude Fable 5 (fresh-context subagent WITH code execution)
# Differentiator: re-ran every number against source data. All reproduced.
# Findings: 1 ERROR (relative-deviation claim false: reaches 7.5% at smallest
# losses), 1 WINCE (corner "typically 3e-4" -> median 1e-3), 6 rounding/
# precision nits (incl. reverting round-4 Gemini's wrong 0.38% back to 0.37%).
# Also verified: PR claims against the actual git commit; physics rechecked by
# hand (LZ reduction, projection law, corner, rank criterion) — all correct.
# Verdict: SHIP-AFTER-FIXES. All fixes applied in commit 6389bef.
# (Full transcript lived in the session task log; this is the summary of record.)
