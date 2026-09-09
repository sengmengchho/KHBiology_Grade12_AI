"""Non-interactive smoke test of every mode/feature through the real app path.

Uses the exact same code path as app/main.py (retrieve -> rerank_with_scores
-> abstain check -> generate_answer -> format_answer). Prints short excerpts
so behavior can be verified without opening the browser.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import RETRIEVAL_SCORE_THRESHOLD, NOT_FOUND_MESSAGE
from app.retrieval import get_embedding_model, get_vector_db, get_reranker, retrieve, rerank_with_scores
from app.rag import generate_answer
from app.prompt import format_answer

Q = 'តើ DNA មានតួនាទី និងរចនាសម្ព័ន្ធដូចម្តេច?'
OFF = 'ប្រាប់ខ្ញុំពីរឿងកុនថ្មីៗ'

CASES = [
    ('normal+explain', Q, 'normal', 'explain'),
    ('easy+explain', Q, 'easy', 'explain'),
    ('exam+explain', Q, 'exam', 'explain'),
    ('normal+quiz', Q, 'normal', 'quiz'),
    ('normal+summary', Q, 'normal', 'summary'),
]


def clip(t, n=200):
    t = t.replace('\n', ' ')
    return t[:n] + ('…' if len(t) > n else '')


def main():
    emb = get_embedding_model()
    db = get_vector_db()
    rk = get_reranker()

    print('Loading models OK', flush=True)

    emb_q = emb
    for name, q, mode, feature in CASES:
        print(f'\n=== {name} ===', flush=True)
        r = retrieve(q, emb_q, db)
        docs = r['documents'][0]
        metas = r['metadatas'][0]
        if not docs:
            print('  ABSTAIN (no docs)', flush=True)
            continue
        rd, rs, sc = rerank_with_scores(q, docs, metas, rk)
        top = sc[0]
        print(f'  top rerank score: {top:.3f} (threshold {RETRIEVAL_SCORE_THRESHOLD})', flush=True)
        if not rd or top < RETRIEVAL_SCORE_THRESHOLD:
            print(f'  ABSTAIN: {clip(NOT_FOUND_MESSAGE, 120)}', flush=True)
            continue
        answer = generate_answer(q, '\n\n'.join(rd), mode, feature)
        final = format_answer(answer, rs)
        print(f'  ANSWER  : {clip(answer.splitlines()[0])}', flush=True)
        print(f'  SOURCES : {len(rs)}', flush=True)
        print(f'  length  : {len(answer)} chars', flush=True)

    print(f'\n=== out-of-scope (should ABSTAIN) ===', flush=True)
    r = retrieve(OFF, emb_q, db)
    docs = r['documents'][0]
    metas = r['metadatas'][0]
    rd, rs, sc = rerank_with_scores(OFF, docs, metas, rk)
    top = sc[0]
    print(f'  top rerank score: {top:.3f} (threshold {RETRIEVAL_SCORE_THRESHOLD})', flush=True)
    if not rd or top < RETRIEVAL_SCORE_THRESHOLD:
        print(f'  ABSTAIN  : {clip(NOT_FOUND_MESSAGE, 120)}', flush=True)
    else:
        print('  !!! WOULD ANSWER (unexpected)', flush=True)


if __name__ == '__main__':
    main()