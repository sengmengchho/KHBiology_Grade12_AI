# OCR STATUS  (2026-09-08)
EXTRACTED: 197 / 257 pages in data/extracted/biology_raw_text.jsonl
  models used: legacy(12), 3.5-flash-lite(51), 3.1-flash-lite(50),
               flash-lite-latest(50), 3.5-flash(18), 3.7-flash(12),
               3.6-flash(1), 3.8-flash(3)
Pipeline on 197 pages: cleaned -> parsed (ch1-6) -> 834 chunks -> Chroma vector_db
RETRIEVAL: validated OK on full corpus (DNA->p159, gymnosperm->p6, angiosperm->p12,
           pine life cycle->p9, cycads->p7)
REMAINING: 60 pages. Each Gemini model has fresh 20/day+s tomorrow.
RESUME:  python scripts\ocr_gemini.py --models "gemini-3.6-flash,gemini-3.5-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-flash-lite-latest,gemini-3.8-flash,gemini-3.7-flash"
  then rebuild: clean_text.py -> parse_lessons.py -> chunk_text.py -> build_vector_db.py
OTHER MODELS PROBED: 2.5-flash / 2.5-flash-lite = retired(404); omni-1.1-flash = quota; flash-latest = quota
