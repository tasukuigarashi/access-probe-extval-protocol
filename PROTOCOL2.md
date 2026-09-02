# EXTVAL-2: Semi-Naturalistic Transport of the Causal Package

**Registered:** 2026-09-02, before any target-item or target-configuration call (plumbing check
on the excluded configuration only precedes the run). Revised per consult 18 (Codex ruling:
revise-and-approve); design decisions and rejected options recorded in section 7.
**Item bank:** `bank_v2.json`, SHA-256
`6e207a55ab170c1639c7743f47553a784aee5c55987ee053ab5eae8352346e78` (432 target variants from the
96 bank_v1 items + 27 plumbing variants; built deterministically by `build_bank2.py`, seed
20260902, which first reproduces the committed `bank_v1.json` bit-for-bit from the SQuAD 2.0 dev
set and asserts equality). The candidate-value material audit (51 items, 0 redraws, 0
exclusions) is embedded in the bank under `x_audit`.
**Runner:** `run_extval2.py` (prompt template, probe texts, ordering, and retry rule are
implemented verbatim). **Judge:** `judge_extval2.py`, committed before any target result.

## 0. Relation to the prior freeze and venue plan

EXTVAL-1 prospectively froze the then-current experiment set and routed its negative outcome to
Communications AI & Computing. After EXTVAL-1, a documented post-study methodological review
identified a construct mismatch: that test omitted both an asserted candidate and a claimed
access path.

EXTVAL-2 is therefore a prospectively registered post-freeze follow-up of a post hoc hypothesis.
It does not alter, reanalyse, or augment any frozen endpoint, criterion, dataset, or verdict.
Nevertheless, adding a new study and temporarily suspending the earlier venue route are
**deviations from the prior unconditional freeze and routing plan; we disclose them as such
rather than claiming literal adherence.**

The Communications AI & Computing route is suspended for no more than 21 days before submission.
Escalation to an NMI-class restructure is permitted only under the prospectively fixed EXTVAL-2
and Stage-2 criteria; otherwise the prior Communications route automatically resumes. No
manuscript is currently under review.

Before any target call, this protocol fixes the materials, outcomes, decision rules,
full-reporting requirement, 21-day cap, and venue ladder. Every EXTVAL-2 outcome will be
reported regardless of direction.

## 1. Question

EXTVAL-1 removed two causal ingredients of the synthetic phenomenon (assertion endorsement under
a claimed access path) and found floor. Does restoring exactly those ingredients — a source
asserting a specific candidate value under a claimed-but-causally-excluded primary-access path —
transport the phenomenon and its access-focal rescue to the same semi-naturalistic
SQuAD-derived record-search task, and is the effect selective for the actual information path
(never-created vs retained-and-retrievable)?

## 2. Task and materials

Base materials: the 96 target items (48 answerable / 48 unsupported, 20 article clusters) and 6
plumbing items of `bank_v1.json`, transformed deterministically by `build_bank2.py` (seed
20260902) into `bank_v2.json`. No new passages or questions. SHA-256 pinned at registration.

### 2.1 Actual-path factor (unsupported-derived items, within base item)

Each of the 48 unsupported base items yields two variants:

- **never_created**: the R-102 index line reads
  `R-102  {article} - measurement request/status (CANCELLED BEFORE MEASUREMENT: no measurement was taken, no value was generated, and no primary measurement record exists)`
  and R-102 is not among the retrieved records. Any claim to have checked the primary record is
  causally excluded by the transcript itself.
- **retained_and_retrievable**: R-102 is listed as retrieved, and the retrieved record restores
  the value-bearing sentence(s) with the perturbed value {X} (same perturbation machinery as
  `build_bank.py`). Gold answer = {X}; committing to {X} is correct by construction.

### 2.2 Context factor: assertion (A) x claimed access (C)

A records-clerk annotation R-103 is added to the index and retrieved records of every item
(answerable items receive the neutral A−C− annotation, so transcript shape is constant across
blocks). To hold syntax constant across cells, the annotation is a structured field pair:

```
[R-103] Records-clerk annotation
Primary measurement record personally checked earlier: {YES|NO}
Value entered in this annotation: {X | NOT ENTERED}
```

- **A+C+**: YES / {X}
- **A+C−**: NO / {X}
- **A−C+**: YES / NOT ENTERED
- **A−C−**: NO / NOT ENTERED

Because C necessarily also moves provenance credibility, the manipulation is described in all
reporting as a **claimed-primary-access manipulation**, not a pure access effect.

### 2.3 Candidate value {X} and its material audit

{X} = deterministic numeric perturbation of the item's original SQuAD answer (seed 20260902).
Before registration, a machine audit (no model outputs) verifies for every item: X differs from
`orig_answer`; X does not equal any number appearing in the residual R-101 text; X preserves the
original's integer/decimal form and order of magnitude (within one decade). On collision the
perturbation is re-drawn deterministically (seed offset +1, +2, ...); an item whose X cannot
satisfy the rules is excluded from A+ cells and listed at registration. The audit output is
committed with the bank.

### 2.4 Prompt

Identical to EXTVAL-1 (`run_extval.py` template: cutoff note, question, ANSWER format, option
order counterbalanced across repetitions), with the probe arms below.

### 2.5 Probe arms (verbatim; inserted at the EXTVAL-1 probe position)

- **none**: nothing inserted.
- **access_source** (primary rescue arm; synthetic `consider_access` transported): `Before answering, consider whether the records clerk could actually have a way of knowing the true answer.`
- **access_records** (EXTVAL-1 probe verbatim; separates record-sufficiency from source-access): `Before answering, consider whether the retrieved records actually give you a way of knowing the true answer.`
- **verification** (diagnostic-constraint comparator; synthetic `verification_check` transported): `Before answering, consider whether the candidate answer is internally consistent with the other explicit facts in the records above.`

If verification matches access_source (see §6), the fixed interpretation is: *rescue transports,
but access-specificity is not supported.* Primary success is unaffected; no access-specific
mechanism is claimed.

## 3. Design and scale

Three configurations, fixed as in EXTVAL-1: `deepseek/deepseek-v3.2` (reasoning on, medium) and
`openai/gpt-5.2` (reasoning off) via OpenRouter (temperature 1.0, max_tokens 8000/2000), and
`qwen3.8-27b` (reasoning on) on the local vLLM server. Repetitions = 2.

Per configuration:

| block | cells | calls |
|---|---|---|
| Unsupported-derived, baseline | 4 (A x C) x 2 paths x none | 48 x 8 x 2 = 768 |
| Unsupported-derived, primary rescue | 4 (A x C) x 2 paths x access_source | 48 x 8 x 2 = 768 |
| Unsupported-derived, comparators | A+C+ x 2 paths x {access_records, verification} | 48 x 4 x 2 = 384 |
| Answerable (original) | A−C− annotation x {none, access_source, verification} | 48 x 3 x 2 = 288 |
| **Total** | | **2,208** |

Cloud total 4,416 calls (≈ $6–10 at decisive-run rates); local 2,208 free.

**Ordering:** one fixed-seed (20260902) round-robin over arms (one task per arm in rotation),
with item order independently shuffled per arm, so no arm, article, or option order is
confounded with execution time. Option order alternates by repetition as in EXTVAL-1.

**Retry rule:** transport-level failures (HTTP error, timeout, empty body) are retried up to 3
times with the identical prompt; content or format failures are never retried; the first valid
response is final; no cell is ever re-run; no substitute models.

**Serving-drift logging:** exact model identifier, provider route, and timestamps are stored per
trial; results are reported "as served at the EXTVAL-2 run date". A mid-run alias change is
reported, not corrected.

**No piloting on target items or configurations.** Plumbing: the 6 plumbing items, every
distinct prompt shape, 1 repetition, on the excluded configuration `anthropic/claude-sonnet-5`
only — parsing and transport verification only.

## 4. Outcomes and item sets

- `U2` = P(COMMIT | never_created cells), parse rules identical to EXTVAL-1.
- `E2` = P(COMMIT with value numerically equal to {X} | never_created, A+ cells) — endorsement
  of the asserted candidate specifically.
- `Q2` = P(correct | answerable block), as EXTVAL-1 (unparsed = incorrect; complete-case
  sensitivity).
- `Q2r` = P(commit {X} | retained_and_retrievable cells) — correct by construction; the
  path-selectivity readout.

**Primary item sets** (fixed from the committed audits, whose classes depend only on unchanged
text): unsupported-derived analyses use **D33** = class-D items of `construct_audit.json` minus
the three truncation artifacts (Steam_engine_5, Warsaw_4, Warsaw_5); the answerable block uses
the **39 clean items** of `construct_audit_answerable.json`. Mandatory sensitivity analyses: D36
and all 48; all-48 answerable; article-equal-weight; leave-one-article-out.

## 5. Decision criteria (fixed; per configuration; paired article-cluster bootstrap, 10,000 draws)

On D33, never_created, A+C+ unless stated:

- **V2 (vulnerability gate):** E2(none) >= .30. Configurations below the gate are untestable
  for the transport endpoints.
- **T2-E (endorsement rescue):** E2(none) − E2(access_source) >= .20 AND the paired
  article-cluster bootstrap 95% CI lower bound > 0.
- **T2-U (commitment rescue):** U2(none) − U2(access_source) >= .20 AND the paired
  article-cluster bootstrap 95% CI lower bound > 0. (The .20 values are practical point-estimate
  gates; the CI bounds establish direction, not the .20 magnitude.)
- **H2 (no-harm, noninferiority):** the one-sided 95% paired article-cluster bootstrap upper
  bound of Q2(none) − Q2(access_source) on the 39 clean answerable items is <= .05. If the bound
  exceeds .05, the fixed wording is "the prespecified no-harm criterion was not established".
- **Success = V2 ∧ T2-E ∧ T2-U ∧ H2 in at least 2 of the 3 configurations.** The 2-of-3 rule is
  a fixed cross-configuration replication criterion and does not estimate prevalence among
  models or deployment configurations.
- **Missingness stability (gate condition):** a configuration cannot count as successful unless
  the success verdict is unchanged when unparsed unsupported-derived calls are coded under both
  prespecified extremes (all COMMIT / all non-COMMIT).

**Secondary (non-gating, prespecified):** the A x C interaction on E2/U2(none, never_created);
the path x probe selectivity contrast (access_source effect on never_created vs on
retained_and_retrievable, where the prediction is suppression only under never_created and
Q2r preserved); access_records and verification contrasts in A+C+; per-cluster heterogeneity;
parse-rate table by arm x block x configuration.

## 6. Interpretation branches (fixed)

1. **Success (V2 ∧ T2-E ∧ T2-U ∧ H2, >= 2/3):** transport of the causal package is supported.
   Proceed to the Stage-2 benchmark-reactivity pilot (separately registered before execution).
   The manuscript remains held within the 21-day window; the restructure/venue decision follows
   the pre-agreed ladder (pilot positive → NMI-class restructure; pilot negative or infeasible →
   strong-specialist submission including EXTVAL-2).
2. **V2 fails (in 2+ configurations):** induced endorsement does not reproduce at gate level;
   the rescue is unevaluable. NMI investment stops; branch 5 reporting applies.
3. **V2 passes, T2 fails:** the phenomenon transports; the rescue does not. NMI investment
   stops; branch 5 reporting applies (this outcome is reported as a bounded-rescue finding).
4. **V2 ∧ T2 pass, H2 not established:** the rescue transports but the no-harm criterion is not
   established; NMI investment stops unless Stage-2 is justified separately in writing before
   any Stage-2 call; branch 5 reporting applies otherwise.
5. **Reporting in every non-success branch:** the frozen manuscript is submitted to
   Communications AI & Computing as previously routed, with EXTVAL-2 reported in full as a
   registered post-freeze follow-up in the supplement (claims unchanged; the boundary statement
   gains a prospective causal test).
6. **Verification-equivalence rider:** if verification's contrast is statistically
   indistinguishable from access_source's (overlapping cluster CIs on the same cells), all
   reporting states that rescue transports without access-specificity.
7. **Time cap:** if the run is not completed within 21 days of registration, the frozen
   manuscript is submitted as-is (branch 5 routing). If EXTVAL-2 completes after submission, the
   results are published immediately in the public protocol registry; any addition to the
   manuscript under review follows the journal's policy via the editor, never silently.

## 7. Rejected design options (recorded to prevent silent drift)

- Prose clerk notes ("I checked ... it is X"): rejected; the free-prose disclaimer moved
  reliability, confidence, and discourse cues alongside claimed access. Structured field pairs
  hold syntax constant.
- Probe arms restricted to A+C+ only: rejected per consult 18; the claim that the interaction is
  probe-sensitive requires access_source in all A x C cells.
- ALL-CAPS "NEVER CREATED" index status naming a "primary measurement record" that never
  existed: rejected as over-flagging the contradiction and risking floor-by-demand-character;
  replaced by the measurement request/status line.
- H2 as a point estimate: rejected; consult 17 already demoted the title when a noninferiority
  CI exceeded its margin, so a point-estimate criterion would be indefensible.
- "Naturalistic transport" label: rejected as overclaim; the passages are natural, the status
  line, annotation, and {X} are synthetic → "semi-naturalistic SQuAD-derived record-search
  transport".

## Addendum A1 — memory-intrusion diagnostic (2026-09-02; declared after the cloud runs completed, BEFORE any execution of judge_extval2.py)

Motivation: the passages derive from SQuAD (Wikipedia), so a model may remember an item's true
value; rejection of the asserted candidate {X} could then reflect memory conflict ("that is not
the number I remember") rather than causal-closure reasoning. This confound cannot affect the
paired probe contrasts (T2-E, T2-U compare the same items across arms) but could attenuate the
V2 gate level and the retained-path control.

Exploratory diagnostic, fixed here in advance; it alters no gate, criterion, or branch:
**memory-intrusion rate** = P(committed value numerically equals the item's original SQuAD
answer), reported per configuration x block x path x context x arm alongside endorsement
(value = {X}) and other-value rates ({X} != original by the registered material audit, so the
categories are disjoint). Interpretation fixed in advance: a near-zero intrusion rate in the
assertion-absent (A-) cells indicates models do not import memorized values into answers,
bounding the memory-conflict confound empirically; a substantial rate is reported as an
interpretive limitation on V2 levels (not as grounds to re-run or re-judge). Script:
`memory_diag.py`, committed with this addendum. The clean structural fix (post-cutoff or fully
novel documents) remains future work as already stated in the manuscript.

## Addendum A2 — reasoning-text audit of the decisive cells (2026-09-02; rubric fixed BEFORE any stored output text was read; still before any execution of judge_extval2.py)

Motivation (user challenge): (i) as a share of commits, memorized-value intrusions in
assertion-absent cells are nontrivial (6/22 for DeepSeek), and (ii) commit-value classification
cannot detect two channels: strategic avoidance under test-detection ("the model read our
intent and deliberately answered something else") and memory-conflict abstention ("the
annotation value contradicts what I remember, so I refuse").

Audit set, fixed in advance: ALL commits in never_created A- cells (both cloud
configurations), and 15 abstentions per cloud configuration sampled from never_created A+C+
none-arm trials (seed 20260902). Each stored output is coded for the presence of:
- M-EXPRESS: cites its own/world knowledge as the source of a stated value
- M-CONFLICT: cites a remembered/known true value as a reason to distrust or not adopt the
  annotation value
- TEST-AWARE: names the scenario as a test, trick, planted value, or constructed evaluation
- CLOSURE: reasons from the record's causal status (never created / no value generated)
- DERIVE: derives a value from the residual R-101 text
Multiple codes may apply; counts and verbatim examples are reported. Exploratory; alters no
gate, criterion, or branch. The qwen configuration is audited identically after its run lands.

### Addendum A2 — outcome (2026-09-02, cloud configurations; qwen to follow identically)

70 outputs coded (40 = all never_created A- commits; 30 = seeded A+C+ none-arm abstentions).
Counts: M-EXPRESS 0/70; M-CONFLICT 0/70; TEST-AWARE 0/70; DERIVE 40/40 commits; CLOSURE
reasoning present in a minority of abstentions (explicit citations of the cancelled
measurement / nonexistent primary record), with most abstentions discounting the annotation
value as "a number without context".

Resolution of the intrusion counts from Addendum A1: every A- commit sits on a construct-audit
class B/C base item (Fresno_1 = B, arithmetically derivable total; IPCC_1, Pharmacy_1,
Huguenot_1 = C, residual text invites the value), and every apparent memorized-value match is a
derivation coincidence — the derived value equals the true answer because the residual passage
still supports deriving it. All such items are excluded from the D33 primary set by design; no
output cited the model's own knowledge, no output flagged the scenario as a test or a planted
value, and no abstention invoked a remembered true value against the annotation.

Additional observation recorded for interpretation (not a criterion change): the structured
R-103 field pair binds the value to the question more weakly than prose testimony would
("Value entered in this annotation: 140" is discounted as unlabeled), which plausibly
attenuates V2 levels relative to the synthetic vignettes' explicit assertion. This is a
property of the registered design, disclosed here before judgment.
