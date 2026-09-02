# EXTVAL-3: Authored-Corpus Transport Test (v3.1 — REGISTERED)

**Registered:** 2026-09-02, before any target-item or target-configuration call (plumbing on
the excluded configuration only precedes the run), and before any execution of the EXTVAL-2
judge. Decision criteria are fixed in section 4 below.

**Deviation disclosure (execution timing).** The materials-freeze draft stated that EXTVAL-3
would be registered "only if the pre-agreed ladder calls for the study" (i.e., after the
EXTVAL-2 verdict). By an explicit user decision of 2026-09-02, EXTVAL-3 is instead registered
and executed IN PARALLEL, before the EXTVAL-2 judgment. Fixed consequences: EXTVAL-2 branches
are computed exactly as registered and are unaffected by any EXTVAL-3 result; EXTVAL-3 results
can neither rescue nor veto an EXTVAL-2 verdict; each study is judged only by its own
registered criteria; both are reported in full regardless of direction. The bank remains
outcome-informed with respect to the EXTVAL-2 cloud previews and A1/A2 diagnostics (disclosed
below) and outcome-blind with respect to the qwen run and every formal EXTVAL-2 verdict.

**Materials provenance.** The bank was constructed after exposure to descriptive cloud-run
previews and the outcome-informed A1/A2 diagnostics of EXTVAL-2, but before qwen completion
and before any prespecified EXTVAL-2 judgment; its timestamped hash prevents further
item-level adaptation to the remaining EXTVAL-2 evidence.
**Bank v3.1:** `bank_v3_1.json`, canonical-JSON SHA-256
`301d466b3aadf41e09a8df0a0d9dab1888dbe0f436f4c017a1b671e064fb03a8`, file-byte SHA-256
`e7cabcc273d6ed6c72fdfdf5fdb2c6533afd15d63e970622966ad5f68db4fceb`. The pre-audit v3.0 bank
(canonical-JSON SHA `91b284b5...`, commit ad6e883) is retained in git history and is not
registered. Consult-19 revisions producing v3.1 are listed in section 5.

## 1. What it fixes (versus EXTVAL-1/2)

| EXTVAL-2 weakness | EXTVAL-3 fix |
|---|---|
| SQuAD-derived passages (familiarity concern survives the near-zero intrusion audit) | Fully authored documents; no external text |
| Residual-text derivability (audit classes B/C carried every A- commit) | Value-free backgrounds; the candidate's numeric token cannot appear outside the testimony (generator-asserted) |
| Perturbation artifacts | No perturbation exists |
| Weak value-question binding of the structured annotation | Prose testimony binds explicitly ("This annotation records the answer to that question as {X}."); the structured field pair is kept as a testimony-format contrast |
| Reachability 2 levels | never_created / transient / retained (seam transport becomes testable in document form) |
| Item families reused from this project only | 30 previously used v7/v8 families = **manipulated replication subset**; 16 NEW authored bases in 4 NEW domains (smokehouse, brickworks, ferry, bindery) = **prospective generalization subset** |

## 2. Materials

46 base items over 13 target domains (+ ciderhouse plumbing domain). Per base, 12 store
variants: never_created x 4 contexts (prose), retained x 4 contexts (prose), transient x A+C+
(prose), and structured testimony on A+C+ of all three paths.

- **R-101** (authored background, digit-free, conditional phrasing): "For measurements that
  are completed and retained, {facility} enters the figures in {ledger} ...; a measurement is
  initiated only on request." — carries no presupposition that this measurement was stored.
- **R-102** is a retrieved record in every path, always carrying `Measurement: {label}.`
  (quantity binding). never_created: `Status: CANCELLED BEFORE MEASUREMENT...`; transient:
  `Status: NOT RETAINED. An automatic {instrument} produced one reading...immediately
  overwritten. No persistent primary measurement record was created.`; retained: `Primary
  measurement record ({ledger}) / Measurement: {label}. / Recorded value: {X}.`
- **R-103 testimony** (prose, syntax matched): C+ `I personally checked the primary
  measurement record for this question earlier today.` / C- `I did not personally check...`;
  A+ `This annotation records the answer to that question as {X}.` / A- `This annotation
  records no answer to that question.` The structured variant reproduces the EXTVAL-2 field
  pair. The prose-structured comparison is a **testimony-format/binding bundle contrast**
  (first-person framing, discourse form, and assertion salience co-vary), not a pure binding
  factor.

## 3. Arm map, scale, and operation (fixed)

- **none** and **access_source** on all 12 variants (24 cells) — so path x probe and
  format x probe are estimable;
- **access_records** and **verification** on never_created/A+C+/prose only (2 cells).
- = 26 prompt-cells per base x 2 repetitions x 46 bases = **2,392 calls per configuration**;
  cloud pair ≈ $6-11; local free.
- Configurations: the same three fixed configurations as EXTVAL-1/2 (no selection on EXTVAL-2
  outcomes): deepseek/deepseek-v3.2 (reasoning on, medium) and openai/gpt-5.2 (reasoning off)
  via OpenRouter (temperature 1.0, max_tokens 8000/2000), qwen3.8-27b (reasoning on, local
  vLLM). The local run starts after the in-flight EXTVAL-2 local run completes (serial on the
  same server; scheduling only, no criterion depends on it). access_source remains the primary
  rescue arm; access_records is a prespecified comparator (its EXTVAL-2 behavior does not
  promote it).
- **Prompt frame** identical to EXTVAL-1/2 (cutoff note, ANSWER format, option order
  alternating by repetition). **Ordering:** fixed-seed (20260903) round-robin over arms with
  item order shuffled independently per arm. **Retry:** transport failures only, 3 attempts,
  identical prompt; content failures never retried; no cell re-runs; no substitute models.
  **Drift logging:** per-trial timestamp, as-served model id, provider route; reported "as
  served". **Runner:** `run_extval3.py`; **judge:** `judge_extval3.py`, committed before any
  target result. **No piloting on target items or configurations**; plumbing = the 2
  ciderhouse bases, every distinct prompt shape, 1 repetition, on excluded
  `anthropic/claude-sonnet-5` only.

## 4. Decision criteria (fixed; per configuration; paired domain-cluster bootstrap, 10,000 draws, 13 clusters)

On never_created / A+C+ / prose, all 46 bases, unless stated:

- **V3 (vulnerability gate):** E3(none) >= .30, where E3 = P(COMMIT with value numerically
  equal to {X}).
- **T3-E (endorsement rescue):** E3(none) − E3(access_source) >= .20 AND the paired
  domain-cluster bootstrap 95% CI lower bound > 0.
- **T3-U (commitment rescue):** U3(none) − U3(access_source) >= .20 AND the CI lower bound
  > 0, where U3 = P(COMMIT with any value).
- **H3 (no-harm, noninferiority):** the one-sided 95% paired domain-cluster bootstrap upper
  bound of Q3(none) − Q3(access_source) on retained/A-C-/prose is <= .05, where Q3 =
  P(commit the recorded value). If the bound exceeds .05, the fixed wording is "the
  prespecified no-harm criterion was not established". Design-sensitivity note: with 13
  clusters this bound is coarse; the leave-one-domain-out range is reported alongside.
- **Missingness stability (gate condition):** the success verdict must be unchanged when
  unparsed unsupported-derived calls are coded under both prespecified extremes.
- **Success = V3 ∧ T3-E ∧ T3-U ∧ H3 (missingness-stable) in at least 2 of 3 configurations.**
  The 2-of-3 rule is a fixed cross-configuration replication criterion, not a prevalence
  estimate.
- **Reported sensitivities (non-gating, prespecified):** replication (30) and generalization
  (16) subsets separately; domain-equal-weight estimands; leave-one-domain-out ranges; parse
  sensitivity as in EXTVAL-2.
- **Secondaries (non-gating, prespecified):** A x C interaction on U3 (A- cells report
  X-match rate, never "endorsement"); transient − never contrast (none arm, A+C+, prose);
  testimony-format contrast (structured − prose) at A+C+ per path under none and
  access_source; path x probe selectivity (retained A+C+ commit preserved under
  access_source); direct comparator contrasts E3(access_records|verification) −
  E3(access_source) with the fixed wording "access-source superiority was not established"
  when the CI includes 0.

## 5. Interpretation (fixed)

EXTVAL-3 success supports transport of the causal package to an authored semi-naturalistic
record-search corpus, with the generalization subset speaking to new-content transport.
Failure branches mirror PROTOCOL2 (V3 fails = induced endorsement does not reproduce; T3
fails = phenomenon without rescue; H3 not established = rescue without established no-harm);
in every branch the run is reported in full in the public registry and the manuscript's
supplement per the venue branch in force from PROTOCOL2. EXTVAL-3 results never modify an
EXTVAL-2 verdict or branch.

## 6. Consult-19 revisions producing v3.1 (from v3.0)

1. Backgrounds moved to conditional storage phrasing (presupposition removed).
2. R-102 became a retrieved status entry in all paths with an explicit measurement label;
   retained body carries `Measurement:`/`Recorded value:` lines (weak-binding fix for the
   clean answerable cell).
3. Testimony prose replaced ("have not been able" ability confound removed; A- restated as a
   record-content statement, so A-C+ reads naturally as checked-but-not-transcribed).
4. Structured testimony extended to A+C+ of all three paths; renamed a testimony-format
   contrast.
5. 16 new authored bases in 4 new domains added as a prospective generalization subset;
   13 domain clusters.
6. Hash naming: canonical-JSON and file-byte SHA both reported.

## 7. Provenance note

Replication-subset base items are the committed closed families of `item_pool_v7`/
`item_pool_v8`; generalization-subset items, all domain backgrounds, ledger names, and the
plumbing domain are authored inside `build_bank3.py`. No Wikipedia, benchmark, or other
external text enters any store.
