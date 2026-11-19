"""Regression tests for deterministic citation/context integrity.

Run:  python -X utf8 tests/test_citation_integrity.py

No embedding/reranker/Gemini models are loaded.  The q* replay tests
reconstruct the exact chunks that were placed in the v3 context by matching
the stored context blocks against Chroma metadata.
"""

import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "scripts"))

from app.config import VECTOR_DB_DIR  # noqa: E402
from app.prompt import (  # noqa: E402
    PAGE_MARKER, allowed_pages_from_sources, format_answer, format_page_range,
    is_context_source, normalize_khmer_digits, page_range_label,
    parse_page_citations, sanitize_page_citations, source_page_ranges,
)
from evaluation.evaluate_answers import cite_pages, score_answer, strip_sources  # noqa: E402

KH_AND = "និង"
ARCHIVE = os.path.join(BASE, "data", "evaluation", "archive")
V3_ROWS = os.path.join(ARCHIVE, "answer_evaluations_v3.json")
Q84_ROWS = os.path.join(ARCHIVE, "answer_evaluations_v3_q84.json")


def check(name, cond):
    if not cond:
        raise AssertionError(name)
    print(f"  [PASS] {name}")


def src(start, end=None, chapter=5, lesson=1, chapter_title="ជំពូកសាកល្បង",
        lesson_title="មេរៀនសាកល្បង"):
    end = start if end is None else end
    return {
        "page": start,
        "page_start": start,
        "page_end": end,
        "chapter_id": chapter,
        "lesson_id": lesson,
        "chapter_title": chapter_title,
        "lesson_title": lesson_title,
    }


def footer_text(answer):
    idx = answer.find("📚")
    return answer[idx:] if idx >= 0 else answer


def body_text(answer):
    idx = answer.find("📚")
    return answer[:idx].strip() if idx >= 0 else answer.strip()


def footer_lines(answer):
    return [ln.strip() for ln in footer_text(answer).splitlines() if ln.strip().startswith("📄")]


def test_page_range_formatter():
    print("page-range formatter")
    check("same page", format_page_range(164, 164) == "164")
    check("two-page range", format_page_range(164, 165) == "164-165")
    check("reversed range is normalized", format_page_range(165, 164) == "164-165")
    check("missing end falls back to start", format_page_range(164, None) == "164")
    check("zero page is not rendered", format_page_range(0, 0) == "")


def test_page_parser():
    print("citation parser")
    check("single page", parse_page_citations(f"[{PAGE_MARKER} 164]") == [(164, 164)])
    check("range", parse_page_citations(f"[{PAGE_MARKER} 164-165]") == [(164, 165)])
    check("comma list", parse_page_citations(f"[{PAGE_MARKER} 13, 32, 40]") ==
          [(13, 13), (32, 32), (40, 40)])
    check("Khmer and list", parse_page_citations(f"[{PAGE_MARKER} 242 {KH_AND} 246]") ==
          [(242, 242), (246, 246)])
    check("mixed range/list", parse_page_citations(f"[{PAGE_MARKER} 13-14, 20]") ==
          [(13, 14), (20, 20)])
    check("multiple groups", parse_page_citations(
        f"[{PAGE_MARKER} 13] និង [{PAGE_MARKER} 40]") == [(13, 13), (40, 40)])
    check("Khmer single page", parse_page_citations(f"[{PAGE_MARKER} ២៦]") ==
          [(26, 26)])
    check("Khmer comma list", parse_page_citations(f"[{PAGE_MARKER} ២៦, ៤០]") ==
          [(26, 26), (40, 40)])
    check("Khmer range", parse_page_citations(f"[{PAGE_MARKER} ១៦៤-១៦៥]") ==
          [(164, 165)])
    check("mixed Khmer/ASCII list", parse_page_citations(f"[{PAGE_MARKER} ២៦, 40]") ==
          [(26, 26), (40, 40)])
    check("mixed digits inside range", parse_page_citations(f"[{PAGE_MARKER} ១64-១៦៥]") ==
          [(164, 165)])
    check("Khmer and list with Khmer digits",
          parse_page_citations(f"[{PAGE_MARKER} ២៤២ {KH_AND} ២៤៦]") ==
          [(242, 242), (246, 246)])
    check("normalize helper maps Khmer digits",
          normalize_khmer_digits("០១២៣៤៥៦៧៨៩") == "0123456789")
    check("normalize helper preserves non-digit text",
          normalize_khmer_digits("រយៈពេល ២ឆ្នាំ") == "រយៈពេល 2ឆ្នាំ")


def test_sanitizer():
    print("citation sanitizer")
    check("fully supported group unchanged",
          sanitize_page_citations(f"[{PAGE_MARKER} 246]", {246}) ==
          f"[{PAGE_MARKER} 246]")
    check("unsupported page removed",
          sanitize_page_citations(f"[{PAGE_MARKER} 999]", {246}) == "")
    check("partially supported list keeps supported page",
          sanitize_page_citations(f"[{PAGE_MARKER} 242 {KH_AND} 246]", {246}) ==
          f"[{PAGE_MARKER} 246]")
    check("partially supported range keeps supported endpoint",
          sanitize_page_citations(f"[{PAGE_MARKER} 164-165]", {164}) ==
          f"[{PAGE_MARKER} 164]")
    check("non-contiguous supported pages stay split",
          sanitize_page_citations(f"[{PAGE_MARKER} 164-166]", {164, 166}) ==
          f"[{PAGE_MARKER} 164, 166]")
    check("empty brackets are cleaned",
          "[" not in sanitize_page_citations("ចម្លើយ [ទំព័រ 999]។", {246}))
    check("Khmer unsupported page removed",
          sanitize_page_citations(f"[{PAGE_MARKER} ៩៩៩]", {246}) == "")
    check("Khmer partially supported list keeps supported page",
          sanitize_page_citations(f"[{PAGE_MARKER} ២៤២ {KH_AND} ២៤៦]", {246}) ==
          f"[{PAGE_MARKER} 246]")
    check("Khmer range keeps supported endpoint",
          sanitize_page_citations(f"[{PAGE_MARKER} ១៦៤-១៦៥]", {164}) ==
          f"[{PAGE_MARKER} 164]")
    non_citation = sanitize_page_citations(
        f"រយៈពេល ២ឆ្នាំ [{PAGE_MARKER} ២៤៦]", {246})
    check("non-citation Khmer digits untouched", "រយៈពេល ២ឆ្នាំ" in non_citation)
    check("Khmer citation normalized to ASCII",
          f"[{PAGE_MARKER} 246]" in non_citation)


def test_chapter_openers():
    print("chapter-opener eligibility")
    front = {"page": 4, "page_start": 4, "page_end": 4, "lesson_id": 0}
    opener5 = {"page": 5, "page_start": 5, "page_end": 5, "lesson_id": 0}
    opener149 = {"page": 149, "page_start": 149, "page_end": 149, "lesson_id": 0}
    lesson = {"page": 6, "page_start": 6, "page_end": 6, "lesson_id": 1}
    check("front matter p4 excluded", is_context_source(front) is False)
    check("chapter opener p5 allowed", is_context_source(opener5) is True)
    check("chapter opener p149 allowed", is_context_source(opener149) is True)
    check("normal lesson chunk allowed", is_context_source(lesson) is True)


def test_basic_formatting():
    print("basic footer formatting")
    single = format_answer("ចម្លើយ [ទំព័រ 164]", [src(164)])
    check("single page footer", "ទំព័រ 164" in footer_text(single))
    check("single page body retained", "ទំព័រ 164" in body_text(single))

    ranged = format_answer("ចម្លើយ [ទំព័រ 164]", [src(164, 165)])
    check("range footer", "ទំព័រ 164-165" in footer_text(ranged))
    check("body page inside range retained", "ទំព័រ 164" in body_text(ranged))

    duplicate = format_answer("ចម្លើយ [ទំព័រ 164]", [src(164, 165), src(164, 165)])
    check("duplicate range shown once", footer_text(duplicate).count("ទំព័រ 164-165") == 1)

    different = format_answer(
        "ចម្លើយ [ទំព័រ 164] និង [ទំព័រ 170]",
        [src(164, 165), src(170, 171)],
    )
    check("different range 164-165 retained", "ទំព័រ 164-165" in footer_text(different))
    check("different range 170-171 retained", "ទំព័រ 170-171" in footer_text(different))

    page_only = format_answer(
        "ចម្លើយ [ទំព័រ 165]",
        [src(164), src(164, 165)],
    )
    check("page-only dedupe does not hide 164-165", "ទំព័រ 164-165" in footer_text(page_only))

    unsupported = format_answer("ចម្លើយ [ទំព័រ 999]", [src(164)])
    check("unsupported page not displayed", "999" not in unsupported)
    check("context source still displayed", "ទំព័រ 164" in footer_text(unsupported))

    partial = format_answer(
        f"ចម្លើយ [ទំព័រ 242 {KH_AND} 246]",
        [src(246)],
    )
    check("unsupported p242 removed", "242" not in partial)
    check("supported p246 kept", "ទំព័រ 246" in partial)

    khmer_partial = format_answer(
        f"ចម្លើយ [{PAGE_MARKER} ២៤២ {KH_AND} ២៤៦]",
        [src(246)],
    )
    check("Khmer unsupported p242 removed", "242" not in body_text(khmer_partial))
    check("Khmer supported p246 kept", "ទំព័រ 246" in body_text(khmer_partial))


def test_footer_selection_order():
    print("footer source selection")
    sources = [src(10, 11), src(20), src(30)]
    out = format_answer("ចម្លើយ [ទំព័រ 30]", sources)
    lines = footer_lines(out)
    check("body-cited source comes first", "ទំព័រ 30" in lines[0])
    check("remaining context follows rerank order",
          "ទំព័រ 10-11" in lines[1] and "ទំព័រ 20" in lines[2])

    many = [src(100 + i) for i in range(12)]
    capped = format_answer("ចម្លើយដោយគ្មានលេខទំព័រ", many)
    check("footer is capped at 8 sources", len(footer_lines(capped)) == 8)
    check("footer cap keeps the top context order",
          "ទំព័រ 100" in footer_lines(capped)[0] and
          "ទំព័រ 107" in footer_lines(capped)[7])


def test_evaluator_parser():
    print("evaluator citation parser")
    check("evaluator comma list", cite_pages(f"{PAGE_MARKER} 13, 32, 40") == [13, 32, 40])
    check("evaluator Khmer and list", cite_pages(f"{PAGE_MARKER} 242 {KH_AND} 246") == [242, 246])
    check("evaluator Khmer comma list", cite_pages(f"{PAGE_MARKER} ២៦, ៤០") == [26, 40])
    check("evaluator Khmer range", cite_pages(f"{PAGE_MARKER} ១៦៤-១៦៥") == [164, 165])
    check("evaluator range", cite_pages(f"{PAGE_MARKER} 164-165") == [164, 165])


def test_range_aware_score():
    print("range-aware citation scoring")
    rec = {
        "answer": f"ចម្លើយ [{PAGE_MARKER} 165]",
        "context": "",
        "expected_concepts": [],
        "expected_pages": [165],
        "retrieved_pages": [164, 165],
        "abstained": False,
        "expect_abstain": False,
        "question_type": "definition",
    }
    scores = score_answer(rec)
    check("range endpoint is valid", scores["valid_citations"] == [165])
    check("range endpoint is not invalid", scores["invalid_citations"] == [])


def _load_chroma_docs():
    import chromadb
    client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
    collection = client.get_collection("biology")
    got = collection.get(include=["metadatas", "documents"])
    return {doc: meta for doc, meta in zip(got["documents"], got["metadatas"])}


BLOCK_RE = re.compile(
    r"\[" + re.escape(PAGE_MARKER) + r" (\d+)\] (.*?)"
    r"(?=\n\n\[" + re.escape(PAGE_MARKER) + r" |\Z)",
    re.S,
)


def _sources_for_row(row, doc2meta):
    sources = []
    for match in BLOCK_RE.finditer(row.get("context", "")):
        text = match.group(2)
        meta = doc2meta.get(text)
        if meta is not None:
            sources.append(meta)
        else:
            page = int(match.group(1))
            sources.append(src(page))
    return sources


def _load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_replays(doc2meta):
    print("stored-row replays")
    rows = {row["question_id"]: row for row in _load_json(V3_ROWS)}

    q58 = format_answer(rows[58]["answer"], _sources_for_row(rows[58], doc2meta))
    q58_footer = footer_text(q58)
    check("q58 footer keeps p40", "ទំព័រ 40" in q58_footer)
    check("q58 footer keeps p32", "ទំព័រ 32" in q58_footer)
    check("q58 footer keeps p13", "ទំព័រ 13" in q58_footer)

    q63 = format_answer(rows[63]["answer"], _sources_for_row(rows[63], doc2meta))
    q63_footer = footer_text(q63)
    check("q63 footer keeps p64", "ទំព័រ 64" in q63_footer)
    check("q63 footer keeps p62-63", "ទំព័រ 62-63" in q63_footer)
    check("q63 footer keeps p77", "ទំព័រ 77" in q63_footer)
    check("q63 footer keeps p65", "ទំព័រ 65" in q63_footer)

    q115 = rows[115]
    q115_part0 = body_text(q115["answer"])
    q115_out = format_answer(q115_part0, _sources_for_row(q115, doc2meta))
    q115_footer = footer_text(q115_out)
    for page in ("150", "153", "159-160", "162"):
        check(f"q115 part 0 footer keeps p{page}", f"ទំព័រ {page}" in q115_footer)

    q1 = format_answer(rows[1]["answer"], _sources_for_row(rows[1], doc2meta))
    q1_footer = footer_text(q1)
    check("q1 footer keeps p6-7", "ទំព័រ 6-7" in q1_footer)
    check("q1 does not collapse p6-7 to p7", not re.search(r"ទំព័រ 7(?!\d)", q1_footer))

    q35 = format_answer(rows[35]["answer"], _sources_for_row(rows[35], doc2meta))
    check("q35 footer keeps p247-248", "ទំព័រ 247-248" in footer_text(q35))

    q84 = _load_json(Q84_ROWS)[0]
    q84_out = format_answer(q84["answer"], _sources_for_row(q84, doc2meta))
    check("q84 footer keeps p164-165", "ទំព័រ 164-165" in footer_text(q84_out))

    q68_sources = [src(149, chapter=5, lesson=0), src(150), src(160)]
    q68_out = format_answer("ចម្លើយដោយគ្មានលេខទំព័រ", q68_sources)
    check("q68 chapter opener p149 eligible in footer", "ទំព័រ 149" in footer_text(q68_out))

    q47_out = format_answer(rows[47]["answer"], _sources_for_row(rows[47], doc2meta))
    check("q47 unsupported p242 removed from body", "242" not in body_text(q47_out))
    check("q47 supported p246 retained", "246" in body_text(q47_out))


def test_historical_khmer_replay():
    print("historical Khmer citation replay")
    rows = {row["question_id"]: row for row in _load_json(V3_ROWS)}
    expected = {
        8: [26, 27, 40],
        16: [122, 127, 134],
        20: [150, 152, 157, 159, 160, 162, 174],
        108: [15],
    }
    for qid, pages in expected.items():
        body = strip_sources(rows[qid]["answer"])
        check(f"q{qid} stored Khmer citations parse", cite_pages(body) == pages)


def test_helpers():
    print("shared helper consistency")
    sources = [src(164, 165), src(164, 165), src(170, 171), src(0, 0)]
    check("source ranges dedupe exact pairs",
          source_page_ranges(sources) == [(164, 165), (170, 171)])
    check("allowed pages expand ranges",
          allowed_pages_from_sources(sources) == {164, 165, 170, 171})
    check("page label uses range", page_range_label(sources[0]) == "164-165")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    test_page_range_formatter()
    test_page_parser()
    test_sanitizer()
    test_chapter_openers()
    test_basic_formatting()
    test_footer_selection_order()
    test_evaluator_parser()
    test_range_aware_score()
    test_historical_khmer_replay()
    test_helpers()
    test_replays(_load_chroma_docs())
    print("\nALL CITATION-INTEGRITY TESTS PASSED")


if __name__ == "__main__":
    main()
