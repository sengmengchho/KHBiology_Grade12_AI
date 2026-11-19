"""Shared helpers for the v2 evaluation harness.

The query-preparation functions mirror app/main.py's real request path:
  _process_question -> normalize_query
  _answer_multi     -> normalize_query + split_questions
  _answer           -> expand_query
The splitter is imported from app.utils (not app.main, whose import executes
the Streamlit page), so the harness and the real app cannot drift apart.
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GOLD_V2 = os.path.join(BASE, 'data', 'evaluation', 'gold_questions_v2.json')
sys.path.insert(0, BASE)

from app.utils import (  # noqa: E402
    expand_query, normalize_query, split_questions, strip_lead_markers,
)


def prepare_queries(question: str) -> list[str]:
    parts = split_questions(normalize_query(question))
    return [expand_query(p) for p in parts] or [expand_query(question)]


def load_gold(path: str = GOLD_V2) -> list[dict]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def expected_pages_for_part(q: dict, part_idx: int) -> list[int]:
    """Return the gold pages for one part of a multi-part question.

    Most gold questions share one page list across all parts. A few have
    genuinely different answers per part (e.g. q115 part 0 asks about ADN,
    part 1 about ARN); those provide ``expected_source_pages_by_part``.
    """
    by_part = q.get('expected_source_pages_by_part') or []
    if 0 <= part_idx < len(by_part):
        return by_part[part_idx]
    return q.get('expected_source_pages', [])


def expected_pages_for_question(q: dict) -> list[int]:
    """Union of all part-level gold pages, for whole-answer scoring."""
    by_part = q.get('expected_source_pages_by_part') or []
    if by_part:
        return sorted({p for part in by_part for p in part})
    return q.get('expected_source_pages', [])


def meta_pages(meta: dict) -> tuple[int, int]:
    lo = meta.get('page_start', meta.get('page'))
    hi = meta.get('page_end', meta.get('page'))
    lo = lo or 0
    hi = hi or lo
    return lo, hi


def is_page_hit(meta: dict, expected: list[int]) -> bool:
    if not expected:
        return False
    lo, hi = meta_pages(meta)
    return any(p in expected for p in range(lo, hi + 1))


def first_hit_rank(metas: list[dict], expected: list[int]) -> int | None:
    for i, m in enumerate(metas, 1):
        if is_page_hit(m, expected):
            return i
    return None


def at_k_metrics(metas: list[dict], expected: list[int]) -> dict:
    rank = first_hit_rank(metas, expected)
    return {
        'hit1': bool(rank and rank <= 1),
        'hit3': bool(rank and rank <= 3),
        'hit5': bool(rank and rank <= 5),
        'mrr': (1.0 / rank) if rank else 0.0,
    }


def map_docs_to_metas(docs: list[str], metas: list[dict], ranked_docs: list[str]) -> list[dict]:
    """Align reranked document strings back to their metadata rows."""
    out = []
    used = set()
    for doc in ranked_docs:
        for i, d in enumerate(docs):
            if d == doc and i not in used:
                out.append(metas[i])
                used.add(i)
                break
    return out


def mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 3) if values else None
