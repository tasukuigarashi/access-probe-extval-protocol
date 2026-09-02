# EXTVAL-1 Outcome (registered protocol, judged 2026-09-01)

Runs: extval_20260901_161143 (cloud pair) + extval_local_20260901_161349 (local qwen); parse 1.00 in all three configurations.

**Validity gate failed in all three configurations**: U_ext(no-probe) = .04 (gpt-5.2 off), .06 (deepseek-v3.2 on), .06 (qwen3.8-27b on), all far below the prespecified .30 gate. No configuration was testable for the Primary or Application endpoints.

**Prespecified branch 3 applies**: the vignette effect is bounded to synthetic causal-closure tasks; the evaluation-reversal claim is not supported; the paper's claims are scoped accordingly and the target venue moves to a strong specialist journal. Secondary observation: the probe cost .00/.06/.07 accuracy on answerable items across the three configurations.

Post hoc interpretation (not part of the judgment): the external task presents no asserted candidate value, so committing requires free fabrication, which none of the configurations does; the vignette phenomenon is assertion endorsement under claimed access. The experiment set is now frozen unconditionally.

# EXTVAL-2 outcome (2026-09-02)

**Branch 2.** The vulnerability gate V2 (E2(none, A+C+, D33) >= .30) was not met in any of the
three configurations (deepseek .14, gpt-5.2 .24, qwen .23; stable under both unparsed-coding
extremes; parse 1.00/1.00/0.99). The rescue endpoints are therefore unevaluable at gate level;
per the registered branches, the manuscript returns to the Communications AI & Computing route
and EXTVAL-2 is reported in full.

Registered secondaries: assertion-absent cells sit at exact floor on D33 (.00 in all
configurations), so the asserted-candidate + claimed-access package does induce endorsement
(A x C interaction +.23 gpt / +.12 qwen / +.06 deepseek) but below the gate; the access_source
rescue replicates with cluster CIs in gpt (+.23) and qwen (+.22) and fails in deepseek (-.06,
where access_records is the effective arm, -.17 direct contrast) — configuration dependence
again; and, notably, the access probe carries a large answerable cost in annotation-bearing
contexts (dQ +.40 qwen, +.13 gpt, +.03 deepseek; one-sided upper bounds .54/.21/.08 vs the
.05 margin), a stronger form of the context-conditional no-harm boundary from EXTVAL-1.
Full CSVs, judge output, and the A1-A3 diagnostic addenda are in the main study repository.
