"""Validate the rebuilt v3 corpus and write an evidence report.

Usage: python -m scripts.evaluation.validate_corpus
"""

import json
import os
import sys
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCESSED = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "evaluation", "corpus_validation_v3.json")

CLEANED = os.path.join(PROCESSED, "biology_cleaned.json")
STRUCTURED = os.path.join(PROCESSED, "biology_structured.json")
CHUNKS = os.path.join(PROCESSED, "biology_chunks.json")

STALE_FORMS = [
    "ស្ទីចម៉ាត",
    "ស្អិតម៉ាស",
    "បន្សុំ",
    "ជំងឺហមារីក",
    "លក្ខណៈ បន្សំ",
]
REQUIRED_CHUNK_FIELDS = (
    "chunk_id", "page", "page_start", "page_end", "chapter_id",
    "chapter_title", "lesson_id", "lesson_title", "text",
)


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    pages = load(CLEANED)
    structured = load(STRUCTURED)
    chunks = load(CHUNKS)

    errors = []
    page_numbers = [p["page"] for p in pages]
    if len(pages) != 257:
        errors.append(f"expected 257 cleaned pages, got {len(pages)}")
    if page_numbers != list(range(257)):
        errors.append("cleaned pages are not contiguous 0..256")

    if len(structured) != len(pages):
        errors.append(f"structured pages {len(structured)} != cleaned pages {len(pages)}")
    chapter_ids = sorted({p.get("chapter_id") for p in structured})
    if chapter_ids != list(range(1, 9)):
        errors.append(f"chapter ids are {chapter_ids}, expected 1..8")

    page_set = set(page_numbers)
    covered = set()
    for c in chunks:
        missing = [k for k in REQUIRED_CHUNK_FIELDS if k not in c]
        if missing:
            errors.append(f"{c.get('chunk_id')} missing fields {missing}")
            continue
        if not str(c["text"]).strip():
            errors.append(f"{c['chunk_id']} has empty text")
        if c["chapter_id"] not in range(1, 9):
            errors.append(f"{c['chunk_id']} chapter_id {c['chapter_id']} out of range")
        if c["page_start"] > c["page_end"]:
            errors.append(f"{c['chunk_id']} page_start > page_end")
        if not ({c["page_start"], c["page_end"], c["page"]} <= page_set):
            errors.append(f"{c['chunk_id']} refers to a page outside 0..256")
        covered.update(range(c["page_start"], c["page_end"] + 1))

    chunk_ids = [c["chunk_id"] for c in chunks]
    duplicate_ids = [k for k, n in Counter(chunk_ids).items() if n > 1]
    duplicate_texts = [t[:80] for t, n in Counter(c["text"] for c in chunks).items() if n > 1]
    missing_pages = sorted(page_set - covered)
    if duplicate_ids:
        errors.append(f"duplicate chunk ids: {duplicate_ids[:5]}")
    if missing_pages:
        errors.append(f"pages not covered by any chunk: {missing_pages}")

    cleaned_text = "\n".join(p["text"] for p in pages)
    chunk_text = "\n".join(c["text"] for c in chunks)
    stale_counts = {
        term: {"pages": cleaned_text.count(term), "chunks": chunk_text.count(term)}
        for term in STALE_FORMS
    }
    for term, counts in stale_counts.items():
        if counts["pages"] or counts["chunks"]:
            errors.append(f"stale form remains: {term} {counts}")

    # Adaptation vs combination: bare បន្សំ is legitimate in genetics
    # (combination of nucleotides / recombinant DNA); only the adaptation
    # phrases were corrected.
    combo_examples = [
        "បន្សំនុយក្លេអូទីត",
        "ADN បន្សំថ្មី",
    ]
    combo_preserved = {s: (s in cleaned_text and s in chunk_text) for s in combo_examples}
    if not all(combo_preserved.values()):
        errors.append(f"legitimate combination forms were corrupted: {combo_preserved}")

    chapter_counts = Counter(c["chapter_id"] for c in chunks)
    no_lesson = [c["chunk_id"] for c in chunks if not c.get("lesson_id")]
    report = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "cleaned_pages": len(pages),
        "structured_pages": len(structured),
        "chapters": chapter_ids,
        "chunks": len(chunks),
        "chunks_per_chapter": dict(sorted(chapter_counts.items())),
        "chunk_ids_unique": not duplicate_ids,
        "duplicate_chunk_ids": duplicate_ids,
        "duplicate_chunk_texts": duplicate_texts,
        "pages_covered": len(covered),
        "missing_pages": missing_pages,
        "chunks_without_lesson": no_lesson,
        "stale_form_counts": stale_counts,
        "legitimate_combination_preserved": combo_preserved,
        "canonical_counts_in_cleaned": {
            "ស្ទិចម៉ាត": cleaned_text.count("ស្ទិចម៉ាត"),
            "បន្ស៊ាំ": cleaned_text.count("បន្ស៊ាំ"),
            "មហារីក": cleaned_text.count("មហារីក"),
        },
        "chunk_size": {
            "min": min(len(c["text"]) for c in chunks),
            "max": max(len(c["text"]) for c in chunks),
            "avg": round(sum(len(c["text"]) for c in chunks) / len(chunks), 1),
        },
        "page_165_chunks": [
            {k: c[k] for k in ("chunk_id", "page_start", "page_end", "chapter_id", "lesson_id")}
            for c in chunks if c["page_start"] <= 165 <= c["page_end"]
        ],
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

    print(f"{report['status']}: {len(chunks)} chunks, {len(pages)} pages, "
          f"{len(covered)} pages covered, {len(no_lesson)} chunks without lesson")
    print(f"chunks/chapter: {report['chunks_per_chapter']}")
    print(f"stale forms: {stale_counts}")
    print(f"wrote {OUT}")
    if errors:
        for err in errors:
            print("  ERROR:", err)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
