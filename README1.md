# KhmerBio Tutor — Progress Report (2026-09-08)

## What Was Completed

### OCR of the Grade 12 Biology textbook
- Evaluated all free OCR options; the only viable engine is the Gemini API free tier (all free-local engines failed: Ollama gemma3:4b / qwen2.5vl:7b hallucinate Khmer loops, EasyOCR / PaddleOCR / RapidOCR have no Khmer model, Tesseract is only ~67% accurate).
- Discovered that each Gemini model carries its own independent free quota (20+ requests/day/model), so quota can be multiplied by rotating models.
- Added model rotation + retry/cooldown handling to `scripts/ocr_gemini.py`.
- OCR'd **197 / 257 pages** into `data/extracted/biology_raw_text.jsonl` (pages 0–196, gaps in the 190s remain).
- Every page saves immediately, so the script resumes cleanly across quota limits and crashes.

### RAG pipeline rebuilt on the full corpus
- `scripts/clean_text.py` → 197 pages cleaned → `data/processed/biology_cleaned.json`
- `scripts/parse_lessons.py` → chapters 1–6 with lessons detected → `data/processed/biology_structured.json`
- `scripts/chunk_text.py` → **834 chunks** → `data/processed/biology_chunks.json`
- `scripts/build_vector_db.py` → Chroma collection `biology` rebuilt (834 chunks, BGE-M3 embeddings) in `vector_db/`
- `scripts/test_retrieval.py` → retrieval validated on the full corpus:
  - "តើ DNA មានតួនាទីអ្វី?" → page 159 (ch 5)
  - "ស៊ីមណូស្ពែមមានលក្ខណៈអ្វីខ្លះ?" → page 6 (ch 1)
  - "តើអង់ស្យូស្ពែមជាអ្វី?" → page 12 (ch 1)
  - "ពន្យល់ពីវដ្តជីវិតរបស់ស្រល់" → page 9 (ch 1)
  - "cycads ជាអ្វី?" → page 7 (ch 1)

## What Will Be Done Tomorrow

1. **Finish OCR of the remaining ~60 pages** (today's free quotas are exhausted / models are 503-busy; each model's quota resets daily):
   ```
   python scripts\ocr_gemini.py --models "gemini-3.6-flash,gemini-3.5-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-flash-lite-latest,gemini-3.8-flash,gemini-3.7-flash"
   ```
2. **Re-run the pipeline** on the complete 257 pages:
   ```
   python scripts\clean_text.py
   python scripts\parse_lessons.py
   python scripts\chunk_text.py
   python scripts\build_vector_db.py
   ```
3. **Re-validate retrieval** with `python scripts\test_retrieval.py --n 5` on the final corpus.
4. (If Gemini answering quota is available) re-test the end-to-end RAG answer path.

## Quick Reference

- OCR status & engine evaluation: `data/OCR_STATUS.md`, `data/OCR_ENGINE_EVAL.md`
- Config: `.env` (`LLM_PROVIDER=google`, `GOOGLE_API_KEY`, `LLM_MODEL=gemini-3.6-flash`)
- App: `app/main.py` (Streamlit UI), `app/rag.py`, `app/retrieval.py`, `app/prompt.py`, `app/config.py`