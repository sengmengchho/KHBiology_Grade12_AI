"""Retrieval evaluation (v2) on gold_questions_v2.json.

Measures three configurations on the *real* query path:
  embed   : normalize_query + expand_query -> BGE-M3 -> Chroma top-K
  rerank  : the same candidates -> bge-reranker-v2-m3
  real    : the same candidates -> rerank_with_context (what app/main.py uses)

Hit rule: a retrieved chunk is a hit when its page range
[page_start, page_end] intersects the question's expected_source_pages.

Also measures abstention at RETRIEVAL_SCORE_THRESHOLD (default 0.08):
  - in-scope questions should NOT abstain
  - out-of-scope questions SHOULD abstain

Resumable: per-question rows are written after each question.
Outputs (new files, historical results untouched):
  data/evaluation/retrieval_<tag>_results.json
  data/evaluation/retrieval_<tag>_summary.txt

Usage:
  python -m scripts.evaluation.evaluate_retrieval [--fresh] [--limit N]
  python -m scripts.evaluation.evaluate_retrieval --tag v3 --fresh --max-rows 20
"""

import argparse
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, SCRIPTS)

from app.config import TOP_K, RERANKER_TOP_K, RETRIEVAL_SCORE_THRESHOLD  # noqa: E402
from app.retrieval import (  # noqa: E402
    get_embedding_model, get_vector_db, get_reranker, retrieve,
)
from evaluation.common import (  # noqa: E402
    at_k_metrics, expected_pages_for_part, load_gold, mean, prepare_queries,
)

OUT = os.path.join(BASE, 'data', 'evaluation', 'retrieval_v2_results.json')
SUMMARY = os.path.join(BASE, 'data', 'evaluation', 'retrieval_v2_summary.txt')
TAG = 'v2'
VARIANTS = ('embed', 'rerank', 'real')


def load_existing(fresh: bool) -> dict:
    if fresh or not os.path.exists(OUT):
        return {'meta': {}, 'rows': {}}
    with open(OUT, 'r', encoding='utf-8') as f:
        return json.load(f)


def save(data: dict) -> None:
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def _rerank_once(query: str, docs: list[str], metas: list[dict], reranker):
    """Score the candidates once and derive both the plain-rerank ranking and
    the app's rerank_with_context ranking from the same scores.

    This mirrors app/retrieval.py:rerank_with_context exactly (top_k selected
    plus neighbours from selected pages, max_total=12, max_per_page=4) but
    avoids scoring the same 30 pairs twice, which doubled CPU runtime.
    """
    pairs = [[query, doc] for doc in docs]
    scores = reranker.compute_score(pairs, normalize=True, batch_size=2)
    if isinstance(scores, float):
        scores = [scores]
    indexed = sorted(
        zip(docs, metas, [float(s) for s in scores]),
        key=lambda x: x[2], reverse=True,
    )

    plain = indexed[:RERANKER_TOP_K]
    selected = indexed[:RERANKER_TOP_K]
    page_counts = {}
    for _d, m, _s in selected:
        p = m.get('page', m.get('page_start'))
        if p is not None:
            page_counts[p] = page_counts.get(p, 0) + 1
    for item in indexed[RERANKER_TOP_K:]:
        if len(selected) >= 12:
            break
        p = item[1].get('page', item[1].get('page_start'))
        if p is not None and p in page_counts and page_counts[p] < 4:
            page_counts[p] += 1
            selected.append(item)

    plain_metas = [m for _d, m, _s in plain]
    real_metas = [m for _d, m, _s in selected]
    real_scores = [s for _d, _m, s in selected]
    return plain_metas, real_metas, real_scores


def evaluate_row(q: dict, part_idx: int, query: str, emb, db, reranker) -> dict:
    r = retrieve(query, emb, db, top_k=TOP_K)
    docs = r['documents'][0]
    metas = r['metadatas'][0]
    expected = expected_pages_for_part(q, part_idx)

    rerank_metas, real_metas, real_scores = _rerank_once(
        query, docs, metas, reranker
    )
    top_score = real_scores[0] if real_scores else 0.0

    row = {
        'question_id': q['question_id'],
        'part': part_idx,
        'chapter': q['chapter'],
        'question_type': q['question_type'],
        'question': q['question_kh'],
        'query_used': query,
        'expected_pages': expected,
        'expect_abstain': bool(q.get('expect_abstain')),
        'top_score': round(float(top_score), 4),
        'abstained': bool(top_score < RETRIEVAL_SCORE_THRESHOLD),
        'embed': {
            'top5_pages': [m.get('page') for m in metas[:5]],
            **at_k_metrics(metas, expected),
        },
        'rerank': {
            'top5_pages': [m.get('page') for m in rerank_metas[:5]],
            **at_k_metrics(rerank_metas, expected),
        },
        'real': {
            'pages': [m.get('page') for m in real_metas],
            'scores': [round(float(s), 4) for s in real_scores],
            **at_k_metrics(real_metas, expected),
        },
    }
    return row


def select_ids(gold: list[dict], n_v1: int) -> set[int]:
    """Stratified v1 sample (round-robin across chapters) plus every special
    (OCR-garbled, multi-part) and every out-of-scope question."""
    if n_v1 <= 0:
        return {q['question_id'] for q in gold}
    base = [q for q in gold if q.get('source') == 'v1']
    extras = [q for q in gold if q.get('source') != 'v1']
    by_ch = {}
    for q in base:
        by_ch.setdefault(q['chapter'], []).append(q['question_id'])
    ids, r = [], 0
    while len(ids) < n_v1:
        added = False
        for ch in sorted(by_ch):
            if r < len(by_ch[ch]) and len(ids) < n_v1:
                ids.append(by_ch[ch][r])
                added = True
        if not added:
            break
        r += 1
    ids += [q['question_id'] for q in extras]
    return set(ids)


def aggregate(rows: list[dict]) -> dict:
    in_scope = [r for r in rows if not r['expect_abstain']]
    out_scope = [r for r in rows if r['expect_abstain']]

    agg = {}
    for v in VARIANTS:
        agg[v] = {
            'n': len(in_scope),
            'recall@1': mean([float(r[v]['hit1']) for r in in_scope]),
            'recall@3': mean([float(r[v]['hit3']) for r in in_scope]),
            'recall@5': mean([float(r[v]['hit5']) for r in in_scope]),
            'mrr': mean([r[v]['mrr'] for r in in_scope]),
        }

    def rate(items, pred):
        return round(sum(1 for x in items if pred(x)) / len(items), 3) if items else None

    abst = {
        'out_of_scope_n': len(out_scope),
        'out_of_scope_abstained': rate(out_scope, lambda r: r['abstained']),
        'in_scope_n': len(in_scope),
        'in_scope_false_abstain': rate(in_scope, lambda r: r['abstained']),
    }

    by_chapter = {}
    for ch in sorted({r['chapter'] for r in in_scope}):
        sub = [r for r in in_scope if r['chapter'] == ch]
        by_chapter[str(ch)] = {
            'n': len(sub),
            'recall@5_real': mean([float(r['real']['hit5']) for r in sub]),
            'mrr_real': mean([r['real']['mrr'] for r in sub]),
            'false_abstain': rate(sub, lambda r: r['abstained']),
        }

    by_type = {}
    for t in sorted({r['question_type'] for r in in_scope}):
        sub = [r for r in in_scope if r['question_type'] == t]
        by_type[t] = {
            'n': len(sub),
            'recall@5_real': mean([float(r['real']['hit5']) for r in sub]),
            'mrr_real': mean([r['real']['mrr'] for r in sub]),
        }

    per_question = {}
    for r in in_scope:
        e = per_question.setdefault(r['question_id'], {
            'chapter': r['chapter'],
            'question_type': r['question_type'],
            'parts': 0,
            'real_hit5_parts': 0,
            'real_mrr': 0.0,
        })
        e['parts'] += 1
        e['real_hit5_parts'] += int(r['real']['hit5'])
        e['real_mrr'] += r['real']['mrr']
    strict_hit5 = rate(list(per_question.values()), lambda e: e['real_hit5_parts'] == e['parts'])
    any_hit5 = rate(list(per_question.values()), lambda e: e['real_hit5_parts'] > 0)

    return {
        'variants': agg,
        'abstention': abst,
        'by_chapter': by_chapter,
        'by_type': by_type,
        'per_question_counts': {
            'n_questions': len(per_question),
            'strict_hit5': strict_hit5,
            'any_part_hit5': any_hit5,
        },
    }


def write_summary(data: dict) -> None:
    agg = data['aggregate']
    lines = []
    lines.append(f'RETRIEVAL EVALUATION {TAG}')
    lines.append(f"generated: {data['meta'].get('generated')}")
    lines.append(
        f"rows: {data['meta'].get('n_rows')} | in-scope questions: "
        f"{data['meta'].get('n_in_scope')} | threshold: {RETRIEVAL_SCORE_THRESHOLD} | "
        f"TOP_K: {TOP_K} | RERANKER_TOP_K: {RERANKER_TOP_K}"
    )
    lines.append('')
    lines.append('Overall (in-scope rows)')
    lines.append(f'{"metric":<12}{"embed":>9}{"rerank":>9}{"real":>9}')
    for m in ('recall@1', 'recall@3', 'recall@5', 'mrr'):
        v = agg['variants']
        lines.append(f'{m:<12}{v["embed"][m]:>9.3f}{v["rerank"][m]:>9.3f}{v["real"][m]:>9.3f}')
    lines.append('')
    lines.append(
        f"Per-question (multi-part strict): n={agg['per_question_counts']['n_questions']} "
        f"strict_hit5={agg['per_question_counts']['strict_hit5']} "
        f"any_part_hit5={agg['per_question_counts']['any_part_hit5']}"
    )
    lines.append('')
    a = agg['abstention']
    lines.append('Abstention (threshold < %.2f)' % RETRIEVAL_SCORE_THRESHOLD)
    lines.append(f"  out-of-scope abstained: {a['out_of_scope_abstained']} (n={a['out_of_scope_n']})")
    lines.append(f"  in-scope false abstain: {a['in_scope_false_abstain']} (n={a['in_scope_n']})")
    lines.append('')
    lines.append('By chapter (real pipeline)')
    lines.append(f'{"ch":<4}{"n":>5}{"recall@5":>10}{"mrr":>8}{"false_abst":>12}')
    for ch, v in agg['by_chapter'].items():
        lines.append(
            f'{ch:<4}{v["n"]:>5}{v["recall@5_real"]:>10.3f}'
            f'{v["mrr_real"]:>8.3f}{v["false_abstain"]:>12.3f}'
        )
    lines.append('')
    lines.append('By question type (real pipeline)')
    lines.append(f'{"type":<18}{"n":>5}{"recall@5":>10}{"mrr":>8}')
    for t, v in agg['by_type'].items():
        lines.append(f'{t:<18}{v["n"]:>5}{v["recall@5_real"]:>10.3f}{v["mrr_real"]:>8.3f}')
    lines.append('')
    selected = set(data['meta'].get('selected_ids') or [])
    failures = [
        r for r in data['rows'].values()
        if (not selected or r['question_id'] in selected)
        and not r['expect_abstain'] and not r['real']['hit5']
    ]
    lines.append(f'Retrieval failures (real Recall@5 miss): {len(failures)} rows')
    for r in sorted(failures, key=lambda x: (x['question_id'], x['part']))[:40]:
        lines.append(
            f"  q{r['question_id']}.{r['part']} ch{r['chapter']} {r['question_type']} "
            f"exp={r['expected_pages']} got={r['real']['pages'][:5]} top={r['top_score']}"
        )
    text = '\n'.join(lines)
    with open(SUMMARY, 'w', encoding='utf-8') as f:
        f.write(text)
    print('\n' + text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fresh', action='store_true')
    ap.add_argument('--limit', type=int, default=0,
                    help='evaluate only the first N gold questions')
    ap.add_argument('--max-rows', type=int, default=0,
                    help='stop after N new rows this invocation (resumable)')
    ap.add_argument('--sample', type=int, default=0,
                    help='number of stratified v1 questions (specials always included)')
    ap.add_argument('--tag', default='v2',
                    help='output tag; v3 writes retrieval_v3_results.json')
    ap.add_argument('--ids', default='',
                    help='comma-separated question ids to refresh in an existing run')
    args = ap.parse_args()

    global OUT, SUMMARY, TAG
    TAG = args.tag
    if TAG != 'v2':
        OUT = os.path.join(BASE, 'data', 'evaluation', f'retrieval_{TAG}_results.json')
        SUMMARY = os.path.join(BASE, 'data', 'evaluation', f'retrieval_{TAG}_summary.txt')

    gold = load_gold()
    if args.limit:
        gold = gold[: args.limit]

    data = load_existing(args.fresh)
    rows = data.setdefault('rows', {})

    refresh_ids = {
        int(x) for x in args.ids.split(',') if x.strip()
    } if args.ids else set()
    if refresh_ids:
        gold = [q for q in gold if q['question_id'] in refresh_ids]
        for key in list(rows):
            if int(key.split(':', 1)[0]) in refresh_ids:
                rows.pop(key)

    prev_selected = data.get('meta', {}).get('selected_ids')
    if args.sample:
        selected = select_ids(gold, args.sample)
    elif prev_selected:
        selected = set(prev_selected)
    else:
        selected = None
    if selected is not None:
        gold = [q for q in gold if q['question_id'] in selected]

    todo = []
    for q in gold:
        for i, query in enumerate(prepare_queries(q['question_kh'])):
            key = f"{q['question_id']}:{i}"
            if key not in rows:
                todo.append((key, q, i, query))

    if args.max_rows:
        todo = todo[: args.max_rows]

    if todo:
        print(f'Loading models ... ({len(todo)} rows pending)', flush=True)
        emb = get_embedding_model()
        db = get_vector_db()
        reranker = get_reranker()
        print('Models ready. Retrieving ...', flush=True)
        for n, (key, q, i, query) in enumerate(todo, 1):
            rows[key] = evaluate_row(q, i, query, emb, db, reranker)
            save(data)
            if n % 10 == 0 or n == len(todo):
                print(f'  {n}/{len(todo)} rows', flush=True)

    all_rows = [
        r for r in rows.values()
        if selected is None or r['question_id'] in selected
    ]
    data['meta'] = {
        'generated': time.strftime('%Y-%m-%d %H:%M'),
        'n_rows': len(all_rows),
        'total_rows_saved': len(rows),
        'n_in_scope': sum(1 for r in all_rows if not r['expect_abstain']),
        'n_out_of_scope': sum(1 for r in all_rows if r['expect_abstain']),
        'threshold': RETRIEVAL_SCORE_THRESHOLD,
        'top_k': TOP_K,
        'reranker_top_k': RERANKER_TOP_K,
        'gold_file': 'data/evaluation/gold_questions_v2.json',
        'tag': TAG,
        'sample_v1': args.sample or data.get('meta', {}).get('sample_v1'),
        'selected_ids': sorted(selected) if selected is not None else None,
    }
    data['aggregate'] = aggregate(all_rows)
    save(data)
    write_summary(data)
    print(f'\nSaved -> {OUT}')


if __name__ == '__main__':
    main()
