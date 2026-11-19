"""Retrieval smoke/regression checks for the known v3 problem cases.

Runs the real query path (normalize -> split -> expand -> BGE-M3 -> rerank)
through evaluation.evaluate_retrieval.evaluate_row. q111/q115 are reported as
known failures if they still miss; every other in-scope case must hit Recall@5,
and the out-of-scope case must abstain.

Usage: python -m scripts.archive.smoke_retrieval_v3
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, BASE)
sys.path.insert(0, SCRIPTS)

from app.retrieval import (  # noqa: E402
    get_embedding_model, get_reranker, get_vector_db,
)
from evaluation.common import load_gold, prepare_queries  # noqa: E402
from evaluation.evaluate_retrieval import evaluate_row  # noqa: E402

OUT = os.path.join(BASE, 'data', 'evaluation', 'archive', 'retrieval_smoke_v3.json')
KNOWN_FAIL_IDS = {111, 115}
CASE_IDS = [
    (23, 'ADN replication'),
    (24, 'ADN vs ARN'),
    (105, 'cancer treatment'),
    (109, 'stigma OCR'),
    (111, 'adaptation OCR'),
    (115, 'ADN/ARN multi-part'),
    (119, 'protein/peptide bond multi-part'),
    (999, 'out-of-scope abstention'),
]


def main():
    gold = {q['question_id']: q for q in load_gold()}
    out_of_scope = next(q for q in gold.values() if q.get('expect_abstain'))
    gold[999] = out_of_scope

    emb = get_embedding_model()
    db = get_vector_db()
    reranker = get_reranker()

    results = []
    unexpected = []
    for qid, label in CASE_IDS:
        q = gold[qid]
        parts = prepare_queries(q['question_kh'])
        for i, query in enumerate(parts):
            row = evaluate_row(q, i, query, emb, db, reranker)
            if q.get('expect_abstain'):
                status = 'PASS' if row['abstained'] else 'FAIL'
            elif qid in KNOWN_FAIL_IDS and not row['real']['hit5']:
                status = 'KNOWN_FAIL'
            else:
                status = 'PASS' if row['real']['hit5'] else 'FAIL'
            if status == 'FAIL':
                unexpected.append(f"q{qid}.{i}")
            results.append({
                'question_id': qid,
                'part': i,
                'label': label,
                'status': status,
                'query_used': query,
                'expected_pages': row['expected_pages'],
                'retrieved_pages': row['real']['pages'][:8],
                'top_score': row['top_score'],
                'abstained': row['abstained'],
                'hit1': row['real']['hit1'],
                'hit5': row['real']['hit5'],
                'mrr': row['real']['mrr'],
            })

    report = {
        'status': 'PASS' if not unexpected else 'FAIL',
        'unexpected_failures': unexpected,
        'rows': results,
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

    print('RETRIEVAL SMOKE v3:', report['status'])
    for r in results:
        print(f"  q{r['question_id']}.{r['part']} {r['label']:<34} "
              f"{r['status']:<10} hit5={r['hit5']} abstain={r['abstained']} "
              f"top={r['top_score']:.3f} pages={r['retrieved_pages']}")
    print(f'wrote {OUT}')
    return 0 if not unexpected else 1


if __name__ == '__main__':
    sys.exit(main())
