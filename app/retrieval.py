from app.config import EMBEDDING_MODEL, TOP_K, RERANKER_TOP_K, VECTOR_DB_DIR
import chromadb
from FlagEmbedding import FlagReranker


def get_embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL)


def get_vector_db():
    return chromadb.PersistentClient(path=str(VECTOR_DB_DIR))


def get_reranker():
    return FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=True)


def retrieve(query: str, embedding_model, vector_db, collection_name="biology", top_k=TOP_K):
    collection = vector_db.get_or_create_collection(name=collection_name)
    query_embedding = embedding_model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)
    return results


def rerank(query: str, documents: list[str], reranker, top_k=RERANKER_TOP_K):
    pairs = [[query, doc] for doc in documents]
    scores = reranker.compute_score(pairs, normalize=True)
    if isinstance(scores, float):
        scores = [scores]
    ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
    return [doc for doc, score in ranked[:top_k]]


def rerank_with_scores(query: str, documents: list[str], metadatas: list[dict], reranker, top_k=RERANKER_TOP_K):
    """Rerank and return (docs, metadatas, scores) aligned and sorted desc."""
    pairs = [[query, doc] for doc in documents]
    scores = reranker.compute_score(pairs, normalize=True)
    if isinstance(scores, float):
        scores = [scores]
    indexed = sorted(zip(documents, metadatas, scores), key=lambda x: x[2], reverse=True)
    ranked_docs = [d for d, m, s in indexed[:top_k]]
    ranked_metas = [m for d, m, s in indexed[:top_k]]
    ranked_scores = [s for d, m, s in indexed[:top_k]]
    return ranked_docs, ranked_metas, ranked_scores


def rerank_with_context(query, documents, metadatas, reranker, top_k=RERANKER_TOP_K,
                        max_total=12, max_per_page=4):
    """Rerank candidates, then pull in neighbor chunks from already-selected
    pages. Multi-part sections are split across several chunks of the same page
    (e.g. ឫស/ដើម/ស្លឹក of the vegetative organs section); the reranker ranks
    only the single best-matching chunk high, so without this the LLM would
    miss the rest of the section. Neighbors come from the same pages that were
    already selected (in score order), bounded by per-page and total caps.
    Returns (docs, metadatas, scores) aligned and sorted desc by score.
    """
    pairs = [[query, doc] for doc in documents]
    scores = reranker.compute_score(pairs, normalize=True)
    if isinstance(scores, float):
        scores = [scores]
    indexed = sorted(zip(documents, metadatas, scores), key=lambda x: x[2], reverse=True)

    def page_of(m):
        if isinstance(m, dict):
            return m.get("page", m.get("page_start"))
        return None

    selected = indexed[:top_k]

    page_counts = {}
    for _d, m, _s in selected:
        p = page_of(m)
        if p is not None:
            page_counts[p] = page_counts.get(p, 0) + 1

    for item in indexed[top_k:]:
        if len(selected) >= max_total:
            break
        p = page_of(item[1])
        if p is not None and p in page_counts and page_counts[p] < max_per_page:
            page_counts[p] += 1
            selected.append(item)

    return (
        [d for d, m, s in selected],
        [m for d, m, s in selected],
        [s for d, m, s in selected],
    )
