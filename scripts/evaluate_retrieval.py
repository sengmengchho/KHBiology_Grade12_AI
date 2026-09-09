"""Evaluate retrieval quality on the evaluation dataset.

Measures Recall@1, Recall@3, Recall@5, and MRR for:
  1. BGE-M3 embedding search only (no rerank)
  2. BGE-M3 + BGE-reranker-v2-m3

A retrieved chunk is a "hit" if its page is in the question's expected_source_pages.

The run is resumable: it first computes embedding-search results for all questions
(phase 1), then scores reranking (phase 2), so partial progress is kept.

Usage:
    python scripts/evaluate_retrieval.py
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import RERANKER_TOP_K
from app.retrieval import get_embedding_model, get_vector_db, get_reranker, retrieve, rerank

TMP = os.path.join('data', 'evaluation', '_retrieval_tmp.json')


def load_questions():
    with open('data/evaluation/evaluation_questions.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def phase1_retrieve():
    questions = load_questions()
    if os.path.exists(TMP):
        with open(TMP, 'r', encoding='utf-8') as f:
            prev = json.load(f)
    else:
        prev = {}
    done_ids = {int(k) for k in prev.keys()}

    print('Loading embedding + vector DB ...', flush=True)
    emb_model = get_embedding_model()
    vector_db = get_vector_db()

    todo = [q for q in questions if q['question_id'] not in done_ids]
    print(f'Phase 1: retrieving {len(todo)} pending questions ...', flush=True)
    for i, q in enumerate(todo, 1):
        r = retrieve(q['question_kh'], emb_model, vector_db)
        documents = r['documents'][0]
        metadatas = r['metadatas'][0]
        prev[str(q['question_id'])] = {
            'question_id': q['question_id'],
            'chapter': q['chapter'],
            'question': q['question_kh'],
            'expected_pages': q.get('expected_source_pages', []),
            'documents': documents,
            'pages': [m.get('page') for m in metadatas],
            'page_ranges': [[m.get('page_start', m.get('page')), m.get('page_end', m.get('page'))] for m in metadatas],
        }
        with open(TMP, 'w', encoding='utf-8') as f:
            json.dump(prev, f, ensure_ascii=False)
        if i % 10 == 0 or i == len(todo):
            print(f'  retrieved {i}/{len(todo)}', flush=True)
    return prev


def phase2_rerank(records):
    qs = load_questions()
    if os.path.exists(os.path.join('data', 'evaluation', 'retrieval_results.json')):
        with open('data/evaluation/retrieval_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
    else:
        results = {}
    done_ids = {int(r['question_id']) for r in results.values()}

    print('Loading reranker ...', flush=True)
    reranker = get_reranker()

    pending = [q for qid, q in records.items() if int(qid) not in done_ids]
    print(f'Phase 2: reranking {len(pending)} questions ...', flush=True)
    for q in pending:
        documents = q['documents']
        pages = q['pages']
        ranges = q['page_ranges']
        expected = q['expected_pages']
        reranked_docs = rerank(q['question'], documents, reranker)
        reranked_pages = []
        reranked_ranges = []
        used = set()
        for doc in reranked_docs:
            for i, d in enumerate(documents):
                if d == doc and i not in used:
                    reranked_pages.append(pages[i])
                    reranked_ranges.append(ranges[i])
                    used.add(i)
                    break

        def hits(pranges, k):
            """True if any page in the first k chunk ranges hits an expected page."""
            return any(
                any(p in expected for p in range(lo or 0, (hi or lo) + 1))
                for lo, hi in pranges[:k]
            )

        def hit5(pg):
            return hits(pg, 5)
        def hit3(pg):
            return hits(pg, 3)
        def hit1(pg):
            return hits(pg, 1)
        def mrr(pg):
            for i, pr in enumerate(pg, 1):
                if any(p in expected for p in range(pr[0] or 0, (pr[1] or pr[0]) + 1)):
                    return 1.0 / i
            return 0.0

        results[str(q['question_id'])] = {
            'question_id': q['question_id'],
            'chapter': q['chapter'],
            'no_rerank': {
                'top5_pages': pages[:RERANKER_TOP_K],
                'hit1': hit1(ranges),
                'hit3': hit3(ranges),
                'hit5': hit5(ranges),
                'mrr': mrr(ranges[:RERANKER_TOP_K]),
            },
            'rerank': {
                'top5_pages': reranked_pages,
                'hit1': hit1(reranked_ranges),
                'hit3': hit3(reranked_ranges),
                'hit5': hit5(reranked_ranges),
                'mrr': mrr(reranked_ranges),
            },
        }
        with open('data/evaluation/retrieval_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        if len(results) % 10 == 0:
            print(f'  reranked {len(results)} total', flush=True)
    return results


def summarize():
    with open('data/evaluation/retrieval_results.json', 'r', encoding='utf-8') as f:
        results = json.load(f)
    n = len(results)
    key = lambda r: r['rerank' if 'rerank' in r else 'no_rerank']
    agg = {'no_rerank': {'hit1': 0, 'hit3': 0, 'hit5': 0, 'mrr': 0.0},
           'rerank': {'hit1': 0, 'hit3': 0, 'hit5': 0, 'mrr': 0.0}}
    for r in results.values():
        for label in ['no_rerank', 'rerank']:
            d = r[label]
            agg[label]['hit1'] += d['hit1']
            agg[label]['hit3'] += d['hit3']
            agg[label]['hit5'] += d['hit5']
            agg[label]['mrr'] += d['mrr']
    print('\n' + '=' * 60)
    print(f'RETRIEVAL EVALUATION (n={n})')
    print('=' * 60)
    print(f'{"Metric":<12}{"NoRerank":>10}{"WithRerank":>12}{"Delta":>10}')
    order = [('Recall@1', 'hit1'), ('Recall@3', 'hit3'), ('Recall@5', 'hit5'), ('MRR', 'mrr')]
    for label, field in order:
        nv = agg['no_rerank'][field] / n
        rv = agg['rerank'][field] / n
        print(f'{label:<12}{nv:>10.3f}{rv:>12.3f}{rv-nv:>+10.3f}')
    # Save summary
    with open('data/evaluation/retrieval_summary.txt', 'w', encoding='utf-8') as f:
        f.write(f'RETRIEVAL EVALUATION (n={n})\n')
        f.write('Metric      NoRerank  WithRerank  Delta\n')
        for label, field in order:
            nv = agg['no_rerank'][field] / n
            rv = agg['rerank'][field] / n
            f.write(f'{label:<12}{nv:>10.3f}{rv:>12.3f}{rv-nv:>+10.3f}\n')
    print('\nSummary -> data/evaluation/retrieval_summary.txt')


if __name__ == '__main__':
    records = phase1_retrieve()
    results = phase2_rerank(records)
    summarize()
