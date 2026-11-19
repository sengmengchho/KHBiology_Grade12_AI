"""Audit current v3.1 evaluation state without modifying anything."""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVAL = os.path.join(BASE, "data", "evaluation")

gold = json.load(open(os.path.join(EVAL, "gold_questions_v2.json"), encoding="utf-8"))
print("gold questions:", len(gold))
print("gold ids unique:", len({q["question_id"] for q in gold}))
print("gold expect_abstain:", sum(1 for q in gold if q.get("expect_abstain")))

for tag in ("v3", "v3_1"):
    path = os.path.join(EVAL, f"retrieval_{tag}_results.json")
    if not os.path.exists(path):
        print(tag, "MISSING", path)
        continue
    data = json.load(open(path, encoding="utf-8"))
    rows = data.get("rows", {})
    vals = list(rows.values()) if isinstance(rows, dict) else rows
    print("\n", tag, "file rows:", len(vals), "meta:", data.get("meta"))
    print("  in-scope rows:", sum(1 for r in vals if not r.get("expect_abstain")))
    print("  out-of-scope rows:", sum(1 for r in vals if r.get("expect_abstain")))
    ids = [r.get("question_id") for r in vals]
    print("  unique question_ids:", len(set(ids)))
    print("  duplicate question_ids:", sorted({x for x in ids if ids.count(x) > 1}))
    print("  keys sample:", list(rows.keys())[:8] if isinstance(rows, dict) else "list")
    print("  row sample keys:", sorted(vals[0].keys()) if vals else None)
    print("  first/last ids:", ids[:5], ids[-5:])
