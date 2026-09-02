# EXTVAL-1: Pre-registered External-Validation Protocol

Public, timestamped pre-registration of protocol EXTVAL-1 (see PROTOCOL.md), registered BEFORE any target-item or target-configuration execution.

Item bank bank_v1.json (SHA-256 bb4ed3df91e9279a42b546b7e4baeeaaa638dc934c6f8f4f93eba3d34b6f3a0c) is reproduced bit-for-bit from the public SQuAD 2.0 dev set (CC BY-SA 4.0) by build_bank.py. run_extval.py / judge_extval.py are the frozen runner and judgment scripts (they import call plumbing from the main study repository and are included here for verbatim prompt and criteria transparency, not as a standalone mirror).

# EXTVAL-2: Registered Post-Freeze Follow-Up (2026-09-02)

PROTOCOL2.md registers EXTVAL-2 BEFORE any target-item or target-configuration execution: a
semi-naturalistic transport test restoring the two causal ingredients EXTVAL-1 omitted
(asserted candidate + claimed access path), crossed with the actual information path
(never-created vs retained). It is a transparent, prospectively fixed deviation from the
EXTVAL-1 unconditional freeze and venue routing (disclosed as such in PROTOCOL2.md section 0).

Item bank bank_v2.json (SHA-256 6e207a55ab170c1639c7743f47553a784aee5c55987ee053ab5eae8352346e78)
is derived deterministically from bank_v1.json by build_bank2.py (seed 20260902), which first
reproduces bank_v1 bit-for-bit from the SQuAD 2.0 dev set and asserts equality; the
candidate-value material audit is embedded under x_audit. construct_audit.json /
construct_audit_answerable.json are the committed pre-existing item audits that fix the primary
item sets (D33 / 39 clean answerable). run_extval2.py / judge_extval2.py are the frozen runner
and judgment scripts, committed before any target result. Results will be appended to
RESULTS.md regardless of direction.
