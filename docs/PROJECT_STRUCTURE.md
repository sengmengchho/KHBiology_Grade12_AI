# Project Structure

This document is the map of the repository. Each active file has one job.
Historical files are kept in archive folders and are not part of the normal
runtime or test path.

## Directory overview

```text
D:\Khmer Biology AI Tutor\
|-- app/                      Streamlit runtime only
|-- scripts/
|   |-- pipeline/             textbook build pipeline (OCR -> clean -> parse -> chunk -> index)
|   |-- evaluation/           retrieval, answer, corpus, and measurement evaluation
|   `-- archive/              superseded scripts and one-off experiments
|-- tests/                    active regression suites
|-- data/
|   |-- raw/                  source PDFs
|   |-- extracted/            raw OCR JSONL
|   |-- processed/            cleaned, structured, and chunked textbook
|   |-- glossary/             generated glossary
|   `-- evaluation/           current evaluation artifacts + archive/
|-- docs/                     current reports + history/
|-- vector_db/                Chroma database
|-- SKILL.md                  project-specific working instructions
`-- README.md                 project overview
```

## app/ — runtime

| File | Task |
|---|---|
| `app/main.py` | Streamlit UI and the real request flow: normalize, split, retrieve, rerank, abstain, generate, format. |
| `app/config.py` | Environment variables, paths, model names, retrieval settings, threshold. |
| `app/retrieval.py` | Embedding model, Chroma access, retrieval, reranking. |
| `app/rag.py` | Answer generation, model-pool rotation, reduced-context fallback. |
| `app/prompt.py` | System prompts, answer formatting, citation parsing/sanitization, page ranges. |
| `app/ocr.py` | OCR for a student-uploaded question image. |
| `app/utils.py` | Query normalization, question splitting, query expansion, Khmer text fixes. |

## scripts/pipeline/ — textbook build

Run from the project root. Direct paths also work because each script adds the
project root to `sys.path`.

| File | Task | Main output |
|---|---|---|
| `ocr_gemini.py` | OCR PDF pages with Gemini. | `data/extracted/biology_raw_text.jsonl` |
| `ocr_ollama.py` | OCR PDF pages with local Ollama. | `data/extracted/biology_raw_text.jsonl` |
| `clean_text.py` | Normalize Khmer text and apply verified OCR fixes. | `data/processed/biology_cleaned.json` |
| `parse_lessons.py` | Attach chapter/lesson/page metadata. | `data/processed/biology_structured.json` |
| `chunk_text.py` | Split pages into sentence-safe, page-labelled chunks. | `data/processed/biology_chunks.json` |
| `build_vector_db.py` | Embed chunks and rebuild the Chroma collection. | `vector_db/` |
| `build_glossary.py` | Extract term/definition pairs from chunks. | `data/glossary/glossary.{json,md}` |

## scripts/evaluation/ — measurement

| File | Task |
|---|---|
| `common.py` | Shared gold loading, query preparation, page-hit metrics, and part-level helpers. |
| `evaluate_retrieval.py` | Retrieval evaluation on `gold_questions_v2.json`: embed, rerank, real path, abstention. |
| `evaluate_answers.py` | End-to-end answer evaluation with the 7-dimension rubric, plus strict and alias-aware scoring. |
| `rescore_phase3_1.py` | No-Gemini Phase 3.1 rescoring: reproduce strict baseline, write alias-aware outputs and comparison. |
| `validate_corpus.py` | Corpus integrity audit: pages, chapters, chunks, IDs, page ranges, stale OCR forms. |

## tests/ — active regression suites

| File | Task |
|---|---|
| `test_citation_integrity.py` | Citation parsing, sanitization, page ranges, footer selection, stored-row replays. |
| `test_eval_harness.py` | Splitter, query expansion, OCR/query sync, gold labels, scoring, fallback scoring. |
| `test_measurement_integrity.py` | Verified aliases, contextual guards, negative controls, strict baseline, target questions, determinism. |
| `test_rag_fallback.py` | Gemini model rotation and reduced-context fallback. |
| `run_all.py` | Runs all four suites in order and returns a single exit code. |

## data/evaluation/ — current source of truth

| Artifact | Meaning |
|---|---|
| `gold_questions_v2.json` | Frozen gold questions, concepts, and pages. Do not edit without explicit approval. |
| `answer_evaluations_v3_1_citation.json` | Frozen 45 saved answers and accepted strict baseline scores. |
| `answer_evaluation_v3_1_citation_summary.txt` | Accepted strict summary: means, abstention, invalid citations. |
| `answer_evaluations_v3_1_citation_alias_aware.json` | Alias-aware rescoring of the same answers (separate artifact). |
| `answer_evaluation_v3_1_citation_comparison.json` | Full strict-vs-alias comparison, per-question deltas, hashes. |
| `answer_evaluation_v3_1_citation_comparison.csv` | Spreadsheet-friendly comparison. |
| `answer_evaluation_v3_1_citation_comparison_summary.txt` | Short human-readable comparison. |
| `gold_support_audit_phase3_1.json` | Evidence audit of the eight target questions. |
| `measurement_integrity_phase3_1.md` | Phase 3.1 report and verdict. |
| `answer_quality_diagnosis_phase3.md` | Phase 3 answer-quality diagnosis. |
| `answer_review_v3_1_citation.csv` | Manual review sheet for the accepted baseline. |
| `retrieval_v3_1_results.json`, `retrieval_v3_1_summary.txt` | Current retrieval baseline. |
| `corpus_validation_v3.json` | Current corpus validation output. |

`data/evaluation/archive/` contains superseded runs (v1/v2/v3), old logs, q84
variants, dumps, and calibration artifacts. Nothing there is required to run
the app or the current tests, except the historical replay fixtures explicitly
read by `tests/test_citation_integrity.py`.

## docs/

| Path | Meaning |
|---|---|
| `docs/PROJECT_STRUCTURE.md` | This file. |
| `docs/citation_context_integrity_phase2.md` | Phase 2 citation/context report. |
| `docs/failure_analysis_v3_1.md` | v3.1 failure diagnosis. |
| `docs/system_accuracy_evaluation_v3_1.md` | Current system accuracy report. |
| `docs/corpus_audit.md` | Corpus audit notes. |
| `docs/retrieval_evaluation.md` | Retrieval evaluation notes. |
| `docs/history/` | Superseded reports, old README, and OCR notes. |

## archives

| Path | Contains |
|---|---|
| `scripts/archive/` | Superseded v1 evaluators, gold builders, one-off experiments, old smoke/UI tests, report generator. |
| `data/evaluation/archive/` | Historical evaluation runs, logs, dumps, q84 variants, calibration scores. |
| `docs/history/` | Superseded reports and OCR notes. |
| `archive/root/` | Root-level scratch files and old data-root logs. |

Archived code is kept for reproducibility. It may still reference old paths;
use it only when replaying a historical result.

### What is versioned

| Path | Git behavior |
|---|---|
| `app/`, `scripts/pipeline/`, `scripts/evaluation/`, `tests/` | Commit |
| `scripts/archive/`, `docs/history/` | Commit (small historical reference) |
| Current `data/evaluation/` artifacts | Commit (source of truth) |
| `data/evaluation/archive/` | Ignore, except two replay fixtures |
| `data/raw/*.pdf`, `data/processed/*.json`, `data/processed/archive_v3/`, `vector_db/`, `.venv/` | Ignore (large or generated) |
| `archive/root/` | Ignore (local scratch) |

The two tracked archive fixtures are
`data/evaluation/archive/answer_evaluations_v3.json` and
`data/evaluation/archive/answer_evaluations_v3_q84.json`, read by
`tests/test_citation_integrity.py`.

## Command cheat sheet

```powershell
# Textbook pipeline
python -m scripts.pipeline.clean_text
python -m scripts.pipeline.parse_lessons
python -m scripts.pipeline.chunk_text
python -m scripts.pipeline.build_vector_db
python -m scripts.pipeline.build_glossary

# Evaluation
python -m scripts.evaluation.evaluate_retrieval --tag <tag>
python -m scripts.evaluation.evaluate_answers --tag <tag>
python -X utf8 scripts/evaluation/rescore_phase3_1.py
python -X utf8 scripts/evaluation/validate_corpus.py

# All active tests
python -X utf8 tests/run_all.py
```

## Where to change what

| Goal | Edit |
|---|---|
| Change the UI or request flow | `app/main.py` |
| Change retrieval or reranking | `app/retrieval.py` (+ `app/config.py`) |
| Change generation or fallback behavior | `app/rag.py`, `app/prompt.py` |
| Fix query-side Khmer spelling | `app/utils.py` (`QUERY_FIXES`, expansions) |
| Fix corpus-side Khmer spelling | `scripts/pipeline/clean_text.py` (`OCR_FIXES`) |
| Change chunking or metadata | `scripts/pipeline/parse_lessons.py`, `scripts/pipeline/chunk_text.py` |
| Change evaluation dimensions or aliases | `scripts/evaluation/evaluate_answers.py` |
| Change gold data | `data/evaluation/gold_questions_v2.json` only with explicit approval |
| Add a regression test | `tests/` and register it in `tests/run_all.py` |

## Locked baselines

Do not change these without explicit approval:

- `TOP_K`, `RERANKER_TOP_K`, chunk size/overlap
- the `0.08` abstention threshold
- the embedding model, reranker, or Chroma collection
- `data/evaluation/gold_questions_v2.json` concepts and labels
- the accepted strict answer baseline and its summary
