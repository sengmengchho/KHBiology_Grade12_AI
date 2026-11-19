# Citation / Context Integrity — Phase 2 Final Report

**Status:** COMPLETE — 45/45 frozen-sample rows plus q84; all acceptance criteria pass.

**Verdict:** **ACCEPT**

**Date:** 2026-11-02

**Scope:** Citation/context integrity only. No substantive answer-quality fixes; no retrieval, corpus, gold-label, threshold, or system-prompt changes.

---

## 1. Goal

Make the citations displayed to the student match the retrieved context actually used to generate the answer.

The previous behavior had three problems:

1. Page ranges were collapsed to the chunk's first page (`164-165` shown as `164`).
2. Footer sources were filtered to the "primary lesson," which sometimes discarded sources the answer actually cited.
3. Unsupported page tokens in model output were not sanitized. The evaluator also read only the first number in comma-separated citation lists.

Production citation selection must use only:

- retrieved/reranked chunks
- chunks actually placed into the Gemini context
- `page_start` / `page_end`
- deterministic formatting

Gold labels are never used for production citation selection.

---

## 2. Files changed

| File | Change |
|---|---|
| `app/prompt.py` | Added shared page-range formatter, citation parser, sanitizer, exact-range deduplication, chapter-opener eligibility, and deterministic footer source selection. |
| `app/main.py` | Context filter now drops only front matter p0–p4; chapter openers remain eligible. Context labels now use page ranges. |
| `scripts/evaluation/evaluate_answers.py` | Uses the shared citation parser and range helpers; records `retrieved_ranges` and `raw_answer`; reports invalid-citation rows. |
| `tests/test_citation_integrity.py` | New regression suite covering ranges, parsing, sanitization, chapter openers, footer selection, evaluator behavior, and q1/q35/q47/q58/q63/q68/q84/q115 replays. |

No changes were made to:

- `app/retrieval.py`
- `app/rag.py`
- `app/utils.py`
- embedding/reranker configuration
- `TOP_K` or `RERANKER_TOP_K`
- chunk size or overlap
- corpus / Chroma / vector DB
- `0.08` threshold
- Gemini model pool
- prompt/system-prompt wording
- gold labels

The working tree already contained unrelated pre-existing modifications (for example `app/rag.py`, `app/utils.py`, `README1.md`, and build scripts). Those were left untouched. No code changes were made during the evaluation itself.

---

## 3. Implementation

### 3.1 Page ranges

A shared deterministic formatter renders:

- `164, 164` → `164`
- `164, 165` → `164-165`

Range metadata is preserved end-to-end:

- context labels supplied to Gemini
- footer source labels
- evaluator page validation
- citation sanitization

The display does not fall back to only `page` when `page_start`/`page_end` exist.

### 3.2 Deduplication

Sources are deduplicated by exact:

```text
(page_start, page_end)
```

`164` and `164-165` are therefore distinct ranges and are not collapsed into one another.

### 3.3 Context labels

Gemini receives range-aware labels such as:

```text
[ទំព័រ 164-165]
```

instead of the previous page-only label.

The evaluator uses the same helper, so application and evaluation behavior cannot drift.

### 3.4 Chapter openers

The old filter removed every chunk whose `lesson_id` was falsey. That also removed legitimate chapter-opening content.

The new rule:

- p0–p4 = front matter → excluded
- p5, p25, p59, p121, p149, p195, p227, p245 = legitimate chapter openers → kept
- normal lesson chunks → kept

No lesson IDs are fabricated.

This lets q68 receive p149 context without changing retrieval or the corpus, and lets q56/q96 see p5 as a normal chapter opener.

### 3.5 Footer source selection

Footer sources now come from chunks actually supplied to Gemini.

Deterministic order:

1. Sources corresponding to valid body-cited pages
2. Remaining top context sources in rerank/context order
3. Deduplicate by exact `(page_start, page_end)`
4. Maximum 8 sources per footer

For multi-part answers, each part gets its own footer and its own 8-source cap. The old primary-lesson-only filter was removed. No gold pages are used.

### 3.6 Citation parsing

The shared parser supports:

- `ទំព័រ 164`
- `ទំព័រ 164-165`
- `ទំព័រ 13, 40`
- `ទំព័រ 13, 32, 40`
- `ទំព័រ 242 និង 246`
- mixed ranges/lists such as `ទំព័រ 13-14, 20`

The evaluator expands every page/range instead of reading only the first number.

### 3.7 Sanitization

Only unsupported page-citation tokens are removed.

- Supported pages in a mixed list are kept.
- Fully unsupported citation groups are removed cleanly, including empty brackets.
- Biological wording and facts are not rewritten.
- Unsupported pages are never replaced with gold pages.
- No citation is added unless it comes from context.

Whitespace adjacent to removed tokens is normalized. A citation-stripped comparison of raw and display text verifies that no biological wording changed.

### 3.8 Raw output preservation

The evaluator stores:

- `raw_answer` — original model output
- `answer` — sanitized/display output

This distinguishes Gemini citation behavior from deterministic post-processing.

---

## 4. Regression tests

All executed successfully:

```powershell
python tests/test_citation_integrity.py
python tests/test_eval_harness.py
python tests/test_rag_fallback.py
```

Coverage includes:

- single pages and page ranges
- duplicate-range deduplication
- distinct page-only vs page-range sources
- unsupported citation removal
- partially supported citation lists
- comma-separated and Khmer `និង` lists
- mixed range/list parsing
- front matter exclusion
- p5/p149 chapter-opener eligibility
- evaluator parser and range-aware scoring
- deterministic footer order and 8-source cap
- q1, q35, q47, q58, q63, q68, q84, and q115 replays

Results:

- `tests/test_citation_integrity.py`: all cases pass.
- `tests/test_eval_harness.py`: all cases pass. An initial run failed only because the Windows console used cp1252; the same suite passes under `PYTHONIOENCODING=utf-8`.
- `tests/test_rag_fallback.py`: 26/26 pass.

---

## 5. Metrics

### 5.1 v3 baseline

| Metric | v3 |
|---|---:|
| Correctness | 4.59 |
| Completeness | 4.68 |
| Faithfulness | 5.00 |
| Khmer clarity | 4.46 |
| Terminology | 4.80 |
| Citation (raw) | 4.49 |
| Citation (range-aware) | 4.61 |
| Helpfulness (Grade 12 suitability) | 4.41 |
| Overall | 4.63 |
| Invalid citation rows (raw) | 19/41 |
| Invalid citation rows (range-aware) | 1/41 |

The range-aware `4.61` is the meaningful baseline. The raw `4.49` is reported separately because the old evaluator did not recognize range endpoints.

### 5.2 Final v3.1 citation run

Tag: `v3_1_citation` (45 questions)

| Metric | v3 baseline | v3.1 Citation | Delta |
|---|---:|---:|---:|
| Correctness | 4.59 | 4.54 | -0.05 |
| Completeness | 4.68 | 4.63 | -0.05 |
| Faithfulness | 5.00 | 4.98 | -0.02 |
| Khmer clarity | 4.46 | 4.34 | -0.12 |
| Terminology | 4.80 | 4.78 | -0.02 |
| Citation (raw baseline) | 4.49 | **4.80** | **+0.31** |
| Citation (range-aware baseline) | 4.61 | **4.80** | **+0.19** |
| Helpfulness (Grade 12 suitability) | 4.41 | 4.27 | -0.14 |
| Overall | 4.63 | 4.62 | -0.01 |
| Invalid citation rows (raw) | 19/41 | **0/41** | — |
| Invalid citation rows (range-aware) | 1/41 | **0/41** | — |

The `4.80` citation score is computed on the delivered answer (body + footer). It is not a like-for-like comparison to the old raw `4.49`, which did not credit range endpoints; the honest improvement is **+0.19 over 4.61**.

### 5.3 Run integrity

- 45/45 rows saved; 45 unique question IDs.
- 0 missing, 0 extra, 0 duplicates; frozen order preserved.
- 0/41 in-scope abstentions.
- 4/4 out-of-scope abstentions.
- 0/45 generation fallbacks.
- 0/41 rows with invalid citations.
- No score, API/provider, or row-level failures.
- The launcher shell reported exit code 1, but this was a PowerShell stderr-redirection artifact from a download warning. All 45 rows, summaries, and CSVs were written. q84 ran separately and exited 0.

### 5.4 q84 supplementary run

q84 is tracked separately from the frozen 45-question sample and was run under tag `v3_1_citation_q84`.

| Metric | Old q84 | New q84 |
|---|---:|---:|
| Citation (raw) | 3 | **4** |
| Citation (range-aware) | 4 | **4** |
| Evaluator-invalid pages (raw) | 2 | **0** |

New q84 quality scores: correctness 5, completeness 5, faithfulness 5, clarity 5, terminology 5, citation 4, helpfulness 3; overall 4.57. The two old invalid pages were range endpoints (p165 inside 164-165, p175 inside 174-175), not pages truly outside the context.

q84's expected pages are `[150, 160, 165]`; overlap improved from 1/3 to 2/3. The body citation `[164]` was removed and the footer now covers `174-175, 174, 190-191, 161, 160-161, 191-192, 193-194, 164-165`. It would be wrong to force a larger increase: the new footer still does not contain p150, and `4` is the defensible score.

### 5.5 Citation-change accounting

Across the 41 in-scope rows, versus the v3 raw scores:

- 12 improvements
- 1 regression (q20)
- 28 unchanged

Versus the range-aware baseline:

- 7 improvements (q58, q63, q65, q86, q87, q111, q115)
- 1 regression (q20)
- 33 unchanged
- q47 removes the last range-aware invalid page (p242) with no range-score change
- q84 is supplementary and unchanged versus its range-aware score (4 → 4)

Classification:

| Class | Meaning | Rows |
|---|---|---|
| A | Real citation improvement (body citation correct, or invalid page removed) | q47, q63, q86 |
| C | Raw-score-only improvement; range-aware score already matched (no meaningful citation gain) | q34, q35, q84, q110, q117 |
| D | Regression caused by generation variation | q20 |
| E | Footer-selection effect (footer now covers cited/expected pages; body citations unchanged or removed) | q58, q65, q87, q111, q115 |

q1 is unchanged at 5 but its page-7 endpoint is now recognized as valid and its invalid-citation count drops from p7 to 0.

---

## 6. Target cases — final state

| Case | v3 raw / range | v3.1 | Body citations (v3 → v3.1) | Footer after | Invalid before → after | Classification |
|---|---:|---:|---|---|---:|---|
| q1 | 5 / 5 | 5 | 6 → 6, 7 | 6-7, 6, 10, 10-11, 8, 9, 5, 24 | p7 → 0 | unchanged; range endpoint recognized |
| q35 | 4 / 5 | 5 | 246, 247, 249 → 246, 247, 248, 249 | 246, 247-248, 247-249, 249, 250, 245, 251-252, 235 | p248 → 0 | C |
| q47 | 4 / 5 | 5 | 242, 246 → none | 247-249, 246-247, 247-248, 249, 246, 5, 177-178, 38-39 | p242 → 0 | A |
| q58 | 3 / 4 | 5 | 13, 32, 40 → none | 13, 40, 39-40, 32, 27-28, 29, 6, 41 | 0 → 0 | E |
| q63 | 3 / 3 | 5 | 62, 63, 64, 65, 77 → 60, 62, 63, 64, 65, 77 | 60, 62-63, 64, 65, 77, 210, 60-61, 215 | 0 → 0 | A |
| q68 | 4 / 4 | 4 | none → none | 149, 160, 180, 160-161, 162, 193, 190, 164 | 0 → 0 | context fix; score unchanged |
| q84 | 3 / 4 | 4 | 164 → none | 174-175, 174, 190-191, 161, 160-161, 191-192, 193-194, 164-165 | 2 raw → 0 | C (supplementary) |
| q111 | 3 / 3 | 4 | 200, 236 → 200, 236 | 200, 236-237, 237, 239, 236, 203-204, 176-177, 93-94 | 0 → 0 | E |
| q115 | 4 / 4 | 5 | 150, 153, 159, 162 → none | Two 8-source footers (16 lines): first covers 150, 152, 156, 159-160, 160, 162, 162-163, 163; second covers 159-160, 160, 164-165, 167, 170, 174-175, 192, 211-212 | p165, p175 → 0 | E |

Notes:

- Old evaluator-invalid pages were mostly range endpoints: p7 (inside 6-7), p11 (inside 10-11), p248 (inside 247-248), p165/p175 (inside 164-165/174-175). They were formally invalid only because the old evaluator knew just the chunk's first page.
- q47's p242 was genuinely outside the supplied ranges; the sanitizer removed it rather than replacing it.
- q58 and q115 now rely entirely on the footer for citation credit; the model emitted no body citations on the new run. This is a real footer-selection effect, not a body-citation improvement.
- q111 still has the wrong-chapter substantive problem: correctness remains 3. Its citation score rises to 4 only because the footer now includes p203-204, which was already in context.
- q68 now has p149 in context and in the footer, and the answer uses p149. Citation stays at 4 because p149 does not add an expected page, but the chapter-opener selection bug is fixed.

---

## 7. Answer-quality regressions

All correctness/completeness/helpfulness drops were checked against context changes. None originates from context selection or citation sanitization; they are generation variation and rubric keyword effects.

| Row | Dimension changes | Evidence | Classification |
|---|---|---|---|
| q55 | helpfulness 5 → 3 | Step keyword `ដំណាក់` count 2 → 0; context blocks identical | generation variation / brevity |
| q56 | completeness 5 → 4; helpfulness 5 → 3 | Body 1138 → 171 chars; structured lines 7 → 0; the added p5 block was not used | generation variation / brevity |
| q58 | correctness 5 → 3; completeness 5 → 4; terminology 5 → 4 | Omitted the expected synonym `ដូអែម`; context ranges unchanged | generation variation / rubric keyword |
| q65 | correctness 5 → 3; completeness 5 → 4; terminology 5 → 4 | Used `នាទី` where the rubric expects `តួនាទី`; biological content remains correct | generation variation / rubric keyword |
| q93 | clarity 3 → 2; helpfulness 5 → 3 | Body 404 → 299 chars; grammar/structure; context unchanged | generation variation |
| q96 | completeness 4 → 3 | Concept coverage 0.6 → 0.4; used `បែកមែក` where the rubric expects `បែកខ្នែង`; added p5 unused | generation variation / rubric keyword |

Additional observations:

- q23 faithfulness 5 → 4 and several clarity 5 → 4 drops (q2, q15, q24, q30, q31, q34, q63) are isolated generation variation, not a systematic context effect.
- q87 improved: correctness 3 → 5, completeness 4 → 5.
- q58/q65/q93 had no context-range change; q56/q96 gained p5 but did not use it causally.
- A sanitizer-only comparison over all 45 rows found **0 biological wording changes**. Raw-vs-display differences in q96/q115/q117/q119 come from the pre-existing `format_answer` prefix/`---` cleanup, not from citation sanitization.

---

## 8. Acceptance criteria

| Criterion | Target | Actual | Result |
|---|---|---:|---|
| Citation mean | ≥ 4.61 | **4.80** | PASS |
| Stretch citation | ~4.78 if supported | **4.80** | PASS |
| Invalid/unsupported rows | ≤ 1/41, ideally 0/41 | **0/41** | PASS |
| Correctness | ≥ 4.49 | **4.54** | PASS |
| Completeness | ≥ 4.58 | **4.63** | PASS |
| Faithfulness | ≥ 4.90 | **4.98** | PASS |
| Retrieval unchanged | required | unchanged | PASS |
| Gold labels unchanged | required | hash identical | PASS |
| Regression tests | all pass | all pass | PASS |

The overall mean moves from 4.63 to 4.62 (`-0.01`), well inside the observed generation variation. The citation gain is +0.19 on the meaningful range-aware basis and invalid citations fall from 1/41 to 0/41. The one citation regression (q20) is understood and does not reflect a wrong page being shown.

**Verdict: ACCEPT.**

---

## 9. Retrieval and gold labels

**Retrieval changed:** NO

- No edits to retrieval, embedding, reranker, corpus, Chroma, `TOP_K`, `RERANKER_TOP_K`, chunking, threshold, or model pool.
- Frozen v3.1 retrieval metrics remain: R@1 0.655, R@3 0.888, R@5 1.000, MRR 0.785, false abstention 0/116, OOS abstention 9/9.
- The only context change is eligibility of legitimate chapter openers and range labels; top-k/rerank results are unchanged.

**Gold labels changed:** NO

- `data/evaluation/gold_questions_v2.json` was not edited.
- SHA-256: `333299547501590c0270f05a4366bd004c456232b0f4e98afc87c61295ce8ff0`

**Retrieval artifact unchanged**

- `data/evaluation/retrieval_v3_1_results.json`
- SHA-256: `658a833ed45cbcdff25488c4a17b9b9975c6ed88a3e6f345f0da03f742f40494`

---

## 10. Known limitations and residual risks

1. **Khmer-numeral citations are not parsed.** The parser handles ASCII digits. Khmer numerals such as `ទំព័រ ២៦, ៤០` are not recognized. This occurred in 0/45 v3.1 rows but 4/45 v3 rows (q8, q16, q20, q108). Hypothetical per-row citation scores are unchanged (`5, 5, 5, 4`), so it does not affect this verdict, but a student could still see an unparsed Khmer-numeral citation. Recommended follow-up: normalize Khmer digits before page-token parsing.
2. **q20 is the one citation regression.** The body dropped p150, which was in context but excluded by the 8-source footer cap. No invalid citation was produced; the remaining claims are supported by p152/p159-160. This is a deliberate consequence of the deterministic cap, not a wrong page.
3. **q111 correctness remains 3.** The answer is substantively about the wrong chapter/term; this task only addresses citation/context integrity.
4. **Pre-existing low answer-quality rows** such as q78 and q86 remain out of scope.
5. **Generation variance is uncontrolled.** The evaluation uses one generation per question, so small clarity/helpfulness/terminology movements cannot be attributed to a seed or temperature change. All observed drops were traced to wording choices, not context content.
6. **Whitespace normalization** around removed citation tokens can change spacing/newlines. No biological words, facts, or punctuation content are changed; this is verified by the citation-stripped comparison.

---

## 11. Recommended next task

**Khmer-numeral citation normalization** in the shared parser: map Khmer digits (`០–៩`) to ASCII before `_PAGE_TOKEN_RE` parsing, add cases for `ទំព័រ ២៦, ៤០` and mixed Khmer/ASCII lists to `tests/test_citation_integrity.py`, then re-run the citation integrity suite. This is a contained parser fix and the only known citation gap left by this phase.

Do not begin substantive answer-quality fixes without approval.
