# System Accuracy Evaluation (v2)

Date: 2026-10-23 · Status: first complete pass · Pipeline unchanged for this pass

This report supersedes `docs/retrieval_evaluation.md` for current numbers. That
older file (2026-09-09, n=89) is kept for history but its metrics, and its
statement that the vector DB has 1093 chunks, no longer match the artifacts.

## 1. What was evaluated

- Gold set: `data/evaluation/gold_questions_v2.json` — 119 questions
  (97 v1 questions unchanged + 22 special cases):
  - 110 in-scope questions across all 8 chapters
  - 9 out-of-scope questions (must abstain)
  - 6 OCR-garbled questions, 6 multi-part exam-style questions
- Query path used for evaluation mirrors the real app:
  `normalize_query` → `split_questions` → `expand_query` → BGE-M3 retrieval →
  `rerank_with_context` → 0.08 abstention check → Gemini generation →
  `format_answer`.
- Retrieval: stratified sample of 40 v1 questions + every special/out-of-scope
  question = **69 rows / 55 in-scope questions** (`retrieval_v2_summary.txt`).
- Answers: 20 questions (`DEFAULT_IDS`) = 19 in-scope + 1 out-of-scope, scored
  on 7 dimensions 1–5 (`answer_evaluation_v2_summary.txt`).
- Environment: CPU-only (`torch 2.14.0+cpu`), 16 cores. A reranker row costs
  roughly 30–90 s, so both runs are resumable chunked runs.
- No retrieval parameters, chunking, prompts, or thresholds were changed.

## 2. Retrieval results

Overall, in-scope rows (n=60):

| metric | embed | rerank | real pipeline |
|---|---:|---:|---:|
| Recall@1 | 0.517 | 0.650 | **0.650** |
| Recall@3 | 0.767 | 0.850 | **0.850** |
| Recall@5 | 0.800 | 0.900 | **0.900** |
| MRR | 0.659 | 0.761 | **0.761** |

Per-question (multi-part strict): strict hit@5 **0.891**, any-part hit@5 **0.909**.
Abstention: out-of-scope **9/9 = 1.000**; in-scope false abstain **0/60 = 0.000**.

`real` equals `rerank` because of a defect described in §5: neighbour expansion
in `rerank_with_context` never runs with the current defaults.

### By chapter (real pipeline)

| chapter | n | Recall@5 | MRR | false abstain |
|---|---:|---:|---:|---:|
| 1 | 11 | 0.909 | 0.670 | 0.000 |
| 2 | 7 | 1.000 | 0.821 | 0.000 |
| 3 | 9 | 1.000 | 1.000 | 0.000 |
| 4 | 7 | 0.857 | 0.693 | 0.000 |
| **5** | **7** | **0.571** | **0.458** | 0.000 |
| 6 | 7 | 0.857 | 0.804 | 0.000 |
| 7 | 5 | 1.000 | 0.867 | 0.000 |
| 8 | 7 | 1.000 | 0.786 | 0.000 |

### By type (real pipeline)

| type | n | Recall@5 | MRR |
|---|---:|---:|---:|
| comparison | 3 | 0.667 | 0.708 |
| definition | 14 | 1.000 | 0.800 |
| explanation | 10 | 1.000 | 0.683 |
| multi_part | 11 | 0.818 | 0.827 |
| ocr_garbled | 6 | 0.667 | 0.688 |
| process | 8 | 0.875 | 0.677 |
| quiz | 1 | 1.000 | 0.500 |
| reasoning | 6 | 1.000 | 0.889 |
| summary | 1 | 1.000 | 1.000 |

Comparison and OCR-garbled questions are the weakest non-chapter slices;
chapter 5 (gene expression / biotechnology) is the weakest chapter.

## 3. Answer quality (20 questions)

Dimension means (1–5, in-scope n=19; target ≥ 4.0):

| dimension | mean |
|---|---:|
| correctness | **4.58** |
| completeness | **4.58** |
| faithfulness | **4.79** |
| clarity | **4.53** |
| terminology | **4.68** |
| citation | **4.05** |
| helpfulness | **4.68** |
| **overall** | **4.56** |

- 17 of 19 in-scope answers have an overall ≥ 4.0. The two failures are q1
  (generation blocked, all dimensions 1) and q111 (wrong adaptation term).
  Excluding only the blocked q1, the 18 answered in-scope questions average
  4.78 correctness / 5.00 faithfulness / 4.22 citation (overall 4.79).
- No in-scope question wrongly abstained; the single out-of-scope question
  (q100, water formula) abstained correctly.
- These are automated proxies documented in `scripts/evaluate_answers_v2.py`,
  not teacher grades. `answer_review_v2.csv` has blank teacher columns for
  manual override.

Per-question details:

- q2, q13, q26, q30, q105, q114: all 5s.
- q8 (water absorption): correctness/completeness 5 (clarity 4); q114 (neuron
  types + impulse): all 5s after fixing the scorer's multi-part source
  stripping. q115 (ADN/ARN) is correct and complete (5s for
  correctness/completeness) but citation is 3 because it cites pp. 164/170/174
  instead of expected pp. 150/165.
- q47/q58 (comparisons asked as "ខុសគ្នាដូចម្តេច?"): helpfulness 4, not 5, because
  they give differences but not similarities; the rubric now accepts this as
  correct for a differences-only prompt.
- q71 (fossils): correctness 5 but citation 3 — the answer cites pp. 218–225
  while the expected evidence is pp. 195–198.
- q115: citation 3 — cites pp. 164/170/174, not expected pp. 150/165.
- q108 (stigma OCR): correctness 5, clarity 4 (concise definition is
  appropriate; the scorer no longer penalises short definitions).

## 4. Concrete failures and evidence

### P0 — q111 answers adaptation with the wrong term

Question `តើលក្ខណៈបន្សំសំដៅលើអ្វី?` (stale OCR of `បន្ស៊ាំ`). The query
normalizer does its job: `queries_used` is `តើលក្ខណៈបន្ស៊ាំសំដៅលើអ្វី?`.
The answer still opens `លក្ខណៈបន្សុំ (ឬបន្លំ) ...` and describes adaptation
using pp. 236–237 examples. Expected concepts `បន្ស៊ាំ` and
`ជម្រើសដោយធម្មជាតិ` are absent; retrieval ranks pp. 236/236/237 first while
the definitions on pp. 202–203 are outside the top 5. So this is a
generation-terminology + ranking failure, not a query-normalisation failure.

### P0 — q1 cannot be answered (Gemini blocks the prompt)

`តើស៊ីមណូស្ពែមជាអ្វី? សូមពន្យល់ឱ្យបានច្បាស់` retrieves the right page
(top score 0.948, pages 6/8/9/10/12/24), but the full assembled context triggers
Gemini's safety filter: `prompt_feedback.block_reason = PROHIBITED_CONTENT` and
no candidate is returned. Each individual chunk passes; the concatenation does
not. Primary 3.6/3.5 were also rate-limited (429). Result: all seven models
return empty and the answer is `[GEN_FAILED: All Gemini models exhausted quota
or unavailable.]`.

A related crash was fixed during this evaluation: `response.text` can be `None`
and previously reached `format_answer()` as `'NoneType' object has no attribute
'strip'`. `app/rag.py` now retries/rotates on an empty response. When every
model is blocked it still raises, so the UI must surface a friendly error.

### P1 — chapter 5 retrieval is weak

Chapter 5 Recall@5 is 0.571. Two genuine misses:

- q24 (ADN vs ARN comparison): expected pp. 150/165; top 5 are 174/174/164/174/162.
  The ARN-type table on p165 ranks 8, so the answer is unlikely to cover it.
- q115 (`ក.` ADN, `ខ.` ARN types): expected pp. 150/165; top 5 are
  164/164/160/191/159. p165 is also outside the top 5; the answer cites
  164/170/174 instead.

### P2 — corpus and vector DB are stale

- Vector collection `biology` has **610 chunks**, while `docs/retrieval_evaluation.md`
  still says 1093.
- `data/processed/biology_cleaned.json` still contains stale OCR forms:
  `ស្ទីចម៉ាត` ×2, `ស្អិតម៉ាស` ×3, `ស្ទិចម៉ាត` ×9, `បន្ស៊ាំ` ×2, `បន្សំ` ×12.
- p186 has `ជំងឺហមារីក` for `ជំងឺមហារីក`; that page is the evidence for q105.
- No rebuild was performed in this pass; rebuilding without approval would
  invalidate all result files. Rebuild is the recommended next step.

### P2 — inline `ក./ខ.` multi-part prompts are not split

`prepare_queries('ក. តើ ADN ជាអ្វី? ខ. តើ ARN មានប៉ុន្មានប្រភេទ?')` returns
**one** query, while `I./II.` returns two. Gemini happened to answer both parts
for q115, but a longer inline prompt can silently lose the second part.
`app/main.py` and `scripts/eval_common.py` need the same inline-marker handling.

### P3 — gold labels that need correction (not yet applied except q105)

Page audit evidence:

| question | label | evidence | action |
|---|---|---|---|
| q23 | expects p159 | pp. 157–158 contain DNA replication | add 157/158 |
| q109 | expects pp. 16/17 | p15 defines `ស្ទិចម៉ាត` | add 15 |
| q119.1 | expects pp. 122/127/130 | p126 defines `ចំណងប៉ិបទីត` | add 126 |
| q111 | expects pp. 202/203 | p202/203 define adaptation, but ranking puts examples first | scope/ranking issue, not only a page label |
| q105 | was out-of-scope | p186 says interferon/interleukin treat cancer | **reclassified in-scope, chapter 5, expected p186** |

q105 is the important one: the old "out-of-scope" label was wrong. Keeping it
would have counted a correct textbook answer as a false abstention failure. The
gold builder and result rows were updated; retrieval abstention is now 9/9.

### P3 — `rerank_with_context` neighbour expansion is a no-op

In `app/retrieval.py`, `selected = indexed[:RERANKER_TOP_K]` always has
`RERANKER_TOP_K=12` items, equal to `max_total=12`, so the neighbour loop breaks
on its first iteration. "real" ranking therefore equals plain rerank. This is
not causing a measured regression, but it means the intended page-neighbour
recall improvement is not active. Do not change it without a before/after
evaluation.

### P3 — old evaluation harness measured a different path (fixed in v2)

- `scripts/evaluate_retrieval.py` and `evaluate_answers.py` sent the raw question
  to `retrieve()`, bypassing `normalize_query`/`expand_query`.
- v1 retrieval used plain `rerank`, not `rerank_with_context`.
- v1 answers had no 1–5 rubric and no out-of-scope/OCR/multi-part cases.
- During this pass, scoring was also corrected for: multi-part source footers
  (part II was being hidden), Khmer spelling variants (`ប៉ុបទីត/ប៉ិបទីត/ប៉បទីត`,
  `សំណល់/ផូស៊ីល`, `វិវត្ត/វិវត្តន៍`), and LaTeX `ARN_m`. The stale `បន្សំ` is
  deliberately **not** aliased to `បន្ស៊ាំ`, so q111 keeps failing.

### P4 — abstention threshold and documentation

- Threshold 0.08 let the old q105 (top 0.1703) answer. That turned out to be a
  label error, not a threshold failure, but 0.08 is still low relative to
  in-scope top scores (often 0.85–0.99) and OCR-garbled queries (q109 top 0.1192).
- `docs/retrieval_evaluation.md` must be marked superseded; its n=89 numbers
  (R@5 0.888) and 1093-chunk claim are inconsistent with current artifacts.

## 5. What this pass did not do

- No full 119-question retrieval run (sample of 55 in-scope questions).
- No teacher/manual scoring of the 20 answers.
- No corpus/vector-DB rebuild and no re-indexing.
- No changes to `TOP_K`, `RERANKER_TOP_K`, chunk size, prompt, or 0.08 threshold.
- No fix for the Gemini block or the inline `ក./ខ.` splitter.

## 6. Ranked next actions (need approval)

1. **P0** Rebuild the corpus + vector DB after syncing OCR fixes, then rerun
   retrieval v2 on all 119 questions. Expected to fix stale terms and the
   610-vs-1093 inconsistency.
2. **P0** Add a safe fallback for blocked prompts: on `PROHIBITED_CONTENT`,
   retry with only the top 3 chunks; if still blocked, return a friendly
   "cannot answer from this context" message instead of raising.
3. **P1** Add inline `ក./ខ.` splitting to `app/main.py` and `eval_common.py`.
4. **P1** Investigate chapter 5 ranking (p165 ARN types) without changing
   parameters until a before/after table exists.
5. **P2** Correct gold pages for q23/q109/q119.1 after review; keep q111 as a
   known terminology failure until the corpus/query fix is proven.
6. **P2** Decide whether to activate `rerank_with_context` neighbours
   (`max_total > RERANKER_TOP_K`) and measure Recall@5 before/after.
7. **P3** Calibrate the abstention threshold from in-scope vs out-of-scope score
   distributions; do not hard-code a new value without that data.

## 7. Reproduce

```powershell
$env:PYTHONIOENCODING="utf-8"
.\.venv\Scripts\python.exe -X utf8 scripts\build_gold_v2.py
.\.venv\Scripts\python.exe -X utf8 scripts\evaluate_retrieval_v2.py --sample 40 --max-rows 20
.\.venv\Scripts\python.exe -X utf8 scripts\evaluate_retrieval_v2.py --sample 40
.\.venv\Scripts\python.exe -X utf8 scripts\evaluate_answers_v2.py --max 5
.\.venv\Scripts\python.exe -X utf8 scripts\evaluate_answers_v2.py --score-only
.\.venv\Scripts\python.exe -X utf8 scripts\test_eval_harness.py
```

Artifacts: `data/evaluation/{gold_questions_v2.json, retrieval_v2_results.json,
retrieval_v2_summary.txt, answer_evaluations_v2.json,
answer_evaluation_v2_summary.txt, answer_review_v2.csv}`.
