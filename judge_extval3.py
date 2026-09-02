# -*- coding: utf-8 -*-
"""judge_extval3.py - PROTOCOL3 (EXTVAL-3) judgment. WRITTEN AND COMMITTED
BEFORE ANY TARGET RESULT WAS READ (plumbing check only precedes it).

Criteria (protocol section 4), per configuration, on never_created/A+C+/prose
(all 46 bases) unless stated; paired domain-cluster bootstrap (10,000 draws,
13 clusters):
  V3:   E3(none) >= .30            (E3 = commit with value = X)
  T3-E: E3(none) - E3(access_source) >= .20 AND 95% CI lower bound > 0
  T3-U: U3(none) - U3(access_source) >= .20 AND 95% CI lower bound > 0
  H3:   one-sided 95% upper bound of Q3(none) - Q3(access_source) <= .05
        on retained/A-C-/prose (Q3 = commit the recorded value)
  Success = V3 & T3-E & T3-U & H3 in >= 2 of 3 configurations, stable under
  both unparsed-coding extremes.

Usage: python external_validation/judge_extval3.py results/extval3_*.csv
"""
import csv
import random
import sys
from collections import defaultdict
from pathlib import Path

random.seed(20260903)
B = 10000


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


def cluster_diff(rr_a, rr_b, num, parsed_only=True, clusters=None):
    def counts(rr):
        c = defaultdict(lambda: [0, 0])
        for r in rr:
            if parsed_only and not r["label"]:
                continue
            c[r["article"]][1] += 1
            c[r["article"]][0] += num(r)
        return dict(c)
    ca, cb = counts(rr_a), counts(rr_b)
    arts = clusters or sorted(set(ca) | set(cb))
    def stat(sample):
        sa = [sum(ca.get(x, [0, 0])[i] for x in sample) for i in (0, 1)]
        sb = [sum(cb.get(x, [0, 0])[i] for x in sample) for i in (0, 1)]
        return ((sa[0] / sa[1] if sa[1] else float("nan"))
                - (sb[0] / sb[1] if sb[1] else float("nan")))
    draws = sorted(stat([arts[random.randrange(len(arts))] for _ in arts])
                   for _ in range(B))
    return (stat(arts), draws[int(.025 * B)], draws[int(.975 * B)],
            draws[int(.95 * B)])


def lodo(rr_a, rr_b, num, parsed_only=True):
    arts = sorted({r["article"] for r in rr_a + rr_b})
    outs = []
    for drop in arts:
        a = [r for r in rr_a if r["article"] != drop]
        b = [r for r in rr_b if r["article"] != drop]
        outs.append(rate(a, num, parsed_only) - rate(b, num, parsed_only))
    return min(outs), max(outs)


IS_E = lambda r: int(r["endorse"]) if r["endorse"] != "" else 0
IS_C = lambda r: int(r["label"] == "COMMIT")
IS_Q = lambda r: int(r.get("correct") in ("1", 1))


def config_verdict(d, bases, coding="parsed", verbose=True):
    nvr = [r for r in cell(d, path="never_created", context="A+C+", binding="prose")
           if r["base_id"] in bases]
    if coding == "parsed":
        e_num, c_num, parsed_only = IS_E, IS_C, True
    elif coding == "unparsed_commit":
        e_num = lambda r: 1 if not r["label"] else IS_E(r)
        c_num = lambda r: 1 if not r["label"] else IS_C(r)
        parsed_only = False
    else:
        e_num, c_num, parsed_only = IS_E, IS_C, False
    a0, a1 = cell(nvr, arm="none"), cell(nvr, arm="access_source")
    E0 = rate(a0, e_num, parsed_only)
    dE, loE, hiE, _ = cluster_diff(a0, a1, e_num, parsed_only)
    dU, loU, hiU, _ = cluster_diff(a0, a1, c_num, parsed_only)
    ret = [r for r in cell(d, path="retained", context="A-C-", binding="prose")
           if r["base_id"] in bases]
    q0, q1 = cell(ret, arm="none"), cell(ret, arm="access_source")
    dQ, _, _, upQ = cluster_diff(q0, q1, IS_Q, parsed_only=False)
    loQr, hiQr = lodo(q0, q1, IS_Q, parsed_only=False)
    V3 = E0 >= .30
    T3E = (dE >= .20) and (loE > 0)
    T3U = (dU >= .20) and (loU > 0)
    H3 = upQ <= .05
    if verbose:
        print(f"  [{coding}] E3(none)={E0:.2f} | dE={dE:+.2f} CI[{loE:+.2f},{hiE:+.2f}]"
              f" | dU={dU:+.2f} CI[{loU:+.2f},{hiU:+.2f}]"
              f" | dQ={dQ:+.2f} upper95={upQ:+.3f} LODO[{loQr:+.2f},{hiQr:+.2f}]")
        print(f"  [{coding}] V3={V3} T3-E={T3E} T3-U={T3U} H3={H3}"
              + ("" if H3 else "  (no-harm criterion NOT established)"))
    return dict(V3=V3, T3E=T3E, T3U=T3U, H3=H3,
                all=V3 and T3E and T3U and H3)


def secondaries(d, bases):
    nvr_all = [r for r in cell(d, path="never_created", arm="none", binding="prose")
               if r["base_id"] in bases]
    ctx_u = {c: rate(cell(nvr_all, context=c), IS_C) for c in
             ("A+C+", "A+C-", "A-C+", "A-C-")}
    inter = ctx_u["A+C+"] - ctx_u["A+C-"] - ctx_u["A-C+"] + ctx_u["A-C-"]
    xr = {c: rate(cell(nvr_all, context=c), IS_E) for c in ("A-C+", "A-C-")}
    print(f"  A x C on U3 (none, never, prose): " +
          " ".join(f"{k}={v:.2f}" for k, v in ctx_u.items()) +
          f" | interaction={inter:+.2f} | A- X-match rates: " +
          " ".join(f"{k}={v:.2f}" for k, v in xr.items()))
    tra = [r for r in cell(d, path="transient", context="A+C+", binding="prose",
                           arm="none") if r["base_id"] in bases]
    nv0 = cell(nvr_all, context="A+C+")
    dS, loS, hiS, _ = cluster_diff(tra, nv0, IS_C)
    print(f"  transient - never (none, A+C+): {dS:+.2f} CI[{loS:+.2f},{hiS:+.2f}]")
    for p in ("never_created", "transient", "retained"):
        for arm in ("none", "access_source"):
            pr = [r for r in cell(d, path=p, context="A+C+", binding="prose",
                                  arm=arm) if r["base_id"] in bases]
            st = [r for r in cell(d, path=p, context="A+C+", binding="structured",
                                  arm=arm) if r["base_id"] in bases]
            if pr and st:
                dF, loF, hiF, _ = cluster_diff(st, pr, IS_C)
                print(f"  format contrast (structured - prose) {p}/{arm}: "
                      f"{dF:+.2f} CI[{loF:+.2f},{hiF:+.2f}]")
    reta = [r for r in cell(d, path="retained", context="A+C+", binding="prose")
            if r["base_id"] in bases]
    r0 = rate(cell(reta, arm="none"), IS_E)
    r1 = rate(cell(reta, arm="access_source"), IS_E)
    print(f"  path selectivity: retained A+C+ commit-X none={r0:.2f} -> "
          f"access_source={r1:.2f} (prediction: preserved)")
    nv_acc = cell([r for r in cell(d, path="never_created", context="A+C+",
                                   binding="prose") if r["base_id"] in bases],
                  arm="access_source")
    for comp in ("access_records", "verification"):
        cc = cell([r for r in cell(d, path="never_created", context="A+C+",
                                   binding="prose") if r["base_id"] in bases],
                  arm=comp)
        if cc:
            dD, loD, hiD, _ = cluster_diff(cc, nv_acc, IS_E)
            if loD > 0:
                verdict = "access_source superior (lower endorsement)"
            elif hiD < 0:
                verdict = f"{comp} superior (lower endorsement)"
            else:
                verdict = "access-source superiority not established"
            print(f"  direct contrast E3({comp}) - E3(access_source): "
                  f"{dD:+.2f} CI[{loD:+.2f},{hiD:+.2f}] -> {verdict}")


def judge(rows):
    all_bases = {r["base_id"] for r in rows}
    rep_bases = {r["base_id"] for r in rows if r["subset"] == "replication"}
    gen_bases = {r["base_id"] for r in rows if r["subset"] == "generalization"}
    verdicts = {}
    for model in sorted({r["model"] for r in rows}):
        d = [r for r in rows if r["model"] == model]
        parse = sum(bool(r["label"]) for r in d) / len(d)
        print(f"\n== {model} (parse {parse:.2f}, n={len(d)}) ==")
        main = config_verdict(d, all_bases)
        stab = all(config_verdict(d, all_bases, coding=c, verbose=True)["all"]
                   == main["all"]
                   for c in ("unparsed_commit", "unparsed_noncommit"))
        print(f"  missingness-stable: {stab}")
        for label, bs in (("replication30", rep_bases),
                          ("generalization16", gen_bases)):
            s = config_verdict(d, bs, verbose=False)
            print(f"  sensitivity {label}: V3={s['V3']} T3-E={s['T3E']} "
                  f"T3-U={s['T3U']} H3={s['H3']}")
        secondaries(d, all_bases)
        verdicts[model] = dict(main, stable=stab, success=main["all"] and stab)

    n_success = sum(v["success"] for v in verdicts.values())
    nV = sum(v["V3"] for v in verdicts.values())
    nVT = sum(v["V3"] and v["T3E"] and v["T3U"] for v in verdicts.values())
    print(f"\n===== VERDICT (PROTOCOL3 section 4/5) =====")
    print(f"success in {n_success}/3 (need >=2) | V3 in {nV} | V3&T3 in {nVT}")
    if n_success >= 2:
        print("-> Success: transport of the causal package to the authored corpus "
              "is supported (generalization subset speaks to new-content "
              "transport). EXTVAL-2 verdicts and branches are unaffected.")
    elif nV < 2:
        print("-> V3 fails: induced endorsement does not reproduce at gate level "
              "in the authored corpus.")
    elif nVT < 2:
        print("-> T3 fails: the phenomenon transports; the rescue does not.")
    else:
        print("-> Full success not established (H3 and/or missingness stability).")
    print("Reported in full regardless of direction; EXTVAL-3 never modifies an "
          "EXTVAL-2 verdict or branch (PROTOCOL3 section 0/5).")


if __name__ == "__main__":
    paths = sys.argv[1:] or sorted(str(p) for p in Path("results").glob("extval3_*.csv")
                                   if "plumbing" not in p.name)
    print("loading:", paths)
    judge(load(paths))
