"""Read-only experiment: test candidate query rewrites on the real pipeline.

Loads BGE-M3 + reranker once and prints top-12 pages/scores for each variant.
No corpus, config, or gold files are modified.
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "scripts"))

from app.config import TOP_K  # noqa: E402
from app.retrieval import (  # noqa: E402
    get_embedding_model, get_vector_db, get_reranker, retrieve, rerank_with_context,
)

OUT = os.path.join(BASE, "data", "evaluation", "query_variant_experiment.txt")
sys.stdout = open(OUT, "w", encoding="utf-8")

CASES = [
    ("q55", [9], [
        "ចូរពន្យល់ពីដំណើរការលំអងរបស់ស្រល់",
        "ចូរពន្យល់ពីដំណើរការលំអងរបស់ស្រល់ ស៊ីមណូស្ពែម កោន",
        "ដំណើរលំអងរបស់ស្រល់ ស៊ីមណូស្ពែម",
        "ចូរពន្យល់ពីដំណើរការលំអងរបស់ស្រល់ (gymnosperm)",
    ]),
    ("q56", [12, 18], [
        "តើអង្ករសំរូបដែលយើងបរិភោគជាផ្នែកណារបស់រុក្ខជាតិ?",
        "តើគ្រាប់ស្រូវដែលយើងបរិភោគជាផ្នែកណារបស់រុក្ខជាតិ?",
        "អង្ករសំរូប គ្រាប់ អាល់ប៊ុយមែន",
        "តើគ្រាប់រុក្ខជាតិមានផ្នែកអ្វីខ្លះ? អាល់ប៊ុយមែន",
    ]),
    ("q68", [149, 150, 160], [
        "ពន្យល់ពីរបៀបដែលព័ត៌មានសេនេទិចត្រូវបានបញ្ជូនពីមេទៅកូន",
        "ការបញ្ជូនព័ត៌មានសេនេទិចពីមេទៅកូន តំណពូជ ADN",
        "តើព័ត៌មានសេនេទិចត្រូវបានបញ្ជូនពីមេទៅកូនដោយរបៀបណា?",
    ]),
    ("q84", [150, 160, 164, 165], [
        "ចូរបង្កើតសំណួរសាកល្បង 3 អំពី ADN និង ARN",
        "ADN និង ARN",
        "ADN ARN មុខងារ រចនាសម្ព័ន្ធ",
        "សំណួរអំពី ADN និង ARN",
    ]),
    ("q86", [26], [
        "ចូរបង្កើតសំណួរសាកល្បង 3 អំពីការស្រូបទឹករបស់រុក្ខជាតិ",
        "ការស្រូបទឹករបស់រុក្ខជាតិ",
        "ការស្រូបទឹកពីដីរបស់រុក្ខជាតិ",
        "ឫស ស្រូបទឹក រុក្ខជាតិ",
    ]),
    ("q115p0", [150, 160], [
        "តើ ADN ជាអ្វី?",
        "ADN ជាអ្វី? និយមន័យ ADN",
        "តើ ADN ជាអ្វី? សម្ភារៈសេនេទិច",
    ]),
    ("q115p1", [164, 165], [
        "តើ ARN មានប៉ុន្មានប្រភេទ?",
        "ARN មានប៉ុន្មានប្រភេទ? ARNm ARNt ARNr",
    ]),
    ("q78", [150, 155, 160, 165, 174, 175], [
        "ក្នុងប្រឡង៖ តើអ្វីជានិយមន័យរបស់ហ្សែន (gene)?",
        "ក្នុងប្រឡង៖ តើអ្វីជានិយមន័យរបស់សែន (gene)?",
        "តើសែនជាអ្វី? និយមន័យសែន",
    ]),
]

print("Loading models ...", flush=True)
emb = get_embedding_model()
db = get_vector_db()
reranker = get_reranker()
print("Models ready.", flush=True)

only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
for name, expected, queries in CASES:
    if only and name not in only:
        continue
    print("\n" + "=" * 100, flush=True)
    print(f"{name} expected={expected}", flush=True)
    for q in queries:
        r = retrieve(q, emb, db, top_k=TOP_K)
        docs = r["documents"][0]
        metas = r["metadatas"][0]
        _docs, rmetas, rscores = rerank_with_context(q, docs, metas, reranker)
        pages = [m.get("page") for m in rmetas]
        hit = None
        for i, m in enumerate(rmetas, 1):
            lo = m.get("page_start", m.get("page"))
            hi = m.get("page_end", m.get("page"))
            if any(p in expected for p in range(lo, hi + 1)):
                hit = i
                break
        print(f"\n  QUERY: {q}", flush=True)
        print(f"  hit_rank={hit} top_score={rscores[0]:.4f}", flush=True)
        print(f"  pages={pages}", flush=True)
        print(f"  scores={[round(float(s), 4) for s in rscores]}", flush=True)
