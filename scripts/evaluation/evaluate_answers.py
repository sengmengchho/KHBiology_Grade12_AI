"""End-to-end answer evaluation (v2) with a 7-dimension 1-5 rubric.

Runs the real pipeline for each sampled question:
  normalize/split/expand -> retrieve -> rerank_with_context -> abstain check
  -> generate_answer -> format_answer

Dimensions (1-5):
  correctness, completeness, faithfulness, clarity, terminology, citation,
  helpfulness

Scores are transparent automated proxies (documented in docs/). They are not a
substitute for teacher review; answer_review_v2.csv provides blank columns for
manual overrides.

Outputs (new files):
  data/evaluation/answer_evaluations_v2.json
  data/evaluation/answer_evaluation_v2_summary.txt
  data/evaluation/answer_review_v2.csv

Usage:
  python -m scripts.evaluation.evaluate_answers [--questions 1,8,24] [--fresh]
                                                 [--max N] [--score-only] [--tag v3]
"""

import argparse
import csv
import json
import os
import re
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, SCRIPTS)

from app.config import RETRIEVAL_SCORE_THRESHOLD, NOT_FOUND_MESSAGE  # noqa: E402
from app.prompt import (  # noqa: E402
    allowed_pages_from_sources, format_answer, is_context_source,
    page_range_label, parse_page_citations, source_page_ranges,
)
from app.rag import generate_answer  # noqa: E402
from app.retrieval import (  # noqa: E402
    get_embedding_model, get_vector_db, get_reranker,
    retrieve, rerank_with_context,
)
from app.rag import GENERATION_FALLBACK_MESSAGE  # noqa: E402
from evaluation.common import (  # noqa: E402
    expected_pages_for_question, load_gold, prepare_queries,
)

OUT = os.path.join(BASE, 'data', 'evaluation', 'answer_evaluations_v2.json')
SUMMARY = os.path.join(BASE, 'data', 'evaluation', 'answer_evaluation_v2_summary.txt')
REVIEW = os.path.join(BASE, 'data', 'evaluation', 'answer_review_v2.csv')
TAG = 'v2'

DEFAULT_IDS = [1, 2, 108, 8, 58, 13, 114, 16, 19, 20, 24, 115,
               26, 111, 30, 71, 34, 47, 100, 105]

DIMENSIONS = ['correctness', 'completeness', 'faithfulness', 'clarity',
              'terminology', 'citation', 'helpfulness']

BANNED_TERMS = [
    'ស្ទីចម៉ាត', 'ស្អិតម៉ាស', 'អរុស្បល', 'ល៉ែយ៉ូ', 'ជង់កិល',
    'ស្ដែម៉ាតូស្យីត', 'អូអូម៉ូស្យូប៊ោកតី', 'សត្វរ៉ាព', 'រលកសូររ',
]
KH_DIGITS = str.maketrans('០១២៣៤៥៦៧៨៩', '0123456789')

# Accepted spelling/synonym variants for gold concepts. Deliberately explicit:
# do NOT strip Khmer diacritics globally, because that would make the stale
# form បន្សំ match the correct បន្ស៊ាំ (q111 must keep failing).
CONCEPT_ALIASES = {
    'gymnosperm': ['gymnosperm', 'ស៊ីមណូស្ពែម'],
    'សំណល់': ['សំណល់', 'ផូស៊ីល', 'ហ្វូស៊ីល'],
    'វិវត្តន៍': ['វិវត្តន៍', 'វិវត្ត'],
    'ចំណងប៉ុបទីត': ['ចំណងប៉ុបទីត', 'ចំណងប៉ិបទីត', 'ចំណងប៉បទីត'],
    'ជម្រើសដោយធម្មជាតិ': ['ជម្រើសដោយធម្មជាតិ', 'ជម្រើសធម្មជាតិ'],
    'ARNm': ['ARNm', 'ARN នាំសារ'],
}

SCORING_MODES = ('strict', 'alias_aware')

# Alias-aware-only rules. These are evaluated only after strict matching has
# failed. Each occurrence must have at least one of ``context_any`` within
# ``window`` characters on either side; occurrences containing ``reject_any``
# in the same window are ignored. This keeps ambiguous words (e.g. នាទី,
# បន្លំ) from becoming unrestricted global substring aliases.
CONTEXTUAL_ALIASES = {
    'ហ្សែន': [{
        'alias': 'សែន',
        'context_any': ('ADN', 'ព័ត៌មានសេនេទិច', 'នុយក្លេអូទីត',
                        'ក្រូម៉ូសូម', 'កំណត់លក្ខណៈ', 'សំយោគប្រូតេអ៊ីន'),
        'window': 120,
    }],
    'ស្រូបទឹក': [{
        'alias': 'ស្រូបយកទឹក',
        'context_any': ('ឫស', 'រុក្ខជាតិ', 'ដី', 'រោមជញ្ជក់',
                        'ស៊ីឡែម', 'សរសៃនាំ'),
        'window': 100,
    }],
    'ដូអែម': [{
        'alias': 'ផ្លូអែម',
        'context_any': ('អាហារ', 'សារធាតុសរីរាង្គ', 'សំយោគ',
                        'ស្ករ', 'កាបូអ៊ីដ្រាត'),
        'window': 100,
    }],
    'តួនាទី': [{
        'alias': 'នាទី',
        'context_any': ('ប្រូតេអ៊ីន',),
        'window': 100,
    }],
    'បន្ស៊ាំ': [
        {
            'alias': 'បន្លាំ',
            'context_any': ('សម្របប្រួល', 'មជ្ឈដ្ឋាន', 'រស់រាន',
                            'កូនចៅ', 'ជំនាន់', 'ភាវៈរស់', 'វិវត្តន៍'),
            'reject_any': ('ឯកសារ', 'ហត្ថលេខា', 'ក្លែងក្លាយ',
                           'ទំនិញ', 'ផលិតផល', 'គ្រាប់រុក្ខជាតិ', 'សិទ្ធិ'),
            'window': 100,
        },
        {
            'alias': 'បន្លំ',
            'context_any': ('សម្របប្រួល', 'មជ្ឈដ្ឋាន', 'រស់រាន',
                            'កូនចៅ', 'ជំនាន់', 'ភាវៈរស់', 'វិវត្តន៍'),
            'reject_any': ('ឯកសារ', 'ហត្ថលេខា', 'ក្លែងក្លាយ',
                           'ទំនិញ', 'ផលិតផល', 'គ្រាប់រុក្ខជាតិ', 'សិទ្ធិ'),
            'window': 100,
        },
    ],
    'ទ្រនុងបែកខ្នែង': [{
        'alias': 'ទ្រនុងបែកមែក',
        'context_any': ('ស្លឹក', 'ឌីកូទីលេដូន', 'សរសៃនាំ'),
        'window': 80,
    }],
}


def _alias_present(alias: str, body_l: str, rule: dict) -> bool:
    """True when an alias occurrence has the required local context."""
    alias_l = normalize_match(alias)
    context = [normalize_match(c) for c in rule.get('context_any', ())]
    reject = [normalize_match(c) for c in rule.get('reject_any', ())]
    window = int(rule.get('window', 100))
    start = body_l.find(alias_l)
    while start != -1:
        end = start + len(alias_l)
        local = body_l[max(0, start - window):min(len(body_l), end + window)]
        if not any(r in local for r in reject):
            if not context or any(c in local for c in context):
                return True
        start = body_l.find(alias_l, start + 1)
    return False


def concept_present(concept: str, body_l: str, mode: str = 'strict') -> bool:
    if mode not in SCORING_MODES:
        raise ValueError(f'Unknown scoring mode: {mode}')
    variants = CONCEPT_ALIASES.get(concept, [concept])
    if any(normalize_match(v) in body_l for v in variants):
        return True
    if mode == 'strict':
        return False
    return any(_alias_present(rule['alias'], body_l, rule)
               for rule in CONTEXTUAL_ALIASES.get(concept, []))


def matched_concepts(rec: dict, mode: str = 'strict') -> list[str]:
    """Return the expected concepts found in the answer body."""
    body_l = normalize_match(strip_sources(rec.get('answer', '')))
    return [c for c in rec.get('expected_concepts', [])
            if c and concept_present(c, body_l, mode)]


def alias_matches(rec: dict) -> list[dict]:
    """Describe concepts that alias-aware mode found but strict mode did not."""
    body_l = normalize_match(strip_sources(rec.get('answer', '')))
    out = []
    for concept in rec.get('expected_concepts', []):
        if not concept or concept_present(concept, body_l, 'strict'):
            continue
        for rule in CONTEXTUAL_ALIASES.get(concept, []):
            if _alias_present(rule['alias'], body_l, rule):
                out.append({'concept': concept, 'alias': rule['alias']})
                break
    return out


def strip_sources(answer: str) -> str:
    """Remove every per-part source footer, keeping all multi-part answers.

    A footer starts at the heavy rule and ends at the next numbered part
    (``**2.``) or at the end of the answer. Splitting only on the first rule
    would hide part II of a multi-part answer from the scorer.
    """
    cleaned = re.sub(r'\n\s*━{3,}[\s\S]*?(?=\n\*\*\d+\.|\Z)', '\n', answer)
    return cleaned.strip()


def normalize_match(text: str) -> str:
    """Fold LaTeX wrappers so e.g. $\\text{ARN}_{\\text{m}}$ matches ARNm."""
    t = text.lower().replace('$', '').replace('\\text', '').replace('\\mathrm', '')
    return t.replace('{', '').replace('}', '').replace('_', '')


def cite_pages(answer: str) -> list[int]:
    """Expand every page/range in every citation group, including lists."""
    out = set()
    for lo, hi in parse_page_citations(answer):
        out.update(range(lo, hi + 1))
    return sorted(out)


def numbers(text: str) -> list[str]:
    t = text.translate(KH_DIGITS)
    return re.findall(r'\d+(?:[.,]\d+)?', t)


def clamp(v: float) -> int:
    return max(1, min(5, int(round(v))))


def score_answer(rec: dict, mode: str = 'strict') -> dict:
    if mode not in SCORING_MODES:
        raise ValueError(f'Unknown scoring mode: {mode}')
    body = strip_sources(rec.get('answer', ''))
    context = rec.get('context', '')
    expected_concepts = [c for c in rec.get('expected_concepts', []) if c]
    expected_pages = rec.get('expected_pages', [])
    retrieved_pages = rec.get('retrieved_pages', [])
    abstained = rec.get('abstained', False)
    expect_abstain = rec.get('expect_abstain', False)
    footer = 'មិនបានរកឃើញព័ត៌មានគ្រប់គ្រាន់' in body

    if body.startswith(('[GEN_FAILED', '[GEN_EMPTY', '[FAILED')) \
            or body.startswith(GENERATION_FALLBACK_MESSAGE):
        return {d: 1 for d in DIMENSIONS} | {
            'concept_coverage': 0.0, 'grounded_number_ratio': None,
            'banned_terms': [], 'cited_pages': [], 'valid_citations': [],
            'gen_fallback': body.startswith(GENERATION_FALLBACK_MESSAGE),
        }

    if expect_abstain:
        correctness = completeness = faithfulness = clarity = 5 if (abstained or footer) else 1
        terminology = 5
        citation = 5 if (abstained or footer) else 3
        helpfulness = 5 if (abstained or footer) else 1
        return {
            'correctness': correctness, 'completeness': completeness,
            'faithfulness': faithfulness, 'clarity': clarity,
            'terminology': terminology, 'citation': citation,
            'helpfulness': helpfulness,
            'concept_coverage': None,
            'grounded_number_ratio': None,
        }

    if abstained or footer:
        return {d: 1 for d in DIMENSIONS} | {
            'concept_coverage': 0.0, 'grounded_number_ratio': None,
        }

    body_l = normalize_match(body)
    found = [c for c in expected_concepts if concept_present(c, body_l, mode)]
    coverage = round(len(found) / len(expected_concepts), 2) if expected_concepts else None

    correctness = clamp(1 + 4 * (coverage if coverage is not None else 0.5))

    length_part = min(1.0, len(body) / 300.0)
    completeness = clamp(1 + 4 * (0.7 * (coverage or 0.0) + 0.3 * length_part))

    ctx_nums = set(numbers(context))
    body_nums = numbers(body)
    if body_nums:
        grounded = sum(1 for n in body_nums if n in ctx_nums or n in
                       {str(p) for p in retrieved_pages})
        grounded_ratio = round(grounded / len(body_nums), 2)
    else:
        grounded_ratio = 1.0
    faithfulness = clamp(1 + 4 * grounded_ratio)

    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    struct_lines = sum(
        1 for ln in lines
        if re.match(r'^([-*•]|\d+[.)]|\*\*)', ln)
    )
    struct_ratio = min(1.0, struct_lines / max(3, len(lines) * 0.5))
    sentences = [s for s in re.split(r'[។.!?]+', body) if len(s.strip()) > 3]
    avg_sentence = (sum(len(s) for s in sentences) / len(sentences)) if sentences else 0
    readable = 0.5 < avg_sentence / 60 < 4 or 40 <= avg_sentence <= 160
    body_end = re.sub(r'\s*\[[^\]]*\]\s*$', '', body).strip()
    truncated = (not body_end) or body_end[-1] not in '។.!?)」"'
    if rec.get('question_type') in ('definition', 'ocr_garbled'):
        struct_component = 1.0 if len(body) >= 60 else 0.5
    else:
        struct_component = struct_ratio
    clarity = clamp(1 + 4 * (0.5 * (1 if readable else 0.3) + 0.3 * struct_component
                             + 0.2 * (0 if truncated else 1)))

    banned_hits = [t for t in BANNED_TERMS if t in body]
    terminology = clamp(1 + 4 * (0.5 * (1 - min(1, len(banned_hits))) +
                                 0.5 * (coverage if coverage is not None else 1.0)))

    cited = cite_pages(rec.get('answer', ''))
    valid = [p for p in cited if p in retrieved_pages]
    invalid = [p for p in cited if p not in retrieved_pages]
    validity = len(valid) / len(cited) if cited else 0.0
    overlap = len(set(cited) & set(expected_pages)) / len(expected_pages) if expected_pages else 0.0
    citation = clamp(1 + 4 * (0.5 * validity + 0.5 * overlap))

    qtype = rec.get('question_type', '')
    if qtype == 'comparison':
        has_sim = 'ដូចគ្នា' in body
        has_diff = 'ខុសគ្នា' in body
        aspects = len(re.findall(r'^\s*[-*•]', body, re.MULTILINE))
        if has_sim and has_diff:
            rel = 1.0
        elif has_diff and aspects >= 2:
            rel = 0.8  # e.g. "ខុសគ្នាដូចម្តេច?" only asks for differences
        elif has_diff:
            rel = 0.6
        else:
            rel = 0.3
    elif qtype == 'quiz':
        rel = 1.0 if len(re.findall(r'សំណួរទី\s*\d+', body)) >= 3 else 0.4
    elif qtype == 'summary':
        rel = 1.0 if struct_lines >= 3 else 0.4
    elif qtype == 'process':
        steps = sum(body.count(w) for w in ('ដំណាក់', 'ជំហាន', 'ដំបូង', 'ចាប់ពី',
                                            'បន្ទាប់មក', 'បន្ទាប់ពី', 'ចុងក្រោយ'))
        rel = 1.0 if steps >= 2 else 0.4
    elif qtype in ('definition', 'ocr_garbled'):
        rel = 1.0 if ('គឺ' in body or 'ជា' in body) and len(body) >= 60 else 0.4
    else:
        rel = 1.0 if (struct_lines >= 2 or len(body) >= 350) else 0.4
    helpfulness = clamp(1 + 4 * rel)

    return {
        'correctness': correctness, 'completeness': completeness,
        'faithfulness': faithfulness, 'clarity': clarity,
        'terminology': terminology, 'citation': citation,
        'helpfulness': helpfulness,
        'concept_coverage': coverage,
        'grounded_number_ratio': grounded_ratio,
        'banned_terms': banned_hits,
        'cited_pages': cited,
        'valid_citations': valid,
        'invalid_citations': invalid,
    }


def _retrieved_pages(metas) -> list[int]:
    return sorted(allowed_pages_from_sources(metas))


def _retrieved_ranges(metas) -> list[list[int]]:
    return [list(r) for r in source_page_ranges(metas)]


def answer_part(query: str, emb, db, reranker, mode='normal', feature='explain') -> dict:
    r = retrieve(query, emb, db)
    docs = r['documents'][0]
    metas = r['metadatas'][0]
    reranked_docs, reranked_metas, scores = rerank_with_context(
        query, docs, metas, reranker
    )
    top_score = float(scores[0]) if scores else 0.0
    if not reranked_docs or top_score < RETRIEVAL_SCORE_THRESHOLD:
        return {
            'answer': NOT_FOUND_MESSAGE, 'raw_answer': NOT_FOUND_MESSAGE,
            'abstained': True, 'top_score': top_score,
            'retrieved_pages': _retrieved_pages(reranked_metas),
            'retrieved_ranges': _retrieved_ranges(reranked_metas),
            'context': '',
        }
    kept = [
        (d, m) for d, m in zip(reranked_docs, reranked_metas)
        if is_context_source(m)
    ]
    kept = kept or [(reranked_docs[0], reranked_metas[0])]
    kept_metas = [m for _d, m in kept]
    context = '\n\n'.join(
        f"[ទំព័រ {page_range_label(m)}] {d}" for d, m in kept
    )
    try:
        answer = generate_answer(query, context, mode, feature)
    except Exception as err:  # noqa: BLE001
        failure = f'[GEN_FAILED: {err}]'
        return {
            'answer': failure, 'raw_answer': failure,
            'abstained': False,
            'top_score': top_score,
            'retrieved_pages': _retrieved_pages(kept_metas),
            'retrieved_ranges': _retrieved_ranges(kept_metas),
            'context': context,
            'gen_error': str(err)[:200],
        }
    if not isinstance(answer, str):
        answer = None
    for _ in range(2):
        if isinstance(answer, str) and answer.strip() and len(answer.strip()) >= 20:
            break
        time.sleep(1)
        try:
            answer = generate_answer(query, context, mode, feature)
        except Exception as err:  # noqa: BLE001
            failure = f'[GEN_FAILED: {err}]'
            return {
                'answer': failure, 'raw_answer': failure,
                'abstained': False,
                'top_score': top_score,
                'retrieved_pages': _retrieved_pages(kept_metas),
                'retrieved_ranges': _retrieved_ranges(kept_metas),
                'context': context,
                'gen_error': str(err)[:200],
            }
        if not isinstance(answer, str):
            answer = None
    if not (isinstance(answer, str) and answer.strip() and len(answer.strip()) >= 20):
        failure = f'[GEN_EMPTY: {repr(answer)[:60]}]'
        return {
            'answer': failure, 'raw_answer': failure,
            'abstained': False,
            'top_score': top_score,
            'retrieved_pages': _retrieved_pages(kept_metas),
            'retrieved_ranges': _retrieved_ranges(kept_metas),
            'context': context,
            'gen_error': f'empty type={type(answer).__name__}',
        }
    raw_answer = answer
    try:
        formatted = format_answer(answer, kept_metas)
    except Exception:  # noqa: BLE001
        formatted = answer
    return {
        'answer': formatted,
        'raw_answer': raw_answer,
        'abstained': False, 'top_score': top_score,
        'retrieved_pages': _retrieved_pages(kept_metas),
        'retrieved_ranges': _retrieved_ranges(kept_metas),
        'context': context,
    }


def evaluate_question(q: dict, emb, db, reranker) -> dict:
    t0 = time.time()
    queries = prepare_queries(q['question_kh'])
    parts = [answer_part(qq, emb, db, reranker) for qq in queries]
    if len(parts) == 1:
        final = parts[0]['answer']
        raw_final = parts[0].get('raw_answer', parts[0]['answer'])
    else:
        blocks = [
            f"**{i}. {qq}**\n\n{p['answer']}"
            for i, (qq, p) in enumerate(zip(queries, parts), 1)
        ]
        raw_blocks = [
            f"**{i}. {qq}**\n\n{p.get('raw_answer', p['answer'])}"
            for i, (qq, p) in enumerate(zip(queries, parts), 1)
        ]
        final = '\n\n---\n\n'.join(blocks)
        raw_final = '\n\n---\n\n'.join(raw_blocks)
    abstained = all(p['abstained'] for p in parts) if not q.get('expect_abstain') else parts[0]['abstained']
    ranges = {
        (r[0], r[1])
        for part in parts
        for r in part.get('retrieved_ranges', [])
    }
    rec = {
        'question_id': q['question_id'],
        'chapter': q['chapter'],
        'question_type': q['question_type'],
        'question': q['question_kh'],
        'queries_used': queries,
        'expected_concepts': q.get('expected_concepts', []),
        'expected_pages': expected_pages_for_question(q),
        'expect_abstain': bool(q.get('expect_abstain')),
        'retrieved_pages': sorted({p for part in parts for p in part['retrieved_pages'] if p}),
        'retrieved_ranges': [list(r) for r in sorted(ranges)],
        'top_score': round(parts[0]['top_score'], 4),
        'abstained': abstained,
        'context': '\n\n'.join(p['context'] for p in parts if p['context']),
        'answer': final,
        'raw_answer': raw_final,
        'seconds': round(time.time() - t0, 1),
    }
    rec['scores'] = score_answer(rec)
    return rec


def load_rows() -> list[dict]:
    if os.path.exists(OUT):
        with open(OUT, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save(rows: list[dict]) -> None:
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def summarize(rows: list[dict]) -> str:
    in_scope = [r for r in rows if not r['expect_abstain']]
    out_scope = [r for r in rows if r['expect_abstain']]
    lines = [f'Answer evaluation {TAG} ({len(rows)} questions)', '']
    lines.append('Dimension means (in-scope, 1-5; target >= 4.0):')
    for d in DIMENSIONS:
        vals = [r['scores'][d] for r in in_scope]
        m = round(sum(vals) / len(vals), 2) if vals else None
        lines.append(f'  {d:<14}{m}')
    mean_all = [sum(r['scores'][d] for d in DIMENSIONS) / len(DIMENSIONS) for r in in_scope]
    lines.append(f'  {"overall":<14}{round(sum(mean_all)/len(mean_all), 2) if mean_all else None}')
    lines.append('')
    if out_scope:
        ok = sum(1 for r in out_scope if r['abstained'])
        lines.append(f'Out-of-scope abstention: {ok}/{len(out_scope)} = {round(ok/len(out_scope),3)}')
    fa = sum(1 for r in in_scope if r['abstained'])
    lines.append(f'In-scope false abstain: {fa}/{len(in_scope)}')
    fb = sum(1 for r in rows if r['scores'].get('gen_fallback'))
    lines.append(f'Generation fallbacks: {fb}/{len(rows)}')
    inv = sum(1 for r in in_scope if r['scores'].get('invalid_citations'))
    lines.append(f'Rows with invalid citations: {inv}/{len(in_scope)}')
    lines.append('')
    lines.append('Per-question: id | ch | type | correctness..helpfulness | coverage | cited/valid')
    for r in sorted(rows, key=lambda x: x['question_id']):
        s = r['scores']
        dims = ' '.join(str(s[d]) for d in DIMENSIONS)
        lines.append(
            f"  q{r['question_id']:>3} | {r['chapter']} | {r['question_type'][:12]:<12} | "
            f"{dims} | {s.get('concept_coverage')} | "
            f"{len(s.get('cited_pages', []))}/{len(s.get('valid_citations', []))}"
        )
    text = '\n'.join(lines)
    with open(SUMMARY, 'w', encoding='utf-8') as f:
        f.write(text)
    with open(REVIEW, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['question_id', 'chapter', 'question_type', 'question'] +
                   [f'auto_{d}' for d in DIMENSIONS] +
                   [f'teacher_{d}' for d in DIMENSIONS] + ['teacher_notes'])
        for r in sorted(rows, key=lambda x: x['question_id']):
            w.writerow([r['question_id'], r['chapter'], r['question_type'], r['question']] +
                       [r['scores'][d] for d in DIMENSIONS] + [''] * len(DIMENSIONS) + [''])
    return text


def main():
    global OUT, SUMMARY, REVIEW, TAG
    ap = argparse.ArgumentParser()
    ap.add_argument('--questions', type=str, default='')
    ap.add_argument('--fresh', action='store_true')
    ap.add_argument('--max', type=int, default=0)
    ap.add_argument('--score-only', action='store_true')
    ap.add_argument('--tag', type=str, default='v2',
                    help='output tag, e.g. v3 (writes *_v3.json/_v3.csv)')
    args = ap.parse_args()

    TAG = args.tag.strip() or 'v2'
    OUT = os.path.join(BASE, 'data', 'evaluation', f'answer_evaluations_{TAG}.json')
    SUMMARY = os.path.join(BASE, 'data', 'evaluation',
                           f'answer_evaluation_{TAG}_summary.txt')
    REVIEW = os.path.join(BASE, 'data', 'evaluation', f'answer_review_{TAG}.csv')

    if args.score_only:
        rows = load_rows()
        if not rows:
            raise SystemExit(f'No rows to rescore: {OUT} does not exist')
        gold = {q['question_id']: q for q in load_gold()}
        for r in rows:
            g = gold.get(r['question_id'])
            if g:  # keep labels in sync with the audited gold set
                r['chapter'] = g['chapter']
                r['question_type'] = g['question_type']
                r['question'] = g['question_kh']
                r['expected_concepts'] = g.get('expected_concepts', [])
                r['expected_pages'] = expected_pages_for_question(g)
                r['expect_abstain'] = bool(g.get('expect_abstain'))
            r['scores'] = score_answer(r)
        save(rows)
        text = summarize(rows)
        print(text)
        print(f'\nSaved -> {OUT}\n{SUMMARY}\n{REVIEW}')
        return

    gold = {q['question_id']: q for q in load_gold()}
    ids = [int(x) for x in args.questions.split(',') if x.strip()] if args.questions else DEFAULT_IDS
    missing = [i for i in ids if i not in gold]
    if missing:
        raise SystemExit(f'Unknown question ids: {missing}')

    rows = [] if args.fresh else load_rows()
    done = {r['question_id'] for r in rows}
    todo = [gold[i] for i in ids if i not in done]
    if args.max:
        todo = todo[: args.max]

    if todo:
        print(f'Loading models ... ({len(todo)} pending)', flush=True)
        emb = get_embedding_model()
        db = get_vector_db()
        reranker = get_reranker()
        for n, q in enumerate(todo, 1):
            print(f"  q{q['question_id']} ...", flush=True)
            try:
                rec = evaluate_question(q, emb, db, reranker)
            except Exception as err:  # noqa: BLE001
                rec = {
                    'question_id': q['question_id'], 'chapter': q['chapter'],
                    'question_type': q['question_type'], 'question': q['question_kh'],
                    'queries_used': [], 'expected_concepts': q.get('expected_concepts', []),
                    'expected_pages': expected_pages_for_question(q),
                    'expect_abstain': bool(q.get('expect_abstain')),
                    'retrieved_pages': [], 'retrieved_ranges': [],
                    'top_score': 0.0, 'abstained': False,
                    'context': '', 'answer': f'[FAILED: {err}]',
                    'raw_answer': f'[FAILED: {err}]', 'seconds': 0.0,
                }
                rec['scores'] = {d: 1 for d in DIMENSIONS} | {
                    'concept_coverage': 0.0, 'grounded_number_ratio': None,
                    'error': str(err)[:200],
                }
            rows = [r for r in rows if r['question_id'] != rec['question_id']] + [rec]
            save(rows)
            s = rec['scores']
            print(f"    done in {rec['seconds']}s abstained={rec['abstained']} "
                  f"overall={round(sum(s[d] for d in DIMENSIONS)/len(DIMENSIONS),2)}", flush=True)

    text = summarize(rows)
    print('\n' + text)
    print(f'\nSaved -> {OUT}\n{SUMMARY}\n{REVIEW}')


if __name__ == '__main__':
    main()
