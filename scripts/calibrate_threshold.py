"""Collect top rerank scores over the evaluation questions to calibrate the
abstain threshold. Incrementally saves progress so a long run is resumable.

Usage: python scripts/calibrate_threshold.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUT = os.path.join('data', 'evaluation', 'top_rerank_scores.json')


def main():
    with open('data/evaluation/evaluation_questions.json', 'r', encoding='utf-8') as f:
        qs = json.load(f)

    done = []
    if os.path.exists(OUT):
        with open(OUT, 'r', encoding='utf-8') as f:
            done = json.load(f)
    done_ids = {d['question_id'] for d in done}
    pending = [q for q in qs if q['question_id'] not in done_ids]
    print(f'resume: {len(done)} done, {len(pending)} pending', flush=True)

    from app.retrieval import get_embedding_model, get_vector_db, get_reranker, retrieve, rerank_with_scores
    emb = get_embedding_model(); db = get_vector_db(); rk = get_reranker()
    print('models loaded', flush=True)

    for q in pending:
        r = retrieve(q['question_kh'], emb, db)
        rd, rs, sc = rerank_with_scores(q['question_kh'], r['documents'][0], r['metadatas'][0], rk)
        top = round(sc[0], 3) if sc else 0.0
        done.append({'question_id': q['question_id'], 'chapter': q['chapter'], 'top_score': top})
        with open(OUT, 'w', encoding='utf-8') as f:
            json.dump(done, f, ensure_ascii=False, indent=2)
        print(f"  q{q['question_id']:>2} top={top:.3f}", flush=True)

    s = sorted(d['top_score'] for d in done)
    n = len(s)
    def pct(p):
        return s[min(n - 1, int(p / 100 * n))]
    print(f'--- n={n} min={s[0]:.3f} p10={pct(10):.3f} p25={pct(25):.3f} '
          f'median={pct(50):.3f} p90={pct(90):.3f} max={s[-1]:.3f}', flush=True)
    for t in (0.03, 0.05, 0.08, 0.10, 0.12, 0.15, 0.20):
        print(f'  below {t}: {sum(1 for v in s if v < t)}/{n}', flush=True)


if __name__ == '__main__':
    main()