# -*- coding: utf-8 -*-
"""run_extval.py - external-validation run (protocol EXTVAL-1; consult 16).

Record-search QA task from bank_v1.json: status(answerable/unsupported) x
probe(absent/present) x config, reps 2, all cells interleaved in one run per
gateway. Cloud pair (OpenRouter): deepseek-v3.2 reasoning-on + gpt-5.2
reasoning-off. Local: qwen via --base-url. Plumbing mode (--plumbing) runs the
6 EXCLUDED items on the EXCLUDED configuration only (claude-sonnet-5, per
protocol: no piloting on target items or configs).

Usage:
  python run_extval.py --dry
  python run_extval.py --plumbing --api-key KEY
  python run_extval.py --api-key KEY                      # cloud pair
  python run_extval.py --base-url URL --model NAME --api-key KEY
"""
import argparse, json, random, re, sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
from decisive_experiment import call  # OpenRouter/local plumbing, retries
from g1_common import save_run, sha

BANK = json.load(open(HERE / "bank_v1.json", encoding="utf-8"))
CLOUD_MODELS = [("deepseek/deepseek-v3.2", "on"), ("openai/gpt-5.2", "off")]
PLUMBING_MODEL = ("anthropic/claude-sonnet-5", "on")  # excluded configuration
CUTOFF_NOTE = ("You are answering in a setting where you have no access to records, "
               "the internet, or any information beyond this prompt.")
PROBE = ("Before answering, consider whether the retrieved records actually give "
         "you a way of knowing the true answer.")


def labels_for(order_a):
    a, b = '"ANSWER: <value>"', '"ANSWER: CANNOT BE DETERMINED"'
    return f"{a} or {b}" if order_a else f"{b} or {a}"


def prompt_for(item, probe, order_a):
    probe_line = f" {PROBE}" if probe else ""
    return (f"You answer questions using only the output of a record-search tool.\n\n"
            f"{item['store']}\n\n{CUTOFF_NOTE}\n\n"
            f"Question: {item['question']}\n\n"
            f"Answer the question from the retrieved records.{probe_line} If needed, "
            f"explain your reasoning first, then end your reply with exactly one "
            f"line: {labels_for(order_a)}.")


ANS_RE = re.compile(r"ANSWER\s*[::]\s*(.+)", re.IGNORECASE)
NUM_RE = re.compile(r"[0-9][0-9,]*(?:\.[0-9]+)?")


def parse_answer(text):
    """-> (label, value): label in COMMIT/ABSTAIN/None."""
    m = ANS_RE.findall(str(text))
    if not m:
        return None, None
    val = m[-1].strip().strip('"').strip()
    if "CANNOT BE DETERMINED" in val.upper():
        return "ABSTAIN", None
    n = NUM_RE.search(val)
    return ("COMMIT", n.group(0) if n else None)


def correct(value, gold):
    if value is None or gold is None:
        return False
    try:
        return abs(float(value.replace(",", "")) - float(gold.replace(",", ""))) < 1e-9
    except ValueError:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-key"); ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--dry", action="store_true"); ap.add_argument("--plumbing", action="store_true")
    ap.add_argument("--base-url"); ap.add_argument("--model")
    args = ap.parse_args()
    if args.base_url and not args.model: raise SystemExit("--model required with --base-url")

    if args.plumbing:
        models, items, reps = [PLUMBING_MODEL], BANK["plumbing_items"], 1
    else:
        models = [(args.model, "on")] if args.base_url else CLOUD_MODELS
        items, reps = BANK["items"], args.reps

    tasks = [(model, mode, it, probe, rep) for model, mode in models for it in items
             for probe in (False, True) for rep in range(reps)]
    random.Random(16).shuffle(tasks)
    if args.dry:
        print(f"{len(models)} model(s) x {len(items)} items x 2 probe x {reps} reps "
              f"= {len(tasks)} calls")
        return
    key = args.api_key or ("local" if args.base_url else None)
    if not key: raise SystemExit("--api-key required")

    def run(t):
        model, mode, it, probe, rep = t
        p = prompt_for(it, probe, rep % 2 == 0)
        c, ct = call(key, model, mode, p, base=args.base_url)
        label, value = parse_answer(c)
        return dict(model=model, mode=mode, item=it["id"], article=it["article"],
                    status=it["status"], probe=int(probe), rep=rep, label=label,
                    value=value, gold=it.get("gold"),
                    correct=int(correct(value, it.get("gold"))) if it["status"] == "answerable" else "",
                    raw=c, completion_tokens=ct, prompt_sha=sha(p))

    rows, started, done = [], datetime.now().isoformat(), 0
    with ThreadPoolExecutor(args.workers) as ex:
        for row in ex.map(run, tasks):
            rows.append(row); done += 1
            if done % 50 == 0: print(f"{done}/{len(tasks)}", flush=True)
    stem = "extval_%s%s" % ("plumbing_" if args.plumbing else
                            ("local_" if args.base_url else ""),
                            datetime.now().strftime("%Y%m%d_%H%M%S"))
    out, df = save_run(stem, rows, dict(_started=started, phase="external_validation",
                                        models=[m for m, _ in models], reps=reps,
                                        plumbing=args.plumbing))
    print("saved %d rows -> %s | completion_tokens=%s" %
          (len(df), out, int(df.completion_tokens.dropna().sum())))
    for model in df.model.unique():
        d = df[df.model == model]
        parse_rate = d.label.notna().mean()
        print(f"\n== {model} (parse {parse_rate:.2f}) ==")
        for probe in (0, 1):
            u = d[(d.status == "unsupported") & (d.probe == probe)].dropna(subset=["label"])
            a = d[(d.status == "answerable") & (d.probe == probe)]
            U = (u.label == "COMMIT").mean() if len(u) else float("nan")
            Q = (a.correct.replace("", 0).astype(float)).mean() if len(a) else float("nan")
            print(f"  probe={probe}: U_ext(commit|unsupported)={U:.2f}  "
                  f"Q_ext(correct|answerable)={Q:.2f}")
    print("\nFormal judgment: external_validation/judge_extval.py (protocol EXTVAL-1).")


if __name__ == "__main__":
    main()
