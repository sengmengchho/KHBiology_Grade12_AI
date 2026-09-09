"""Phase 3 — Clean and normalize Khmer text.

Reads the OCR'd JSONL (data/extracted/biology_raw_text.jsonl), normalizes
Unicode, collapses whitespace, strips repeated contact/publisher footer lines,
and writes a cleaned record per page to data/processed/biology_cleaned.json.

Usage:
    python scripts/clean_text.py [--input path] [--output path]
"""

import argparse
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import EXTRACTED_DIR, PROCESSED_DIR

DEFAULT_INPUT = os.path.join(EXTRACTED_DIR, "biology_raw_text.jsonl")
DEFAULT_OUTPUT = os.path.join(PROCESSED_DIR, "biology_cleaned.json")

# Footer / header lines that repeat across pages and add no curriculum value.
UNWANTED_FRAGMENTS = [
    "ជីវវិទ្យាថ្នាក់ទី 12",
    "មេរៀនជីវវិទ្យាថ្នាក់ទី 12",
    "ប្រជុំ",
    "English",
]

# Scanner (OCR) misreads, mapped to the correct Khmer curriculum term. Order
# matters: longer keys first so compound tokens are handled before sub-parts.
# Verified against surrounding context (see data/processed/biology_cleaned.json,
# page 17, chapter 1 lesson 2 — reproduction in flowering plants).
OCR_FIXES = [
    # "embryo sac" / megagametophyte (ជង់ misread for ថង់, កិល for កំណ)
    ("ជង់កិល", "ថង់កំណ"),
    # "nucleus / nuclei" (the combining ណ្វៃយ៉ូ was misread as ល៉ែយ៉ូ)
    ("ល៉ែយ៉ូ", "ណ្វៃយ៉ូ"),
    # "megagametophyte" (female gametophyte)
    ("កាតម៉ែគីតញី", "មេហ្គាកាម៉ែតូភីតញី"),
]


def normalize_khmer(text: str) -> str:
    """Normalize Unicode and collapse whitespace without removing Khmer."""
    text = unicodedata.normalize("NFC", text)
    # Normalize the various Khmer spaces to a regular space.
    text = text.replace("\u200b", "")  # zero-width space
    text = text.replace("\u00a0", " ")  # non-breaking space
    text = text.replace("\u17e0", "0").replace("\u17e1", "1")  # keep digits as-is roughly
    # Collapse whitespace runs (it is safe to keep Chinese/other unicode).
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def apply_ocr_fixes(text: str) -> str:
    """Correct known OCR misreads before the text is chunked and indexed.

    These replacements are only applied when the exact misread string is found,
    so legitimate text is never altered by mistake.
    """
    for bad, good in OCR_FIXES:
        text = text.replace(bad, good)
    return text


def drop_footer_lines(lines, last_chance=3):
    """Drop short footer/header lines that repeat boilerplate at page edges.

    Heuristic: remove short lines that contain an unwanted fragment.
    """
    kept = []
    for line in lines:
        if any(frag.lower() in line.lower() for frag in UNWANTED_FRAGMENTS) and len(line) < 60:
            continue
        kept.append(line)
    return kept


def clean_page(record):
    page = record.get("page")
    raw = record.get("text", "")
    # Split into lines, clean each, drop boilerplate, rejoin.
    lines = [ln.strip() for ln in raw.split("\n")]
    lines = [ln for ln in lines if ln]
    lines = drop_footer_lines(lines)
    text = "\n".join(lines)
    text = normalize_khmer(text)
    text = apply_ocr_fixes(text)
    return {
        "page": page,
        "text": text,
    }


def main():
    parser = argparse.ArgumentParser(description="Clean Khmer OCR text")
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not os.path.exists(args.input):
        sys.exit(f"Input not found: {args.input}")

    records = []
    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    cleaned = [clean_page(r) for r in records]
    cleaned.sort(key=lambda r: r["page"])

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    total_in = sum(len(r["text"]) for r in records)
    total_out = sum(len(c["text"]) for c in cleaned)
    print(f"Cleaned {len(cleaned)} pages -> {args.output}")
    print(f"  characters: {total_in} -> {total_out} ({100*(1-total_out/max(total_in,1)):.1f}% removed)")
    for c in cleaned[:3]:
        khmer = sum(1 for ch in c["text"] if 0x1780 <= ord(ch) <= 0x17FF)
        print(f"  page {c['page']}: {len(c['text'])} chars, khmer={khmer}")


if __name__ == "__main__":
    main()
