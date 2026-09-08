"""OCR the Grade 12 Biology SalaDigital scan using local Ollama vision model.

Free, offline, unlimited. Renders each PDF page to a PNG, sends it to the
local Ollama vision model (gemma3:4b) for Khmer transcription, and appends
JSONL to data/extracted/biology_raw_text.jsonl. Resumable: skips pages that
already exist in the output file.

Usage:
    python scripts/ocr_ollama.py [--pages 0-30] [--sleep 0.5] [--max-pages 50]
"""

import argparse
import base64
import json
import os
import sys
import urllib.request

import pymupdf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import BASE_DIR, EXTRACTED_DIR, OLLAMA_BASE_URL

DEFAULT_PDF = os.path.join(BASE_DIR, "data", "raw", "biology_grade12_saladigital.pdf")
OUTPUT_JSONL = os.path.join(EXTRACTED_DIR, "biology_raw_text.jsonl")
MODEL = "gemma3:4b"
DPI = 150

TRANSCRIBE_PROMPT = (
    "Please transcribe all text on this textbook page exactly as written, "
    "in Khmer. Preserve headings, subheadings, and numbered lists. "
    "Output only the plain-text transcription, no commentary. "
    "Start directly with the page content."
)


def render_page(doc, page_index, dpi=DPI):
    page = doc[page_index]
    pix = page.get_pixmap(dpi=dpi)
    return pix.tobytes("png")


def ask_ollama(prompt: str, image_bytes: bytes) -> str:
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "images": [base64.b64encode(image_bytes).decode("ascii")],
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 4000},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body.get("response", "").strip()


def main():
    parser = argparse.ArgumentParser(description="OCR Biology PDF via local Ollama")
    parser.add_argument("--pdf", default=DEFAULT_PDF)
    parser.add_argument("--out", default=OUTPUT_JSONL)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)
    parser.add_argument("--dpi", type=int, default=DPI)
    parser.add_argument("--pages", type=str, default="",
                        help="Comma-separated page ranges/indices, e.g. 0-5,14")
    parser.add_argument("--sleep", type=float, default=0.0,
                        help="Seconds to pause between pages.")
    parser.add_argument("--max-pages", type=int, default=0,
                        help="Stop after at most this many new pages this run (0 = unlimited).")
    args = parser.parse_args()

    doc = pymupdf.open(args.pdf)

    if args.pages:
        indices = set()
        for part in args.pages.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                a, b = part.split("-")
                indices.update(range(int(a), int(b) + 1))
            else:
                indices.add(int(part))
        indices = sorted(indices)
    else:
        end = args.end if args.end is not None else len(doc)
        indices = list(range(args.start, min(end, len(doc))))

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    existing = set()
    if os.path.exists(args.out):
        with open(args.out, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    existing.add(json.loads(line)["page"])

    processed = 0
    for idx in indices:
        if idx in existing:
            print(f"page {idx:>3}: skip (already done)")
            continue
        if args.max_pages and processed >= args.max_pages:
            print(f"Reached --max-pages={args.max_pages}; stopping early.")
            break
        img = render_page(doc, idx, args.dpi)
        try:
            text = ask_ollama(TRANSCRIBE_PROMPT, img)
        except Exception as err:  # noqa: BLE001
            print(f"page {idx:>3}: ERROR {err}")
            continue
        if not text:
            print(f"page {idx:>3}: empty response, skipping")
            continue
        with open(args.out, "a", encoding="utf-8") as f:
            f.write(json.dumps({"page": idx, "text": text}, ensure_ascii=False) + "\n")
        processed += 1
        khmer = sum(1 for c in text if 0x1780 <= ord(c) <= 0x17FF)
        print(f"page {idx:>3}: {len(text)} chars, khmer={khmer}")
        sys.stdout.flush()
        if args.sleep:
            import time
            time.sleep(args.sleep)

    done = len(existing) + processed
    print(f"\nDone. {done}/{len(doc)} pages in {args.out}")


if __name__ == "__main__":
    main()