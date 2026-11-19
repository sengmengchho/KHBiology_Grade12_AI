"""Phase 3.1 evaluator-only rescoring of the saved 45-question artifact.

Loads the frozen v3_1_citation answers, verifies that strict scoring reproduces
the accepted baseline exactly, then computes a separate alias-aware score set.
No retrieval, generation, or Gemini calls are made.

Outputs:
  data/evaluation/answer_evaluations_v3_1_citation_alias_aware.json
  data/evaluation/answer_evaluation_v3_1_citation_comparison.json
  data/evaluation/answer_evaluation_v3_1_citation_comparison.csv
  data/evaluation/answer_evaluation_v3_1_citation_comparison_summary.txt

Usage:
  python -X utf8 -m scripts.evaluation.rescore_phase3_1
"""

import csv
import hashlib
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, SCRIPTS)

from evaluation.evaluate_answers import (  # noqa: E402
    DIMENSIONS, alias_matches, matched_concepts, score_answer,
)
from evaluation.common import expected_pages_for_question, load_gold  # noqa: E402

EVAL = os.path.join(BASE, 'data', 'evaluation')
SRC = os.path.join(EVAL, 'answer_evaluations_v3_1_citation.json')
GOLD = os.path.join(EVAL, 'gold_questions_v2.json')
CORPUS = os.path.join(BASE, 'data', 'processed', 'biology_chunks.json')
SUMMARY_SRC = os.path.join(EVAL, 'answer_evaluation_v3_1_citation_summary.txt')
ALIAS_ROWS = os.path.join(EVAL, 'answer_evaluations_v3_1_citation_alias_aware.json')
COMPARISON = os.path.join(EVAL, 'answer_evaluation_v3_1_citation_comparison.json')
COMPARISON_CSV = os.path.join(EVAL, 'answer_evaluation_v3_1_citation_comparison.csv')
COMPARISON_TXT = os.path.join(EVAL, 'answer_evaluation_v3_1_citation_comparison_summary.txt')

BASELINE = {
    'correctness': 4.54,
    'completeness': 4.63,
    'faithfulness': 4.98,
    'clarity': 4.34,
    'terminology': 4.78,
    'citation': 4.8,
    'helpfulness': 4.27,
    'overall': 4.62,
}

TARGET_IDS = [78, 86, 58, 65, 55, 94, 96, 111]
SCORE_KEYS = DIMENSIONS + [
    'concept_coverage', 'grounded_number_ratio', 'banned_terms',
    'cited_pages', 'valid_citations', 'invalid_citations',
]


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def aggregate(rows, mode):
    in_scope = [r for r in rows if not r.get('expect_abstain')]
    scores = [score_answer(r, mode) for r in in_scope]
    out = {}
    for dim in DIMENSIONS:
        vals = [s[dim] for s in scores]
        out[dim] = round(sum(vals) / len(vals), 2)
    per_row = [sum(s[d] for d in DIMENSIONS) / len(DIMENSIONS) for s in scores]
    out['overall'] = round(sum(per_row) / len(per_row), 2)
    out['in_scope_count'] = len(in_scope)
    out['out_of_scope_count'] = len(rows) - len(in_scope)
    out['invalid_citation_rows'] = sum(
        1 for s in scores if s.get('invalid_citations')
    )
    return out


def main():
    rows = load_json(SRC)
    gold_rows = load_gold(GOLD)
    gold = {q['question_id']: q for q in gold_rows}

    strict_scores = {}
    alias_scores = {}
    mismatches = []
    label_mismatches = []
    per_question = []
    alias_output = []

    for rec in rows:
        qid = rec['question_id']
        strict = score_answer(rec, 'strict')
        alias = score_answer(rec, 'alias_aware')
        strict_scores[qid] = strict
        alias_scores[qid] = alias

        saved = rec.get('scores', {})
        for key in sorted(set(saved) | set(strict)):
            if saved.get(key) != strict.get(key):
                mismatches.append({
                    'question_id': qid,
                    'key': key,
                    'saved': saved.get(key),
                    'strict_rescored': strict.get(key),
                })

        g = gold.get(qid)
        if g is not None:
            if rec.get('expected_concepts') != g.get('expected_concepts', []):
                label_mismatches.append({
                    'question_id': qid, 'field': 'expected_concepts',
                    'saved': rec.get('expected_concepts'),
                    'gold': g.get('expected_concepts', []),
                })
            if rec.get('expected_pages') != expected_pages_for_question(g):
                label_mismatches.append({
                    'question_id': qid, 'field': 'expected_pages',
                    'saved': rec.get('expected_pages'),
                    'gold': expected_pages_for_question(g),
                })

        changed_dims = {
            dim: {'strict': strict[dim], 'alias_aware': alias[dim]}
            for dim in DIMENSIONS if strict[dim] != alias[dim]
        }
        per_question.append({
            'question_id': qid,
            'chapter': rec.get('chapter'),
            'question_type': rec.get('question_type'),
            'question': rec.get('question'),
            'changed': bool(changed_dims),
            'strict': {k: strict.get(k) for k in SCORE_KEYS if k in strict},
            'alias_aware': {k: alias.get(k) for k in SCORE_KEYS if k in alias},
            'delta': {
                dim: alias[dim] - strict[dim]
                for dim in DIMENSIONS
            },
            'changed_dimensions': changed_dims,
            'matched_concepts_strict': matched_concepts(rec, 'strict'),
            'matched_concepts_alias_aware': matched_concepts(rec, 'alias_aware'),
            'alias_matches': alias_matches(rec),
        })

        alias_rec = dict(rec)
        alias_rec['evaluation_mode'] = 'alias_aware'
        alias_rec['strict_scores'] = strict
        alias_rec['scores'] = alias
        alias_rec['measurement_integrity'] = {
            'matched_concepts_strict': matched_concepts(rec, 'strict'),
            'matched_concepts_alias_aware': matched_concepts(rec, 'alias_aware'),
            'alias_matches': alias_matches(rec),
        }
        alias_output.append(alias_rec)

    strict_agg = aggregate(rows, 'strict')
    alias_agg = aggregate(rows, 'alias_aware')
    baseline_match = {
        key: strict_agg[key] == BASELINE[key] for key in BASELINE
    }
    baseline_reproduced = all(baseline_match.values())
    difference = {
        key: round(alias_agg[key] - strict_agg[key], 2) for key in BASELINE
    }

    changed = [q for q in per_question if q['changed']]
    target_rows = [q for q in per_question if q['question_id'] in TARGET_IDS]

    report = {
        'phase': '3.1',
        'evaluator_only': True,
        'gemini_calls': 0,
        'source_rows': os.path.relpath(SRC, BASE),
        'frozen_gold': os.path.relpath(GOLD, BASE),
        'corpus': os.path.relpath(CORPUS, BASE),
        'hashes': {
            'source_rows_sha256': sha256(SRC),
            'frozen_gold_sha256': sha256(GOLD),
            'corpus_sha256': sha256(CORPUS),
            'accepted_summary_sha256': sha256(SUMMARY_SRC),
        },
        'strict_reproduction': {
            'passed': not mismatches and baseline_reproduced,
            'score_mismatches': mismatches,
            'baseline_match': baseline_match,
            'saved_baseline': BASELINE,
            'strict_rescored': {
                key: strict_agg[key] for key in BASELINE
            },
        },
        'gold_labels_unchanged': not label_mismatches,
        'gold_label_mismatches': label_mismatches,
        'counts': {
            'total': len(rows),
            'in_scope': strict_agg['in_scope_count'],
            'out_of_scope': strict_agg['out_of_scope_count'],
            'invalid_citation_rows': strict_agg['invalid_citation_rows'],
        },
        'strict': {key: strict_agg[key] for key in BASELINE},
        'alias_aware': {key: alias_agg[key] for key in BASELINE},
        'difference': difference,
        'changed_question_ids': [q['question_id'] for q in changed],
        'target_question_ids': TARGET_IDS,
        'target_questions': target_rows,
        'per_question': per_question,
    }

    with open(ALIAS_ROWS, 'w', encoding='utf-8') as f:
        json.dump(alias_output, f, ensure_ascii=False, indent=2)
    with open(COMPARISON, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    with open(COMPARISON_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        dims = DIMENSIONS
        writer.writerow(
            ['question_id', 'chapter', 'question_type', 'changed'] +
            [f'strict_{d}' for d in dims] +
            [f'alias_{d}' for d in dims] +
            [f'delta_{d}' for d in dims] +
            ['strict_coverage', 'alias_coverage',
             'matched_concepts_strict', 'matched_concepts_alias_aware',
             'accepted_aliases']
        )
        for q in sorted(per_question, key=lambda x: x['question_id']):
            writer.writerow(
                [q['question_id'], q['chapter'], q['question_type'], q['changed']] +
                [q['strict'][d] for d in dims] +
                [q['alias_aware'][d] for d in dims] +
                [q['delta'][d] for d in dims] +
                [q['strict'].get('concept_coverage'),
                 q['alias_aware'].get('concept_coverage'),
                 '; '.join(q['matched_concepts_strict']),
                 '; '.join(q['matched_concepts_alias_aware']),
                 '; '.join(m['alias'] for m in q['alias_matches'])]
            )

    lines = [
        'Phase 3.1 strict vs alias-aware comparison (45 saved answers, no Gemini)',
        '',
        f"Strict baseline reproduced: {'PASS' if report['strict_reproduction']['passed'] else 'FAIL'}",
        f"Gold labels unchanged: {'PASS' if report['gold_labels_unchanged'] else 'FAIL'}",
        f"In-scope rows: {report['counts']['in_scope']}",
        f"Invalid-citation rows: {report['counts']['invalid_citation_rows']}",
        '',
        'Metric | Strict baseline | Alias-aware | Difference',
        '--- | ---: | ---: | ---:',
    ]
    for key in ['correctness', 'completeness', 'faithfulness', 'clarity',
                'terminology', 'citation', 'helpfulness', 'overall']:
        lines.append(
            f"{key} | {strict_agg[key]:.2f} | {alias_agg[key]:.2f} | "
            f"{difference[key]:+.2f}"
        )
    lines += ['', 'Changed questions:']
    for q in changed:
        dims_text = ', '.join(
            f"{d} {v['strict']}->{v['alias_aware']}"
            for d, v in q['changed_dimensions'].items()
        )
        aliases = ', '.join(
            f"{m['concept']} via {m['alias']}" for m in q['alias_matches']
        )
        lines.append(
            f"  q{q['question_id']}: coverage "
            f"{q['strict'].get('concept_coverage')}->"
            f"{q['alias_aware'].get('concept_coverage')}; {dims_text}; "
            f"alias: {aliases or 'none'}"
        )
    unchanged = [q for q in target_rows if not q['changed']]
    lines += ['', 'Target questions unchanged: ' + ', '.join(
        f"q{q['question_id']}" for q in unchanged
    )]
    lines += ['', f"Saved -> {os.path.relpath(ALIAS_ROWS, BASE)}",
              f"Saved -> {os.path.relpath(COMPARISON, BASE)}",
              f"Saved -> {os.path.relpath(COMPARISON_CSV, BASE)}"]

    text = '\n'.join(lines)
    with open(COMPARISON_TXT, 'w', encoding='utf-8') as f:
        f.write(text)
    print(text)
    if not report['strict_reproduction']['passed']:
        raise SystemExit('Strict baseline reproduction FAILED')
    if not report['gold_labels_unchanged']:
        raise SystemExit('Gold-label consistency check FAILED')


if __name__ == '__main__':
    main()
