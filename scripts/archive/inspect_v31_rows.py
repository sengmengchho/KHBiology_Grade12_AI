"""Inspect selected v3.1 rows and page text for failure analysis."""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVAL = os.path.join(BASE, "data", "evaluation")
PROC = os.path.join(BASE, "data", "processed")

gold = {q["question_id"]: q for q in json.load(open(os.path.join(EVAL, "gold_questions_v2.json"), encoding="utf-8"))}
pages = {p["page"]: p for p in json.load(open(os.path.join(PROC, "biology_structured.json"), encoding="utf-8"))}

for tag in ("v3", "v3_1"):
    data = json.load(open(os.path.join(EVAL, f"retrieval_{tag}_results.json"), encoding="utf-8"))
    print("\n=====", tag, "=====")
    for qid in (55, 56, 68, 84, 86, 115):
        rows = [r for r in data["rows"].values() if r.get("question_id") == qid]
        g = gold[qid]
        print(f"\n--- q{qid} | ch{g['chapter']} | {g['question_type']} | expect_abstain={g.get('expect_abstain')} ---")
        print("question:", g["question_kh"])
        print("expected_pages:", g.get("expected_source_pages"))
        print("expected_concepts:", g.get("expected_concepts"))
        for r in rows:
            real = r.get("real") or {}
            print(f" part={r.get('part')} query={r.get('query_used')!r}")
            print("  real pages:", real.get("pages"))
            print("  real scores:", real.get("scores"))
            print("  abstained:", r.get("abstained"), "top:", r.get("top_score"))
        print("page snippets:")
        for p in g.get("expected_source_pages", []):
            t = pages.get(p, {}).get("text", "")
            print(f"  EXPECT p{p}: {' '.join(t.split())[:180]}")
        for p in (rows[0].get("real") or {}).get("pages", [])[:5] if rows else []:
            t = pages.get(p, {}).get("text", "")
            print(f"  GOT p{p}: {' '.join(t.split())[:180]}")
