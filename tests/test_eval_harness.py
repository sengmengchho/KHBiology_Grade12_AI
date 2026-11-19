"""Regression tests for the v2 evaluation harness.

Run:  python -X utf8 tests/test_eval_harness.py
"""

import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "scripts"))

from app.rag import GENERATION_FALLBACK_MESSAGE  # noqa: E402
from app.utils import QUERY_FIXES, expand_query, normalize_query  # noqa: E402
from app.utils import split_questions as app_split_questions  # noqa: E402
from evaluation.common import (  # noqa: E402
    at_k_metrics, expected_pages_for_part, expected_pages_for_question,
    is_page_hit, load_gold, mean, prepare_queries,
    split_questions, strip_lead_markers,
)
from evaluation.evaluate_answers import (  # noqa: E402
    concept_present, normalize_match, score_answer, strip_sources,
)
from pipeline.clean_text import OCR_FIXES, apply_ocr_fixes  # noqa: E402
from pipeline.parse_lessons import (  # noqa: E402
    CHAPTER_OPEN_RE, LESSON_ID_RE, to_int,
)


def check(name, cond):
    if not cond:
        raise AssertionError(name)
    print(f'  PASS {name}')


def test_metrics():
    metas = [
        {'page': 5, 'page_start': 5, 'page_end': 6},
        {'page': 9, 'page_start': 9, 'page_end': 9},
    ]
    check('page range hit (p6 inside 5-6)', is_page_hit(metas[0], [6]))
    check('page range miss (p7 outside)', not is_page_hit(metas[0], [7]))
    m = at_k_metrics(metas, [6])
    check('hit@1/mrr for first-page hit', m['hit1'] and m['mrr'] == 1.0)
    m2 = at_k_metrics(metas, [9])
    check('hit@3 not hit@1', m2['hit3'] and not m2['hit1'] and m2['mrr'] == 0.5)
    check('mean empty is None', mean([]) is None)


def test_query_path():
    check('strip marker I.', strip_lead_markers('I. តើអ្វី?') == 'តើអ្វី?')
    check('app and eval share one splitter', split_questions is app_split_questions)
    parts = split_questions('I. តើ A? II. តើ B?')
    check('split I./II. into 2', len(parts) == 2)
    qs = prepare_queries('I. តើណឺរ៉ូនមានប្រភេទអ្វីខ្លះ? II. តើអាំងភ្លុចប្រសាទធ្វើដំណើរយ៉ាងដូចម្តេច?')
    check('prepare_queries splits multi-part', len(qs) == 2)
    check('prepare_queries keeps question text', 'អាំងភ្លុច' in qs[1])

    khmer = split_questions('ក. តើ ADN ជាអ្វី? ខ. តើ ARN មានប៉ុន្មានប្រភេទ?')
    check('split Khmer ក./ខ. into 2', len(khmer) == 2)
    check('Khmer parts drop markers', khmer == ['តើ ADN ជាអ្វី?', 'តើ ARN មានប៉ុន្មានប្រភេទ?'])
    five = split_questions('ក. A? ខ. B? គ. C? ឃ. D? ង. E?')
    check('split Khmer five-marker series', five == ['A?', 'B?', 'C?', 'D?', 'E?'])
    check('single Khmer marker is not a split',
          split_questions('ក. តើ ADN ជាអ្វី?') == ['តើ ADN ជាអ្វី?'])
    check('non-consecutive Khmer markers are not split',
          len(split_questions('ក. A? គ. C?')) == 1)
    check('Khmer markers after ? without spaces split',
          split_questions('ក. A?ខ. B?') == ['A?', 'B?'])
    mixed = split_questions('I. ក. A? ខ. B? II. C?')
    check('mixed Roman + Khmer split', mixed == ['A?', 'B?', 'C?'])

    q115 = prepare_queries('ក. តើ ADN ជាអ្វី? ខ. តើ ARN មានប៉ុន្មានប្រភេទ?')
    check('prepare_queries splits Khmer multi-part', len(q115) == 2)
    check('prepare_queries keeps both Khmer questions',
          'ADN' in q115[0] and 'ARN' in q115[1])
    check('gene alias ហ្សែន -> សែន', normalize_query('ហ្សែន') == 'សែន')
    check('gene alias inside a question',
          normalize_query('តើហ្សែនជាអ្វី?') == 'តើសែនជាអ្វី?')

    q55 = expand_query('ចូរពន្យល់ពីដំណើរការលំអងរបស់ស្រល់')
    check('pine question gains gymnosperm/cone terms',
          'ស៊ីមណូស្ពែម' in q55 and 'កោន' in q55)
    check('pine expansion keeps the original wording',
          q55.startswith('ចូរពន្យល់ពីដំណើរការលំអងរបស់ស្រល់'))
    check('pine expansion is idempotent', expand_query(q55) == q55)
    check('unrelated query is not expanded',
          expand_query('តើ ADN ជាអ្វី?') == 'តើ ADN ជាអ្វី?')

    q56 = expand_query('តើអង្ករសំរូបដែលយើងបរិភោគជាផ្នែកណារបស់រុក្ខជាតិ?')
    check('rice question gains seed/albumen/endosperm terms',
          all(t in q56 for t in ('គ្រាប់ស្រូវ', 'អាល់ប៊ុយមែន', 'អង់ដូស្ពែម')))
    check('rice expansion keeps the original wording',
          q56.startswith('តើអង្ករសំរូបដែលយើងបរិភោគ'))
    check('rice expansion is idempotent', expand_query(q56) == q56)


def test_gold_parts():
    shared = {'expected_source_pages': [10, 11]}
    check('shared gold used for single-part question',
          expected_pages_for_part(shared, 0) == [10, 11])
    per_part = {
        'expected_source_pages': [10, 11],
        'expected_source_pages_by_part': [[10], [11, 12]],
    }
    check('part 0 uses its own gold', expected_pages_for_part(per_part, 0) == [10])
    check('part 1 uses its own gold', expected_pages_for_part(per_part, 1) == [11, 12])
    check('missing part falls back to shared gold',
          expected_pages_for_part(per_part, 2) == [10, 11])
    check('whole-question gold is the union',
          expected_pages_for_question(per_part) == [10, 11, 12])


def test_parser_headers():
    thai_n = '\u0e19'
    content = f'ជំពូកទី២ មេរៀ{thai_n}ទី1 ការលូតលាស់ផ្នែកទឹក'
    m = LESSON_ID_RE.search(content)
    check('Thai น lesson header parsed', m is not None and to_int(m.group(2)) == 1)
    check('Thai lesson header is not a chapter opening',
          not CHAPTER_OPEN_RE.match(content))
    khmer = 'ជំពូកទី២ មេរៀនទី2 កំណប់រំញោច'
    check('Khmer lesson header still parses',
          LESSON_ID_RE.search(khmer).group(2) == '2')
    check('Khmer lesson header is not a chapter opening',
          not CHAPTER_OPEN_RE.match(khmer))
    chapter_open = 'ជំពូក 2 ការលូតលាស់និងតំណប់រំញោចរុក្ខជាតិ'
    check('real chapter opening still detected',
          CHAPTER_OPEN_RE.match(chapter_open) is not None)


def test_gold():
    gold = load_gold()
    by_id = {q['question_id']: q for q in gold}
    check('gold size 119', len(gold) == 119)
    check('gold ids unique', len(by_id) == len(gold))
    check('in-scope 110', sum(1 for q in gold if not q.get('expect_abstain')) == 110)
    check('abstain 9', sum(1 for q in gold if q.get('expect_abstain')) == 9)
    check('all chapters present', {q['chapter'] for q in gold} >= {1, 2, 3, 4, 5, 6, 7, 8})
    check('q105 reclassified in-scope ch5', by_id[105]['chapter'] == 5
          and not by_id[105]['expect_abstain']
          and by_id[105]['expected_source_pages'] == [186])
    check('q111 still expects correct adaptation term',
          by_id[111]['expected_concepts'][0] == 'បន្ស៊ាំ')
    check('q111 labels still require the definition pages',
          by_id[111]['expected_source_pages'] == [202, 203])
    check('q23 replication includes mechanism pages',
          by_id[23]['expected_source_pages'] == [157, 158, 159])
    check('q109 stigma includes definition page 15',
          by_id[109]['expected_source_pages'] == [15, 16, 17])
    check('q119 adds peptide-bond definition page 126',
          by_id[119]['expected_source_pages'] == [122, 126, 127])
    check('q53 compares gymnosperm/angiosperm seed pages',
          by_id[53]['expected_source_pages'] == [6, 12])
    check('q62 uses nerve-transmission pages',
          by_id[62]['expected_source_pages'] == [65, 70])
    check('q69 uses nucleotide-definition pages',
          by_id[69]['expected_source_pages'] == [153, 154, 156])
    check('q83 uses food-chain definition page',
          by_id[83]['expected_source_pages'] == [247])
    check('q89 uses nervous-system summary page',
          by_id[89]['expected_source_pages'] == [77])


def test_ocr_sync():
    audit_pairs = [
        ('ស្ទីចម៉ាត', 'ស្ទិចម៉ាត'),
        ('ស្អិតម៉ាស', 'ស្ទិចម៉ាត'),
        ('បន្សុំ', 'បន្ស៊ាំ'),
        ('លក្ខណៈ បន្សំ', 'លក្ខណៈបន្ស៊ាំ'),
        ('ជំងឺហមារីក', 'ជំងឺមហារីក'),
    ]
    for pair in audit_pairs:
        check(f'OCR/query sync {pair[0]}', pair in OCR_FIXES and pair in QUERY_FIXES)
    for text in ('ស្ទីចម៉ាត', 'ស្អិតម៉ាស', 'បន្សុំ',
                 'លក្ខណៈ បន្សំ', 'ជំងឺហមារីក'):
        check(f'corpus and query normalize {text}',
              normalize_query(text) == apply_ocr_fixes(text) != text)
    check('adaptation plain form fixed', 'បន្ស៊ាំ' in normalize_query('លក្ខណៈបន្សំ'))
    check('legitimate combination បន្សំ preserved (new DNA)',
          'បន្សំ' in apply_ocr_fixes('ADN បន្សំថ្មី'))
    check('legitimate combination បន្សំ preserved (nucleotide)',
          'បន្សំ' in apply_ocr_fixes('បន្សំនុយក្លេអូទីត'))
    check('legitimate combination បន្សំ preserved in queries',
          normalize_query('ADN បន្សំថ្មី') == 'ADN បន្សំថ្មី')


def test_strip_sources():
    p1 = 'A\n\n━━━━━━━━━━━━━━━━━━\n📚 **ប្រភព (Sources)**\nទំព័រ 1'
    p2 = '**2. តើ B?**\n\nB\n\n━━━━━━━━━━━━━━━━━━\n📚 **ប្រភព (Sources)**\nទំព័រ 2'
    body = strip_sources(f'**1. តើ A?**\n\n{p1}\n\n---\n\n{p2}')
    check('multi-part body keeps part II', 'B' in body)
    check('multi-part body drops both footers', '📚' not in body and '━━━' not in body)
    check('failure text not mistaken for footer',
          strip_sources('[GEN_FAILED: quota]') == '[GEN_FAILED: quota]')


def test_concepts():
    check('peptide-bond spelling alias',
          concept_present('ចំណងប៉ុបទីត', normalize_match('ចំណងប៉បទីត')))
    check('fossil synonym', concept_present('សំណល់', normalize_match('ផូស៊ីល')))
    check('evolution variant', concept_present('វិវត្តន៍', normalize_match('ការវិវត្ត')))
    check('latex RNA_m', concept_present('ARNm', normalize_match('$\\text{ARN}_{\\text{m}}$')))
    check('stale adaptation form rejected',
          not concept_present('បន្ស៊ាំ', normalize_match('លក្ខណៈបន្សំ')))


def test_scores():
    failed = {'answer': '[GEN_FAILED: quota]', 'expect_abstain': False,
              'expected_concepts': ['x'], 'expected_pages': [1],
              'retrieved_pages': [1], 'question_type': 'definition'}
    check('generation failure = 1 on every dimension',
          set(score_answer(failed)[d] for d in
              ('correctness', 'completeness', 'faithfulness', 'clarity',
               'terminology', 'citation', 'helpfulness')) == {1})
    fallback = dict(failed, answer=GENERATION_FALLBACK_MESSAGE)
    fb_scores = score_answer(fallback)
    check('friendly fallback is scored as a generation failure',
          fb_scores['correctness'] == 1 and fb_scores.get('gen_fallback') is True)
    abstained = {'answer': 'សូមទោស! មិនបានរកឃើញព័ត៌មានគ្រប់គ្រាន់',
                 'expect_abstain': True, 'abstained': True,
                 'expected_concepts': [], 'expected_pages': [],
                 'retrieved_pages': [], 'question_type': 'out_of_scope'}
    check('correct abstention = 5s', score_answer(abstained)['correctness'] == 5)


def main():
    test_metrics()
    test_query_path()
    test_parser_headers()
    test_gold_parts()
    test_gold()
    test_ocr_sync()
    test_strip_sources()
    test_concepts()
    test_scores()
    print('\nALL EVAL-HARNESS TESTS PASSED')


if __name__ == '__main__':
    main()
