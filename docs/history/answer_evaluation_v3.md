# Answer Evaluation v3

**Status:** Complete for the 45-question main sample; q84 evaluated separately as a supplementary difficult case.  
**Teacher review:** `Teacher review pending`  
**Scope:** Answer generation and scoring only. No retrieval, corpus, prompt, threshold, or application-code changes were made.

---

## Dataset

| Item | Value |
|---|---:|
| Main-sample questions | 45 |
| Main-sample rows | 45 |
| In-scope rows | 41 |
| Out-of-scope rows | 4 |
| Duplicate rows | 0 |
| Missing rows | 0 |
| Extra rows | 0 |
| Provider/API failures in saved rows | 0 |
| Generation fallbacks | 0 |
| Gemini `PROHIBITED_CONTENT` | 0 |

The 45-question sample was drawn from the 119-question gold set. It contains 41 in-scope questions and 4 out-of-scope questions. The fixed sample did **not** include q84, so q84 was evaluated in a separate single-question run (`--tag v3_q84`) and is reported as a supplementary case. q84 is included in the teacher-review CSV but is excluded from the 45-row metrics.

### Chapters represented

| Chapter | Questions | In-scope |
|---|---:|---:|
| 1 | 8 | 8 |
| 2 | 5 | 5 |
| 3 | 6 | 6 |
| 4 | 5 | 5 |
| 5 | 7 | 7 |
| 6 | 3 | 3 |
| 7 | 3 | 3 |
| 8 | 4 | 4 |
| 0 (out-of-scope) | 4 | 0 |
| **Total** | **45** | **41** |

All eight in-scope chapters are represented.

### Question types represented

| Type | Count |
|---|---:|
| Definition | 6 |
| Comparison | 5 |
| Process | 8 |
| Explanation | 2 |
| Reasoning | 4 |
| Summary | 3 |
| Exam | 1 |
| Quiz | 3 |
| Cause/effect | 1 |
| Prevention | 1 |
| Application | 1 |
| OCR-garbled | 3 |
| Multi-part | 3 |
| Out-of-scope | 4 |
| **Total** | **45** |

The sample includes comparison, process, reasoning, quiz, application, OCR-garbled, multi-part, and out-of-scope questions.

---

## Answer-quality metrics

Means use the same methodology as v2: equal weight per in-scope question, dimensions on a 1–5 scale, and overall as the mean of the seven dimension scores per question. The four out-of-scope rows are excluded from dimension means and are counted separately in the abstention metric.

| Dimension | Mean (n=41) | Minimum | Target | Result |
|---|---:|---:|---:|---|
| Correctness | **4.59** | 1 | ≥ 4.0 | Pass |
| Completeness | **4.68** | 2 | ≥ 4.0 | Pass |
| Faithfulness | **5.00** | 5 | ≥ 4.0 | Pass |
| Khmer clarity | **4.46** | 3 | ≥ 4.0 | Pass |
| Terminology | **4.80** | 3 | ≥ 4.0 | Pass |
| Citation accuracy | **4.49** | 3 | ≥ 4.0 | Pass |
| Grade 12 suitability / helpfulness | **4.41** | 3 | ≥ 4.0 | Pass |
| **Overall** | **4.63** | — | ≥ 4.0 | **Pass** |

### Abstention and integrity checks

- Out-of-scope abstention: **4/4 = 1.0** (q98, q100, q102, q104).
- In-scope false abstention: **0/41**.
- Generation fallbacks: **0/45**.
- All 45 rows contain seven numeric dimension scores.
- No saved row contains `[FAILED]`, `[GEN_FAILED]`, an API error, a quota error, or an empty answer.
- q1 generated a full answer; no `PROHIBITED_CONTENT` was observed.

The overall score is above the 4.0 target, but the lowest rows are concentrated in answer completeness, terminology, and citation selection rather than in retrieval or provider reliability.

---

## Comparison with v2

### Raw sample comparison

| Dimension | v2 | v3 | Difference | Status |
|---|---:|---:|---:|---|
| Correctness | 4.58 | 4.59 | +0.01 | Stable |
| Completeness | 4.58 | 4.68 | +0.10 | Improved |
| Faithfulness | 4.79 | 5.00 | +0.21 | Improved |
| Khmer clarity | 4.53 | 4.46 | −0.07 | Stable |
| Terminology | 4.68 | 4.80 | +0.12 | Improved |
| Citation accuracy | 4.05 | 4.49 | +0.44 | Improved |
| Grade 12 suitability | 4.68 | 4.41 | −0.27 | Regressed |
| **Overall** | **4.56** | **4.63** | **+0.07** | **Stable** |

Status rule used here: a change smaller than 0.10 in absolute value is treated as **Stable**; changes of at least +0.10 or −0.10 are **Improved** or **Regressed**.

**Important caveat:** the v2 baseline used 20 questions (19 in-scope, 1 out-of-scope), while v3 uses 45 questions (41 in-scope, 4 out-of-scope). The raw table is therefore descriptive, not a controlled comparison. The v2 sample also included a q1 failure scored 1/1/1/1/1/1/1 with no citations, which lowers the v2 means. The apparent raw helpfulness regression is largely a sample-composition effect: the v3 sample adds many quiz, application, and long process questions that score 3 on helpfulness.

### Matched subset comparison

To separate sample effects from real changes, the 14 in-scope questions present in both evaluations were compared directly. q1 is excluded here because its v2 failure dominates the comparison; q1 is reported separately below.

| Dimension | v2 matched (n=14) | v3 matched (n=14) | Difference | Status |
|---|---:|---:|---:|---|
| Correctness | 4.71 | 4.86 | +0.14 | Improved |
| Completeness | 4.71 | 4.79 | +0.07 | Stable |
| Faithfulness | 5.00 | 5.00 | 0.00 | Stable |
| Khmer clarity | 4.64 | 4.57 | −0.07 | Stable |
| Terminology | 4.86 | 4.93 | +0.07 | Stable |
| Citation accuracy | 4.14 | 4.29 | +0.14 | Improved |
| Grade 12 suitability | 4.86 | 4.86 | 0.00 | Stable |
| **Overall** | **4.70** | **4.76** | **+0.05** | **Stable** |

On the matched subset, no dimension regressed by more than 0.07, and the overall score improved slightly. This does **not** support a claim of a broad v3 regression. It does support a claim that citation accuracy improved and that the raw helpfulness drop is a sample-composition artifact.

### q1 comparison

| q1 | v2 | v3 |
|---|---:|---:|
| Correctness | 1 | 5 |
| Completeness | 1 | 5 |
| Faithfulness | 1 | 5 |
| Clarity | 1 | 4 |
| Terminology | 1 | 5 |
| Citation | 1 | 5 |
| Grade 12 suitability | 1 | 5 |
| Overall | 1.00 | 4.86 |
| Cited / valid pages | 0 / 0 | 5 / 4 |

q1 no longer produces `PROHIBITED_CONTENT`; it generates a complete answer. The q1 fallback was **not** triggered. The remaining q1 issues are inherited textbook OCR terminology and one unsupported page reference (p7). This is the current behavior baseline before any fallback implementation.

---

## Failure analysis

### Retrieval failures

- **0/41 in-scope Recall@5 failures** in the answer sample.
- **0/41 in-scope false abstentions**.
- **4/4 out-of-scope questions abstained correctly**.
- One retrieval-to-generation context gap: **q68**. Gold page p149 is a chapter opener without a `lesson_id`; the application context filter drops it, so the generator does not see the direct parent-to-child statement even though the retrieval row passes. This is not an R@5 failure.
- q84's expected p165 is not in the retrieved set; the answer cites p165 in its footer. This is a citation issue, not a retrieval failure.
- q1's p7, q115's p165/p175, and q84's p165/p175 are also citation issues, not retrieval failures.
- q55, q78, and q86 have low automated concept coverage because of expected-concept wording, not because retrieval failed.

### Answer-generation failures

Of the 41 in-scope answers, **35 are factually correct with only minor style, terminology, or citation issues**. **6 have substantive answer-quality issues**:

| Question | Type | Issue |
|---|---|---|
| q56 | Reasoning | Explains seed/endosperm components but never states directly that milled rice is the seed/endosperm; answer is evasive. |
| q68 | Process | Explains DNA replication, cell division, asexual reproduction, and twins, but omits sexual reproduction/meiosis/fertilization; uses “មេតាបូល” incorrectly. |
| q87 | Quiz | Creates three population/community questions but does not explicitly use the “សហគមន៍” concept; questions are convoluted. |
| q94 | Prevention | Recommends iodine-rich foods and seafood but omits iodized salt; incomplete prevention advice. |
| q96 | Application | Implies mango is a dicot but never states the conclusion directly; opening is awkward and hedged. |
| q111 | OCR-garbled | Uses “បន្លំ” (camouflage) as a synonym for adaptation, omits natural selection, and cites chapter 7 pages instead of the chapter 6 adaptation pages. |

**No confirmed hallucinated Biology facts** were found in the 41 in-scope answers. The substantive failures are incompleteness, indirect answering, terminology, and citation selection—not invented facts.

### Terminology errors

**Model-introduced terminology issues:**

- **q68:** “មេតាបូល” is used where cell division/mitosis is meant; “ស្ទុយដំឡើងទ្វេ” is also awkward, though it mirrors textbook OCR.
- **q111:** “បន្លំ” means camouflage/deception, not adaptation; the correct term in the retrieved context is “លក្ខណៈបន្ស៊ាំ.”
- **q96:** “ដែលបានផ្ដល់ឱ្យ” is an awkward opening, and the answer hedges instead of stating the classification.
- **q56:** The answer hedges with “គ្មានការបញ្ជាក់ផ្ទាល់” and never gives the direct conclusion.

**Inherited textbook OCR terminology (faithful but confusing):**

- **q1:** “គ្រាប់ទី1” and “គ្រាប់នរល” come directly from the textbook OCR.
- **q78:** “អង្គធាតុមួយរបស់ ADN” and “អង្គត់” come from the textbook summary.
- **q115:** “ចរាក់,” “កានីន,” and “ស៊ីតូស៊ីន” come from the textbook OCR.
- **q55:** “ស៊ីហ្គោតបង្កកំណើត” is awkward, though the surrounding process is correct.

These inherited terms should not be counted as model factual errors, but they do reduce clarity for students.

### Citation errors

Citation accuracy improved from 4.05 (v2) to 4.49 (v3), but it remains one of the weaker dimensions.

- **19/41 in-scope rows** contain at least one page reference that was not in the retrieved context. Most are one-page footer overruns, such as q1 (p7), q24 (p166/p175), q34 (p248), q35 (p248), q47 (p242/p248), q56 (p13), q58 (p11), q108 (p23), q110 (p84/p90), q115 (p165/p175), q117 (p248), and q119 (p123).
- **Three rows have citation score 3:** q58 (invalid p11), q63 (all cited pages valid, but the answer adds off-topic chapter 6 pages 209–215 to a chapter 3 comparison), and q111 (cites chapter 7 pages 236–240 instead of the chapter 6 adaptation pages 202–203).
- **q68** cites only valid pages but misses the gold page p149, which is the direct parent-to-child statement.
- **q84** (supplementary) cites p165 and p175, neither of which is in its retrieved context.
- **q115** cites p165 and p175, neither of which is in its retrieved context.

The main root cause is footer page-range expansion: the answer formatter turns a cited page into a range that includes adjacent pages not present in the retrieved context. A second cause is topic selection: when the context contains both the target chapter and a later chapter, the generator sometimes cites the later chapter (q111, q63).

### Provider/API failures

- **Main 45-row run:** 0 provider/API failures, 0 quota/rate-limit errors, 0 empty responses, 0 scoring failures.
- **Gemini `PROHIBITED_CONTENT`:** 0/45. q1 generated a full answer and did not trigger the fallback.
- **Supplementary q84 run:** the first single-question attempt exited with code 1 after printing `q84 ...` and wrote no result row. A retry under the same tag succeeded. This was a transient run/provider failure, not a content rejection; it is not counted in the 45-row metrics.

### Evaluation-metric artifacts

The following low automated scores do **not** reflect factual errors:

| Question | Auto scores (C/Comp/F/C/T/Cit/H) | Manual inspection | Why the auto score is low |
|---|---|---|---|
| q55 | 3/4/5/5/4/5/5 | 5/5/5/5/4/5/5 | Expected concept “លំអងផ្កា” is absent, but the answer uses the textbook term “គ្រាប់លំអង.” |
| q78 | 1/2/5/4/3/5/3 | 5/5/5/5/5/5/5 | Expected concept “ហ្សែន” is not matched to the textbook spelling “សែន.” |
| q86 | 1/2/5/5/3/4/3 | 5/5/5/5/5/4/4 | Expected phrase “ស្រូបទឹក” is not matched to “ស្រូបយកទឹក” / “ចលនាទឹក.” |

Additional style/verbosity artifacts:

- q3, q9, q15, and q35 score 3 on helpfulness despite correct, detailed answers; the likely cause is answer length/advanced detail rather than factual quality.
- q52 scores 3 on clarity and helpfulness despite a correct answer; the concise style and textbook term “គ្រាប់នរល” likely drive the score.
- q85 and q87 score 3 on helpfulness because they provide quiz questions without answers; the question only asks for questions, so this is a format effect, not a factual error.

These artifacts should not be counted as system factual errors. They are candidates for future alias/scoring improvements, not for answer-content fixes in this task.

### Correct answers

- **4/4 out-of-scope questions** correctly abstained.
- **35/41 in-scope answers** are factually correct with only minor style/citation issues.
- **6/41 in-scope answers** have substantive answer-quality issues (q56, q68, q87, q94, q96, q111).
- **0 confirmed factual hallucinations.**

---

## Difficult cases

The table below compares the automated scores with a manual inspection by the evaluation reviewer. The manual column is **not** a teacher rating; it is an inspection aid. Teacher fields in the CSV remain blank.

Score order: **Correctness / Completeness / Faithfulness / Clarity / Terminology / Citation / Helpfulness**.

| Question | Auto | Manual inspection | Verdict |
|---|---|---|---|
| q1 | 5/5/5/4/5/5/5 | 5/5/5/4/4/4/5 | Correct; inherited OCR terms and p7 citation issue. |
| q55 | 3/4/5/5/4/5/5 | 5/5/5/5/4/5/5 | Correct; expected-concept artifact. |
| q56 | 5/5/5/5/5/5/5 | 4/3/5/4/5/4/3 | Incomplete/evasive; does not state the direct conclusion. |
| q68 | 5/5/5/5/5/4/3 | 4/3/5/3/3/3/3 | Incomplete; wrong term; p149 context gap. |
| q78 | 1/2/5/4/3/5/3 | 5/5/5/5/5/5/5 | Correct; alias artifact. |
| q84 | 5/5/5/5/5/3/3 | 5/5/5/5/5/3/3 | Correct; invalid footer pages. |
| q86 | 1/2/5/5/3/4/3 | 5/5/5/5/5/4/4 | Correct; concept/phrase artifact and footer issue. |
| q111 | 3/3/5/5/4/3/5 | 3/3/5/5/3/2/4 | Terminology, citation, and completeness problem. |
| q115 | 5/5/5/5/5/4/5 | 5/5/5/5/5/4/5 | Correct; minor OCR terminology and invalid footer pages. |

### q1 — Gymnosperm definition (chapter 1, definition)

- **Question:** តើស៊ីមណូស្ពែមជាអ្វី? សូមពន្យល់ឱ្យបានច្បាស់
- **Retrieved evidence:** top score 0.9481; pages `[6, 8, 9, 10, 12, 24]`; expected `[6]`. The p6 context contains the definition, the “គ្រាប់ទី1”/“គ្រាប់នរល” wording, the four extant groups, and the habitat/leaf/root facts.
- **Generated answer:** Defines gymnosperms as seed plants older than angiosperms, with naked seeds, needle/scale leaves, deep roots, and four extant groups (Cycads, Conifers, Ginkgoes, Gnetophytes). Cites p6–7, p10, p8, p9.
- **Correct:** Auto 5/5; manual 5/5.
- **Complete:** Auto 5/5; manual 5/5.
- **Faithful:** Auto 5/5; manual 5/5.
- **Terminology:** Auto 5/5; manual 4/5. “គ្រាប់ទី1” and “គ្រាប់នរល” are inherited textbook OCR terms; they are faithful but confusing.
- **Citation:** Auto 5/5 (5 cited, 4 valid); manual 4/5. p7 is not in the retrieved context; the footer says p6–7.
- **Provider failure:** No. No `PROHIBITED_CONTENT`; the full answer was generated and the fallback was not triggered.
- **Problem found:** Correct answer with inherited OCR terminology and one unsupported page reference. Not a factual error.
- **Likely root cause:** Textbook OCR wording is copied faithfully; the footer page-range expansion adds p7.

### q55 — Pine pollination process (chapter 1, process)

- **Question:** ចូរពន្យល់ពីដំណើរការលំអងរបស់ស្រល់
- **Retrieved evidence:** top score 0.93; pages `[6, 8, 9, 10, 15, 16, 17, 23, 24, 57]`; expected `[9]`. The p10 context describes male cones producing pollen grains, the ovule in the female cone, fertilization, and the ovule becoming a seed.
- **Generated answer:** Wind carries pollen grains from male cones to female cones; pollen collects in the sticky substance produced by the ovule; male and female gametes meet; scales close; fertilization produces a zygote, which becomes an embryo.
- **Correct:** Auto 3/5; manual 5/5.
- **Complete:** Auto 4/5; manual 5/5.
- **Faithful:** Auto 5/5; manual 5/5.
- **Terminology:** Auto 4/5; manual 4/5. Uses the textbook term “គ្រាប់លំអង”; “ស៊ីហ្គោតបង្កកំណើត” is awkward.
- **Citation:** Auto 5/5; manual 5/5. p9/p10 are valid.
- **Provider failure:** No.
- **Problem found:** The automated score penalizes the absence of the exact expected phrase “លំអងផ្កា,” but the answer uses “គ្រាប់លំអង,” which is the textbook term. No factual error.
- **Likely root cause:** Expected-concept mismatch/alias, not an answer-generation failure.

### q56 — Milled rice (chapter 1, reasoning)

- **Question:** តើអង្ករសំរូបដែលយើងបរិភោគជាផ្នែកណារបស់រុក្ខជាតិ?
- **Retrieved evidence:** top score 0.1551; pages `[6, 12, 17, 18, 19, 20, 21, 24, 131]`; expected `[12, 18]`. The p18 context defines the endosperm and seed; p12 describes angiosperm roots.
- **Generated answer:** Says the textbook does not directly mention “អង្ករសំរូប,” then explains that rice is a monocot, describes albumen/endosperm, and lists the components of a seed. It never states directly that milled rice is the seed/endosperm.
- **Correct:** Auto 5/5; manual 4/5. The components are correct, but the conclusion is implicit.
- **Complete:** Auto 5/5; manual 3/5. The answer does not directly answer “which part of the plant.”
- **Faithful:** Auto 5/5; manual 5/5.
- **Terminology:** Auto 5/5; manual 5/5.
- **Citation:** Auto 5/5 (8 cited, 7 valid); manual 4/5. p13 is invalid; p12/p18 are valid.
- **Provider failure:** No.
- **Problem found:** Evasive/incomplete answer; it explains seed anatomy but does not conclude that milled rice is the seed/endosperm.
- **Likely root cause:** Reasoning question requires an inference the textbook does not state verbatim; the generator hedged instead of giving a direct conclusion.

### q68 — Parent-to-child genetic information (chapter 5, process)

- **Question:** ពន្យល់ពីរបៀបដែលព័ត៌មានសេនេទិចត្រូវបានបញ្ជូនពីមេទៅកូន
- **Retrieved evidence:** top score 0.7929; pages `[150, 159, 160, 162, 164, 174, 180, 190, 193]`; expected `[149, 150]`. p149, the direct parent-to-child statement, is not in the context. p150 covers DNA structure; p160 covers replication and cell division.
- **Generated answer:** Explains DNA replication, cell division, asexual reproduction/tissue culture, and identical twins; does not explain sexual reproduction, meiosis, gametes, or fertilization. Uses “មេតាបូល” incorrectly and cites p150, p159, p160.
- **Correct:** Auto 5/5; manual 4/5. The cell-division facts are correct, but the answer misses the main parent-to-child route.
- **Complete:** Auto 5/5; manual 3/5. Omits sexual inheritance.
- **Faithful:** Auto 5/5; manual 5/5. Grounded in retrieved pages.
- **Terminology:** Auto 5/5; manual 3/5. “មេតាបូល” is the wrong term; “ស្ទុយដំឡើងទ្វេ” is textbook OCR.
- **Citation:** Auto 4/5; manual 3/5. p150/p159/p160 are valid, but p149 is missing.
- **Provider failure:** No.
- **Problem found:** Incomplete for the question, wrong term, and missing the gold page that directly answers parent-to-child inheritance.
- **Likely root cause:** p149 is a chapter opener without a `lesson_id`, so the application context filter drops it. The generator fills the gap with cell-division and asexual-reproduction content. Retrieval R@5 passes, so this is a context-filter/generation issue, not an R@5 failure.

### q78 — Gene definition (chapter 5, exam)

- **Question:** ក្នុងប្រឡង៖ តើអ្វីជានិយមន័យរបស់ហ្សែន (gene)?
- **Retrieved evidence:** top score 0.1585; pages `[162, 163, 173, 174, 189, 190, 192, 193, 205]`; expected `[174]`. p174 defines a gene; p163 also contains the definition.
- **Generated answer:** “សែន គឺជាអង្គធាតុមួយរបស់ ADN ដែលផ្ទុកព័ត៌មានសេនេទិចកំណត់សំយោគប្រូតេអីនប្រភេទមួយ ឬអង្គត់មួយរបស់ ADN ដែលផ្ទុកព័ត៌មានមួយដែលលំអចេញជាលក្ខណៈមួយ។”
- **Correct:** Auto 1/5; manual 5/5.
- **Complete:** Auto 2/5; manual 5/5.
- **Faithful:** Auto 5/5; manual 5/5.
- **Terminology:** Auto 3/5; manual 5/5. “សែន” is the textbook spelling; the question uses “ហ្សែន.”
- **Citation:** Auto 5/5; manual 5/5. p174/p163 are valid.
- **Provider failure:** No.
- **Problem found:** The automated scores are alias artifacts; the definition is correct and textbook-faithful.
- **Likely root cause:** Expected concept “ហ្សែន” is not matched to the textbook spelling “សែន”; there is no gene alias in the concept matcher.

### q84 — ADN/ARN quiz (chapter 5, quiz; supplementary)

- **Question:** ចូរបង្កើតសំណួរសាកល្បង 3 អំពី ADN និង ARN
- **Retrieved evidence:** top score 0.8925; pages `[160, 161, 164, 174, 190, 191, 192, 193, 194]`; expected `[150, 160, 165]`. p164 covers ARN types; p160 covers ADN bases; p174 contains the gene summary.
- **Generated answer:** Three quiz questions: (1) differences between ADN and ARN, including composition and bases; (2) the number and names of ARN types; (3) comparison of ADN/ARN length and mass. Inline citation p164; footer cites p174–175 and p164–165.
- **Correct:** Auto 5/5; manual 5/5.
- **Complete:** Auto 5/5; manual 5/5.
- **Faithful:** Auto 5/5; manual 5/5.
- **Terminology:** Auto 5/5; manual 5/5.
- **Citation:** Auto 3/5 (4 cited, 2 valid); manual 3/5. p164 and p174 are valid; p165 and p175 are not in the retrieved context.
- **Provider failure:** The successful run had no provider failure. The first supplementary attempt exited with code 1 and wrote no row; the retry succeeded. This was transient, not a content rejection.
- **Problem found:** Correct quiz questions; invalid footer pages.
- **Likely root cause:** q84 was omitted from the fixed 45-question sample, so it was run separately; the footer page-range expansion added p165/p175.

### q86 — Water-absorption quiz (chapter 2, quiz)

- **Question:** ចូរបង្កើតសំណួរសាកល្បង 3 អំពីការស្រូបទឹករបស់រុក្ខជាតិ
- **Retrieved evidence:** top score 0.9499; pages `[26, 27, 28, 31, 40, 41, 57, 58, 256]`; expected `[26, 27, 40]`. p26/p27/p40 contain the water-absorption facts: root hairs, osmosis, active transport, endodermis, xylem.
- **Generated answer:** Three questions about root hairs, osmosis/active transport, and movement from the endodermis to the xylem. Inline citations p26/p27; footer cites p57–58.
- **Correct:** Auto 1/5; manual 5/5.
- **Complete:** Auto 2/5; manual 5/5.
- **Faithful:** Auto 5/5; manual 5/5.
- **Terminology:** Auto 3/5; manual 5/5. Uses textbook terms “អង្គខ្មែរ” and “សរសៃស៊ីឡែម.”
- **Citation:** Auto 4/5; manual 4/5. Inline p26/p27 are valid; footer p57–58 is irrelevant.
- **Provider failure:** No.
- **Problem found:** The quiz questions are relevant and correct; the automated concept score misses the phrase “ស្រូបទឹក,” and the footer cites unrelated pages.
- **Likely root cause:** Expected-phrase mismatch and footer page-range expansion; not a factual error.

### q111 — Adaptation (chapter 6, OCR-garbled)

- **Question:** តើលក្ខណៈបន្សំសំដៅលើអ្វី?
- **Retrieved evidence:** top score 0.3127; pages `[93, 96, 139, 176, 200, 202, 203, 236, 237, 239, 240]`; expected `[202, 203]`. p202/203 discuss variation, competition, and natural selection; p236–240 are chapter 7 interaction pages.
- **Generated answer:** “បន្លំ (ឬលក្ខណៈបន្ស៊ាំ) គឺការសម្របប្រួលរបស់ភាវៈរស់ទៅនឹងមជ្ឈដ្ឋាន …” It gives a generic adaptation definition, does not mention natural selection, and cites p236/237/239/240.
- **Correct:** Auto 3/5; manual 3/5. The general idea is right, but “បន្លំ” is a misleading synonym and natural selection is missing.
- **Complete:** Auto 3/5; manual 3/5.
- **Faithful:** Auto 5/5; manual 5/5. The claims are grounded in the retrieved context, but the cited chapter is wrong for the question.
- **Terminology:** Auto 4/5; manual 3/5. “បន្លំ” means camouflage/deception, not adaptation.
- **Citation:** Auto 3/5; manual 2/5. The answer cites chapter 7 pages instead of the chapter 6 adaptation pages 202–203.
- **Provider failure:** No.
- **Problem found:** Misleading synonym, missing natural-selection concept, and wrong-chapter citations.
- **Likely root cause:** p202/203 were retrieved, but the generator selected later chapter 7 pages from the context and conflated adaptation with camouflage. This is a generation/citation-selection issue, not a retrieval failure.

### q115 — ADN/ARN multi-part (chapter 5, multi-part)

- **Question:** ក. តើ ADN ជាអ្វី? ខ. តើ ARN មានប៉ុន្មានប្រភេទ?
- **Retrieved evidence:** top score 0.8054; pages `[150, 152, 153, 154, 156, 157, 159, 160, 162, 163, 164, 167, 169, 170, 174, 191, 192, 211]`; expected `[150, 160, 164, 165]`. p150/p153/p160 cover ADN; p164 covers the three ARN types.
- **Generated answer:** Part 1 defines ADN, nucleotides, bases A/T/C/G, and the double helix; part 2 lists three ARN types (mRNA, tRNA, rRNA). Inline citations p150, p153, p159, p162; footer includes p164–165, p170, p167, p174–175, p169–170.
- **Correct:** Auto 5/5; manual 5/5.
- **Complete:** Auto 5/5; manual 5/5. Both parts are answered.
- **Faithful:** Auto 5/5; manual 5/5.
- **Terminology:** Auto 5/5; manual 4/5. “ចរាក់,” “កានីន,” and “ស៊ីតូស៊ីន” are textbook OCR terms; confusing but faithful.
- **Citation:** Auto 4/5 (10 cited, 8 valid); manual 4/5. p165 and p175 are invalid; the other pages are valid.
- **Provider failure:** No.
- **Problem found:** Correct multi-part answer with minor OCR terminology and invalid footer pages.
- **Likely root cause:** Textbook OCR wording and footer page-range expansion.

---

## Human review status

`Teacher review pending`

- Teacher-review CSV: `data/evaluation/answer_review_v3.csv`.
- It contains **20 representative rows**: 19 rows from the 45-question main sample plus the supplementary q84 row.
- It uses the required columns:
  `question_id`, `part`, `question`, `generated_answer`, `expected_pages`, `retrieved_pages`, `auto_correctness`, `auto_completeness`, `auto_faithfulness`, `auto_clarity`, `auto_terminology`, `auto_citation`, `auto_grade12_suitability`, `teacher_correctness`, `teacher_completeness`, `teacher_clarity`, `teacher_terminology`, `teacher_citation`, `teacher_comments`.
- All teacher fields are blank. No teacher ratings were invented.
- The selection covers all eight chapters, comparison (q24), process (q9, q15, q35, q68), multi-part (q115), difficult/reasoning (q28, q56, q68, q111), and previously problematic questions (q1, q55, q56, q68, q78, q84, q86, q111, q115).
- The full 45-row automated results remain in `data/evaluation/answer_evaluations_v3.json` and `data/evaluation/answer_evaluation_v3_summary.txt`.

The manual inspection in this report is an evaluation aid, not a teacher rating. The final judgement on correctness, completeness, clarity, terminology, and citation quality must come from the teacher review.

---

## Recommendation

1. **Is retrieval still considered stable?**  
   **Yes.** Retrieval v3.1 is complete and stable: 125/125 rows, Recall@5 = 1.000, MRR = 0.785, in-scope false abstention = 0/116, out-of-scope abstention = 9/9. No retrieval changes were made in this task. q68 is a context-filter gap, not an R@5 failure.

2. **Is answer correctness ≥ 4.0/5?**  
   **Yes.** Correctness = 4.59/5 (n=41).

3. **Is completeness ≥ 4.0/5?**  
   **Yes.** Completeness = 4.68/5 (n=41).

4. **Is faithfulness ≥ 4.0/5?**  
   **Yes.** Faithfulness = 5.00/5 (n=41).

5. **Is Khmer clarity ≥ 4.0/5?**  
   **Yes.** Clarity = 4.46/5 (n=41).

6. **Is terminology ≥ 4.0/5?**  
   **Yes.** Terminology = 4.80/5 (n=41).

7. **Is citation accuracy ≥ 4.0/5?**  
   **Yes.** Citation = 4.49/5 (n=41), up from 4.05 in v2, though it remains one of the weaker dimensions.

8. **Which questions still need fixes?**  
   Prioritized:
   - **P1 — substantive answer quality:** q111 (terminology/citation/natural selection), q68 (incomplete; p149 context gap; “មេតាបូល”), q56 (does not state the direct conclusion).
   - **P2 — incomplete/indirect:** q96 (mango classification not stated directly), q94 (iodized salt omitted), q87 (community concept missing/awkward questions).
   - **P3 — citation and inherited terminology:** q1 (p7; OCR terms), q35 (p248), q58 (p11), q63 (off-topic chapter 6 citations), q84 (p165/p175), q115 (p165/p175; OCR terms).
   - **P4 — style/helpfulness:** q3, q9, q15, q35, q52, q85, q86, q87 (overlong/advanced answers or quiz questions without answers). These are not factual errors.
   - **Metric artifacts, not answer fixes:** q55 (“លំអងផ្កា” vs “គ្រាប់លំអង”), q78 (“ហ្សែន” vs “សែន”), q86 (“ស្រូបទឹក” vs “ស្រូបយកទឹក”). These need alias/scoring review in a future task, not answer regeneration.

9. **Is the system ready for teacher review?**  
   **Yes.** The 45/45 evaluation is complete, the teacher-review CSV is ready, and all teacher fields are blank. Teacher review is still pending.

10. **Is it ready for student testing?**  
    **Not yet for unsupervised student testing.** The aggregate metrics pass, but six answers have substantive completeness/terminology/citation issues, and 19/41 rows contain at least one invalid or unsupported page reference. Complete teacher review, fix the P1/P2 cases and the citation footer behavior, then rerun the same 45-question evaluation and the matched v2 subset before a supervised student pilot.

---

## Known regressions

- **No confirmed answer-quality regression on the matched 14-question subset:** overall +0.05, no dimension worse than −0.07 (clarity, stable).
- **Raw helpfulness drop (4.68 → 4.41)** is a sample-composition effect: the v3 sample adds quiz, application, and long process questions that score 3 on helpfulness. On the matched subset, helpfulness is unchanged at 4.86.
- **Citation accuracy is still the weakest dimension** despite improving from 4.05 to 4.49. q111 and q63 cite the wrong topic/chapter; q68 misses p149; q1, q35, q58, q84, and q115 have invalid footer pages.
- **q1 no longer produces `PROHIBITED_CONTENT`**, but it still inherits OCR terminology and cites p7. The fallback was not triggered.
- **q84 is supplementary:** it was omitted from the fixed 45-question sample and evaluated separately. Its first run failed transiently; the retry succeeded.

---

## Recommended next task

**One task:** Implement targeted answer-generation and citation fixes for the six substantive cases (q56, q68, q87, q94, q96, q111), including the q68 p149 context gap and q111 adaptation/natural-selection terminology, then rerun the same 45-question evaluation and the matched v2 subset. Do not change retrieval parameters, the corpus, the vector DB, or the 0.08 threshold.
