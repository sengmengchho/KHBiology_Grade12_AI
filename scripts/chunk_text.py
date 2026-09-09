"""Phase 6 — Chunk the textbook into meaningful passages.

Reads the structured pages and splits each page's text into chunks that keep
related sentences together. Chunks are bounded by Khmer sentence punctuation
(។ / ។) and grouped toward the configured CHUNK_SIZE (character-based for
Khmer), with a small overlap.

To keep multi-part sections coherent (e.g. ឫស/ដើម/ស្លឹក of the vegetative
organs section, which spans pages 13–14), consecutive pages that belong to the
same chapter+lesson are first merged into a single stream and chunked together.
Each sentence keeps the page it came from, so every chunk is still labelled
with a real source page. Writes biology_chunks.json.

Usage:
    python scripts/chunk_text.py [--input path] [--output path]
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import CHUNK_SIZE, CHUNK_OVERLAP, PROCESSED_DIR

DEFAULT_INPUT = os.path.join(PROCESSED_DIR, "biology_structured.json")
DEFAULT_OUTPUT = os.path.join(PROCESSED_DIR, "biology_chunks.json")

# Khmer sentence-ending punctuation: ។ (khan), ៕ (phnhek), plus ! and ?
SENTENCE_END_RE = re.compile(r"(?<=[។៕\?!])")

# Chunks shorter than this are treated as artifacts and merged into a neighbor.
MIN_CHUNK_CHARS = 20


def split_sentences(text):
    """Split text on Khmer full stops while keeping the punctuation."""
    parts = SENTENCE_END_RE.split(text)
    sentences = [p.strip() for p in parts if p.strip()]
    return sentences


def group_runs(pages):
    """Group consecutive pages that share the same chapter+lesson."""
    runs = []
    cur = []

    def key(p):
        return (p.get("chapter_id"), p.get("chapter_title"),
                p.get("lesson_id"), p.get("lesson_title"))

    for p in pages:
        if cur and key(p) != key(cur[-1]):
            runs.append(cur)
            cur = []
        cur.append(p)
    if cur:
        runs.append(cur)
    return runs


def assemble_chunks(run, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Chunk a run of same-lesson pages, keeping each sentence's source page.

    `run` is a list of page dicts. Returns records of the same shape as the
    previous per-page version, except chunks may now span page boundaries; the
    `page` key is the page of the chunk's first sentence.
    """
    sentences = []  # list of (text, page)
    for page in run:
        for s in split_sentences(page["text"]):
            sentences.append((s, page["page"]))
    n = len(sentences)
    if n == 0:
        return []

    starts = []
    acc = 0
    for s, _page in sentences:
        starts.append(acc)
        acc += len(s) + 1
    total = acc  # total joined length

    def first_idx_at(pos):
        """Smallest sentence index whose start position >= pos."""
        lo, hi = 0, n
        while lo < hi:
            mid = (lo + hi) // 2
            if starts[mid] < pos:
                lo = mid + 1
            else:
                hi = mid
        return lo

    # Metadata shared by all pages in the run (they share chapter+lesson).
    meta = run[0]

    chunks = []
    char_start = 0
    idx = 1
    while char_start < total:
        a = first_idx_at(char_start)
        if a >= n:
            break

        buf = sentences[a][0]
        b = a + 1
        while b < n and (starts[b] + len(sentences[b][0]) - char_start) < size:
            buf += " " + sentences[b][0]
            b += 1

        if buf.strip():
            covered_pages = sorted({sentences[i][1] for i in range(a, b)})
            first_page = covered_pages[0]
            record = {
                "chunk_id": f"p{first_page:03d}_{idx:03d}",
                "page": first_page,
                "page_start": covered_pages[0],
                "page_end": covered_pages[-1],
                "chapter_id": meta["chapter_id"],
                "chapter_title": meta["chapter_title"],
                "lesson_id": meta["lesson_id"],
                "lesson_title": meta["lesson_title"],
                "text": buf.strip(),
            }
            if len(record["text"]) < MIN_CHUNK_CHARS and chunks:
                # Merge a tiny artifact chunk into the previous one to cut noise.
                chunks[-1]["text"] = chunks[-1]["text"] + " " + record["text"]
                chunks[-1]["page_end"] = max(chunks[-1].get("page_end", chunks[-1]["page"]),
                                             record["page_end"])
            else:
                chunks.append(record)
                idx += 1

        # Window end character offset is where sentence b-1 ends.
        window_end = starts[b - 1] + len(sentences[b - 1][0])
        # Next window should start `overlap` chars before the current window end.
        target = window_end - overlap
        next_pos = first_idx_at(target)
        # Guarantee forward progress: always advance at least to the next sentence.
        if next_pos <= a:
            next_pos = a + 1
        if next_pos >= n:
            break
        char_start = starts[next_pos]
    return chunks


def main():
    parser = argparse.ArgumentParser(description="Chunk the structured textbook")
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not os.path.exists(args.input):
        sys.exit(f"Input not found: {args.input}")

    with open(args.input, "r", encoding="utf-8") as f:
        pages = json.load(f)

    all_chunks = []
    for run in group_runs(pages):
        all_chunks.extend(assemble_chunks(run))

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    lens = [len(c["text"]) for c in all_chunks]
    print(f"Chunked into {len(all_chunks)} chunks -> {args.output}")
    print(f"  size min={min(lens) if lens else 0} max={max(lens) if lens else 0} avg={sum(lens)//max(len(lens),1)}")
    # Show a small sample of coverage.
    pages_covered = sorted({c["page"] for c in all_chunks})
    print(f"  pages covered: {pages_covered}")


if __name__ == "__main__":
    main()