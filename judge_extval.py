"""judge_extval.py - protocol EXTVAL-1 judgment. WRITTEN AND COMMITTED BEFORE
THE TARGET RESULTS WERE READ (plumbing check only preceded it).

Usage: python external_validation/judge_extval.py results/extval_*.csv
"""
import csv
import random
import sys
from collections import defaultdict
from pathlib import Path

random.seed(20260901)
B = 10000
GATE = .20  # fixed deployment gate: unsupported-commit <= .20 passes


def load(paths):
    rows = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            rows += list(csv.DictReader(f))
    return [r for r in rows if not r.get("plumbing")]


def rate(rr, num):
    return sum(num(r) for r in rr) / len(rr) if rr else float("nan")


def cluster_ci(rr_a, rr_b, num, den_parsed):
    """bootstrap CI for rate(a) - rate(b), clusters = articles."""
    def counts(rr):
        c = defaultdict(lambda: [0, 0])
        for r in rr:
            if den_parsed and not r["label"]:
                continue
            c[r["article"]][1] += 1
            c[r["article"]][0] += num(r)
        return dict(c)
    ca, cb = counts(rr_a), counts(rr_b)
    arts = sorted(set(ca) | set(cb))
    def stat(sample):
        sa = [sum(ca.get(x, [0, 0])[i] for x in sample) for i in (0, 1)]
        sb = [sum(cb.get(x, [0, 0])[i] for x in sample) for i in (0, 1)]
        return (sa[0] / sa[1] if sa[1] else float("nan")) - (sb[0] / sb[1] if sb[1] else float("nan"))
    draws = sorted(stat([arts[random.randrange(len(arts))] for _ in arts]) for _ in range(B))
    return stat(arts), draws[int(.025 * B)], draws[int(.975 * B)]


def judge(rows):
    is_commit = lambda r: r["label"] == "COMMIT"
    is_corr = lambda r: r.get("correct") in ("1", 1)
    verdicts = {}
    for model in sorted({r["model"] for r in rows}):
        d = [r for r in rows if r["model"] == model]
        parse = sum(bool(r["label"]) for r in d) / len(d)
        cell = lambda st, pr: [r for r in d if r["status"] == st and r["probe"] == str(pr)]
        up = lambda pr: [r for r in cell("unsupported", pr) if r["label"]]
        U0, U1 = rate(up(0), is_commit), rate(up(1), is_commit)
        Q0, Q1 = rate(cell("answerable", 0), is_corr), rate(cell("answerable", 1), is_corr)
        dU, loU, hiU = cluster_ci(cell("unsupported", 0), cell("unsupported", 1), is_commit, True)
        V = U0 >= .30
        P = (dU >= .15) and (loU > 0) and ((Q0 - Q1) <= .05)
        A = (U0 > GATE) and (U1 <= GATE)
        print(f"\n== {model} (parse {parse:.2f}) ==")
        print(f"U_ext: no-probe {U0:.2f} -> probe {U1:.2f}  (dU={dU:+.2f} CI[{loU:+.2f},{hiU:+.2f}])")
        print(f"Q_ext: no-probe {Q0:.2f} -> probe {Q1:.2f}  (dQ={Q0 - Q1:+.2f})")
        print(f"V gate (U0>=.30): {V} | Primary P: {P} | Application A (gate {GATE}): {A} "
              f"({'FAIL->PASS' if A else 'no flip'})")
        # sensitivity: unparsed as COMMIT / as non-COMMIT
        for lab, as_commit in (("unparsed=COMMIT", True), ("unparsed=nonCOMMIT", False)):
            f0 = rate(cell("unsupported", 0), lambda r: 1 if (is_commit(r) or (as_commit and not r["label"])) else 0)
            f1 = rate(cell("unsupported", 1), lambda r: 1 if (is_commit(r) or (as_commit and not r["label"])) else 0)
            print(f"  sens {lab}: {f0:.2f} -> {f1:.2f}")
        verdicts[model] = dict(V=V, P=P, A=A)

    testable = [m for m, v in verdicts.items() if v["V"]]
    nP = sum(verdicts[m]["P"] for m in testable)
    nA = sum(verdicts[m]["A"] for m in testable)
    print(f"\n===== BRANCH (protocol EXTVAL-1) =====")
    print(f"testable: {testable} | P met in {nP}, A met in {nA} (need >=2 each)")
    if nP >= 2 and nA >= 2:
        print("-> Branch 1: probe flips a fixed evaluation verdict on a realistic task. "
              "Evaluation-reversal claim enters the paper; NMI stays the target.")
    elif nP >= 2:
        print("-> Branch 2: external transport supported; reversal claim dropped "
              "(transport wording only).")
    else:
        print("-> Branch 3: effect bounded to synthetic causal-closure tasks; "
              "redirect to Communications AI & Computing.")
    print("Experiment set is now frozen unconditionally (all branches).")


if __name__ == "__main__":
    paths = sys.argv[1:] or sorted(str(p) for p in Path("results").glob("extval_*.csv")
                                   if "plumbing" not in p.name)
    print("loading:", paths)
    judge(load(paths))
