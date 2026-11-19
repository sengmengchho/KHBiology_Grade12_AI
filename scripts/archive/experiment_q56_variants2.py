"""Follow-up q56 variants: does keeping the question frame cross 0.08?

Run: python scripts/experiment_q56_variants2.py
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE)

from app.config import TOP_K  # noqa: E402
from app.retrieval import (  # noqa: E402
    get_embedding_model, get_vector_db, get_reranker, retrieve, rerank_with_context,
)

OUT = os.path.join(BASE, "data", "evaluation", "q56_variant_experiment2.txt")
sys.stdout = open(OUT, "w", encoding="utf-8")

EXPECTED = [12, 18]
QUERIES = [
    "តើអង្ករសំរូបដែលយើងបរិភោគជាផ្នែកណារបស់រុក្ខជាតិ? គ្រាប់ស្រូវ អាល់ប៊ុយមែន អង់ដូស្ពែម",
    "តើអង្ករសំរូបជាផ្នែកណារបស់រុក្ខជាតិ? គ្រាប់ស្រូវ អាល់ប៊ុយមែន អង់ដូស្ពែម",
    "អង្ករសំរូប គ្រាប់ស្រូវ អាល់ប៊ុយមែន",
    "តើអង្ករសំរូបជាគ្រាប់ឬអាល់ប៊ុយមែន?",
]

print("Loading models ...", flush=True)
emb = get_embedding_model()
db = get_vector_db()
reranker = get_reranker()
print("Models ready.", flush=True)

for q in QUERIES:
    r = retrieve(q, emb, db, top_k=TOP_K)
    docs = r["documents"][0]
    metas = r["metadatas"][0]
    _docs, rmetas, rscores = rerank_with_context(q, docs, metas, reranker)
    rows = []
    hit = None
    for i, (m, s) in enumerate(zip(rmetas, rscores), 1):
        lo = m.get("page_start", m.get("page"))
        hi = m.get("page_end", m.get("page"))
        pages = list(range(lo, hi + 1)) if lo is not None else []
        is_hit = any(p in EXPECTED for p in pages)
        if is_hit and hit is None:
            hit = i
        rows.append((i, m.get("page"), lo, hi, round(float(s), 4), is_hit))
    print("\n" + "=" * 100, flush=True)
    print(f"QUERY: {q}", flush=True)
    print(f"hit_rank={hit} top_score={round(float(rscores[0]), 4)}", flush=True)
    for i, page, lo, hi, s, is_hit in rows:
        mark = " <== GOLD" if is_hit else ""
        print(f"  {i:>2}. page={page} range={lo}-{hi} score={s}{mark}", flush=True)
