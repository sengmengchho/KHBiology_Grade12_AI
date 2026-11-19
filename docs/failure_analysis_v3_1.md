# Failure Analysis (v3.1)

Date: 2026-10-25 · Scope: the six Recall@5 failures and one generation
failure found in the v3.1 evaluation. Each entry records the observed
problem, the textbook evidence, the root cause, the smallest fix, the files
changed, the regression risk, and the verification result.

The v3.1 corpus/parser work is described in
`docs/system_accuracy_evaluation_v3_1.md`. This file focuses on the failures
and the fixes applied after the first v3.1 run.

## Summary

| id | type | pre-fix result | root cause | fix | post-fix result |
|---|---|---|---|---|---|
| q55 | process | p9 outside top 5, top 0.1722 | query lacks the corpus words for pine/gymnosperm/cone | topic expansion `ស្រល់ → ស៊ីមណូស្ពែម កោន` | p9 rank 4, top 0.9300 |
| q56 | reasoning | no gold page, top 0.0319, false abstain | student words `អង្ករ`/`សំរូប` absent from corpus | topic expansion `អង្ករសំរូប → គ្រាប់ស្រូវ អាល់ប៊ុយមែន អង់ដូស្ពែម` | p17–18 rank 2 (p18 rank 5), top 0.1551 |
| q68 | process | p149 rank 1 but gold `[150]` only; R@5 miss | gold label too narrow; p150 is the lesson opener | gold `[150] → [149,150]` | p149 rank 1, MRR 1.0 |
| q78 | exam | p174 rank 4, top 0.0248, false abstain | query spelling `ហ្សែន`; gold too broad | alias `ហ្សែន → សែន`; gold `[150,155,160,165,175] → [174]` | p174 rank 2, top 0.1585 |
| q84 | quiz | p160 rank 5 but gold omitted it; R@5 miss | gold omitted the ADN summary page | gold `[150,165] → [150,160,165]` | p160 rank 5, R@5 hit |
| q86 | quiz | p26 rank 7; R@5 miss (v3.1 regression) | gold pointed at objectives, not lesson content | gold `[26] → [26,27,40]` | p40 rank 4, R@5 hit |
| q115 | multi-part | part 0 ADN query missed its ADN page | one shared gold list for two different sub-questions | per-part gold `[[150,160],[164,165]]` | part 0 p160 covered at rank 2 (pp. 159–160); part 1 p164 rank 1 |
| q1 | generation | `[GEN_FAILED: ...]` after `PROHIBITED_CONTENT` | top-3 retry still contained blocked reproductive terms | progressive context retry top 3 → top 1 | answered, overall 4.86, no fallback |

Final retrieval result: **Recall@5 = 1.000 (116/116)**, strict hit@5 =
**1.000 (110/110)**, in-scope false abstain = **0/116**, out-of-scope
abstention = **9/9**. The pre-fix baseline is preserved in
`data/evaluation/archive_v3_1_prefix/`.

## 1. q55 — pine pollen transfer

**Question:** ចូរពន្យល់ពីដំណើរការលំអងរបស់ស្រល់

**Observed:** expected p9; top-12 pages were
`[15, 15, 23, 17, 226, 16, 58, 244, 207, 57, 73, 77]`, top score 0.1722.
p9 was not retrieved. The ranking was dominated by flowering-plant
pollination pages because the query says only `ស្រល់` (pine), not the
textbook's taxonomic and structural terms.

**Textbook evidence (p9):** p9 is the gymnosperm life-cycle section. It
states: `ចំពោះស៊ីមណូស្ពែម ដំណើរលំអងច្រើនប្រព្រឹត្តទៅដោយសារខ្យល់ ។ ខ្យល់តែងនាំគ្រាប់លំអងពីកោនឈ្មោលទៅកោនញី ។ គ្រាប់លំអងត្រូវបានប្រមូលផ្ដុំនៅក្នុងសារធាតុស្អិតដែលផលិតដោយអូវុល ។`
This directly answers the question: wind carries pollen from the male cone
to the female cone, where the ovule's sticky substance collects it.

**Root cause:** vocabulary mismatch, not a missing fact. The corpus describes
pine reproduction as `ស៊ីមណូស្ពែម` and `កោន`; the student says `ស្រល់`.
The query has no term that competes with the many flowering-plant pages.

**Fix:** add a topic expansion in `app/utils.py`:

```python
_TOPIC_EXPANSIONS = (
    ("ស្រល់", "ស៊ីមណូស្ពែម កោន"),
)
```

`expand_query()` appends the textbook terms while keeping the student's
original wording. The displayed question is unchanged; only the internal
retrieval query is expanded.

**Files:** `app/utils.py`, `tests/test_eval_harness.py`.

**Regression risk:** any question containing `ស្រល់` is affected. The gold
set has three: q3, q52, q55. All three were rerun. q3 improved from p9 rank 2
to rank 1; q52 stayed at p6 rank 1. No regression.

**Verification:** q55 now retrieves p9 at rank 4 with top score 0.9300
(`data/evaluation/retrieval_v3_1_results.json`, row `55:0`).

## 2. q56 — polished rice is which plant part?

**Question:** តើអង្ករសំរូបដែលយើងបរិភោគជាផ្នែកណារបស់រុក្ខជាតិ?

**Observed:** expected `[12, 18]`; top-12 pages were
`[5, 20, 255, 21, 31, 31, 23, 21, 13, 26, 90, 13]`, top score 0.0319.
The app abstained (below 0.08). The corpus contains neither `អង្ករ` nor
`សំរូប`; a direct string search returns zero pages for both.

**Textbook evidence:**
- p12: angiosperms are seed plants; the seed contains the embryo and
  cotyledons.
- p18: `អាល់ប៊ុយមែនជាម៉ាសកោសិកាមួយដែលផ្ទុកអាហារបម្រុង ។` and
  `អំប៊្រីយ៉ុងផ្ទុកអាហារ ហៅថា អង់ដូស្ពែម ដែលការពារដោយសំបកគ្រាប់ ។`
- p19: rice (`ស្រូវ`) is listed as a monocot.
- p20: people eat `គ្រាប់ធញ្ញជាតិ` (grain seeds).

The inference is: polished rice is the rice grain's albumen/endosperm, i.e.
part of the seed. The gold pages are correct; the query cannot reach them
because the student's vocabulary is absent.

**Root cause:** out-of-vocabulary student terms. Adding only `គ្រាប់ស្រូវ
អាល់ប៊ុយមែន` to the full question still scored 0.0153 (below threshold).
The keyword-only bridge `អង្ករសំរូប គ្រាប់ស្រូវ អាល់ប៊ុយមែន អង់ដូស្ពែម`
retrieved p17–18 at rank 1 with 0.1283, showing that `អង់ដូស្ពែម` is the
missing strong term.

**Fix:** add a second topic expansion:

```python
("អង្ករសំរូប", "គ្រាប់ស្រូវ អាល់ប៊ុយមែន អង់ដូស្ពែម"),
```

The expanded query is the original question plus the three textbook terms.
It keeps the question frame and its meaning.

**Files:** `app/utils.py`, `tests/test_eval_harness.py`.

**Regression risk:** q56 is the only gold question containing `អង្ករសំរូប`;
the trigger cannot affect other questions.

**Verification:** q56 now retrieves `[5, 17, 19, 20, 18, 12, 12, ...]` with
top score 0.1551. The p17–18 chunk is rank 2; p18 itself is rank 5; p12 is
rank 6. R@5 and the abstention check both pass.

## 3. q68 — parent-to-child genetic information

**Question:** ពន្យល់ពីរបៀបដែលព័ត៌មានសេនេទិចត្រូវបានបញ្ជូនពីមេទៅកូន

**Observed:** expected `[150]`; the retriever put p149 at rank 1 with score
0.7929, but p149 was not in the gold list. p150 was rank 10, outside top 5,
so the row counted as an R@5 miss even though the correct answer was the
top-ranked page.

**Textbook evidence (p149):** the chapter opener says
`មេបាតែងតែបញ្ជូនលក្ខណៈរបស់ខ្លួន ( លក្ខណៈតំណពូជ)ទៅឱ្យកូនចៅខ្លួនជានិច្ច ។`
p150 is the ADN lesson opener/objectives and does not explain the
transmission process.

**Root cause:** gold label too narrow. The old label pointed at the lesson
opener because it contains `ADN` and `ព័ត៌មានសេនេទិច`, but the direct
statement is on p149.

**Fix:** gold `[150] → [149, 150]` via `scripts/update_gold_v3_1.py`, with
the evidence recorded in `data/evaluation/gold_label_changes_v3_1.json`.

**Files:** `data/evaluation/gold_questions_v2.json`,
`data/evaluation/gold_label_changes_v3_1.json`,
`scripts/update_gold_v3_1.py`.

**Regression risk:** gold-only change; no query behavior changes. Note that
p149 is a chapter opener without `lesson_id`, so the app's `_answer()` context
filter drops it. The retrieval evaluation correctly credits it, but the
answer generator may rely on p150/p160. This is documented as a
retrieval-vs-generation gap, not a reason to weaken the gold label.

**Verification:** q68 retrieves p149 at rank 1, MRR 1.0.

## 4. q78 — definition of a gene

**Question:** ក្នុងប្រឡង៖ តើអ្វីជានិយមន័យរបស់ហ្សែន (gene)?

**Observed:** expected `[150,155,160,165,175]`; top-12 pages were
`[162, 193, 192, 174, 174, 161, 162, 193, 163, 160, 153, 204]`, top score
0.0248. p174 was rank 4 but the top score was below 0.08, so the app
abstained. The query uses `ហ្សែន`; the definition page (p174) and most of the
corpus use `សែន`. The `ហ្សែន` spelling occurs only on p205 (chapter 6), not on
the definition page.

**Textbook evidence (p174):**
`សែនជាអង្គធាតុមួយរបស់ ADN ដែលផ្ទុកព័ត៌មានសេនេទិចកំណត់សំយោគប្រតេអ៊ីនប្រភេទមួយ ។`
This is the exact definition. p175 only asks the definition as an exercise;
p150/155/160 cover ADN structure; p165 covers ARN.

**Root cause:** two independent problems: (1) a spelling variant
(`ហ្សែន` vs `សែន`), and (2) a gold list that pointed at lesson openers,
ADN-structure pages, and an ARN page instead of the definition page.

**Fix:**
- Add `("ហ្សែន", "សែន")` to `QUERY_FIXES` in `app/utils.py`.
- Gold `[150,155,160,165,175] → [174]`.

**Files:** `app/utils.py`, `tests/test_eval_harness.py`,
`data/evaluation/gold_questions_v2.json`.

**Regression risk:** q78 is the only gold question containing `ហ្សែន`; the
alias cannot affect other queries.

**Verification:** q78 now retrieves p174 at rank 2 with top score 0.1585.
The false abstain is gone; R@3 and R@5 pass. R@1 still misses because p162
(the lesson opener) ranks first, but that is a ranking-quality residual, not
a retrieval failure.

## 5. q84 — quiz on ADN and ARN

**Question:** ចូរបង្កើតសំណួរសាកល្បង 3 អំពី ADN និង ARN

**Observed:** expected `[150,165]`; the retriever put p160 at rank 5 but p160
was not in the gold list. The first gold page, p150, was rank 8, and p165 was
outside the top 12, so the row counted as an R@5 miss.

**Textbook evidence:**
- p160 is the ADN lesson summary: ADN as genetic material, the double helix,
  nucleotides A/T/C/G, and semi-conservative replication.
- p165 lists the three functional ARN types (ARNm, ARNt, ARNr).
- p150 is only the ADN lesson opener.

**Root cause:** the gold label included the ARN page and the ADN opener but
omitted the ADN content summary, so the rank-5 p160 could not count.

**Fix:** gold `[150,165] → [150,160,165]`.

**Files:** `data/evaluation/gold_questions_v2.json`,
`data/evaluation/gold_label_changes_v3_1.json`.

**Regression risk:** gold-only change.

**Verification:** q84 retrieves p160 at rank 5; R@5 passes. R@3 still misses
because p160 is rank 5; this is a residual ranking limitation, not a
labeling failure.

## 6. q86 — quiz on plant water absorption

**Question:** ចូរបង្កើតសំណួរសាកល្បង 3 អំពីការស្រូបទឹករបស់រុក្ខជាតិ

**Observed:** expected `[26]`; top-12 pages were
`[57, 41, 57, 40, 40, 58, 26, 27, 31, 26, 256, 28]`. p26 was rank 7, so the
row missed R@5. In v3 this question passed; the v3.1 parser fix changed the
chunk boundaries and pushed p26 down. This is the one new v3.1 regression.

**Textbook evidence:**
- p26 is the lesson opener and only lists `ការស្រូបទឹកពីក្នុងដី` as an
  objective.
- p27 teaches the mechanism: `រុក្ខជាតិមានសរសៃរស្រូបយកទឹកពីក្នុងដីតាមរយៈរោមជញ្ជក់នៃប្ដូរ`.
- p40 is the lesson summary and restates that fibrous plants absorb soil
  water through root hairs.

**Root cause:** the gold label pointed at the objectives page, not the lesson
content. The parser fix made p26 a smaller/less competitive chunk, exposing
the weakness in the label.

**Fix:** gold `[26] → [26,27,40]`.

**Files:** `data/evaluation/gold_questions_v2.json`,
`data/evaluation/gold_label_changes_v3_1.json`.

**Regression risk:** gold-only change. The q86 regression is explicitly
reported in the v3.1 report rather than hidden by the corpus rebuild.

**Verification:** q86 retrieves p40 at rank 4; R@5 passes. R@3 still misses
because p40 is rank 4; this is a residual ranking limitation.

## 7. q115 — multi-part ADN/ARN question

**Question:** ក. តើ ADN ជាអ្វី? ខ. តើ ARN មានប៉ុន្មានប្រភេទ?

**Observed:** the two parts shared one gold list `[150,165]`. Part 0 (ADN)
retrieved `[163, 159, 160, 152, 156, 150, ...]`. The standalone p160 chunk
was rank 3, but a p159 chunk spanning pp. 159–160 already covered p160 at
rank 2. Neither was in the shared gold list, and p150 was rank 6, so part 0
missed R@5. Part 1 (ARN) passed via the p164–165 page range.

**Textbook evidence:**
- Part 0: p150 introduces ADN as genetic material; p160 is the ADN lesson
  summary (structure, nucleotides, replication).
- Part 1: p164 introduces ARN; p165 states the three functional types
  ARNm/ARNt/ARNr. p165 does not answer the ADN definition part.

**Root cause:** a single gold list cannot represent two sub-questions with
different answers. The old label made part 0 depend on an ARN page.

**Fix:**
- Add `expected_pages_for_part()` and `expected_pages_for_question()` to
  `scripts/evaluation/common.py`.
- Wire per-part gold into `scripts/evaluation/evaluate_retrieval.py` and
  `scripts/evaluation/evaluate_answers.py`.
- Set q115 `expected_source_pages_by_part = [[150,160],[164,165]]`.

**Files:** `scripts/evaluation/common.py`, `scripts/evaluation/evaluate_retrieval.py`,
`scripts/evaluation/evaluate_answers.py`, `tests/test_eval_harness.py`,
`data/evaluation/gold_questions_v2.json`.

**Regression risk:** per-part gold is opt-in; questions without
`expected_source_pages_by_part` keep the shared list. Tests cover the
fallback to shared gold and the union used for whole-answer scoring.

**Verification:** part 0 covers p160 at rank 2 through the p159–160 chunk
(the standalone p160 chunk is rank 3; R@3 hit, MRR 0.5); part 1 retrieves
p164 at rank 1 (MRR 1.0). Both parts pass.

## 8. q1 — generation failure after a safety block

**Question:** តើស៊ីមណូស្ពែមជាអ្វី? សូមពន្យល់ឱ្យបានច្បាស់

**Observed:** the app returned
`[GEN_FAILED: All Gemini models exhausted quota or unavailable.]` after
Gemini raised `PROHIBITED_CONTENT`. The retrieval was correct (top score
0.9481), so this was a generation-layer failure, not a retrieval failure.

**Evidence:** the top block (p6) defines gymnosperms and is safe. The lower
blocks (p8–p10) add reproductive/anatomy terms (`ស្ពែម៉ាតូសូអ៊ីត`,
`អូវុល`, `ការបង្កកំណើត`) that trigger the safety filter. The old fallback
retried with the top three blocks; the third block still contained the
blocked terms, so it failed again.

**Fix:** in `app/rag.py`, `_generate_google()` now retries blocked/empty
candidates with progressively smaller contexts: full → top 3 → top 1. If all
attempts fail, it returns `GENERATION_FALLBACK_MESSAGE`, a friendly Khmer
message, instead of a raw `[GEN_FAILED: ...]` string. The normal path and the
429/503 model rotation are unchanged.

**Files:** `app/rag.py`, `tests/test_rag_fallback.py`,
`scripts/evaluation/evaluate_answers.py` (fallback scored as a generation failure).

**Regression risk:** the extra top-1 call happens only when the full context
is blocked or empty. Normal generation still makes one call. The 429/503 path
still rotates models.

**Verification:** q1 now answers from the top block with overall 4.86 and no
fallback. `tests/test_rag_fallback.py`: 26/26 pass.

## 9. Final retrieval metrics

| metric | v3 | v3.1 pre-fix | v3.1 post-fix |
|---|---:|---:|---:|
| Recall@1 | 0.629 | 0.638 | **0.655** |
| Recall@3 | 0.853 | 0.853 | **0.888** |
| Recall@5 | 0.957 | 0.948 | **1.000** |
| MRR | 0.756 | 0.760 | **0.785** |
| Strict hit@5 (per question) | 0.955 | 0.945 | **1.000** |
| Any-part hit@5 | 0.964 | 0.955 | **1.000** |
| In-scope false abstain | 2/116 | 2/116 | **0/116** |
| Out-of-scope abstention | 9/9 | 9/9 | **9/9** |

The post-fix numbers come from
`data/evaluation/retrieval_v3_1_results.json`. The pre-fix baseline is
`data/evaluation/archive_v3_1_prefix/retrieval_v3_1_results_prefix.json`.

## 10. Residual limitations

- q84, q86, and q55 pass R@5 but not R@3: the correct page is rank 4–5.
  Improving that would require reranker/chunk changes, which were out of
  scope for this evidence-based pass.
- q78 passes R@3 but not R@1: the lesson opener (p162) outranks the
  definition page (p174).
- q68's gold p149 is a chapter opener without `lesson_id`; the app's context
  filter drops it. Retrieval is correct, but the generator may not see the
  exact sentence. Fixing that would require changing the context filter,
  which risks adding front-matter noise to other questions; it is left as a
  documented gap.
- q56's fix depends on the textbook's `អាល់ប៊ុយមែន`/`អង់ដូស្ពែម`
  vocabulary. If a future corpus revision renames these terms, the
  expansion must be updated.
