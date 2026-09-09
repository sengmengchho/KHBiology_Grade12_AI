"""Phase 4 — Organize the textbook by chapter and lesson.

Reads the cleaned pages and attaches chapter/lesson metadata.

The textbook is a clean, sequential document where every chapter and lesson is
introduced by a dedicated title page. A chapter title page begins with
"ជំពូក N <Title>"; a lesson title page begins with "មេរៀនទី N <Title>"
followed by the chapter-objectives header ("...មេរៀននេះ សិស្សអាច ...").

Only those boundary pages carry a *clean* title. Ordinary content pages start
with a running header ("ជំពូកទីN មេរៀនទីM ...") whose following text is body
content, not a title — the previous parser wrongly captured that body text as
chapter/lesson titles, which produced garbled citations (e.g. "ជំពូក ?",
"មេរៀនទី២ ឫស").

Strategy:
  1. Detect chapter id on every page from the header (used as a fallback id).
  2. Detect lesson id on every page from the header (used as a fallback id).
  3. Assign clean chapter titles from a curated chapter map (8 chapters).
  4. Assign clean lesson titles only from genuine lesson boundary pages,
     carried forward page by page.
  5. Correct OCR-garbled header numbers (wrong chapter/lesson ids on some
     content pages) by assigning each page to its true chapter based on the
     known contiguous chapter page ranges, then to the running lesson.

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

# Matches a chapter running header / title: "ជំពូក 1", "ជំពូកទី1", "ជំពូក១"...
CHAPTER_ID_RE = re.compile(r"ជំពូក\s*(ទី\s*)?\s*(\d+|[១២៣៤៥៦៧៨៩០]+)")

# Matches a lesson running header / title: "មេរៀន 2", "មេរៀនទី2", "មេរៀនទី # 2"...
LESSON_ID_RE = re.compile(
    r"មេរៀន\s*(ទី\s*)?\s*[#]?\s*(\d+|[១២៣៤៥៦៧៨៩០]+)"
)

# A genuine lesson boundary page begins with "មេរៀនទី N <Title>" followed by
# a chapter-objectives header. The header always contains the token "...រៀននេះ"
# (OCR sometimes adds/drops "មេ" before it, and sometimes renders the trailing
# "ន" as the visually-identical Thai "ន" U+0E19). The objectives word begins
# with "ច" (ចប់/ចង់/ច្ប/ច្បរ/ចំណុច/ចប...). We treat the text between the lesson
# number and that "ច..." word as the lesson title.
_LESSON_META_RE = re.compile(r"មេរៀន\s*(ទី\s*)?\s*[#]?\s*(\d+|[១២៣៤៥៦៧៨៩០]+)")
# The objectives token "...រៀននេះ" with OCR variants: the trailing consonant
# is Khmer "ន" U+1793, sometimes rendered as the visually-identical Thai "น"
# U+0E19, and occasionally duplicated by OCR (both variants together). We also
# allow an optional dropped "មេ" (→ "រៀននេះ").
_LESSON_TOKEN_RE = re.compile(
    r"(?:មេ)?រៀ[\u1793\u0e19]{1,2}\u17c1\u17c7"
)


def match_lesson_boundary(head):
    """Return (lesson_id, title) if `head` begins a lesson boundary page."""
    m = _LESSON_META_RE.match(head)
    if not m:
        return None
    lesson_id = to_int(m.group(2))
    rest = head[m.end():]
    tm = _LESSON_TOKEN_RE.search(rest)
    if not tm:
        return None
    # The objectives word immediately precedes the token; it starts with "ច"
    # (ចប់/ចង់/ច្ប/ច្បរ/ចំណុច/ចប...). Drop it by keeping only the text before
    # the last whitespace-separated token that begins with "ច".
    header = rest[: tm.start()]
    # Work on the raw (un-rstriped unicode-stripped) header to split by spaces.
    ci = header.rfind("ច")
    if ci != -1:
        # Find the start of the word containing that "ច" (the objectives word).
        start = ci
        while start > 0 and header[start - 1] != " ":
            start -= 1
        before = header[:start].rstrip()
        if before.strip():
            header = before
    title = clean_title(header)
    return lesson_id, title

KHMER_DIGITS = str.maketrans("០១២៣៤៥៦៧៨៩", "0123456789")


def to_int(s):
    s = s.translate(KHMER_DIGITS)
    m = re.search(r"\d+", s or "")
    return int(m.group(0)) if m else None


# Curated chapter titles (the fixed Grade 12 Biology chapter list). Only 8
# chapters; OCR noise in the title pages makes a hardcoded map far more
# reliable than parsing them.
CHAPTER_TITLES = {
    1: "ស៊ីមណូស្ពែម និងអង់ស្យូស្ពែម",
    2: "ការលូតលាស់ និងតំណប់រំញោចរុក្ខជាតិ",
    3: "ការផ្លាស់ប្ដូរ (ចលនា) និងទំនាក់ទំនងរបស់សារពាង្គកាយ",
    4: "ព័ត៌មានសេនេទិច និងការបង្ហាញចេញនៃសែន",
    5: "ការសំយោគប្រូតេអ៊ីន និងបច្ចេកវិទ្យាជីវៈ",
    6: "ការវិវត្តនៃសារពាង្គកាយ",
    7: "ពពួកនិងសហគមន៍",
    8: "អេកូឡូស៊ី",
}


def clean_title(raw, max_len=60):
    """Normalize an extracted title: strip OCR noise and trim to a sane length."""
    if not raw:
        return None
    t = re.sub(r"\s+", " ", raw).strip(" .:្។-–—•*_")
    # Trim at the first sentence terminator if the title overran its line.
    cut = re.split(r"[។៕\?!]", t, maxsplit=1)[0].strip()
    t = cut if cut else t
    t = re.sub(r"\.{2,}", "", t).strip(" -–—")
    if not t:
        return None
    return t[:max_len].strip()


def parse_pages(pages):
    # First pass: build chapter page ranges from genuine chapter title pages.
    # A genuine chapter open page is "ជំពូក N <Title>..." where the text right
    # after the number is a title, NOT a "មេរៀនទី M" running header. Content
    # pages ("ជំពូកទីN មេរៀនទីM ...") must be excluded.
    chapter_pages = {}
    for page in pages:
        t = page["text"].lstrip()
        m = re.match(
            r"ជំពូក\s*(ទី\s*)?\s*(\d+|[១២៣៤៥៦៧៨៩០]+)\s+"
            r"(?!មេរៀន\s*(ទី\s*)?\s*[#]?\s*\d)",
            t,
        )
        if m and to_int(m.group(2)) is not None:
            chapter_pages.setdefault(page["page"], to_int(m.group(2)))

    bounds = sorted(chapter_pages.items())  # (page, chapter_id)
    page_count = len(pages)
    last_page = max(p["page"] for p in pages)

    def chapter_for_page(pg):
        ch = None
        for p_, c in bounds:
            if p_ <= pg:
                ch = c
        return ch or (bounds[0][1] if bounds else None)

    # Second pass: walk pages, picking up clean lesson titles at boundaries and
    # correcting chapter/lesson ids by page range.
    structured = []
    current_lesson_id = None
    current_lesson_title = None

    for page in pages:
        pg = page["page"]
        text = page["text"]
        head = text[:200]

        # Detect a genuine chapter title page (resets lesson context).
        is_chapter_open = bool(
            re.match(
                r"ជំពូក\s*(ទី\s*)?\s*(\d+|[១២៣៤៥៦៧៨៩០]+)\s+"
                r"(?!មេរៀន\s*(ទី\s*)?\s*[#]?\s*\d)",
                text.lstrip(),
            )
        )
        if is_chapter_open:
            current_lesson_id = None
            current_lesson_title = None

        # Clean lesson title boundary?
        lb = match_lesson_boundary(head)
        if lb:
            current_lesson_id, current_lesson_title = lb
            lesson_id = current_lesson_id
        else:
            # Fallback lesson id from running header (not a clean title).
            lm_id = LESSON_ID_RE.search(head)
            lid = to_int(lm_id.group(2)) if lm_id else None
            lesson_id = lid if lid is not None else current_lesson_id

        # True chapter comes from the page-range map (fixes OCR-garbled ids).
        true_ch = chapter_for_page(pg)

        structured.append({
            "page": pg,
            "chapter_id": true_ch,
            "chapter_title": CHAPTER_TITLES.get(true_ch),
            "lesson_id": lesson_id,
            "lesson_title": current_lesson_title,
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
    # Summary of chapter coverage.
    from collections import OrderedDict
    seen = OrderedDict()
    for p in structured:
        key = (p["chapter_id"], p["chapter_title"])
        pages = seen.setdefault(key, [])
        pages.append(p["page"])
    for (cid, ctitle), pgs in seen.items():
        print(f"  chapter {cid} ({ctitle}): pages {min(pgs)}-{max(pgs)} ({len(pgs)} pages)")
    missing = [p["page"] for p in structured if not p["chapter_title"]]
    if missing:
        print(f"WARNING: pages without chapter title: {missing}")


if __name__ == "__main__":
    main()
