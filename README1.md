# KhmerBio Tutor — Progress & Next Steps

AI study assistant for Cambodian Grade 12 Biology, grounded strictly in the national textbook.

## What has been done so far

### 1. OCR & corpus
- Extracted **257/257 pages** of the Grade 12 Biology textbook using Gemini (`scripts/ocr_gemini.py`). Status tracked in `data/OCR_STATUS.md`.
- Pipeline rebuilt over the full corpus:
  `clean_text.py` → `parse_lessons.py` → `chunk_text.py` → `build_vector_db.py`
- **1,093 chunks** (size 500, overlap 100) covering all 257 pages, organized into **8 chapters**.

### 2. Corpus audit — PASS
- No missing / duplicate / empty / broken pages.
- All 257 pages covered by chunks; only 7 TOC chunks (pages 0–3) lack chapter metadata (expected).
- Known cosmetic issue: OCR-garbled chapter/lesson titles.

### 3. Retrieval pipeline
- Embeddings: `BAAI/bge-m3`; reranker: `BAAI/bge-reranker-v2-m3`; Chroma (cosine), collection `biology`.
- `TOP_K=20` → rerank → `RERANKER_TOP_K=5` fed to the LLM.

### 4. Evaluation suite
- **89-question dataset** (`data/evaluation/evaluation_questions.json`) covering all 8 chapters; types: definition, explanation, process, reasoning, summary, comparison, exam, quiz.
- `scripts/evaluate_retrieval.py` — resumable retrieval evaluation.
- `scripts/evaluate_answers.py` — resumable RAG answer evaluation (`--sample`, `--questions`, `--score-only`).

### 5. Retrieval evaluation results
| Metric | BGE-M3 only | BGE-M3 + reranker |
|---|---|---|
| Recall@1 (Hit@1) | 0.404 | **0.506** |
| Recall@3 | 0.719 | **0.787** |
| Recall@5 | 0.899 | 0.843 |
| MRR | 0.573 | **0.646** |

Verdict: keep the reranker. Full report: `docs/retrieval_evaluation.md`.

### 6. RAG answer evaluation
- **v1 (primary model `gemini-3.6-flash` had quota):** concept coverage mean **0.74**, page recall mean **0.89** (20/20 ≥ 0.5).
- **v2 (re-run on fallback pool models, primary quota exhausted):** concept coverage mean **0.58**, page recall mean **0.89**.
- Outcome: citation/pages are reliable regardless of model; answer depth drops sharply on weaker fallback models. **Model availability is the #1 quality variable.**

### 7. Hallucination protection
- **Retrieval-confidence gate:** if the best reranked chunk scores below `RETRIEVAL_SCORE_THRESHOLD`, the app politely abstains instead of guessing.
- Threshold **calibrated on all 89 questions** (`data/evaluation/top_rerank_scores.json`): on-topic median 0.92 (p25 0.76), off-topic ~0.005 → threshold set to **0.08** (the earlier 0.20 rejected valid questions such as a DNA question scoring 0.195).
- **Model-pool rotation** in `app/rag.py::_call_google_rotate`: primary model first, then the `GOOGLE_MODEL_POOL` chain on 429/503; skips models that return empty or <80-char responses.
- Config: `RETRIEVAL_SCORE_THRESHOLD`, `GOOGLE_MODEL_POOL` in `app/config.py`.

### 8. Streamlit app (`app/main.py`)
- Modes: **Normal / Easy / Exam**; features: **Explain / Quiz / Summary**.
- Cached embedding/reranker/vector-DB resources; Khmer error handling; chat clear button.
- Citations (`ប្រភព`) fixed: chapter/lesson/page labels now clipped to 16 chars (garbled OCR titles no longer bloat them).

### 9. Biology glossary
- `scripts/build_glossary.py` extracts terms + definitions from the 1,093 chunks (no LLM calls).
- **51 unique terms** with definition, English gloss, page, chapter → `data/glossary/glossary.json` + `glossary.md`.
- Capacity note: exact term-matching is limited by OCR spelling noise; LLM-assisted curation is the natural next upgrade.

## Known issues to improve
1. **Fallback model quality** — when quota is exhausted, pool models produce short/mid-quality answers (concept coverage 0.74 → 0.58). Mitigations: stronger-only pool, better prompts for weak models, answer-caching/resume across days, retry the primary model later.
2. **OCR-garbled titles** in metadata (cosmetic; affected citations — mitigated by clipping).
3. **7 TOC chunks** lack chapter metadata (expected; excluded from chapter grouping).
4. **Interactive QA pending** — browser testing of every mode/feature is the immediate next step.

## Next steps (in order)
1. **Manual browser QA** — test Normal / Easy / Exam + Explain / Quiz / Summary + out-of-scope + clear-chat. Judge correctness, clarity, usefulness, Grade-12 suitability, source accuracy. (Note: if testing same day as heavy use, answers may come from fallback models.)
2. **Re-run the 20-answer evaluation** on a fresh day / with primary-model quota to measure best-case quality, and compare against v1/v2.
3. **Fix remaining problems** — only those surfaced by QA/evaluation.
4. **Student/teacher testing** — share with real Grade 12 students and Biology teachers; collect ratings and comments.
5. **Apply real-user feedback** — improve wording, terminology, explanation clarity, answer length, quiz quality, source presentation.
6. **Deploy** — only after steps 1–5 look good.
7. **Fine-tune only if still needed** — reserve for repeated problems prompting/RAG cannot solve.

## Key files
- `app/` — Streamlit UI (`main.py`), RAG (`rag.py`), prompts (`prompt.py`), retrieval (`retrieval.py`), config (`config.py`)
- `scripts/` — OCR, cleaning, chunking, vector DB, evaluation, threshold calibration, glossary
- `data/evaluation/` — 89-question dataset, retrieval + answer results, top-score calibration data
- `data/glossary/` — generated glossary (JSON + Markdown)
- `docs/` — `corpus_audit.md`, `retrieval_evaluation.md`