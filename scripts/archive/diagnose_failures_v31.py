"""Evidence dump for the six v3.1 Recall@5 failures (plus q78). Read-only."""
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVAL = os.path.join(BASE, "data", "evaluation")
PROC = os.path.join(BASE, "data", "processed")
sys.stdout = open(os.path.join(EVAL, "v31_evidence_dump.txt"), "w", encoding="utf-8")

gold = {q["question_id"]: q for q in json.load(open(os.path.join(EVAL, "gold_questions_v2.json"), encoding="utf-8"))}
pages = {p["page"]: p for p in json.load(open(os.path.join(PROC, "biology_structured.json"), encoding="utf-8"))}
chunks = json.load(open(os.path.join(PROC, "biology_chunks.json"), encoding="utf-8"))
v31 = json.load(open(os.path.join(EVAL, "retrieval_v3_1_results.json"), encoding="utf-8"))
v3 = json.load(open(os.path.join(EVAL, "retrieval_v3_results.json"), encoding="utf-8"))


def show(qid, page_list, terms):
    q = gold[qid]
    print("\n" + "=" * 100)
    print(f"q{qid} | ch{q['chapter']} | {q['question_type']} | difficulty={q.get('difficulty')}")
    print("Q:", q["question_kh"])
    print("expected_pages:", q["expected_source_pages"])
    print("expected_concepts:", q.get("expected_concepts"))
    print("expected_answer:", repr(q.get("expected_answer")))
    print("notes:", repr(q.get("notes")))
    for tag, data in (("v3", v3), ("v3.1", v31)):
        for r in data["rows"].values():
            if r["question_id"] == qid:
                print(f"  [{tag}] part={r['part']} query={r['query_used']!r}")
                print(f"    real pages={r['real']['pages']}")
                print(f"    real scores={r['real']['scores']}")
                print(f"    hit1={r['real']['hit1']} hit3={r['real']['hit3']} hit5={r['real']['hit5']} mrr={r['real']['mrr']} abstained={r['abstained']}")
    print("\n  TERM OCCURRENCES:")
    for term in terms:
        hits = sorted(p for p, rec in pages.items() if term in rec.get("text", ""))
        print(f"    {term!r}: {hits}")
    print("\n  PAGE TEXT:")
    for p in page_list:
        rec = pages.get(p)
        if not rec:
            print(f"    p{p}: MISSING")
            continue
        txt = " ".join(rec.get("text", "").split())
        print(f"    --- p{p} | chapter={rec.get('chapter')} lesson={rec.get('lesson_id')} ---")
        print("    " + txt)
    print("\n  CHUNKS ON PAGES:")
    for c in chunks:
        if c["page"] in page_list:
            txt = " ".join(c["text"].split())
            print(f"    {c['chunk_id']} p{c['page']} range={c['page_start']}-{c['page_end']} lesson={c.get('lesson_id')} len={len(c['text'])}")
            print(f"      {txt[:600]}")


show(55, [8, 9, 10, 11, 15], ["លំអង", "ស្រល់", "កោន", "មីក្រូស្ព័រ"])
show(56, [11, 12, 13, 17, 18, 19, 20], ["អង្ករ", "សំរូប", "គ្រាប់", "ស្រូវ", "អាល់ប៊ុយមែន"])
show(68, [148, 149, 150, 151, 160], ["សេនេទិច", "ព័ត៌មានសេនេទិច", "តំណពូជ"])
show(84, [150, 151, 160, 164, 165, 166, 174], ["ADN", "ARN", "សំណួរ"])
show(86, [25, 26, 27, 28, 29, 30, 31, 40, 41, 57], ["ស្រូបទឹក", "ទឹក", "ឫស"])
show(115, [150, 151, 160, 164, 165, 166], ["ADN", "ARN"])
show(78, [150, 155, 160, 165, 174, 175], ["ហ្សែន", "សែន"])

print("\n" + "=" * 100)
print("q78 v3.1 full row:")
for r in v31["rows"].values():
    if r["question_id"] == 78:
        print(json.dumps(r, ensure_ascii=False, indent=2))

print("\nGold label change log:")
print(open(os.path.join(EVAL, "gold_label_changes_v3.json"), encoding="utf-8").read())
