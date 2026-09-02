# -*- coding: utf-8 -*-
"""build_bank3.py - EXTVAL-3 item bank v3.1 (PROTOCOL3 DRAFT; consult 19).

v3.0 (canonical-JSON sha 91b284b5..., commit ad6e883) is retained in git as the
pre-audit bank; v3.1 implements the consult-19 corrections:
- backgrounds use the conditional storage phrasing ("For measurements that are
  completed and retained, ...") so never/transient carry no presupposition;
- R-102 is a retrieved status entry in every path, with an explicit
  "Measurement: {label}." line (quantity binding; fixes the weak-binding risk
  in the retained/clean-answerable cell);
- testimony prose per consult 19: C+/C- = personally checked / did not
  personally check; A+/A- = "This annotation records the answer to that
  question as {X}." / "This annotation records no answer to that question.";
- the structured field-pair testimony sits on A+C+ of ALL THREE paths
  (testimony-format contrast, explicitly a format/binding bundle, not a pure
  binding factor);
- a prospective generalization subset: 4 NEW authored domains x 4 families
  (16 bases) alongside the 30 previously used v7/v8 families (manipulated
  replication subset). 13 domain clusters + plumbing domain.

Variants per base = 12: never x 4 contexts (prose) + retained x 4 contexts
(prose) + transient A+C+ (prose) + structured A+C+ x {never, transient,
retained}. Deterministic, no RNG. Output: bank_v3_1.json + canonical-JSON
SHA-256 and file-byte SHA-256 printed.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
from item_pool_v7 import CLOSED as V7_CLOSED
from item_pool_v8 import V8_CLOSED

# Authored, value-free domain background (conditional phrasing) + ledger name.
DOMAINS = {
    "weaving": ("For measurements that are completed and retained, the Hirakawa weaving "
                "workshop stores the resulting figures in a bound workshop ledger, and a "
                "measurement is initiated only when the floor manager requests one for a "
                "specific run. Instruments are compared against the house standards at the "
                "opening of each season.", "the workshop ledger"),
    "apiary": ("For measurements that are completed and retained, the Beppu apiary enters "
               "the figures in a shed book kept by the duty keeper, and a measurement is "
               "initiated only on request. Scales and meters are checked against the "
               "cooperative's references between seasons.", "the shed book"),
    "quarry": ("For measurements that are completed and retained, the Ishibe quarry enters "
               "the figures in a yard ledger held at the office, and a measurement is "
               "commissioned per job rather than continuously. Gauges are serviced by the "
               "supplier on a rolling schedule.", "the yard ledger"),
    "greenhouse": ("For measurements that are completed and retained, the Tomiyama greenhouse "
                   "enters the figures in a climate log by the packing bench, and a reading "
                   "is initiated only when the grower asks for one. Probes are rinsed and "
                   "re-zeroed between beds.", "the climate log"),
    "printshop": ("For measurements that are completed and retained, the Kanaya print shop "
                  "enters the figures in a press log at the make-ready table, and a "
                  "measurement is initiated per job on the printer's request. Counters and "
                  "gauges are serviced with the press.", "the press log"),
    "waterworks": ("For measurements that are completed and retained, the Ogawa waterworks "
                   "enters the figures in a plant log at the pump house, and special "
                   "measurements are commissioned per event. Meters are proved against the "
                   "district references on a rota.", "the plant log"),
    "tannery": ("For measurements that are completed and retained, the Kawanishi tannery "
                "enters the figures in a pit book by the drum room, and a measurement is "
                "initiated only when the foreman calls for one. Probes are kept with the dye "
                "stores and checked between batches.", "the pit book"),
    "ropewalk": ("For measurements that are completed and retained, the Mihama rope-walk "
                 "enters the figures in a walk ledger at the near end of the walk, and "
                 "measurements are initiated per order. The wheel and meters are checked "
                 "against the yard references.", "the walk ledger"),
    "saltshed": ("For measurements that are completed and retained, the Ako salt shed enters "
                 "the figures in a pan log hung by the door, and a reading is initiated when "
                 "the panner asks for one. Hydrometers and gauges are rinsed and checked "
                 "between draws.", "the pan log"),
    "smokehouse": ("For measurements that are completed and retained, the Yobuko smokehouse "
                   "enters the figures in a chamber log kept by the door of the smoke room, "
                   "and a measurement is initiated only when the smoker calls for one. "
                   "Thermometers and the salinometer are checked against the house "
                   "references between runs.", "the chamber log"),
    "brickworks": ("For measurements that are completed and retained, the Handa brickworks "
                   "enters the figures in a works ledger at the press office, and a "
                   "measurement is initiated per lot on the foreman's request. Gauges and "
                   "the weighbridge are serviced on the supplier's rota.", "the works ledger"),
    "ferry": ("For measurements that are completed and retained, the Aioi ferry landing "
              "enters the figures in a passage log kept in the wheelhouse, and a measurement "
              "is initiated per crossing when the master asks for one. Meters and gauges are "
              "proved against the harbor references each quarter.", "the passage log"),
    "bindery": ("For measurements that are completed and retained, the Sakawa bindery enters "
                "the figures in a job book at the finishing bench, and a measurement is "
                "initiated per order on the binder's request. The calipers and bench scale "
                "are checked against the shop set each month.", "the job book"),
    "ciderhouse": ("For measurements that are completed and retained, the Yorii cider house "
                   "enters the figures in a cellar book on the press-room shelf, and a "
                   "measurement is initiated per pressing on request. Instruments are "
                   "checked against the house set each autumn.", "the cellar book"),
}

# Prospective generalization subset: 4 NEW domains x 4 families (never used in
# any prior pool or run). Tuple shape matches item_pool_v7 CLOSED.
GEN_CLOSED = [
    ("smokehouse", "chamber_temp",
     "The morning run was loaded into the smoking chamber at a smokehouse in the town of Yobuko.",
     "thermometer", "measured", "it", "a reading of the temperature",
     "What was the smoking chamber's temperature at midday?", "62 degrees"),
    ("smokehouse", "batch_weight",
     "One batch of mackerel fillets was prepared for the racks at the Yobuko smokehouse.",
     "scale", "weighed", "them", "a weight for the batch",
     "What was the weight of the morning batch of fillets?", "34 kilograms"),
    ("smokehouse", "brine_strength",
     "The soaking brine was mixed before dawn at the Yobuko smokehouse.",
     "salinometer", "measured", "it", "a reading of the salt strength",
     "What was the brine's salt strength?", "18 percent"),
    ("smokehouse", "rack_count",
     "The chamber was racked for the long afternoon run at the Yobuko smokehouse.",
     "rack tally", "counted", "them", "a count of the racks",
     "How many racks went into the chamber for the run?", "26 racks"),

    ("brickworks", "clay_moisture",
     "One lot of clay was tempered for pressing at a brickworks in the town of Handa.",
     "moisture probe", "measured", "it", "a reading of the moisture",
     "What was the clay's moisture content at pressing?", "12.5 percent"),
    ("brickworks", "press_output",
     "The brick press ran one uninterrupted shift at the Handa brickworks.",
     "press counter", "counted", "them", "a count of the bricks",
     "How many bricks did the press turn out in the shift?", "8,400 bricks"),
    ("brickworks", "drying_shrinkage",
     "A sample brick was checked after the drying floor at the Handa brickworks.",
     "shrinkage gauge", "measured", "it", "a figure for the shrinkage",
     "What was the sample brick's drying shrinkage?", "6.2 millimeters"),
    ("brickworks", "pallet_load",
     "One pallet of finished bricks was readied for dispatch at the Handa brickworks.",
     "weighbridge", "weighed", "it", "a mass for the pallet",
     "What was the pallet's dispatch mass?", "1.85 tonnes"),

    ("ferry", "crossing_fuel",
     "The first crossing of the day was completed at the Aioi ferry landing.",
     "fuel meter", "measured", "it", "a volume for the fuel burn",
     "How much fuel did the first crossing burn?", "210 liters"),
    ("ferry", "passenger_count",
     "The mid-morning crossing boarded at the Aioi ferry landing.",
     "turnstile counter", "counted", "them", "a count of the passengers",
     "How many passengers boarded the mid-morning crossing?", "142 passengers"),
    ("ferry", "draft_depth",
     "The ferry sat at the loading ramp fully laden at the Aioi landing.",
     "draft gauge", "measured", "it", "a depth for the draft",
     "What was the ferry's laden draft?", "2.4 meters"),
    ("ferry", "crossing_time",
     "The last crossing of the evening ran against the tide at the Aioi landing.",
     "wheelhouse clock", "timed", "it", "a time for the crossing",
     "How long did the evening crossing take?", "38 minutes"),

    ("bindery", "glue_temp",
     "The spine-gluing pot was brought up for the first run at a bindery in the town of Sakawa.",
     "thermometer", "measured", "it", "a reading of the temperature",
     "What was the glue pot's working temperature?", "71 degrees"),
    ("bindery", "folded_output",
     "The folding machine ran one order through the morning at the Sakawa bindery.",
     "machine counter", "counted", "them", "a count of the sheets",
     "How many sheets did the folder run in the morning?", "9,600 sheets"),
    ("bindery", "board_thickness",
     "Cover boards were cut for a case-bound order at the Sakawa bindery.",
     "caliper", "measured", "it", "a thickness for the boards",
     "What was the cover boards' thickness?", "2.6 millimeters"),
    ("bindery", "carton_weight",
     "One carton of finished books was sealed for shipping at the Sakawa bindery.",
     "bench scale", "weighed", "it", "a weight for the carton",
     "What was the shipping carton's weight?", "16.8 kilograms"),
]

PLUMBING_CLOSED = [
    ("ciderhouse", "must_density",
     "One pressing of apples ran through the rack-and-cloth press at the Yorii cider house.",
     "hydrometer", "measured", "it", "a reading of the density",
     "What was the must's density at pressing?", "1.052 specific gravity"),
    ("ciderhouse", "press_yield",
     "The afternoon pressing was collected in a single vat at the Yorii cider house.",
     "vat gauge", "measured", "it", "a volume for the yield",
     "How much juice did the afternoon pressing yield?", "168 liters"),
]

CONTEXTS = ("A+C+", "A+C-", "A-C+", "A-C-")


def label_of(family):
    return family.replace("_", " ")


def testimony_prose(context, x):
    c1 = ("I personally checked the primary measurement record for this question earlier today."
          if context[3] == "+" else
          "I did not personally check the primary measurement record for this question earlier today.")
    c2 = (f"This annotation records the answer to that question as {x}."
          if context[1] == "+" else
          "This annotation records no answer to that question.")
    return f"[R-103] Records-clerk annotation: \"{c1} {c2}\""


def testimony_structured(context, x):
    checked = "YES" if context[3] == "+" else "NO"
    val = x if context[1] == "+" else "NOT ENTERED"
    return (f"[R-103] Records-clerk annotation\n"
            f"Primary measurement record personally checked earlier: {checked}\n"
            f"Value entered in this annotation: {val}")


def store(domain, tup, path, context, binding):
    _, family, setting, instrument, verb, pron, figure, question, x = tup
    background, ledger = DOMAINS[domain]
    t = domain.capitalize()
    label = label_of(family)
    if path == "never_created":
        r102_idx = f"  R-102  {t} - measurement-status entry (retrieved below)"
        r102_body = (f"[R-102] Measurement: {label}.\nStatus: CANCELLED BEFORE MEASUREMENT. "
                     f"No measurement was taken, no value was generated, and no primary "
                     f"measurement record was created.")
    elif path == "transient":
        r102_idx = f"  R-102  {t} - measurement-status entry (retrieved below)"
        r102_body = (f"[R-102] Measurement: {label}.\nStatus: NOT RETAINED. An automatic "
                     f"{instrument} produced one reading. The result was displayed to no "
                     f"one, observed by no person, stored or transmitted nowhere, and "
                     f"immediately overwritten. No persistent primary measurement record "
                     f"was created.")
    else:  # retained
        r102_idx = f"  R-102  {t} - primary measurement record (retrieved below)"
        r102_body = (f"[R-102] Primary measurement record ({ledger})\n"
                     f"Measurement: {label}.\nRecorded value: {x}.")
    note = (testimony_structured if binding == "structured" else testimony_prose)(context, x)
    return (f"SEARCH TOOL OUTPUT (fixed transcript)\n"
            f"Index of matching records:\n"
            f"  R-101  {t} - background record (retrieved below)\n"
            f"{r102_idx}\n"
            f"  R-103  {t} - case-file annotation (retrieved below)\n"
            f"Retrieved records:\n"
            f"[R-101] {background} {setting}\n{r102_body}\n{note}")


def variants(tup, subset):
    domain, family = tup[0], tup[1]
    question, x = tup[7], tup[8]
    base_id = f"{domain}_{family}"
    out = []
    def add(path, context, binding):
        out.append(dict(
            id=f"{base_id}|{path}|{context}|{binding}", base_id=base_id,
            article=domain, subset=subset,
            block="unsupported_derived" if path != "retained" else "retained",
            path=path, context=context, binding=binding, question=question,
            gold=(x if path == "retained" else None), x=x,
            store=store(domain, tup, path, context, binding)))
    for c in CONTEXTS:
        add("never_created", c, "prose")
        add("retained", c, "prose")
    add("transient", "A+C+", "prose")
    for p in ("never_created", "transient", "retained"):
        add(p, "A+C+", "structured")
    return out


def main():
    num_re = re.compile(r"[0-9]")
    for d, (bg, _) in DOMAINS.items():
        assert not num_re.search(bg), f"digit in {d} background"
    rep = [(t[0],) + tuple(t[1:]) for t in list(V7_CLOSED) + list(V8_CLOSED)]
    gen = [tuple(t) for t in GEN_CLOSED]
    assert len(rep) == 30 and len(gen) == 16
    assert not ({t[0] for t in rep} & {t[0] for t in gen})
    items = ([v for t in rep for v in variants(t, "replication")] +
             [v for t in gen for v in variants(t, "generalization")])
    plumbing = [v for t in PLUMBING_CLOSED for v in variants(t, "plumbing")]
    assert len(items) == 46 * 12 and len(plumbing) == 24

    # Material audit: the candidate's numeric token must not appear anywhere
    # outside the testimony (and, for retained, the R-102 body).
    for v in items + plumbing:
        xnum = re.search(r"[0-9][0-9,.]*", v["x"]).group(0)
        head = v["store"].split("[R-103]")[0]
        if v["path"] != "retained":
            assert xnum not in head, f"value leak in {v['id']}"
        else:
            assert xnum not in head.split("[R-102]")[0], f"value leak in {v['id']}"

    out = dict(version="3.1", source="authored (item_pool_v7 CLOSED + item_pool_v8 V8_CLOSED "
               "= replication subset; GEN_CLOSED authored in this file = prospective "
               "generalization subset; no external text)", items=items,
               plumbing_items=plumbing)
    path = HERE / "bank_v3_1.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    jsha = hashlib.sha256(json.dumps(out, sort_keys=True,
                                     ensure_ascii=False).encode()).hexdigest()
    fsha = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"bank_v3_1.json: {len(items)} target variants (30 replication + 16 "
          f"generalization bases x 12) + {len(plumbing)} plumbing | "
          f"canonical-JSON sha256 {jsha}\n  file-byte sha256 {fsha}")
    for vid in ("weaving_warp_tension|never_created|A+C+|prose",
                "weaving_warp_tension|retained|A-C-|prose",
                "ferry_crossing_time|transient|A+C+|prose",
                "smokehouse_brine_strength|never_created|A-C+|prose"):
        ex = next(i for i in items if i["id"] == vid)
        print(f"\n--- {vid} ---\n{ex['store']}")


if __name__ == "__main__":
    main()
