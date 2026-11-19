"""End-to-end test for comparison-format and quiz-format enforcement.

Reuses the real app pipeline (retrieve -> rerank -> generate -> format).
Checks:
  1. comparison question answer contains BOTH លក្ខណៈដូចគ្នា and លក្ខណៈខុសគ្នា
  2. quiz answer uses **សំណួរទី X:** / **ចម្លើយ:** and has no <details>
  3. quiz answer parses into >=1 expander (via the same logic as main.py)
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.config import RETRIEVAL_SCORE_THRESHOLD
from app.retrieval import get_embedding_model, get_vector_db, get_reranker, retrieve, rerank_with_scores
from app.rag import generate_answer
from app.prompt import format_answer

COMPARE_Q = "ចូរប្រៀបធៀប ADN និង ARNm"
QUIZ_Q = "សូមសាកល្បងខ្ញុំអំពីប្រព័ន្ធបញ្ជូនសរសៃប្រសាទ"

def clip(t, n=160):
    t = (t or "").replace("\n", " ")
    return t[:n] + ("…" if len(t) > n else "")


def run(q, mode, feature):
    emb = get_embedding_model()
    db = get_vector_db()
    rk = get_reranker()
    r = retrieve(q, emb, db)
    docs = r["documents"][0]
    metas = r["metadatas"][0]
    rd, rs, sc = rerank_with_scores(q, docs, metas, rk)
    if not rd or sc[0] < RETRIEVAL_SCORE_THRESHOLD:
        return None, sc[0]
    answer = generate_answer(q, "\n\n".join(rd), mode, feature)
    return format_answer(answer, rs), sc[0]


def check_comparison():
    ok = True
    out, score = run(COMPARE_Q, "normal", "explain")
    print(f"=== COMPARISON ({COMPARE_Q}) top-score={score:.3f} ===")
    if out is None:
        print("[FAIL] abstained (below threshold)")
        return False
    body = out
    has_same = "លក្ខណៈដូចគ្នា" in body
    has_diff = "លក្ខណៈខុសគ្នា" in body
    print(f"  has លក្ខណៈដូចគ្នា : {has_same}")
    print(f"  has លក្ខណៈខុសគ្នា : {has_diff}")
    print("  answer :", clip(body))
    if has_same and has_diff:
        print("[PASS]")
    else:
        print("[FAIL] missing one or both sections")
        ok = False
    return ok


def check_quiz():
    ok = True
    out, score = run(QUIZ_Q, "normal", "quiz")
    print(f"=== QUIZ ({QUIZ_Q}) top-score={score:.3f} ===")
    if out is None:
        print("[FAIL] abstained (below threshold)")
        return False
    body = out
    qnums = re.findall(r"\*\*សំណួរទី\s*(\d+)\s*:", body)
    has_details = "<details" in body.lower()
    has_answer = re.search(r"\*\*ចម្លើយ:\*\*", body) is not None
    print(f"  questions found : {qnums}")
    print(f"  has ចម្លើយ      : {has_answer}")
    print(f"  has <details>  : {has_details}")
    print("  answer :", clip(body))
    if len(qnums) >= 1 and has_answer and not has_details:
        print("[PASS]")
    else:
        print("[FAIL] quiz format broken")
        ok = False
    return ok


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    ok_all = True
    if only in (None, "compare"):
        ok_all &= check_comparison()
        print()
    if only in (None, "quiz"):
        ok_all &= check_quiz()
        print()
    print("ALL PASS" if ok_all else "SOME FAILED")
    sys.exit(0 if ok_all else 1)