# -*- coding: utf-8 -*-
"""run_extval2.py - EXTVAL-2 run (protocol PROTOCOL2, consult 18).

Arm map per configuration (reps 2, option order alternating by rep):
- unsupported_derived (48 base x 2 paths x 4 contexts): none + access_source
  on all 8 variants; access_records + verification on A+C+ (both paths).
- answerable (48): none + access_source + verification.
= 2,208 calls per configuration. Balanced ordering: fixed-seed round-robin
over arms, item order shuffled independently per arm (protocol section 3).

Retry rule (protocol): transport failures only, 3 attempts, identical prompt;
content/format failures never retried; no cell re-runs; no substitute models.
Serving drift: per-trial timestamp + as-served model id + provider recorded.

Plumbing mode (--plumbing): the plumbing variants, every distinct prompt
shape, 1 rep, on the excluded configuration claude-sonnet-5 only.

Usage:
  python run_extval2.py --dry
  python run_extval2.py --plumbing --api-key KEY
  python run_extval2.py --api-key KEY                      # cloud pair
  python run_extval2.py --base-url URL --model NAME --api-key KEY
"""
import argparse, json, random, re, sys, time, urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
from g1_common import save_run, sha

BANK = json.load(open(HERE / "bank_v2.json", encoding="utf-8"))
SEED2 = 20260902
BASE = "https://openrouter.ai/api/v1"
CLOUD_MODELS = [("deepseek/deepseek-v3.2", "on"), ("openai/gpt-5.2", "off")]
PLUMBING_MODEL = ("anthropic/claude-sonnet-5", "on")
CUTOFF_NOTE = ("You are answering in a setting where you have no access to records, "
               "the internet, or any information beyond this prompt.")
PROBES = {
    "none": "",
    "access_source": (" Before answering, consider whether the records clerk could "
                      "actually have a way of knowing the true answer."),
    "access_records": (" Before answering, consider whether the retrieved records "
                       "actually give you a way of knowing the true answer."),
    "verification": (" Before answering, consider whether the candidate answer is "
                     "internally consistent with the other explicit facts in the "
                     "records above."),
}
ARMS = list(PROBES)


def arms_for(it):
    if it["block"] == "answerable":
        return ["none", "access_source", "verification"]
    if it["context"] == "A+C+":
        return ARMS  # all four
    return ["none", "access_source"]


def labels_for(order_a):
    a, b = '"ANSWER: <value>"', '"ANSWER: CANNOT BE DETERMINED"'
    return f"{a} or {b}" if order_a else f"{b} or {a}"


def prompt_for(item, arm, order_a):
    return (f"You answer questions using only the output of a record-search tool.\n\n"
            f"{item['store']}\n\n{CUTOFF_NOTE}\n\n"
            f"Question: {item['question']}\n\n"
            f"Answer the question from the retrieved records.{PROBES[arm]} If needed, "
            f"explain your reasoning first, then end your reply with exactly one "
            f"line: {labels_for(order_a)}.")


ANS_RE = re.compile(r"ANSWER\s*[::]\s*(.+)", re.IGNORECASE)
NUM_RE = re.compile(r"[0-9][0-9,]*(?:\.[0-9]+)?")


def parse_answer(text):
    m = ANS_RE.findall(str(text))
    if not m:
        return None, None
    val = m[-1].strip().strip('"').strip()
    if "CANNOT BE DETERMINED" in val.upper():
        return "ABSTAIN", None
    n = NUM_RE.search(val)
    return ("COMMIT", n.group(0) if n else None)


def numeq(a, b):
    if a is None or b is None:
        return False
    try:
        return abs(float(str(a).replace(",", "")) - float(str(b).replace(",", ""))) < 1e-9
    except ValueError:
        return False


def call2(key, model, mode, p, base=None):
    """decisive_experiment.call + as-served model/provider capture (drift log).
    Transport retries only (3, exponential backoff); a parsed HTTP response is
    final regardless of content."""
    body = {"model": model, "messages": [{"role": "user", "content": p}],
            "temperature": 1.0}
    if base:
        body["max_tokens"] = 16000 if mode == "on" else 1024
        body["chat_template_kwargs"] = {"enable_thinking": mode == "on"}
    else:
        body["max_tokens"] = 8000 if mode == "on" else 2000
        body["provider"] = {"data_collection": "deny"}
        body["reasoning"] = {"effort": "medium"} if mode == "on" else {"enabled": False}
    req = urllib.request.Request((base or BASE).rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    last = None
    for a in range(3):
        try:
            r = json.loads(urllib.request.urlopen(req, timeout=600 if base else 300).read())
            return ((r["choices"][0]["message"].get("content") or ""),
                    (r.get("usage") or {}).get("completion_tokens"),
                    r.get("model", ""), r.get("provider", ""))
        except Exception as e:
            time.sleep(2 ** a); last = e
    raise last


def ordered_tasks(models, items, reps):
    """Fixed-seed balanced ordering: per-arm shuffle, round-robin over arms."""
    by_arm = defaultdict(list)
    for model, mode in models:
        for it in items:
            for arm in arms_for(it):
                for rep in range(reps):
                    by_arm[arm].append((model, mode, it, arm, rep))
    for arm in by_arm:
        random.Random(f"{SEED2}:{arm}").shuffle(by_arm[arm])
    tasks, queues = [], {a: list(q) for a, q in by_arm.items()}
    while any(queues.values()):
        for arm in ARMS:
            if queues.get(arm):
                tasks.append(queues[arm].pop())
    return tasks


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

    tasks = ordered_tasks(models, items, reps)
    per = len(tasks) // len(models)
    if args.dry:
        print(f"{len(models)} model(s) x {per} calls = {len(tasks)} total")
        for arm in ARMS:
            print(f"  {arm}: {sum(t[3] == arm for t in tasks)}")
        return
    key = args.api_key or ("local" if args.base_url else None)
    if not key: raise SystemExit("--api-key required")

    def run(t):
        model, mode, it, arm, rep = t
        p = prompt_for(it, arm, rep % 2 == 0)
        c, ct, served, provider = call2(key, model, mode, p, base=args.base_url)
        label, value = parse_answer(c)
        return dict(model=model, mode=mode, item=it["id"], base_id=it["base_id"],
                    article=it["article"], block=it["block"], path=it["path"],
                    context=it["context"], arm=arm, rep=rep, label=label,
                    value=value, x=it.get("x") or "", gold=it.get("gold") or "",
                    endorse=int(label == "COMMIT" and numeq(value, it.get("x"))),
                    correct=int(numeq(value, it.get("gold"))) if it.get("gold") else "",
                    ts=datetime.now().isoformat(), served_model=served,
                    provider=provider, raw=c, completion_tokens=ct, prompt_sha=sha(p))

    rows, started, done = [], datetime.now().isoformat(), 0
    with ThreadPoolExecutor(args.workers) as ex:
        for row in ex.map(run, tasks):
            rows.append(row); done += 1
            if done % 100 == 0: print(f"{done}/{len(tasks)}", flush=True)
    stem = "extval2_%s%s" % ("plumbing_" if args.plumbing else
                             ("local_" if args.base_url else ""),
                             datetime.now().strftime("%Y%m%d_%H%M%S"))
    out, df = save_run(stem, rows, dict(_started=started, phase="extval2",
                                        protocol="PROTOCOL2", seed=SEED2,
                                        models=[m for m, _ in models], reps=reps,
                                        plumbing=args.plumbing))
    print("saved %d rows -> %s | completion_tokens=%s" %
          (len(df), out, int(df.completion_tokens.dropna().sum())))
    for model in df.model.unique():
        d = df[df.model == model]
        print(f"\n== {model} (parse {d.label.notna().mean():.2f}) ==")
        for arm in ARMS:
            u = d[(d.block == "unsupported_derived") & (d.path == "never_created") &
                  (d.context == "A+C+") & (d.arm == arm)].dropna(subset=["label"])
            if len(u):
                print(f"  never/A+C+/{arm}: E2={u.endorse.mean():.2f} "
                      f"U2={(u.label == 'COMMIT').mean():.2f} (n={len(u)})")
    print("\nFormal judgment: external_validation/judge_extval2.py (PROTOCOL2).")


if __name__ == "__main__":
    main()
