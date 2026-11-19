"""Build the v2 gold evaluation set without touching the v1 source of truth.

v2 = all 97 v1 questions (unchanged) + special cases required by the
evaluation spec:
  - out_of_scope  : answerable only by guessing outside the textbook
  - ocr_garbled   : in-scope questions written with known OCR corruptions
  - multi_part    : exam-style I./II. or ក./ខ. multi-question prompts

Output: data/evaluation/gold_questions_v2.json
Usage:  python scripts/build_gold_v2.py
"""

import copy
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(BASE, 'data', 'evaluation', 'evaluation_questions.json')
OUT = os.path.join(BASE, 'data', 'evaluation', 'gold_questions_v2.json')
CHANGELOG = os.path.join(BASE, 'data', 'evaluation', 'gold_label_changes_v3.json')

SPECIALS = [
    # --- Out of scope: must abstain (no textbook support) ---
    dict(question_kh='តើព្រះអាទិត្យមានអាយុប៉ុន្មានឆ្នាំ?', chapter=0,
         question_type='out_of_scope', difficulty='easy',
         expected_concepts=[], expected_source_pages=[], expect_abstain=True,
         expected_answer='', notes='Astronomy; not in the Grade 12 biology textbook.'),
    dict(question_kh='តើរដ្ឋធានីនៃប្រទេសជប៉ុនមានឈ្មោះអ្វី?', chapter=0,
         question_type='out_of_scope', difficulty='easy',
         expected_concepts=[], expected_source_pages=[], expect_abstain=True,
         expected_answer='', notes='Geography; not in the textbook.'),
    dict(question_kh='តើរូបមន្តគីមីនៃទឹកគឺជាអ្វី?', chapter=0,
         question_type='out_of_scope', difficulty='easy',
         expected_concepts=[], expected_source_pages=[], expect_abstain=True,
         expected_answer='', notes='Chemistry formula; a hard negative because "ទឹក" appears in plant chapters.'),
    dict(question_kh='តើភាសាផ្លូវការរបស់ប្រទេសបារាំងគឺជាអ្វី?', chapter=0,
         question_type='out_of_scope', difficulty='easy',
         expected_concepts=[], expected_source_pages=[], expect_abstain=True,
         expected_answer='', notes='Language/geography; not in the textbook.'),
    dict(question_kh='តើធ្វើដូចម្តេចដើម្បីដំឡើងកម្មវិធីកុំព្យូទ័រ Windows?', chapter=0,
         question_type='out_of_scope', difficulty='easy',
         expected_concepts=[], expected_source_pages=[], expect_abstain=True,
         expected_answer='', notes='IT support; not in the textbook.'),
    dict(question_kh='តើអ្នកណាឈ្នះពានរង្វាន់បាល់ទាត់ពិភពលោកឆ្នាំ ២០២២?', chapter=0,
         question_type='out_of_scope', difficulty='easy',
         expected_concepts=[], expected_source_pages=[], expect_abstain=True,
         expected_answer='', notes='Sports; not in the textbook.'),
    dict(question_kh='តើប្រទេសកម្ពុជាមានខេត្តប៉ុន្មាន?', chapter=0,
         question_type='out_of_scope', difficulty='easy',
         expected_concepts=[], expected_source_pages=[], expect_abstain=True,
         expected_answer='', notes='Geography; not in the textbook.'),
    # Reclassified after audit: p186 explicitly says interferon and
    # interleukin are used to treat cancer (OCR: ជំងឺហមារីក). Kept at id 105
    # so existing result files stay aligned.
    dict(question_kh='តើថ្នាំអ្វីប្រើសម្រាប់ព្យាបាលជំងឺមហារីក?', chapter=5,
         question_type='explanation', difficulty='medium',
         expected_concepts=['អាំងទែរផេរ៉ុង', 'អាំងទែរឡូគីន'],
         expected_source_pages=[186], expect_abstain=False,
         expected_answer='', notes='Textbook p186: interferon and interleukin are used to treat cancer; not out of scope.'),
    dict(question_kh='តើសហគមន៍អឺរ៉ុបបង្កើតឡើងនៅឆ្នាំណា?', chapter=0,
         question_type='out_of_scope', difficulty='easy',
         expected_concepts=[], expected_source_pages=[], expect_abstain=True,
         expected_answer='', notes='History/politics; not in the textbook.'),
    dict(question_kh='តើរថយន្តម៉ូដែលណាល្អបំផុតក្នុងឆ្នាំ ២០២៦?', chapter=0,
         question_type='out_of_scope', difficulty='easy',
         expected_concepts=[], expected_source_pages=[], expect_abstain=True,
         expected_answer='', notes='Consumer advice; not in the textbook.'),

    # --- OCR-garbled in-scope questions (must still answer correctly) ---
    dict(question_kh='តើស្ទីចម៉ាតជាអ្វី?', chapter=1,
         question_type='ocr_garbled', difficulty='easy',
         expected_concepts=['ស្ទិចម៉ាត', 'លំអង'],
         expected_source_pages=[15, 17, 18], expect_abstain=False,
         expected_answer='', notes='Corruption ស្ទីចម៉ាត -> ស្ទិចម៉ាត; stigma part of the pistil that receives pollen.'),
    dict(question_kh='តើស្អិតម៉ាសមាននាទីអ្វី?', chapter=1,
         question_type='ocr_garbled', difficulty='easy',
         expected_concepts=['ស្ទិចម៉ាត', 'គ្រាប់លំអង'],
         expected_source_pages=[16, 17], expect_abstain=False,
         expected_answer='', notes='Corruption ស្អិតម៉ាស -> ស្ទិចម៉ាត; receives pollen grains.'),
    dict(question_kh='តើរលកសូមាននាទីអ្វី?', chapter=3,
         question_type='ocr_garbled', difficulty='medium',
         expected_concepts=['រលកសូរ', 'ត្រចៀក'],
         expected_source_pages=[87, 89], expect_abstain=False,
         expected_answer='', notes='Corruption រលកសូ -> រលកសូរ; sound waves reach the inner ear.'),
    dict(question_kh='តើលក្ខណៈបន្សំសំដៅលើអ្វី?', chapter=6,
         question_type='ocr_garbled', difficulty='medium',
         expected_concepts=['បន្ស៊ាំ', 'ជម្រើសដោយធម្មជាតិ'],
         expected_source_pages=[202, 203], expect_abstain=False,
         expected_answer='', notes='Corruption បន្សំ -> បន្ស៊ាំ; adaptation under natural selection.'),
    dict(question_kh='តើសត្វរ៉ាពមានលក្ខណៈបន្សំអ្វី?', chapter=6,
         question_type='ocr_garbled', difficulty='hard',
         expected_concepts=['ប្រេដាទ័រ', 'បន្ស៊ាំ'],
         expected_source_pages=[239], expect_abstain=False,
         expected_answer='', notes='Corruption សត្វរ៉ាព -> ប្រេដាទ័រ (predator); adaptations for catching prey.'),
    dict(question_kh='តើណឺរ៉ូនពហុប្ដួលជាអ្វី?', chapter=3,
         question_type='ocr_garbled', difficulty='medium',
         expected_concepts=['ណឺរ៉ូន', 'ពហុប៉ូល'],
         expected_source_pages=[67, 68], expect_abstain=False,
         expected_answer='', notes='Corruption ពហុប្ដួល -> ពហុប៉ូល; multipolar neuron anatomy.'),

    # --- Multi-part exam-style prompts (top-level I./II. and ក./ខ.) ---
    dict(question_kh='I. តើណឺរ៉ូនមានប្រភេទអ្វីខ្លះ? II. តើអាំងភ្លុចប្រសាទធ្វើដំណើរយ៉ាងដូចម្តេច?', chapter=3,
         question_type='multi_part', difficulty='medium',
         expected_concepts=['ណឺរ៉ូន', 'អាំងភ្លុចប្រសាទ', 'អាក់សូន'],
         expected_source_pages=[68, 69, 70], expect_abstain=False,
         expected_answer='', notes='Two top-level roman-numeral questions; marker stripping must not cause abstain.'),
    dict(question_kh='ក. តើ ADN ជាអ្វី? ខ. តើ ARN មានប៉ុន្មានប្រភេទ?', chapter=5,
         question_type='multi_part', difficulty='medium',
         expected_concepts=['ADN', 'ARN', 'ARNm'],
         expected_source_pages=[150, 165], expect_abstain=False,
         expected_answer='', notes='Khmer sub-question markers ក./ខ.; both parts must be answered.'),
    dict(question_kh='I. តើរុក្ខជាតិស្រូបទឹកដោយរបៀបណា? II. តើទឹកឡើងដល់ស្លឹកដោយរបៀបណា?', chapter=2,
         question_type='multi_part', difficulty='hard',
         expected_concepts=['ស្រូបទឹក', 'ស៊ីឡែម', 'ភាយចំហាយទឹក'],
         expected_source_pages=[26, 28, 40], expect_abstain=False,
         expected_answer='', notes='Multi-part water absorption + ascent; needs both process descriptions.'),
    dict(question_kh='I. តើខ្សែអាហារជាអ្វី? II. តើថាមពលហូរកាត់ខ្សែអាហារយ៉ាងដូចម្តេច?', chapter=8,
         question_type='multi_part', difficulty='medium',
         expected_concepts=['ខ្សែអាហារ', 'ថាមពល', 'អ្នកផលិត'],
         expected_source_pages=[246, 248, 249], expect_abstain=False,
         expected_answer='', notes='Definition + energy flow in one exam-style prompt.'),
    dict(question_kh='I. តើស៊ីមណូស្ពែមជាអ្វី? II. តើអង់ស្យូស្ពែមជាអ្វី?', chapter=1,
         question_type='multi_part', difficulty='medium',
         expected_concepts=['ស៊ីមណូស្ពែម', 'អង់ស្យូស្ពែម', 'គ្រាប់'],
         expected_source_pages=[6, 12], expect_abstain=False,
         expected_answer='', notes='Two definitions in one prompt, each needs its own retrieval.'),
    dict(question_kh='I. តើប្រូតេអ៊ីនបង្កើតពីអ្វី? II. តើចំណងប៉ុបទីតជាអ្វី?', chapter=4,
         question_type='multi_part', difficulty='medium',
         expected_concepts=['អាស៊ីតអាមីណេ', 'ចំណងប៉ុបទីត'],
         expected_source_pages=[122, 127, 130], expect_abstain=False,
         expected_answer='', notes='Protein building blocks + peptide bond.'),
]


# Page-label audit (v3). Each entry records the old labels, the corrected
# labels, the textbook evidence, and why the old label was wrong/incomplete.
# Applied after the v1+specials merge, so question ids stay stable.
GOLD_LABEL_CORRECTIONS = [
    dict(
        question_id=23,
        old_pages=[159],
        new_pages=[157, 158, 159],
        evidence=('p157: "3.2. ស្វ័យដំឡើងទ្វេ ADN" explains the semi-conservative '
                  'mechanism; p158 continues with prokaryote replication; '
                  'p159: "គ. ដំណើរទ្វេ ADN ក្នុងអ៊ូកាយ៉ូត" covers eukaryotes.'),
        reason='The question asks for the replication process, not only its role; '
               'p159 alone omits the mechanism on p157-158.',
    ),
    dict(
        question_id=109,
        old_pages=[16, 17],
        new_pages=[15, 16, 17],
        evidence=('p15 explicitly defines "ស្ទិចម៉ាត" as the sticky stigma that receives '
                  'pollen grains; p16-17 use OCR variants in pollination/fertilization context.'),
        reason='The canonical definition and role are on p15; retaining 16-17 preserves '
               'the applied context.',
    ),
    dict(
        question_id=119,
        old_pages=[122, 127, 130],
        new_pages=[122, 126, 127],
        evidence=('p122 introduces amino acids/peptide bonds; p126 defines '
                  '"ចំណងប៉ិបទីត" (peptide bond); p127 states the basic component of '
                  'protein is amino acids. p130 covers protein roles, not either answer.'),
        reason='Add the actual peptide-bond definition (p126); replace p130, which does '
               'not answer either sub-question.',
    ),
    dict(
        question_id=53,
        old_pages=[196, 197, 209],
        new_pages=[6, 12],
        evidence=('p6 defines gymnosperm seeds as naked seeds without a protective '
                  'outer coat; p12 states that angiosperm seeds are protected by the '
                  'fruit/shell. The old pages 196, 197 and 209 are in chapters 6-7 and '
                  'do not discuss gymnosperm/angiosperm seeds.'),
        reason='The old labels are from unrelated later chapters; replace them with the '
               'chapter 1 pages that directly compare the two seed types.',
    ),
    dict(
        question_id=62,
        old_pages=[60],
        new_pages=[65, 70],
        evidence=('p65 explains that information travels along nerve fibres carrying '
                  'electrical signals to the body; p70 explains neurotransmitter '
                  'transmission across the synapse. p60 is the lesson overview and '
                  'objectives, not the transmission mechanism.'),
        reason='Use the pages that actually describe nerve-impulse transmission; p60 '
               'alone only introduces the nervous-system lesson.',
    ),
    dict(
        question_id=69,
        old_pages=[165],
        new_pages=[153, 154, 156],
        evidence=('p153 defines a nucleotide as the repeating unit of DNA and lists its '
                  'three components (deoxyribose, phosphate, nitrogenous base); p154 '
                  'describes the four nucleotide types; p156 explains base pairing in '
                  'the DNA double helix. p165 is the ARN lesson and does not define a '
                  'nucleotide.'),
        reason='The old label pointed to the wrong molecule/lesson; replace it with the '
               'nucleotide-composition and DNA-structure pages.',
    ),
    dict(
        question_id=83,
        old_pages=[246],
        new_pages=[247],
        evidence=('p247 explicitly defines "ខ្សែអាហារ" as the sequential feeding '
                  'relationship through which organisms obtain energy. p246 contains '
                  'the lesson objectives and introduction, not the definition.'),
        reason='The direct definition is on p247, not the chapter-opening page.',
    ),
    dict(
        question_id=89,
        old_pages=[246, 247, 248, 256],
        new_pages=[77],
        evidence=('p77 is the chapter 3 lesson summary describing how nervous systems '
                  'and nerve networks coordinate responses. The old pages 246-248 and '
                  '256 are chapter 8 food-chain/energy pages and do not discuss the '
                  'nervous system.'),
        reason='Replace the unrelated chapter 8 labels with the chapter 3 summary page '
               'that directly answers the question.',
    ),
]


def apply_gold_label_corrections(gold):
    changes = []
    by_id = {q['question_id']: q for q in gold}
    for fix in GOLD_LABEL_CORRECTIONS:
        item = by_id[fix['question_id']]
        if item['expected_source_pages'] != fix['old_pages']:
            raise AssertionError(
                f"q{fix['question_id']} has {item['expected_source_pages']}, "
                f"expected pre-correction {fix['old_pages']}"
            )
        item['expected_source_pages'] = list(fix['new_pages'])
        note = (f"Page-label audit v3: {fix['old_pages']} -> {fix['new_pages']}. "
                f"{fix['evidence']} Reason: {fix['reason']}")
        item['notes'] = (item.get('notes') + ' ' + note).strip()
        changes.append({
            'question_id': fix['question_id'],
            'old_pages': fix['old_pages'],
            'new_pages': fix['new_pages'],
            'evidence': fix['evidence'],
            'reason': fix['reason'],
        })
    return changes


def main():
    with open(SRC, 'r', encoding='utf-8') as f:
        v1 = json.load(f)

    gold = []
    for q in v1:
        item = copy.deepcopy(q)
        item['expect_abstain'] = False
        item['source'] = 'v1'
        item.setdefault('notes', '')
        gold.append(item)

    next_id = max(q['question_id'] for q in gold) + 1
    for spec in SPECIALS:
        item = {'question_id': next_id, 'source': 'special'}
        item.update(spec)
        gold.append(item)
        next_id += 1

    changes = apply_gold_label_corrections(gold)

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(gold, f, ensure_ascii=False, indent=1)
    with open(CHANGELOG, 'w', encoding='utf-8') as f:
        json.dump(changes, f, ensure_ascii=False, indent=1)

    from collections import Counter
    ch = Counter(q['chapter'] for q in gold if q['chapter'])
    types = Counter(q['question_type'] for q in gold)
    print(f'wrote {len(gold)} questions -> {OUT}')
    print('chapters:', dict(sorted(ch.items())))
    print('special types:', {k: v for k, v in types.items()
                             if k in ('out_of_scope', 'ocr_garbled', 'multi_part')})
    print('in-scope:', sum(1 for q in gold if not q['expect_abstain']),
          '| expect_abstain:', sum(1 for q in gold if q['expect_abstain']))
    print('page-label corrections:', [(c['question_id'], c['old_pages'], c['new_pages'])
                                      for c in changes])


if __name__ == '__main__':
    sys.exit(main())
