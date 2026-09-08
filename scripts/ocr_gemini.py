"""OCR the Grade 12 Biology SalaDigital scan using Gemini multimodal.

Renders each PDF page to a high-resolution PNG, sends it to Gemini for
Khmer transcription, and saves the result as JSONL to data/extracted/.
"""

import argparse
import json
import os
import sys
import time

import pymupdf
from google.genai import Client
from google.genai import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import BASE_DIR, EXTRACTED_DIR, GOOGLE_API_KEY, LLM_MODEL

DEFAULT_PDF = os.path.join(BASE_DIR, "data", "raw", "biology_grade12_saladigital.pdf")
OUTPUT_JSONL = os.path.join(EXTRACTED_DIR, "biology_raw_text.jsonl")
DPI = 150
RETRY_ATTEMPTS = 3

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


class QuotaExceededError(Exception):
    pass


class BusyError(Exception):
    pass


def transcribe_page(client, img_bytes, model=LLM_MODEL):
    last_err = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            resp = client.models.generate_content(
                model=model,
                contents=[
                    TRANSCRIBE_PROMPT,
                    types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                ],
            )
            if resp.text and resp.text.strip():
                return resp.text.strip()
        except Exception as err:  # noqa: BLE001
            msg = str(err)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                raise QuotaExceededError(msg)
            if "503" in msg or "UNAVAILABLE" in msg:
                raise BusyError(msg)
            last_err = err
            time.sleep(2 * (attempt + 1))
    if last_err:
        raise last_err
    return ""


class ModelPool:
    """Round-robin generator across models; yields None when all are quota-exhausted."""

    def __init__(self, models):
        self.models = list(models)
        self.counts = {m: 0 for m in self.models}
        self.dead = set()
        self.busy = {m: 0.0 for m in self.models}  # model -> unix ts when it may be retried

    def _alive(self):
        return [m for m in self.models if m not in self.dead]

    def next(self):
        now = time.time()
        alive = [m for m in self._alive() if now >= self.busy[m]]
        if not alive:
            return None
        return min(alive, key=lambda m: self.counts[m])

    def record(self, model, success):
        if success:
            self.counts[model] += 1
        else:
            self.dead.add(model)

    def cooldown(self, model, seconds):
        self.busy[model] = time.time() + seconds

    def all_done(self):
        return not self._alive()


def main():
    parser = argparse.ArgumentParser(description="OCR Grade 12 Biology PDF via Gemini")
    parser.add_argument("--pdf", default=DEFAULT_PDF)
    parser.add_argument("--out", default=OUTPUT_JSONL)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)
    parser.add_argument("--dpi", type=int, default=DPI)
    parser.add_argument("--pages", type=str, default="",
                        help="Comma-separated page ranges/indices to process, e.g. 0-5,14")
    parser.add_argument("--sleep", type=float, default=0.5,
                        help="Seconds to pause between pages (rate limiting).")
    parser.add_argument("--max-pages", type=int, default=0,
                        help="Stop after processing at most this many new pages this run (0 = unlimited).")
    parser.add_argument("--models", type=str, default=LLM_MODEL,
                        help="Comma-separated Gemini model IDs to rotate through for OCR.")
    args = parser.parse_args()

    if not GOOGLE_API_KEY:
        sys.exit("GOOGLE_API_KEY is not set in .env")

    client = Client(api_key=GOOGLE_API_KEY)
    pool = ModelPool([m.strip() for m in args.models.split(",") if m.strip()])
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

    records = []
    processed = 0
    stopped_on_quota = False
    for idx in indices:
        if idx in existing:
            print(f"page {idx:>3}: skip (already done)")
            continue
        if args.max_pages and processed >= args.max_pages:
            print(f"Reached --max-pages={args.max_pages}; stopping early.")
            break
        img = render_page(doc, idx, args.dpi)
        model = None
        quota_hits = 0
        busy_waits = 0
        text = ""
        while True:
            model = pool.next()
            if model is None:
                if pool.all_done():
                    print(f"page {idx:>3}: all models quota-exhausted; stopping for the day.")
                    stopped_on_quota = True
                    break
                now = time.time()
                wait = min(pool.busy[m] for m in pool.models) - now
                if wait <= 0 or busy_waits > 40:
                    print("  all models busy for too long; stopping for now (resume later).")
                    stopped_on_quota = True
                    break
                print(f"  all busy, waiting {wait:.0f}s ...")
                time.sleep(min(wait + 1, 30))
                busy_waits += 1
                continue
            try:
                text = transcribe_page(client, img, model=model)
                pool.record(model, True)
                break
            except QuotaExceededError:
                print(f"  model {model}: daily quota exhausted; marking dead.")
                pool.record(model, False)
                quota_hits += 1
            except BusyError:
                print(f"  model {model}: busy; cooling down. retry another model.")
                pool.cooldown(model, 20)
                busy_waits += 1
            except Exception as err:  # noqa: BLE001
                print(f"  model {model}: transient error; retry later. ({str(err)[:80]})")
                pool.cooldown(model, 15)
                busy_waits += 1
        if stopped_on_quota or not text:
            if stopped_on_quota:
                break
            print(f"page {idx:>3}: gave up after repeated failures; see above.")
        if not text:
            continue
        records.append({"page": idx, "text": text, "model": model})
        with open(args.out, "a", encoding="utf-8") as f:
            f.write(json.dumps({"page": idx, "text": text, "model": model}, ensure_ascii=False) + "\n")
        processed += 1
        print(f"page {idx:>3}: {len(text)} chars [{model}] (pool: "
              + ", ".join(f"{m}={pool.counts[m]}/20" for m in pool.models) + ")")
        sys.stdout.flush()
        if args.sleep:
            time.sleep(args.sleep)

    print(f"\nDone. Processed {len(records)} new pages -> {args.out}")
    print("Per-model today:", ", ".join(f"{m}={pool.counts[m]}/20" for m in pool.models))
    if stopped_on_quota:
        print("Daily free-tier quota used up across pool. Rerun tomorrow to resume (or add more models).")


if __name__ == "__main__":
    main()
