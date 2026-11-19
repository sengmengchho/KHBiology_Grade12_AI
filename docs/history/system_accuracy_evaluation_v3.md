# System Accuracy Evaluation (v3)

Date: 2026-10-23 · Status: full retrieval pass complete · Corpus and evaluation labels corrected

This report supersedes `docs/system_accuracy_evaluation.md` (v2) for current
numbers. The v2 file remains useful as the answer-quality baseline, but its
retrieval sample, chapter 5 finding, and q111 conclusion are now out of date.

## 1. What changed in v3

| area | v2 | v3 |
|---|---|---|
| Corpus | 257 pages, stale OCR forms, 610-chunk claim | 257 pages cleaned, OCR pairs synced, **609 chunks** validated |
| Retrieval index | No `page_start`/`page_end` metadata | Chroma metadata now stores page ranges |
| Gold labels | q23/q109/q119 corrected | q53/q62/q69/q83/q89 also corrected |
| Retrieval evaluation | 40-question sample, 55 in-scope questions | **Full 119-question set**, 110 in-scope questions, 125 rows |
| q24 (ADN/ARN) | Failed, p165 outside top 5 | **Passes** via p164 page range |
| q111 (adaptation) | Retrieval failure | **Retrieval passes**; answer not re-evaluated |
| Chapter 5 | R@5 0.571 on the small sample | **R@5 0.842** on the full set; still the weakest chapter |
| Answer quality | v2 baseline | No answer v3 run |

No retrieval parameters, prompts, chunk size, model pool, or abstention
threshold were changed.

## 2. Corpus and evaluation setup

- Cleaned corpus: `data/processed/biology_cleaned.json`, 257 pages,
  329,653 characters.
- Chunks: `data/processed/biology_chunks.json`, **609 chunks** (expected ~610),
  min 23 / max 3,274 / average 626 characters.
- Coverage: all 257 pages covered; chunk IDs unique; no missing pages.
- Chapter chunk distribution: `{1:49, 2:102, 3:135, 4:70, 5:106, 6:77, 7:40, 8:30}`.
- Stale OCR forms in pages/chunks: **0**. Legitimate `បន្សំ` (“combination”)
  remains preserved in its correct contexts.
- Vector collection `biology`: 609 chunks; `page_start`/`page_end` verified on
  `p164_008` as 164–165.
- Query path mirrors the app: `normalize_query` → shared `split_questions` →
  `expand_query` → BGE-M3 retrieval → `rerank_with_context` → threshold 0.08.
- Full evaluation: 119 gold questions → 125 rows (6 multi-part questions),
  116 in-scope rows, 9 out-of-scope rows.
- Environment: CPU-only (`torch 2.14.0+cpu`), 16 cores.

Validation evidence: `data/evaluation/corpus_validation_v3.json` (PASS).

## 3. Full retrieval results

In-scope rows (n=116):

| metric | embed | rerank | real pipeline |
|---|---:|---:|---:|
| Recall@1 | 0.560 | 0.629 | **0.629** |
| Recall@3 | 0.845 | 0.853 | **0.853** |
| Recall@5 | 0.922 | 0.957 | **0.957** |
| MRR | 0.715 | 0.756 | **0.756** |

Per-question (multi-part strict): strict hit@5 **0.955**, any-part hit@5
**0.964**.

Abstention:

| check | result |
|---|---:|
| Out-of-scope abstained | **9/9 = 1.000** |
| In-scope false abstain | **2/116 = 0.017** |

`real` equals `rerank` because `rerank_with_context` neighbour expansion is
still a no-op with the current defaults.

### By chapter (real pipeline)

| chapter | n | Recall@5 | MRR | false abstain |
|---|---:|---:|---:|---:|
| 1 | 28 | 0.929 | 0.778 | 0.036 |
| 2 | 12 | 1.000 | 0.729 | 0.000 |
| 3 | 15 | 1.000 | 0.922 | 0.000 |
| 4 | 12 | 1.000 | 0.799 | 0.000 |
| **5** | **19** | **0.842** | **0.635** | **0.053** |
| 6 | 9 | 1.000 | 0.678 | 0.000 |
| 7 | 8 | 1.000 | 0.733 | 0.000 |
| 8 | 13 | 1.000 | 0.744 | 0.000 |

Chapter 5 is the only chapter below the 0.85 Recall@5 target. The overall target
is met.

### By question type (real pipeline)

| type | n | Recall@5 | MRR |
|---|---:|---:|---:|
| application | 1 | 1.000 | 1.000 |
| cause_effect | 1 | 1.000 | 1.000 |
| comparison | 9 | 1.000 | 0.815 |
| definition | 21 | 1.000 | 0.811 |
| exam | 7 | 1.000 | 0.619 |
| explanation | 15 | 1.000 | 0.747 |
| multi_part | 12 | 0.917 | 0.931 |
| ocr_garbled | 6 | 1.000 | 0.783 |
| prevention | 1 | 1.000 | 1.000 |
| process | 15 | 0.867 | 0.773 |
| quiz | 6 | 0.833 | 0.535 |
| reasoning | 12 | 0.917 | 0.631 |
| summary | 10 | 1.000 | 0.650 |

## 4. Gold-label corrections

The full run exposed five additional mislabelled questions. They were corrected
in `scripts/build_gold_v2.py` with evidence recorded in
`data/evaluation/gold_label_changes_v3.json`.

| question | old pages | new pages | evidence |
|---|---|---|---|
| q53 | 196, 197, 209 | **6, 12** | p6 defines gymnosperm naked seeds; p12 defines angiosperm seeds protected by fruit/shell. Old pages are unrelated chapters 6–7 pages. |
| q62 | 60 | **65, 70** | p65 describes nerve fibres carrying electrical signals; p70 describes synaptic neurotransmitter transmission. p60 is the lesson overview. |
| q69 | 165 | **153, 154, 156** | p153 defines nucleotide components; p154 lists the four nucleotide types; p156 explains DNA base pairing. p165 is the ARN lesson. |
| q83 | 246 | **247** | p247 explicitly defines `ខ្សែអាហារ`; p246 contains lesson objectives. |
| q89 | 246, 247, 248, 256 | **77** | p77 is the chapter 3 nervous-system summary; the old pages are chapter 8 food-chain/energy pages. |

Previously corrected labels retained: q23 → 157/158/159, q109 → 15/16/17,
q119 → 122/126/127.

q68 was not re-labelled. p149 is the chapter introduction that frames the
question, but p150 is the ADN lesson page; retrieval returns p149 while missing
p150. This is treated as a genuine near-miss, not a label correction.

These corrections turn q53, q62, q69, q83 and q89 from false retrieval failures
into passes. Full-suite metrics in this report already include the corrected
labels.

## 5. Same-question comparison with v2

The v2 sample file has 69 saved rows, but its `selected_ids` contains 62 IDs;
two stale rows (q6/q7) are outside that selection. The correct same-ID baseline
is therefore 67 rows / 58 in-scope, not 69/60. v3 adds one q115 sub-question, so
the corresponding v3 subset is 68 rows / 59 in-scope.

| subset | rows / in-scope | real R@1 | real R@3 | real R@5 | MRR | strict hit@5 |
|---|---:|---:|---:|---:|---:|---:|
| v2, selected IDs | 67 / 58 | 0.672 | 0.862 | 0.897 | 0.778 | 0.887 |
| v3, same IDs | 68 / 59 | 0.712 | 0.932 | **0.983** | **0.828** | **0.981** |
| v2, excluding q115 | 66 / 57 | 0.684 | 0.877 | 0.912 | 0.791 | 0.904 |
| v3, excluding q115 | 66 / 57 | 0.719 | 0.947 | **1.000** | **0.837** | **1.000** |

On the same questions, v3 improves Recall@5 by about 8.6 points and MRR by about
5 points. Excluding the structurally difficult q115, v3 reaches Recall@5 1.000
on this subset. The v2 report’s 0.900/0.761 figures were computed over all 69
saved rows, including the two stray rows; they should not be used for a strict
same-ID comparison.

## 6. Remaining retrieval failures

Five in-scope rows still miss Recall@5:

| question | chapter | expected pages | top 5 retrieved | top score | note |
|---|---:|---|---|---:|---|
| q55.0 | 1 | 9 | 15, 15, 23, 17, 226 | 0.1722 | Pine pollen process is on p9; retrieval misses the diagram-heavy page. |
| q56.0 | 1 | 12, 18 | 5, 20, 255, 21, 31 | 0.0319 | Rice-grain reasoning question; `អង្ករ` does not appear in the corpus. Also a false abstention. |
| q68.0 | 5 | 150 | 149, 160, 180, 160, 162 | 0.7929 | p149 is the chapter introduction; p150 is the ADN lesson page and is absent from the top 5. |
| q84.0 | 5 | 150, 165 | 174, 174, 190, 161, 160 | 0.8925 | Quiz-generation prompt; p174 is the gene/DNA summary, but p165 ARN is absent. |
| q115.0 | 5 | 150, 165 | 163, 159, 160, 152, 156 | 0.8054 | ADN sub-question; p150 is around rank 6. q115.1 (ARN) passes via the p164 page range, but q115 is a strict failure. |

Two in-scope false abstentions remain:

- q56.0: top score 0.0319, below the 0.08 threshold; also an R@5 miss.
- q78.0: top score 0.0248; hit@5 is actually true, but the threshold rejects it.
  The query uses `ហ្សែន` while the corpus uses `សែន`; no query alias exists yet.
  The expected page set is also broad (150/155/160/165/175), while the actual
  gene definition is on p174. This needs a terminology-plus-label fix, not a
  threshold change.

## 7. Answer quality and blockers

No answer v3 evaluation was run. The current answer baseline remains the v2
20-question run (`answer_evaluation_v2_summary.txt`):

| dimension | mean |
|---|---:|
| correctness | 4.58 |
| completeness | 4.58 |
| faithfulness | 4.79 |
| clarity | 4.53 |
| terminology | 4.68 |
| citation | 4.05 |
| helpfulness | 4.68 |
| **overall** | **4.56** |

- q1 remains blocked: the full assembled context triggers Gemini
  `PROHIBITED_CONTENT`; individual chunks pass. Primary 3.6/3.5 also returned
  429. All models empty produces
  `[GEN_FAILED: All Gemini models exhausted quota or unavailable.]`.
- q111 retrieval now passes in v3, but its answer was not re-generated; the v2
  answer score (about 3.43) is still the last answer-level evidence.
- q115’s citation was weak in v2 (cited pp. 164/170/174 instead of 150/165).
  Chroma now stores page ranges, but answer citation code may still display the
  primary `page`; this needs checking before claiming a citation improvement.
- Validation reports **84/609 chunks without `lesson_id`**. If `_answer` filters
  truthy `lesson_id`, part of the corpus may be dropped from answer context; this
  was not changed in v3 and must be checked before answer-level evaluation.
- `rerank_with_context` remains a no-op: `selected = indexed[:12]` equals
  `max_total=12`, so neighbour expansion never runs.
- Broader OCR list parity remains open: 347 OCR fixes vs 325 query fixes, with
  only the five stale-form pairs newly synced.

## 8. Limitations

- The v3 report measures retrieval, not answer quality. Do not describe answer
  accuracy as improved without a new answer run.
- The full 125-row run and the v2 sample are not directly comparable; use the
  same-ID table in §5.
- q115 is a multi-part question with one shared gold page set (`[150,165]`).
  Per-part labels are still coarse; q115.0 fails while q115.1 passes.
- q84 is a generative quiz prompt rather than a normal factual retrieval
  question; its gold page set is narrower than the pages that could support a
  valid answer.
- q78’s `ហ្សែន`/`សែន` mismatch is a real query-normalisation gap, but changing
  it without correcting the gold pages would trade a false abstention for a
  retrieval miss.
- The q1 Gemini block and the `rerank_with_context` no-op are unchanged.
- No teacher/manual scoring was added; answer scores are automated proxies.

## 9. Reproduce

```powershell
$env:PYTHONIOENCODING="utf-8"
$env:PYTHONPATH="D:\Khmer Biology AI Tutor"

.\.venv\Scripts\python.exe -X utf8 scripts\build_gold_v2.py
.\.venv\Scripts\python.exe -X utf8 scripts\validate_corpus_v3.py
.\.venv\Scripts\python.exe -X utf8 scripts\smoke_retrieval_v3.py
.\.venv\Scripts\python.exe -X utf8 scripts\evaluate_retrieval_v2.py --tag v3 --fresh
.\.venv\Scripts\python.exe -X utf8 scripts\test_eval_harness.py
```

To refresh only questions whose gold labels changed:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts\evaluate_retrieval_v2.py --tag v3 --ids 53,62,69,83,89
```

Artifacts:

- `data/evaluation/gold_questions_v2.json`
- `data/evaluation/gold_label_changes_v3.json`
- `data/evaluation/corpus_validation_v3.json`
- `data/evaluation/retrieval_smoke_v3.json`
- `data/evaluation/retrieval_v3_results.json`
- `data/evaluation/retrieval_v3_summary.txt`
- `data/processed/biology_chunks.json`
- `data/processed/biology_cleaned.json`
- `docs/system_accuracy_evaluation.md` (v2 answer baseline)
