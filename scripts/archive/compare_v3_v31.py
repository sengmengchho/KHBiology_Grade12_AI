"""Compare v3 and v3.1 retrieval results using the same row definitions."""
import json
import os
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVAL = os.path.join(BASE, "data", "evaluation")


def load(tag):
    return json.load(open(os.path.join(EVAL, f"retrieval_{tag}_results.json"), encoding="utf-8"))


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def agg(rows):
    ins = [r for r in rows if not r["expect_abstain"]]
    oos = [r for r in rows if r["expect_abstain"]]
    out = {}
    for key in ("embed", "rerank", "real"):
        out[key] = {
            "r1": mean([r[key]["hit1"] for r in ins]),
            "r3": mean([r[key]["hit3"] for r in ins]),
            "r5": mean([r[key]["hit5"] for r in ins]),
            "mrr": mean([r[key]["mrr"] for r in ins]),
        }
    # strict / any per question
    byq = defaultdict(list)
    for r in ins:
        byq[r["question_id"]].append(r)
    strict = mean([all(p["real"]["hit5"] for p in ps) for ps in byq.values()])
    anyp = mean([any(p["real"]["hit5"] for p in ps) for ps in byq.values()])
    out["strict"] = strict
    out["any"] = anyp
    out["false_abstain"] = sum(1 for r in ins if r["abstained"])
    out["n_in"] = len(ins)
    out["oos_ok"] = sum(1 for r in oos if r["abstained"])
    out["n_oos"] = len(oos)
    return out


def group(rows, key):
    d = defaultdict(list)
    for r in rows:
        if not r["expect_abstain"]:
            d[r[key]].append(r)
    out = {}
    for k, rs in d.items():
        out[k] = {
            "n": len(rs),
            "r5": mean([r["real"]["hit5"] for r in rs]),
            "mrr": mean([r["real"]["mrr"] for r in rs]),
            "fa": mean([r["abstained"] for r in rs]),
        }
    return dict(sorted(out.items(), key=lambda kv: str(kv[0])))


v3 = load("v3")
v31 = load("v3_1")
for name, d in (("v3", v3), ("v3.1", v31)):
    print(name, d["meta"])
    print(" rows", len(d["rows"]), "agg", agg(list(d["rows"].values())))

a, b = agg(list(v3["rows"].values())), agg(list(v31["rows"].values()))
print("\nCOMPARISON")
print("metric,v3,v3.1,diff")
for label, key in (("Recall@1", "r1"), ("Recall@3", "r3"), ("Recall@5", "r5"), ("MRR", "mrr")):
    print(f"{label},{a['real'][key]:.4f},{b['real'][key]:.4f},{b['real'][key]-a['real'][key]:+.4f}")
print(f"False abstain,{a['false_abstain']}/{a['n_in']},{b['false_abstain']}/{b['n_in']},0")
print(f"OOS abstention,{a['oos_ok']}/{a['n_oos']},{b['oos_ok']}/{b['n_oos']},0")
print(f"Strict hit@5,{a['strict']:.4f},{b['strict']:.4f},{b['strict']-a['strict']:+.4f}")
print(f"Any-part hit@5,{a['any']:.4f},{b['any']:.4f},{b['any']-a['any']:+.4f}")

print("\nBY CHAPTER")
for ch in sorted(set(group(list(v3["rows"].values()), "chapter")) | set(group(list(v31["rows"].values()), "chapter"))):
    x = group(list(v3["rows"].values()), "chapter").get(ch, {})
    y = group(list(v31["rows"].values()), "chapter").get(ch, {})
    print(ch, x, y)

print("\nBY TYPE")
for t in sorted(set(group(list(v3["rows"].values()), "question_type")) | set(group(list(v31["rows"].values()), "question_type"))):
    x = group(list(v3["rows"].values()), "question_type").get(t, {})
    y = group(list(v31["rows"].values()), "question_type").get(t, {})
    print(t, x, y)

# row-level changes
v3r = {k: r for k, r in v3["rows"].items()}
v31r = {k: r for k, r in v31["rows"].items()}
print("\nROW CHANGES (real hit5)")
for k in sorted(set(v3r) & set(v31r), key=lambda s: tuple(map(int, s.split(":")))):
    if v3r[k]["real"]["hit5"] != v31r[k]["real"]["hit5"]:
        print(k, "v3", v3r[k]["real"]["hit5"], "v3.1", v31r[k]["real"]["hit5"],
              "exp", v3r[k]["expected_pages"], "v3pages", v3r[k]["real"]["pages"][:5],
              "v31pages", v31r[k]["real"]["pages"][:5])
