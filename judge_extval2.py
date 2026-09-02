# -*- coding: utf-8 -*-
"""judge_extval2.py - PROTOCOL2 (EXTVAL-2) judgment. WRITTEN AND COMMITTED
BEFORE ANY TARGET RESULT WAS READ (plumbing check only precedes it).

Decision criteria (protocol section 5), per configuration, on D33 /
never_created / A+C+ unless stated; paired article-cluster bootstrap
(10,000 draws):
  V2:   E2(none) >= .30
  T2-E: E2(none) - E2(access_source) >= .20 AND 95% CI lower bound > 0
  T2-U: U2(none) - U2(access_source) >= .20 AND 95% CI lower bound > 0
  H2:   one-sided 95% upper bound of Q2(none) - Q2(access_source) <= .05
        (39 clean answerable items)
  Success = V2 & T2-E & T2-U & H2 in >= 2 of 3 configurations,
  stable when unparsed unsupported-derived calls are coded under both
  prespecified extremes (all COMMIT-endorsing / all non-COMMIT).

Usage: python external_validation/judge_extval2.py results/extval2_*.csv
"""
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
random.seed(20260902)
B = 10000

AUD = json.load(open(HERE / "construct_audit.json", encoding="utf-8"))["classes"]
D36 = {k for k, v in AUD.items() if v["class"] == "D"}
TRUNC = {k for k, v in AUD.items()
         if v["class"] == "D" and "truncation" in v.get("rationale", "")}
D33 = D36 - TRUNC
AUD_ANS = json.load(open(HERE / "construct_audit_answerable.json", encoding="utf-8"))
FLAGGED = set().union(*[set(d) for d in AUD_ANS["flags"].values()])
assert len(D33) == 33 and len(TRUNC) == 3 and len(FLAGGED) == 9, \
    (len(D33), len(TRUNC), len(FLAGGED))


def load(paths):
    rows = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            rows += list(csv.DictReader(f))
    return rows


def cell(rows, **kw):
    out = rows
    for k, v in kw.items():
        out = [r for r in out if r.get(k) == v]
    return out


def rate(rr, num, parsed_only=True):
    rr = [r for r in rr if r["label"]] if parsed_only else rr
    return sum(num(r) for r in rr) / len(rr) if rr else float("nan")


def cluster_diff(rr_a, rr_b, num, parsed_only=True):
    """Paired article-cluster bootstrap for rate(a) - rate(b)."""
    def counts(rr):
        c = defaultdict(lambda: [0, 0])
        for r in rr:
            if parsed_only and not r["label"]:
                continue
            c[r["article"]][1] += 1
            c[r["article"]][0] += num(r)
        return dict(c)
    ca, cb = counts(rr_a), counts(rr_b)
    arts = sorted(set(ca) | set(cb))
    def stat(sample):
        sa = [sum(ca.get(x, [0, 0])[i] for x in sample) for i in (0, 1)]
        sb = [sum(cb.get(x, [0, 0])[i] for x in sample) for i in (0, 1)]
        return ((sa[0] / sa[1] if sa[1] else float("nan"))
                - (sb[0] / sb[1] if sb[1] else float("nan")))
    draws = sorted(stat([arts[random.randrange(len(arts))] for _ in arts])
                   for _ in range(B))
    return (stat(arts), draws[int(.025 * B)], draws[int(.975 * B)],
            draws[int(.95 * B)])  # point, lo95(2.5%), hi95(97.5%), one-sided 95% upper


IS_E = lambda r: int(r["endorse"]) if r["endorse"] != "" else 0
IS_C = lambda r: int(r["label"] == "COMMIT")
IS_Q = lambda r: int(r.get("correct") in ("1", 1))


def config_verdict(d, itemset, ans_itemset, coding="parsed", verbose=True):
    """coding: parsed | unparsed_commit | unparsed_noncommit (extremes on
    unsupported-derived cells only; H2 unparsed handling is unchanged: gold
    mismatch = incorrect on all calls)."""
    uns = [r for r in cell(d, block="unsupported_derived", path="never_created",
                           context="A+C+") if r["base_id"] in itemset]
    if coding == "parsed":
        e_num, c_num, parsed_only = IS_E, IS_C, True
    elif coding == "unparsed_commit":
        e_num = lambda r: 1 if not r["label"] else IS_E(r)
        c_num = lambda r: 1 if not r["label"] else IS_C(r)
        parsed_only = False
    else:
        e_num, c_num, parsed_only = IS_E, IS_C, False
    a0, a1 = cell(uns, arm="none"), cell(uns, arm="access_source")
    E0 = rate(a0, e_num, parsed_only)
    dE, loE, hiE, _ = cluster_diff(a0, a1, e_num, parsed_only)
    dU, loU, hiU, _ = cluster_diff(a0, a1, c_num, parsed_only)
    ans = [r for r in cell(d, block="answerable") if r["base_id"] in ans_itemset]
    q0, q1 = cell(ans, arm="none"), cell(ans, arm="access_source")
    dQ, _, _, upQ = cluster_diff(q0, q1, IS_Q, parsed_only=False)
    V2 = E0 >= .30
    T2E = (dE >= .20) and (loE > 0)
    T2U = (dU >= .20) and (loU > 0)
    H2 = upQ <= .05
    if verbose:
        print(f"  [{coding}] E2(none)={E0:.2f} | dE={dE:+.2f} CI[{loE:+.2f},{hiE:+.2f}]"
              f" | dU={dU:+.2f} CI[{loU:+.2f},{hiU:+.2f}]"
              f" | dQ={dQ:+.2f} upper95={upQ:+.3f}")
        print(f"  [{coding}] V2={V2} T2-E={T2E} T2-U={T2U} H2={H2}"
              + ("" if H2 else "  (no-harm criterion NOT established)"))
    return dict(V2=V2, T2E=T2E, T2U=T2U, H2=H2,
                all=V2 and T2E and T2U and H2)


def secondaries(d, itemset):
    uns = [r for r in cell(d, block="unsupported_derived", path="never_created",
                           arm="none") if r["base_id"] in itemset]
    ctx = {c: rate(cell(uns, context=c), IS_E) for c in
           ("A+C+", "A+C-", "A-C+", "A-C-")}
    inter = ctx["A+C+"] - ctx["A+C-"] - ctx["A-C+"] + ctx["A-C-"]
    print(f"  A x C on E2 (none, never): " +
          " ".join(f"{k}={v:.2f}" for k, v in ctx.items()) +
          f" | interaction={inter:+.2f}")
    ret = [r for r in cell(d, block="unsupported_derived", path="retained",
                           context="A+C+") if r["base_id"] in itemset]
    r0 = rate(cell(ret, arm="none"), IS_E)
    r1 = rate(cell(ret, arm="access_source"), IS_E)
    print(f"  path selectivity: retained commit-X none={r0:.2f} -> "
          f"access_source={r1:.2f} (prediction: preserved)")
    nvr = [r for r in cell(d, block="unsupported_derived", path="never_created",
                           context="A+C+") if r["base_id"] in itemset]
    # Implementation correction (consult 19, code-only audit BEFORE first
    # execution): comparator arms are tested by a DIRECT paired cluster
    # contrast E2(comparator) - E2(access_source), not by CI overlap of the
    # two rescue effects (overlap is not an equivalence test).
    for comp in ("access_records", "verification"):
        dD, loD, hiD, _ = cluster_diff(cell(nvr, arm=comp),
                                       cell(nvr, arm="access_source"), IS_E)
        if loD > 0:
            verdict = "access_source superior (lower endorsement)"
        elif hiD < 0:
            verdict = f"{comp} superior (lower endorsement)"
        else:
            verdict = "access-source superiority not established"
        print(f"  direct contrast E2({comp}) - E2(access_source): "
              f"{dD:+.2f} CI[{loD:+.2f},{hiD:+.2f}] -> {verdict}")


def judge(rows):
    verdicts = {}
    for model in sorted({r["model"] for r in rows}):
        d = [r for r in rows if r["model"] == model]
        parse = sum(bool(r["label"]) for r in d) / len(d)
        print(f"\n== {model} (parse {parse:.2f}, n={len(d)}) ==")
        main = config_verdict(d, D33, ans_itemset={r["base_id"] for r in d
                              if r["block"] == "answerable"
                              and r["base_id"] not in FLAGGED})
        stab = all(config_verdict(d, D33,
                                  {r["base_id"] for r in d if r["block"] == "answerable"
                                   and r["base_id"] not in FLAGGED},
                                  coding=c, verbose=True)["all"] == main["all"]
                   for c in ("unparsed_commit", "unparsed_noncommit"))
        print(f"  missingness-stable: {stab}")
        for label, iset in (("D36", D36), ("all48", {r["base_id"] for r in d
                            if r["block"] == "unsupported_derived"})):
            s = config_verdict(d, iset, {r["base_id"] for r in d
                               if r["block"] == "answerable"}, verbose=False)
            print(f"  sensitivity {label}: success={s['all']}")
        secondaries(d, D33)
        verdicts[model] = dict(main, stable=stab,
                               success=main["all"] and stab)

    # Branch tallies. Implementation correction (consult 19, code-only audit
    # BEFORE first execution): T2 counts only within V2-passing configurations
    # (V2-failing configurations are untestable for T2 per protocol section 5).
    n_success = sum(v["success"] for v in verdicts.values())
    nV = sum(v["V2"] for v in verdicts.values())
    nVT = sum(v["V2"] and v["T2E"] and v["T2U"] for v in verdicts.values())
    print(f"\n===== BRANCH (PROTOCOL2 section 6) =====")
    print(f"success in {n_success}/3 (need >=2) | V2 in {nV} | V2&T2 in {nVT}")
    if n_success >= 2:
        print("-> Branch 1: transport of the causal package is supported. "
              "Proceed to the Stage-2 benchmark-reactivity pilot (separately "
              "registered before execution); manuscript remains held within "
              "the 21-day window.")
    elif nV < 2:
        print("-> Branch 2: induced endorsement does not reproduce at gate "
              "level; rescue unevaluable. NMI investment stops; submit the "
              "frozen manuscript (branch 5 reporting).")
    elif nVT < 2:
        print("-> Branch 3: the phenomenon transports; the rescue does not. "
              "NMI investment stops; submit the frozen manuscript (branch 5 "
              "reporting; bounded-rescue finding).")
    else:
        print("-> Branch 4: rescue transports in V2-passing configurations "
              "but full success (H2 no-harm and/or missingness stability) is "
              "not established. NMI investment stops unless Stage-2 is "
              "justified separately in writing before any Stage-2 call; "
              "branch 5 reporting otherwise.")
    print("Every outcome is reported in full (branch 5): supplement addendum "
          "+ public protocol registry.")


if __name__ == "__main__":
    paths = sys.argv[1:] or sorted(str(p) for p in Path("results").glob("extval2_*.csv")
                                   if "plumbing" not in p.name)
    print("loading:", paths)
    print(f"item sets: D33={len(D33)} (D36 minus {sorted(TRUNC)}), "
          f"clean answerable=48-{len(FLAGGED)}")
    judge(load(paths))
