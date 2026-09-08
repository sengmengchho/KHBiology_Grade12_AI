"""Phase 4 — Organize the textbook by chapter and lesson.

Reads the cleaned pages and attaches chapter/lesson metadata by detecting
Khmer structure markers (ជំពូក = chapter, មេរៀន = lesson, ផ្នែក/1.1 = section).
Writes a structured dataset to data/processed/biology_structured.json.

Usage:
    python scripts/parse_lessons.py [--input path] [--output path]
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import PROCESSED_DIR

DEFAULT_INPUT = os.path.join(PROCESSED_DIR, "biology_cleaned.json")
DEFAULT_OUTPUT = os.path.join(PROCESSED_DIR, "biology_structured.json")

# Matches: ជំពូក 1, ជំពូកទី1, ជំពូក1, ជំពូកទី១, ជំពូក១, ជំពូក ១
CHAPTER_RE = re.compile(
    r"ជំពូក\s*(ទី\s*)?\s*(\d+|[១២៣៤៥៦៧៨៩០]+)"
)
LESSON_RE = re.compile(
    r"មេរៀន\s*(ទី\s*)?\s*(\d+|[១២៣៤៥៦៧៨៩០]+)"
)

KHMER_DIGITS = str.maketrans("០១២៣៤៥៦៧៨៩", "0123456789")


def to_int(s):
    s = s.translate(KHMER_DIGITS)
    m = re.search(r"\d+", s or "")
    return int(m.group(0)) if m else None


def find_marker(text, regex):
    """Return (match, remainder_after_match) for the first occurrence of regex in text."""
    m = regex.search(text)
    if not m:
        return None, None
    nxt = text[m.end():]
    # Cap the title at a reasonable length (next marker, punctuation, or spacing).
    nxt = re.split(r"[។។\n]", nxt, maxsplit=1)[0]
    return m, nxt


def title_from_remainder(remainder):
    if not remainder:
        return None
    title = re.sub(r"^\s*[:：]*\s*", "", remainder)
    title = re.split(r"\s{2,}|\.\.\.+|\.\s*\d", title, maxsplit=1)[0]
    title = re.sub(r"\s+", " ", title).strip()
    return title or None


def parse_pages(pages):
    # Track current chapter/lesson over the stream of pages.
    chapter_id = None
    chapter_title = None
    lesson_id = None
    lesson_title = None

    structured = []
    for page in pages:
        text = page["text"]
        head = text[:120]

        cm, crem = find_marker(head, CHAPTER_RE)
        if cm:
            chapter_id = to_int(cm.group(2))
            t = title_from_remainder(crem)
            if t:
                chapter_title = t

        lm, lrem = find_marker(head, LESSON_RE)
        if lm:
            lesson_id = to_int(lm.group(2))
            t = title_from_remainder(lrem)
            if t:
                lesson_title = t

        structured.append({
            "page": page["page"],
            "chapter_id": chapter_id,
            "chapter_title": chapter_title,
            "lesson_id": lesson_id,
            "lesson_title": lesson_title,
            "text": text,
        })
    return structured


def main():
    parser = argparse.ArgumentParser(description="Organize pages by chapter/lesson")
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not os.path.exists(args.input):
        sys.exit(f"Input not found: {args.input}")

    with open(args.input, "r", encoding="utf-8") as f:
        pages = json.load(f)

    structured = parse_pages(pages)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(structured, f, ensure_ascii=False, indent=2)

    print(f"Structured {len(structured)} pages -> {args.output}")
    for p in structured:
        print(f"  page {p['page']:>3}: ch={p['chapter_id']} lesson={p['lesson_id']}")
    if not any(p["chapter_id"] for p in structured):
        print("WARNING: no chapters detected. Inspect the text patterns and update regexes.")


if __name__ == "__main__":
    main()
