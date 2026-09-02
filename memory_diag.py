# -*- coding: utf-8 -*-
"""memory_diag.py - PROTOCOL2 Addendum A1: memory-intrusion diagnostic.
Declared 2026-09-02 BEFORE any execution of judge_extval2.py. Exploratory;
alters no gate, criterion, or branch.

For every COMMIT, classifies the committed value as: X (the asserted/planted
candidate), ORIG (the item's original SQuAD answer = memorized true value),
or OTHER. Reported per configuration x block x path x context x arm.

Usage: python external_validation/memory_diag.py results/extval2_*.csv
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BANK2 = json.load(open(HERE / "bank_v2.json", encoding="utf-8"))
BANK1 = json.load(open(HERE / "bank_v1.json", encoding="utf-8"))
ORIG = {b: a["orig"] for b, a in BANK2["x_audit"].items()}
ORIG.update({i["id"]: i["orig_answer"] for i in BANK1["items"] + BANK1["plumbing_items"]
             if i["id"] not in ORIG})


def numeq(a, b):
    try:
        return abs(float(str(a).replace(",", "")) - float(str(b).replace(",", ""))) < 1e-9
    except (ValueError, TypeError):
        return False


def main(paths):
    rows = []
    for p in paths:
        rows += list(csv.DictReader(open(p, encoding="utf-8")))
    for model in sorted({r["model"] for r in rows}):
        print(f"\n== {model} ==")
        cells = defaultdict(lambda: [0, 0, 0, 0])  # n_commit, x, orig, other
        n_trials = defaultdict(int)
        for r in rows:
            if r["model"] != model:
                continue
            key = (r["block"], r["path"], r["context"], r["arm"])
            n_trials[key] += 1
            if r["label"] != "COMMIT":
                continue
            c = cells[key]
            c[0] += 1
            orig = ORIG.get(r["base_id"])
            if r["x"] and numeq(r["value"], r["x"]):
                c[1] += 1
            elif orig and numeq(r["value"], orig):
                c[2] += 1
            else:
                c[3] += 1
        print(f"{'cell':<58}{'n':>5}{'commit':>8}{'=X':>6}{'=ORIG':>7}{'other':>7}")
        for key in sorted(cells):
            n, (nc, nx, no, noth) = n_trials[key], cells[key]
            label = "/".join(k for k in key if k)
            print(f"{label:<58}{n:>5}{nc:>8}{nx:>6}{no:>7}{noth:>7}")
        # headline: intrusion in assertion-absent never_created cells
        a_minus = [k for k in cells if k[0] == "unsupported_derived"
                   and k[1] == "never_created" and k[2] in ("A-C+", "A-C-")]
        tot = sum(n_trials[k] for k in a_minus)
        commits = sum(cells[k][0] for k in a_minus)
        intr = sum(cells[k][2] for k in a_minus)
        print(f"  HEADLINE never_created A- cells: {commits} commits / {tot} trials; "
              f"memorized-value intrusions = {intr} ({intr / tot:.3f} of trials)")


if __name__ == "__main__":
    main(sys.argv[1:] or sorted(str(p) for p in Path("results").glob("extval2_*.csv")
                                if "plumbing" not in p.name))
