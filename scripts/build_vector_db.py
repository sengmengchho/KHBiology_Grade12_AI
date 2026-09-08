"""Phase 8 — Build the vector database from chunks.

Loads biology_chunks.json, embeds each chunk with the configured embedding
model (BAAI/bge-m3), and stores it in the Chroma collection "biology" with
chapter/lesson/page metadata. Rebuilds the collection from scratch by default
so reruns stay idempotent.

Usage:
    python scripts/build_vector_db.py [--chunks path] [--collection biology]
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import EMBEDDING_MODEL, PROCESSED_DIR, VECTOR_DB_DIR
from app.retrieval import get_embedding_model, get_vector_db

DEFAULT_CHUNKS = os.path.join(PROCESSED_DIR, "biology_chunks.json")


def main():
    parser = argparse.ArgumentParser(description="Build Chroma vector DB from chunks")
    parser.add_argument("--chunks", default=DEFAULT_CHUNKS)
    parser.add_argument("--collection", default="biology")
    args = parser.parse_args()

    if not os.path.exists(args.chunks):
        sys.exit(f"Chunks not found: {args.chunks}")

    with open(args.chunks, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    if not chunks:
        sys.exit("No chunks to embed.")

    print(f"Loading embedding model: {EMBEDDING_MODEL} ...")
    model = get_embedding_model()
    db = get_vector_db()

    try:
        db.delete_collection(name=args.collection)
    except Exception:
        pass  # collection may not exist yet on first run
    collection = db.get_or_create_collection(
        name=args.collection,
        metadata={"hnsw:space": "cosine"},
    )

    texts = [c["text"] for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    metadatas = [{
        "chunk_id": c["chunk_id"],
        "page": int(c["page"]) if c["page"] is not None else 0,
        "chapter_id": int(c["chapter_id"]) if c["chapter_id"] is not None else 0,
        "chapter_title": c["chapter_title"] or "",
        "lesson_id": int(c["lesson_id"]) if c["lesson_id"] is not None else 0,
        "lesson_title": c["lesson_title"] or "",
    } for c in chunks]

    print(f"Embedding {len(texts)} chunks ...")
    embeddings = model.encode(texts, batch_size=16, show_progress_bar=True).tolist()

    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    print(f"Stored {collection.count()} chunks in collection '{args.collection}'")
    print(f"Vector DB: {VECTOR_DB_DIR}")


if __name__ == "__main__":
    main()