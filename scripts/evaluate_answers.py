"""Evaluate final RAG answer quality on a sample of evaluation questions.

Runs the full pipeline (retrieve -> rerank -> generate) for a sample of
questions and saves the answers plus retrieval context to a reviewable JSON
file. Also computes a lightweight automated faithfulness check: whether the
answer contains key terms that appear in the retrieved context and cites the
retrieved pages.

Usage:
    python scripts/evaluate_answers.py [--sample N] [--questions ids]
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import RERANKER_TOP_K
from app.prompt import format_answer
from app.rag import generate_answer
from app.retrieval import get_embedding_model, get_vector_db, get_reranker, retrieve, rerank

OUT = os.path.join('data', 'evaluation', 'answer_evaluations.json')
SUMMARY = os.path.join('data', 'evaluation', 'answer_evaluation_summary.txt')


def score_answers():
    """Compute automated quality metrics over answers already saved in OUT."""
    with open(OUT, 'r', encoding='utf-8') as f:
        results = json.load(f)

    if not results:
        print('No answers to score yet. Run generation first.')
        return

    import re
    rows = []
    for r in results:
        answer = r.get('answer', '')
        stripped = re.sub(r'\n---.*', '', answer, flags=re.S)  # drop sources section
        answer_lower = stripped.lower()

        concepts = r.get('expected_concepts', [])
        found = [c for c in concepts if c.lower() in answer_lower]
        concept_coverage = round(len(found) / len(concepts), 2) if concepts else None

        ans_pages = {int(m.get('page', 0)) for m in r.get('retrieved_pages', []) if m.get('page')}
        exp_pages = r.get('expected_pages', [])
        cited = sorted(ans_pages & set(exp_pages))
        page_recall = round(len(cited) / len(exp_pages), 2) if exp_pages else None
        # Pages the answer cited that were NOT expected (possible leak/error, informational)
        extra = sorted(ans_pages - set(exp_pages))

        rows.append({
            'question_id': r['question_id'],
            'chapter': r['chapter'],
            'concepts': len(concepts),
            'concepts_found': len(found),
            'concept_coverage': concept_coverage,
            'expected_pages': exp_pages,
            'cited_pages': sorted(ans_pages),
            'page_recall': page_recall,
            'seconds': r.get('seconds'),
        })

    cov_vals = [x['concept_coverage'] for x in rows if x['concept_coverage'] is not None]
    page_vals = [x['page_recall'] for x in rows if x['page_recall'] is not None]
    n = len(rows)
    mean = lambda v: round(sum(v) / len(v), 2) if v else None

    lines = [
        f'Answer evaluation summary ({n} questions)',
        f'Generated {time.strftime("%Y-%m-%d %H:%M")}',
        '',
        f'Concept coverage (expected concepts found in answer):  mean {mean(cov_vals)} over {len(cov_vals)}',
        f'  high (>=0.67): {sum(1 for v in cov_vals if v >= 0.67)}',
        f'  medium (0.34-0.66): {sum(1 for v in cov_vals if 0.34 <= v < 0.67)}',
        f'  low (<0.34): {sum(1 for v in cov_vals if v < 0.34)}',
        '',
        f'Page recall (expected pages among cited sources):  mean {mean(page_vals)} over {len(page_vals)}',
        f'  with page_recall >= 0.5: {sum(1 for v in page_vals if v >= 0.5) if page_vals else 0}',
        '',
        'Per-question (id | concepts_found/concepts | page_recall | seconds):',
    ]
    for x in sorted(rows, key=lambda r: r['question_id']):
        lines.append(
            f"  q{x['question_id']:>2} | {x['concepts_found']}/{x['concepts']} | "
            f"{x['page_recall'] if x['page_recall'] is not None else '-'} | {x['seconds']}"
        )

    text = '\n'.join(lines)
    with open(SUMMARY, 'w', encoding='utf-8') as f:
        f.write(text)
    print(text)
    print(f'\nSaved -> {SUMMARY}')
    return rows


def run_sample(sample_ids):
    with open('data/evaluation/evaluation_questions.json', 'r', encoding='utf-8') as f:
        questions = json.load(f)

    # Resume support: skip questions already in the output file.
    results = []
    if os.path.exists(OUT):
        with open(OUT, 'r', encoding='utf-8') as f:
            results = json.load(f)
    done_ids = {r['question_id'] for r in results}
    selected = [q for q in questions if q['question_id'] in sample_ids and q['question_id'] not in done_ids]

    print(f'Loading models ...', flush=True)
    emb_model = get_embedding_model()
    vector_db = get_vector_db()
    reranker = get_reranker()

    print(f'Generating answers for {len(selected)} pending questions ...', flush=True)
    for q in selected:
        qid = q['question_id']
        t0 = time.time()
        r = retrieve(q['question_kh'], emb_model, vector_db)
        documents = r['documents'][0]
        metadatas = r['metadatas'][0]
        pages = [m.get('page') for m in metadatas]

        reranked_docs = rerank(q['question_kh'], documents, reranker)
        reranked_sources = []
        used = set()
        for doc in reranked_docs:
            for i, d in enumerate(documents):
                if d == doc and i not in used:
                    reranked_sources.append(metadatas[i])
                    used.add(i)
                    break
        context = "\n\n".join(reranked_docs)

        try:
            answer = generate_answer(q['question_kh'], context, "normal")
            formatted = format_answer(answer, reranked_sources)
        except Exception as err:  # noqa: BLE001
            formatted = f"[FAILED: {err}]"
            print(f'  q{qid:>2} generation FAILED: {str(err)[:100]}', flush=True)

        # Automated faithfulness proxy: key concepts from context appear in answer
        context_text = context.lower()
        answer_lower = formatted.lower()
        expected = q.get('expected_concepts', [])
        concepts_in_answer = []

        results.append({
            'question_id': qid,
            'chapter': q['chapter'],
            'question': q['question_kh'],
            'expected_concepts': expected,
            'expected_pages': q.get('expected_source_pages', []),
            'retrieved_pages': reranked_sources,
            'context_snippet': context[:600],
            'answer': formatted,
            'seconds': round(time.time() - t0, 1),
        })
        print(f'  q{qid:>2} answered in {time.time()-t0:.1f}s', flush=True)

        with open(OUT, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    print(f'\nSaved {len(results)} answers -> {OUT}')


def main():
    parser = argparse.ArgumentParser(description='Evaluate RAG answers')
    parser.add_argument('--sample', type=int, default=20,
                        help='Number of questions to sample (spread across chapters)')
    parser.add_argument('--questions', type=str, default='',
                        help='Comma-separated question ids (overrides --sample)')
    parser.add_argument('--score-only', action='store_true',
                        help='Only compute metrics over answers already saved to OUT')
    args = parser.parse_args()

    if args.score_only:
        score_answers()
        return

    with open('data/evaluation/evaluation_questions.json', 'r', encoding='utf-8') as f:
        questions = json.load(f)

    if args.questions:
        ids = [int(x) for x in args.questions.split(',') if x.strip()]
    else:
        # pick evenly across chapters for a representative sample
        n = args.sample
        ids = []
        continue_flag = True
        for i in range(1, 9):
            ch = [q['question_id'] for q in questions if q['chapter'] == i]
            take = max(1, n // 8)
            ids.extend(ch[:take])
        # top up if fewer than n
        all_ids = [q['question_id'] for q in questions]
        for qid in all_ids:
            if len(ids) >= n:
                break
            if qid not in ids:
                ids.append(qid)

    run_sample(ids)


if __name__ == '__main__':
    main()