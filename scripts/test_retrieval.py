"""Phase 9 — Test retrieval with sample Khmer Biology questions.

Runs a small set of evaluation questions through embed -> retrieve -> rerank,
writes top results for each question to a UTF-8 report file (the console can
not render Khmer on Windows), and prints summaries that avoid Khmer output.

Usage:
    python scripts/test_retrieval.py [--out report.txt] [--n 5]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.retrieval import get_embedding_model, get_vector_db, get_reranker, retrieve, rerank

SAMPLE_QUESTIONS = [
    "តើ DNA មានតួនាទីអ្វី?",
    "ស៊ីមណូស្ពែមមានលក្ខណៈអ្វីខ្លះ?",
    "តើអង់ស្យូស្ពែមជាអ្វី?",
    "ពន្យល់ពីវដ្តជីវិតរបស់ស្រល់",
    "ប្រដ៍ជាអ្វី?",
]


def main():
    parser = argparse.ArgumentParser(description="Test retrieval quality")
    parser.add_argument("--out", default="_retrieval_report.txt")
    parser.add_argument("--n", type=int, default=5)
    args = parser.parse_args()

    print("Loading models ...")
    embedding_model = get_embedding_model()
    vector_db = get_vector_db()
    reranker = get_reranker()

    lines = []
    for q in SAMPLE_QUESTIONS:
        lines.append(f"QUESTION: {q}")
        results = retrieve(q, embedding_model, vector_db, top_k=20)
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results else []

        reranked = rerank(q, documents, reranker, top_k=args.n)
        lines.append(f"  reranked top {args.n} (of {len(documents)}):")
        # Map reranked docs back to their metadata by doc text.
        text_to_meta = {d: m for d, m in zip(documents, metadatas)}
        for rank, doc in enumerate(reranked, start=1):
            m = text_to_meta.get(doc, {})
            lines.append(
                f"    #{rank} page={m.get('page')} ch={m.get('chapter_id')} "
                f"lesson={m.get('lesson_id')} text={doc[:80]!r}"
            )
        lines.append("")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote retrieval report to {args.out}")
    for i in range(len(SAMPLE_QUESTIONS)):
        print(f"  tested question {i+1}")


if __name__ == "__main__":
    main()