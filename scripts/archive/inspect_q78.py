"""Inspect q78 and nearby gene-definition pages."""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVAL = os.path.join(BASE, "data", "evaluation")
PROC = os.path.join(BASE, "data", "processed")
gold = {q["question_id"]: q for q in json.load(open(os.path.join(EVAL, "gold_questions_v2.json"), encoding="utf-8"))}
pages = {p["page"]: p for p in json.load(open(os.path.join(PROC, "biology_structured.json"), encoding="utf-8"))}
chunks = json.load(open(os.path.join(PROC, "biology_chunks.json"), encoding="utf-8"))
data = json.load(open(os.path.join(EVAL, "retrieval_v3_1_results.json"), encoding="utf-8"))
q = gold[78]
print("q78:", q["question_kh"])
print("gold pages:", q["expected_source_pages"])
print("concepts:", q["expected_concepts"])
print("answer:", q["expected_answer"])
for r in data["rows"].values():
    if r["question_id"] == 78:
        print("row:", json.dumps(r, ensure_ascii=False, indent=2))
for p in (172, 173, 174, 175):
    print(f"\n--- p{p} ---")
    print(pages[p]["text"][:1600])
print("\nchunks with សែន/ហ្សែន on p172-175:")
for c in chunks:
    if c["page"] in (172, 173, 174, 175) and ("សែន" in c["text"] or "ហ្សែន" in c["text"]):
        print(c["chunk_id"], c["page"], c["page_start"], c["page_end"], c["lesson_id"], c["text"][:500])
