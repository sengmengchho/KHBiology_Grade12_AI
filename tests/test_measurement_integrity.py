"""Regression tests for Phase 3.1 measurement integrity.

Run:  python -X utf8 tests/test_measurement_integrity.py

Covers:
  - verified alias matching
  - non-equivalent terms (including Group C)
  - context-sensitive variants and guards
  - negative controls
  - strict-baseline preservation
  - alias-aware aggregate changes
  - stable citation scoring
  - deterministic rescoring
  - unchanged gold labels
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "scripts"))

from evaluation.evaluate_answers import (  # noqa: E402
    DIMENSIONS, alias_matches, concept_present, matched_concepts,
    normalize_match, score_answer,
)
from evaluation.common import expected_pages_for_question, load_gold  # noqa: E402

EVAL = os.path.join(BASE, 'data', 'evaluation')
ROWS_PATH = os.path.join(EVAL, 'answer_evaluations_v3_1_citation.json')
GOLD_PATH = os.path.join(EVAL, 'gold_questions_v2.json')

BASELINE = {
    'correctness': 4.54,
    'completeness': 4.63,
    'faithfulness': 4.98,
    'clarity': 4.34,
    'terminology': 4.78,
    'citation': 4.80,
    'helpfulness': 4.27,
    'overall': 4.62,
}
ALIAS_BASELINE = {
    'correctness': 4.83,
    'completeness': 4.85,
    'faithfulness': 4.98,
    'clarity': 4.34,
    'terminology': 4.93,
    'citation': 4.80,
    'helpfulness': 4.27,
    'overall': 4.71,
}
SCORE_KEYS = DIMENSIONS + [
    'concept_coverage', 'grounded_number_ratio', 'banned_terms',
    'cited_pages', 'valid_citations', 'invalid_citations',
]


def check(name, cond):
    if not cond:
        raise AssertionError(name)
    print(f'  PASS {name}')


def load_rows():
    with open(ROWS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def rows_by_id():
    return {r['question_id']: r for r in load_rows()}


def present(concept, text, mode='alias_aware'):
    return concept_present(concept, normalize_match(text), mode)


def record(answer, concepts, qtype='definition'):
    return {
        'answer': answer,
        'context': '',
        'expected_concepts': concepts,
        'expected_pages': [1],
        'retrieved_pages': [1],
        'abstained': False,
        'expect_abstain': False,
        'question_type': qtype,
    }


def aggregate(rows, mode):
    in_scope = [r for r in rows if not r['expect_abstain']]
    out = {}
    for dim in DIMENSIONS:
        vals = [score_answer(r, mode)[dim] for r in in_scope]
        out[dim] = round(sum(vals) / len(vals), 2)
    per_row = [
        sum(score_answer(r, mode)[d] for d in DIMENSIONS) / len(DIMENSIONS)
        for r in in_scope
    ]
    out['overall'] = round(sum(per_row) / len(per_row), 2)
    return out


def test_verified_aliases():
    print('verified aliases')
    gene = 'សែនគឺជាអង្គធាតុមួយរបស់ ADN ដែលផ្ទុកព័ត៌មានសេនេទិច'
    check('gene spelling variant matches only in alias-aware mode',
          not present('ហ្សែន', gene, 'strict') and
          present('ហ្សែន', gene, 'alias_aware'))
    water = 'រុក្ខជាតិស្រូបយកទឹកពីក្នុងដី'
    check('water-absorption variant',
          not present('ស្រូបទឹក', water, 'strict') and
          present('ស្រូបទឹក', water, 'alias_aware'))
    phloem = 'ផ្លូអែមជាជាលិកានាំដែលដឹកនាំអាហារទៅកោសិកា'
    check('phloem spelling variant',
          not present('ដូអែម', phloem, 'strict') and
          present('ដូអែម', phloem, 'alias_aware'))
    protein = 'ប្រូតេអ៊ីនមាននាទីការពារសារពាង្គកាយ'
    check('protein-role variant',
          not present('តួនាទី', protein, 'strict') and
          present('តួនាទី', protein, 'alias_aware'))
    vein = 'ស្លឹកមានទ្រនុងបែកមែក'
    check('dicot vein variant',
          not present('ទ្រនុងបែកខ្នែង', vein, 'strict') and
          present('ទ្រនុងបែកខ្នែង', vein, 'alias_aware'))
    adaptation = 'ការសម្របប្រួលរបស់ភាវៈរស់ទៅនឹងមជ្ឈដ្ឋាន ហៅថា បន្លំ'
    check('adaptation variant បន្លំ',
          not present('បន្ស៊ាំ', adaptation, 'strict') and
          present('បន្ស៊ាំ', adaptation, 'alias_aware'))
    adaptation2 = adaptation.replace('បន្លំ', 'បន្លាំ')
    check('adaptation variant បន្លាំ',
          not present('បន្ស៊ាំ', adaptation2, 'strict') and
          present('បន្ស៊ាំ', adaptation2, 'alias_aware'))


def test_non_equivalent_terms():
    print('non-equivalent terms')
    check('Group C: លំអងផ្កា is not aliased to គ្រាប់លំអង',
          not present('លំអងផ្កា', 'គ្រាប់លំអង', 'alias_aware'))
    check('Group C: គ្រាប់លំអង does not earn លំអងផ្កា in strict mode',
          not present('លំអងផ្កា', 'គ្រាប់លំអង', 'strict'))
    check('អំបិល is not aliased to អាហារសមុទ្រ',
          not present('អំបិល', 'អាហារសមុទ្រ', 'alias_aware'))
    check('អំបិល is not aliased to គ្រឿន',
          not present('អំបិល', 'គ្រឿន', 'alias_aware'))
    check('ដូអែម is not aliased to the sibling tissue ស៊ីឡែម',
          not present('ដូអែម', 'ស៊ីឡែម', 'alias_aware'))
    check('stale adaptation form បន្សំ is rejected in both modes',
          not present('បន្ស៊ាំ', 'លក្ខណៈបន្សំ', 'strict') and
          not present('បន្ស៊ាំ', 'លក្ខណៈបន្សំ', 'alias_aware'))


def test_context_guards():
    print('context guards')
    check('gene alias needs gene context',
          not present('ហ្សែន', 'សែនគឺជាឈ្មោះរបស់មនុស្សម្នាក់', 'alias_aware'))
    check('gene alias accepted with ADN context',
          present('ហ្សែន', 'សែនស្ថិតនៅលើ ADN', 'alias_aware'))
    check('protein role alias needs protein context',
          not present('តួនាទី', 'នាទីរបស់ឫសគឺដឹកនាំទឹក', 'alias_aware'))
    check('protein role alias accepted with protein context',
          present('តួនាទី', 'ប្រូតេអ៊ីនមាននាទីជាអង់ស៊ីម', 'alias_aware'))
    check('adaptation alias rejected in counterfeiting context',
          not present('បន្ស៊ាំ', 'គាត់បន្លំឯកសារដើម្បីទទួលបានសិទ្ធិ', 'alias_aware'))
    check('adaptation alias accepted in adaptation context',
          present('បន្ស៊ាំ', 'ការសម្របប្រួលទៅនឹងមជ្ឈដ្ឋាន ហៅថា បន្លំ', 'alias_aware'))
    check('phloem alias rejected for water-only transport',
          not present('ដូអែម', 'ផ្លូអែមដឹកនាំទឹកនិងអំបិលខនិជពីឫសទៅស្លឹក', 'alias_aware'))
    check('phloem alias accepted for food transport',
          present('ដូអែម', 'ផ្លូអែមដឹកនាំអាហារទៅកោសិកា', 'alias_aware'))
    check('vein alias needs leaf/dicot context',
          not present('ទ្រនុងបែកខ្នែង', 'ទ្រនុងបែកមែក', 'alias_aware'))
    check('vein alias accepted with leaf context',
          present('ទ្រនុងបែកខ្នែង', 'ស្លឹកមានទ្រនុងបែកមែក', 'alias_aware'))


def test_negative_controls():
    print('negative controls')
    cases = [
        ('gene word without gene meaning',
         'ហ្សែន', 'សែនគឺជាឈ្មោះរបស់មនុស្សម្នាក់'),
        ('role word without protein role',
         'តួនាទី', 'នាទីរបស់ឫសគឺដឹកនាំទឹកនិងអំបិលខនិជ'),
        ('counterfeiting បន្លំ',
         'បន្ស៊ាំ', 'គាត់បន្លំឯកសារដើម្បីទទួលបានសិទ្ធិ'),
        ('phloem with wrong water-only function',
         'ដូអែម', 'ផ្លូអែមដឹកនាំទឹកនិងអំបិលខនិជពីឫសទៅស្លឹក'),
    ]
    for name, concept, answer in cases:
        scores = score_answer(record(answer, [concept]), 'alias_aware')
        check(f'{name}: coverage stays 0.0', scores['concept_coverage'] == 0.0)
        check(f'{name}: correctness stays 1', scores['correctness'] == 1)


def test_strict_baseline_preserved():
    print('strict baseline preserved')
    rows = load_rows()
    mismatches = []
    for rec in rows:
        strict = score_answer(rec, 'strict')
        default = score_answer(rec)
        if strict != default:
            mismatches.append((rec['question_id'], 'default != strict'))
        saved = rec.get('scores', {})
        for key in sorted(set(saved) | set(strict)):
            if saved.get(key) != strict.get(key):
                mismatches.append((rec['question_id'], key))
    check('default scoring path is strict', not mismatches)
    agg = aggregate(rows, 'strict')
    for key, value in BASELINE.items():
        check(f'strict {key} = {value:.2f}', agg[key] == value)
    check('invalid citations remain 0/41',
          sum(1 for r in rows if not r['expect_abstain']
              and score_answer(r, 'strict').get('invalid_citations')) == 0)


def test_alias_aware_aggregate_and_targets():
    print('alias-aware aggregate and target questions')
    rows = load_rows()
    by_id = rows_by_id()
    agg = aggregate(rows, 'alias_aware')
    for key, value in ALIAS_BASELINE.items():
        check(f'alias-aware {key} = {value:.2f}', agg[key] == value)

    changed = sorted(
        r['question_id'] for r in rows
        if score_answer(r, 'strict') != score_answer(r, 'alias_aware')
    )
    check('only the five alias-driven questions change',
          changed == [58, 65, 78, 86, 96])
    check('q78 coverage 1.0', score_answer(by_id[78], 'alias_aware')['concept_coverage'] == 1.0)
    check('q86 coverage 1.0', score_answer(by_id[86], 'alias_aware')['concept_coverage'] == 1.0)
    check('q58 coverage 1.0', score_answer(by_id[58], 'alias_aware')['concept_coverage'] == 1.0)
    check('q65 coverage 1.0', score_answer(by_id[65], 'alias_aware')['concept_coverage'] == 1.0)
    check('q96 coverage 0.6', score_answer(by_id[96], 'alias_aware')['concept_coverage'] == 0.6)

    q111 = by_id[111]
    check('q111 coverage stays 0.5',
          score_answer(q111, 'alias_aware')['concept_coverage'] == 0.5)
    check('q111 still misses natural selection',
          'ជម្រើសដោយធម្មជាតិ' not in matched_concepts(q111, 'alias_aware'))
    check('q111 does not earn a free alias match',
          alias_matches(q111) == [])

    q96 = by_id[96]
    check('q96 still misses cotyledon',
          'កូទីលេដុង' not in matched_concepts(q96, 'alias_aware'))
    check('q96 still misses taproot',
          'ឫសកែវ' not in matched_concepts(q96, 'alias_aware'))
    check('q96 never commits to an explicit dicot classification',
          'ស្វាយជារុក្ខជាតិឌីកូទីលេដូន' not in q96['answer'])

    q94 = by_id[94]
    check('q94 coverage stays 0.8',
          score_answer(q94, 'alias_aware')['concept_coverage'] == 0.8)
    check('q94 still misses អំបិល',
          'អំបិល' not in matched_concepts(q94, 'alias_aware'))
    check('q94 answer does not claim iodized salt',
          'អំបិល' not in q94['answer'])

    q55 = by_id[55]
    check('q55 coverage stays 0.5',
          score_answer(q55, 'alias_aware')['concept_coverage'] == 0.5)
    check('q55 still misses Group C term លំអងផ្កា',
          'លំអងផ្កា' not in matched_concepts(q55, 'alias_aware'))


def test_citation_scoring_stable():
    print('citation scoring stable')
    rows = load_rows()
    for rec in rows:
        strict = score_answer(rec, 'strict')
        alias = score_answer(rec, 'alias_aware')
        for key in ('citation', 'cited_pages', 'valid_citations', 'invalid_citations'):
            if strict.get(key) != alias.get(key):
                raise AssertionError(f"q{rec['question_id']} {key} changed")
    check('citation dimensions, pages, and validity unchanged for all 45 rows', True)
    check('invalid citations remain 0/41',
          sum(1 for r in rows if not r['expect_abstain']
              and score_answer(r, 'alias_aware').get('invalid_citations')) == 0)


def test_deterministic_rescoring():
    print('deterministic rescoring')
    rows = load_rows()
    first = [(score_answer(r, 'alias_aware'), matched_concepts(r, 'alias_aware'),
              alias_matches(r)) for r in rows]
    second = [(score_answer(r, 'alias_aware'), matched_concepts(r, 'alias_aware'),
               alias_matches(r)) for r in rows]
    check('alias-aware rescoring is deterministic', first == second)
    check('strict rescoring is deterministic',
          [score_answer(r, 'strict') for r in rows] ==
          [score_answer(r, 'strict') for r in rows])


def test_gold_labels_unchanged():
    print('gold labels unchanged')
    rows = rows_by_id()
    gold = {q['question_id']: q for q in load_gold(GOLD_PATH)}
    missing = sorted(set(rows) - set(gold))
    check('all saved rows have a frozen gold record', not missing)
    for qid, rec in rows.items():
        g = gold[qid]
        if rec.get('expected_concepts') != g.get('expected_concepts', []):
            raise AssertionError(f'q{qid} expected_concepts differ from gold')
        if rec.get('expected_pages') != expected_pages_for_question(g):
            raise AssertionError(f'q{qid} expected_pages differ from gold')
    check('all expected_concepts and expected_pages match the frozen gold', True)
    check('saved rows are a subset of the frozen gold set', set(rows) <= set(gold))
    check('frozen gold retains unsampled questions', len(gold) >= len(rows))


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    test_verified_aliases()
    test_non_equivalent_terms()
    test_context_guards()
    test_negative_controls()
    test_strict_baseline_preserved()
    test_alias_aware_aggregate_and_targets()
    test_citation_scoring_stable()
    test_deterministic_rescoring()
    test_gold_labels_unchanged()
    print('\nALL MEASUREMENT-INTEGRITY TESTS PASSED')


if __name__ == '__main__':
    main()
