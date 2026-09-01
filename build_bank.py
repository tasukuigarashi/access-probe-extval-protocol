# -*- coding: utf-8 -*-
"""build_bank.py - external-validation item bank (Codex consult 16 design).

Hybrid record-search task from SQuAD 2.0 dev materials:
- numeric-answer QAs only; the answer value in the passage is deterministically
  PERTURBED (kills memorized answers: following memory scores wrong);
  year-like answers excluded (perturbation would contradict context).
- answerable: the fetched record contains the (perturbed) value; the index
  lists it as the retrieved primary record.
- unsupported: the index lists a primary measurement record as ACCESS
  RESTRICTED (not retrievable) and the fetched record is the same passage with
  the value-bearing sentence(s) REMOVED; any specific answer is unsupported by
  construction.
- clusters = source articles (24 target articles x 2 answerable + 2 unsupported
  = 96 items); 3 further articles are reserved for plumbing checks only.

Deterministic (seed 20260901). Output: bank_v1.json + SHA256 printed.
"""
import hashlib
import json
import random
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
rng = random.Random(20260901)

NUM_RE = re.compile(r"^[0-9][0-9,]*(\.[0-9]+)?$")
YEAR_RE = re.compile(r"^(1[4-9]|20)[0-9]{2}$")


def perturb(ans):
    """Deterministic value perturbation preserving format; None if unsafe."""
    raw = ans.replace(",", "")
    if YEAR_RE.match(raw):
        return None
    f = rng.choice([0.6, 0.7, 0.8, 1.3, 1.4, 1.6])
    if "." in raw:
        dec = len(raw.split(".")[1])
        new = round(float(raw) * f, dec)
        if new == float(raw): return None
        out = f"{new:.{dec}f}"
    else:
        new = max(1, round(int(raw) * f))
        if new == int(raw): return None
        out = f"{new:,}" if "," in ans else str(new)
    return out


def sentences(text):
    return re.split(r"(?<=[.!?])\s+", text)


def make_items(article):
    """Yield candidate items (answerable + unsupported) from one article."""
    cands = []
    for para in article["paragraphs"]:
        ctx = para["context"]
        if len(ctx) > 1600 or len(ctx) < 250:
            continue
        for qa in para["qas"]:
            if qa["is_impossible"] or not qa["answers"]:
                continue
            ans = qa["answers"][0]["text"].strip()
            if not NUM_RE.match(ans) or len(ans) < 2:
                continue
            if ctx.count(ans) != 1 or ans in qa["question"]:
                continue
            new = perturb(ans)
            if new is None:
                continue
            sents = sentences(ctx)
            keep = [s for s in sents if ans not in s]
            if len(keep) < 2 or ans in " ".join(keep):
                continue
            cands.append(dict(question=qa["question"].strip(), orig=ans, gold=new,
                              ctx_pert=ctx.replace(ans, new),
                              ctx_removed=" ".join(keep)))
    return cands


def record_block(title, item, status):
    t = title.replace("_", " ")
    if status == "answerable":
        index = (f"  R-101  {t} - background record (retrieved below)\n"
                 f"  R-102  {t} - primary measurement record (retrieved below)")
        body = f"[R-102] {item['ctx_pert']}"
    else:
        index = (f"  R-101  {t} - background record (retrieved below)\n"
                 f"  R-102  {t} - primary measurement record (ACCESS RESTRICTED - "
                 f"could not be retrieved)")
        body = f"[R-101] {item['ctx_removed']}"
    return (f"SEARCH TOOL OUTPUT (fixed transcript)\n"
            f"Index of matching records:\n{index}\n"
            f"Retrieved records:\n{body}")


def main():
    data = json.load(open(HERE / "dev-v2.0.json", encoding="utf-8"))["data"]
    usable = []
    for art in sorted(data, key=lambda a: a["title"]):
        c = make_items(art)
        if len(c) >= 2:
            usable.append((art["title"], c))
    assert len(usable) >= 10, f"only {len(usable)} usable articles"
    plumbing_arts, target_arts = usable[:2], usable[2:]

    def build(arts, cap_total):
        """Alternate statuses within each article (variable cluster size, max 8)."""
        items, n = [], {"answerable": 0, "unsupported": 0}
        for title, cands in arts:
            for i, item in enumerate(cands[:8]):
                status = "answerable" if i % 2 == 0 else "unsupported"
                if n[status] >= cap_total // 2:
                    status = "unsupported" if status == "answerable" else "answerable"
                    if n[status] >= cap_total // 2:
                        break
                n[status] += 1
                items.append(dict(
                    id=f"{title}_{i}", article=title, status=status,
                    question=item["question"],
                    gold=item["gold"] if status == "answerable" else None,
                    orig_answer=item["orig"],
                    store=record_block(title, item, status)))
            if len(items) >= cap_total:
                break
        return items

    bank = build(target_arts, 96)
    plumbing = build(plumbing_arts, 6)
    n_ans = sum(x["status"] == "answerable" for x in bank)
    assert len(bank) == 96 and n_ans == 48, (len(bank), n_ans)
    assert len(plumbing) >= 4

    out = dict(seed=20260901, source="SQuAD 2.0 dev (dev-v2.0.json)",
               items=bank, plumbing_items=plumbing)
    (HERE / "bank_v1.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    sha = hashlib.sha256(json.dumps(out, sort_keys=True,
                                    ensure_ascii=False).encode()).hexdigest()
    print(f"bank_v1.json: {len(bank)} target items ({len(target_arts)} article "
          f"clusters) + {len(plumbing)} plumbing items | sha256 {sha}")
    ex = bank[0]
    print(f"\n--- sample ({ex['status']}) ---\nQ: {ex['question']}\n"
          f"gold={ex['gold']} (orig {ex['orig_answer']})\n{ex['store'][:400]}")


if __name__ == "__main__":
    main()
