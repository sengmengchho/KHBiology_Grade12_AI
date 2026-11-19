---
name: khmer-bio-rag-improver
description: Diagnose and improve answer quality, Khmer terminology, citation integrity, and evaluation rubrics for the KhmerBio Tutor Grade 12 Biology RAG system.
---

# KhmerBio Tutor — RAG Diagnosis & Improvement Skill

## Project Overview
KhmerBio Tutor is a Retrieval-Augmented Generation (RAG) AI tutor for Cambodian Grade 12 Biology in Khmer, grounded in the official MoEYS textbook (257 pages, 8 chapters, 567 validated chunks).

- **Retrieval:** `BAAI/bge-m3` + ChromaDB (`vector_db/`) + `BAAI/bge-reranker-v2-m3`
- **Generation:** Google Gemini (`app/rag.py`, `app/prompt.py`)
- **Normalization:** `scripts/pipeline/clean_text.py` (`OCR_FIXES`) and `app/utils.py` (`QUERY_FIXES`)
- **Abstention Guard:** Top rerank score `< 0.08` returns `NOT_FOUND`

## Locked Baselines (Do Not Modify Without Explicit Approval)
- **Corpus & Vector DB:** 567 chunks with `page_start`/`page_end` metadata (`Recall@5 = 1.000`, `MRR = 0.785`, `0/116` false abstentions).
- **Do NOT change:** `TOP_K`, `RERANKER_TOP_K`, chunk size/overlap, the `0.08` threshold, Chroma embeddings, or `data/evaluation/gold_questions_v2.json` unless explicitly instructed.

## Standard Diagnostic & Improvement Workflow
1. **Inspect Evidence First:**
   - Check saved evaluation artifacts (`data/evaluation/answer_evaluations_v3_1_citation.json`, the `_alias_aware` / `_comparison` outputs, `gold_support_audit_phase3_1.json`, and `docs/failure_analysis_v3_1.md`).
   - Compare the student question, retrieved context chunks, `raw_answer`, sanitized `answer`, and citation footer against the textbook pages in `data/processed/biology_cleaned.json`.
2. **Classify the Issue Correctly:**
   - **Terminology/OCR Mismatch:** Fix in `app/utils.py` (`QUERY_FIXES` / `_TOPIC_EXPANSIONS`) and keep in sync with `scripts/pipeline/clean_text.py`. Never add a plain `str.replace` key that is a prefix of a valid Khmer word.
   - **Prompt/Generation Behavior:** Refine instructions in `app/prompt.py` using generalizable rules (never hardcode benchmark question IDs).
   - **Citation/Context Formatting:** Check `app/prompt.py` and `app/main.py` while preserving exact `(page_start, page_end)` range deduplication and sanitization.
   - **Evaluation Rubric Artifact:** If the biology answer is factually faithful to the textbook but penalized for a valid synonym (e.g., `សែន` vs `ហ្សែន`, `គ្រាប់លំអង` vs `លំអងផ្កា`), document it as a rubric/alias gap rather than a model hallucination.
3. **Verify Before Finishing:**
   - Run `python -X utf8 tests/test_citation_integrity.py`
   - Run `python -X utf8 tests/test_eval_harness.py`
   - Run `python -X utf8 tests/test_measurement_integrity.py`
   - Run `python -X utf8 tests/test_rag_fallback.py`
   - Or run all four with `python -X utf8 tests/run_all.py`