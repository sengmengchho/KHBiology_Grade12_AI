# Answer Quality Diagnosis — Phase 3

**Status:** Diagnosis only. No code, gold-label, retrieval, prompt, citation, threshold, model-pool, chunking, Chroma, or generation changes were made. No full evaluation was run and no answers were regenerated. All findings below come from stored v3/v3.1 artifacts and the existing textbook chunk store.

**Question set examined:** q111 in full; q56, q58, q65, q68, q87, q94, q96 as requested; q55, q78, q86, q93 as additional low-score controls discovered while reviewing the 45-row score table.

**Primary artifacts:**

- `data/evaluation/answer_evaluations_v3_1_citation.json`
- `data/evaluation/answer_evaluations_v3.json`
- `data/evaluation/gold_questions_v2.json`
- `data/evaluation/retrieval_v3_1_results.json`
- `data/processed/biology_chunks.json`
- `data/evaluation/answer_evaluation_v3_1_citation_summary.txt`
- `data/evaluation/answer_review_v3_1_citation.csv`
- `scripts/evaluation/evaluate_answers.py` (scoring logic only; not modified)

---

## 1. Executive summary

q111 is **not** a camouflage/definition error. The generated answer gives the textbook definition of adaptation, largely verbatim from p236 (chapter 7), and is fully grounded in the supplied context (faithfulness 5, no invalid citations). The earlier diagnosis that the model “conflated adaptation with camouflage” is **not supported by the textbook evidence** and should be withdrawn.

The real q111 problems are:

1. **A missing mechanism.** The gold requires `ជម្រើសដោយធម្មជាតិ` (“natural selection”). The answer contains `បន្ស៊ាំ` but never mentions natural selection. Its second sentence paraphrases the chapter-7 text in a way that can imply organisms “change themselves” and pass the change on — a Lamarckian-sounding framing that natural selection would correct.
2. **A chunk-level retrieval miss hidden by a page-level hit.** Pages 202 and 203 are in the context, so hit@5 is technically true. But the context’s p202 block is the variation/competition chunk (`p202_014`), and its p203 block is the competition chunk (`p203_016`). The chunk that actually contains the natural-selection definition (`p201_012`, overlapping p202) was **not retrieved**. The only natural-selection phrase in context is a one-line recap in the chapter-7 block (`p236_001`).
3. **A keyword-scoring artifact.** Correctness is `1 + 4 × concept_coverage`. The answer covers 1 of 2 gold concepts (`បន្ស៊ាំ` yes, `ជម្រើសដោយធម្មជាតិ` no), so correctness is 3/5. That number measures keyword coverage, not whether the definition is biologically right. The definition is right.

The previous “wrong chapter” diagnosis is only partly true. Chapter 7 dominates the top of the context, and the answer copies its definition, but chapter 7’s definition is the same concept and is textbook-canonical. The problem is that the chapter-6 **mechanism** was not in the useful part of the context and was not synthesized by the model.

Among the requested secondary cases, only **q96** is a genuine answer failure (it never explicitly classifies mango as a dicot and hedges instead). q56, q58, q65, q68, q87, and q94 are substantially correct; their low scores come from keyword/alias/format artifacts or from a gold concept that the textbook does not actually contain. The same pattern explains the two lowest rows in the whole 45-question set: **q78** (correct gene definition, but the answer uses the query alias `សែន` while the gold keyword is `ហ្សែន`) and **q86** (three valid quiz questions, but the answer says `ស្រូបយកទឹក` while the gold keyword is `ស្រូបទឹក`).

**Bottom line:** the most urgent quality problem is not widespread wrong biology. It is a small number of genuine mechanism/application omissions (q111, q96) plus an evaluator that systematically marks correct Khmer answers as wrong when they use a synonym, an alias, or an OCR variant. Measurement should be fixed before optimizing against the current scores.

---

## 2. Detailed q111 investigation

### 2.1 Question and gold record

| Field | Value |
|---|---|
| Question ID | 111 |
| Type | `ocr_garbled` |
| Chapter | 6 |
| Original question | `តើលក្ខណៈបន្សំសំដៅលើអ្វី?` |
| Normalized query used | `តើលក្ខណៈបន្ស៊ាំសំដៅលើអ្វី?` |
| Gold concepts | `បន្ស៊ាំ`, `ជម្រើសដោយធម្មជាតិ` |
| Gold pages | `[202, 203]` |
| `expected_answer` | empty |
| Gold note | `Corruption បន្សំ -> បន្ស៊ាំ; adaptation under natural selection.` |

The question asks what an adapted characteristic (`លក្ខណៈបន្សំ`, corrected to `លក្ខណៈបន្ស៊ាំ`) refers to. The gold answer is not a stored sentence; it is represented by two concepts. The second concept makes the benchmark expect the natural-selection mechanism, not only a definition.

### 2.2 Retrieval

From `retrieval_v3_1_results.json`, row `111:0`:

| Stage | Top-5 pages | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---|---|---|---|---|
| Embedding | 239, 236, 237, 236, 227 | false | false | false | 0.167 |
| Rerank | 237, 239, 236, 236, 203 | false | false | true | 0.200 |

The real 12-block context, in order, is:

| Rank | Page | Rerank score | Chunk actually in context |
|---:|---:|---:|---|
| 1 | 237 | 0.3127 | `p237_003` |
| 2 | 239 | 0.2560 | `p239_008` |
| 3 | 236–237 | 0.2125 | `p236_002` |
| 4 | 236 | 0.1488 | `p236_001` |
| 5 | 203–204 | 0.1364 | `p203_016` |
| 6 | 176–177 | 0.0238 | `p176_002` |
| 7 | 93–94 | 0.0158 | `p093_029` |
| 8 | 200 | 0.0086 | `p200_008` |
| 9 | 240 | 0.0042 | `p240_011` |
| 10 | 202 | 0.0017 | `p202_014` |
| 11 | 139 | 0.0016 | `p139_009` |
| 12 | 96 | 0.0015 | `p096_035` |

Key point: the page labels 202 and 203 are present, but the specific gold-evidence chunks are not. `p201_012` (the chunk that actually defines natural selection and overlaps p202) is absent. `p202_013` (which repeats the definition and then covers overproduction/variation) is also absent. Block 10 is `p202_014`, which begins at “4.2. បម្រែបម្រួល” and covers variation and competition. Block 5 is `p203_016`, which covers competition. This is why page-level hit@5 = true but the answer still lacks the mechanism.

### 2.3 Context blocks and term placement

| Block | Page label | Chunk | Contains `ជម្រើសដោយធម្មជាតិ`? | Contains `បន្ស៊ាំ`? | Contains `បន្លំ`? |
|---:|---|---|---|---|---|
| 1 | 237 | `p237_003` | no | yes | no |
| 2 | 239 | `p239_008` | no | yes | no |
| 3 | 236–237 | `p236_002` | no | no | yes |
| 4 | 236 | `p236_001` | **yes** (recap only) | no | yes |
| 5 | 203–204 | `p203_016` | no | yes | no |
| 6 | 176–177 | `p176_002` | no | no | no |
| 7 | 93–94 | `p093_029` | no | no | no |
| 8 | 200 | `p200_008` | no | no | `បន្លាំ` |
| 9 | 240 | `p240_011` | no | no | no |
| 10 | 202 | `p202_014` | no | no | no |
| 11 | 139 | `p139_009` | no | no | no |
| 12 | 96 | `p096_035` | no | no | no |

Only block 4 contains `ជម្រើសដោយធម្មជាតិ`, and it is a lead-in sentence, not the definition:

> `ក្នុងជម្រើសដោយធម្មជាតិការរស់ដែលមាន លក្ខណៈល្អ អាចបន្ដរស់នៅនឹងលក្ខខណ្ឌជីវិតនិងរស់រានបាន ហើយអាចបន្តពូជបបង្កើតកូនចៅជំនាន់ ក្រោយ ។`

The definition itself is in the missing `p201_012` / `p202_013` chunks:

> `ជម្រើសដោយធម្មជាតិជាដំណើរដែលឯកត្តៈមានបន្ស៊ាំទៅនឹងមជ្ឈដ្ឋានប្រសើរជាងគេ អាចរស់រានមានជីវិតនិងធ្វើការបន្តពូជបានច្រើនជាងភាវៈរស់ដទៃទៀតក្នុងប្រភេទតែមួយ ។`

So the model had a weak cue (“natural selection” in a recap) but not the mechanism sentence itself.

### 2.4 Actual answer and grounding

Displayed answer:

> `ការសម្របប្រួលរបស់ភាវៈរស់ទៅនឹងមជ្ឈដ្ឋានដើម្បីរស់រាននិងបង្កើតកូនចៅជំនាន់ក្រោយ ហៅថា លក្ខណៈបន្ស៊ាំ ឬបន្លំ។ ក្រោមលក្ខខណ្ឌជីវិតប្រែប្រួល ភាវៈរស់កែប្រែលក្ខណៈរបស់ខ្លួនទៅតាមទិសដៅផ្សេងៗ ដោយរក្សានូវលក្ខណៈល្អៗ ដែលឆ្លងកាត់ការវិវត្តន៍យូរលង់ក្លាយជាលក្ខណៈតពូជ និងអាចបញ្ជូនពីជំនាន់មួយទៅជំនាន់មួយទៀត។`
>
> `[ទំព័រ 200, 236]`

The first sentence is a near-verbatim quote of the chapter-7 definition in `p236_001`/`p236_002`:

> `ការសម្របប្រួលរបស់ភាវៈរស់ទៅនឹងមជ្ឈដ្ឋានដើម្បី រស់រាននិងបង្កើតកូនចៅជំនាន់ក្រោយ ហៅថា បន្លំ ។`

The second sentence is a paraphrase of the same chapter-7 passage:

> `ក្រោមលក្ខខណ្ឌជីវិតប្រែប្រួល ភាវៈរស់កែប្រែលក្ខណៈរបស់ខ្លួនទៅតាមទិសដៅផ្សេងៗ ដោយរក្សាកូននូវលក្ខណៈ ល្អៗ ។ ឆ្លងកាត់ ការវិវត្តន៍យូរលង់ លក្ខណៈបន្លំទាំងអស់គ្នាយយ៉ាងលក្ខណៈតពូជ ហើយអាចបញ្ជូនពីជំនាន់មួយទៅ ជំនាន់មួយ ។`

`raw_answer` and the displayed answer are substantively identical; only spacing/punctuation changed. This is not a sanitizer or citation-parser bug.

### 2.5 Scores

| Dimension | Score | Why |
|---|---:|---|
| Correctness | 3 | `concept_coverage = 0.5`; only `បន្ស៊ាំ` found |
| Completeness | 4 | Coverage 0.5 plus sufficient length |
| Faithfulness | 5 | All content is grounded in the supplied blocks |
| Clarity | 5 | Short, readable definition |
| Terminology | 4 | `បន្សំ`/`បន្ស៊ាំ`/`បន្លំ` variants; one gold concept missing |
| Citation | 4 | Footer pages overlap p203 but not p202; body cites p200, p236 |
| Helpfulness | 5 | Definition-like structure present |
| Concept coverage | 0.5 | `បន្ស៊ាំ` yes; `ជម្រើសដោយធម្មជាតិ` no |
| Invalid citations | 0 | All cited pages are in retrieved pages |

Correctness 3/5 is exactly `clamp(1 + 4 × 0.5)`. It is a coverage score, not a judgment that the definition is wrong. The answer is faithful, grounded, and textbook-derived. The score reflects one missing gold keyword.

### 2.6 Stability across the v3 baseline

The q111 failure is not generation variance. The v3 baseline answer is also the chapter-7 definition:

> `បន្លំ (ឬលក្ខណៈបន្ស៊ាំ) គឺការសម្របប្រួលរបស់ភាវៈរស់ទៅនឹងមជ្ឈដ្ឋាន ...`

The v3 scores were correctness 3, completeness 3, citation 3, coverage 0.5. The v3.1 answer changes the order to `បន្ស៊ាំ ឬបន្លំ` and adds p200 to the citation, but the underlying behavior is the same: the model retrieves and copies the chapter-7 definition, and never states the natural-selection mechanism. This is a systematic context/selection pattern, not a one-off generation fluctuation.

---

## 3. Expected vs actual biological concepts

| Component | Expected (gold) | Generated | Problem |
|---|---|---|---|
| Main biological concept | Adaptation (`បន្ស៊ាំ`) as a heritable characteristic that helps organisms survive and reproduce, understood within natural selection | Adaptation defined as a heritable characteristic that helps organisms survive and reproduce | Main concept is correct; the explanatory frame is incomplete |
| Definition | Characteristics that make an organism suited to its environment and able to survive/reproduce | `ការសម្របប្រួល ... ទៅនឹងមជ្ឈដ្ឋាន ដើម្បីរស់រាននិងបង្កើតកូនចៅជំនាន់ក្រោយ` | Correct, textbook-faithful |
| Required explanation | Natural selection: variation, competition, differential survival/reproduction; adaptation accumulates over generations | “Under changing conditions organisms change their characteristics in various directions, keep the good ones, and over long evolution these become hereditary” | **Missing natural selection**; the wording can imply directed/Lamarckian change rather than selection acting on variation |
| Important terminology | `បន្ស៊ាំ`, `ជម្រើសដោយធម្មជាតិ` | `បន្ស៊ាំ`, `បន្លំ` | `ជម្រើសដោយធម្មជាតិ` missing; `បន្លំ` is a textbook OCR variant, not camouflage |
| Textbook evidence | pp. 202–203, specifically `p201_012`/`p202_013` for the natural-selection definition; `p203_016` for competition | p236 chapter-7 definition and p200 `បន្លាំ` definition; p203 only in footer | Definition evidence is present and correctly used; mechanism evidence is absent from the useful context |
| Final conclusion | Adaptation is the result of natural selection acting on heritable variation | Adaptation is a heritable change that arises under changing conditions | Conclusion is incomplete and mildly misleading about mechanism |

**Correct:** the definition, the survival/reproduction criterion, the heritability statement, and the textbook grounding.
**Missing:** the natural-selection mechanism and the competitive/differential-survival explanation.
**Misleading (mild):** “organisms change their characteristics ... keep the good ones ... become hereditary” can be read as Lamarckian directed adaptation. The textbook’s chapter-7 phrasing itself is loose; the chapter-6 natural-selection passage is the corrective, and it was not in the useful context.
**Not an error:** `បន្លំ`. In this textbook it is used as a variant of `បន្ស៊ាំ`/`បន្លាំ` for adaptation (p236, p206), not as camouflage.

---

## 4. Evidence and context analysis

### 4.1 What the textbook actually says

**Chapter 6, p200 (`បន្លាំ`):**

> `រូបរាងចំពុះជាឧទាហរណ៍មួយនៃ បន្លាំ ។ បន្លាំជាលក្ខណៈមួយដែលធ្វើឱ្យវារៈរស់ ... មានជីវិតនិងបន្តពូជបានសមស្របនឹងមជ្ឈដ្ឋានមួយ ។`

**Chapter 6, p201–202 (`p201_012`, natural selection):**

> `ជម្រើសដោយធម្មជាតិជាដំណើរដែលឯកត្តៈមានបន្ស៊ាំទៅនឹងមជ្ឈដ្ឋានប្រសើរជាងគេ អាចរស់រានមានជីវិតនិងធ្វើការបន្តពូជបានច្រើនជាងភាវៈរស់ដទៃទៀតក្នុងប្រភេទតែមួយ ។`

This is the sentence the gold’s second concept points to. It is not in the q111 context.

**Chapter 6, p202–203 (`p202_015`/`p203_016`, competition and differential survival):**

> `វាបញ្ជូនលក្ខណៈបន្ស៊ាំនេះទៅជំនាន់ក្រោយ ។`

The surrounding text is about competition between organisms and between species. The context includes `p203_016`, but not the earlier natural-selection definition.

**Chapter 7, p236 (`p236_001`/`p236_002`, adaptation definition):**

> `ការសម្របប្រួលរបស់ភាវៈរស់ទៅនឹងមជ្ឈដ្ឋានដើម្បី រស់រាននិងបង្កើតកូនចៅជំនាន់ក្រោយ ហៅថា បន្លំ ។`

This is the sentence the model copied. It is a correct definition of adaptation. The same block’s lead-in mentions `ជម្រើសដោយធម្មជាតិ`, but only as a recap:

> `ក្នុងជម្រើសដោយធម្មជាតិការរស់ដែលមាន លក្ខណៈល្អ អាចបន្ដរស់នៅនឹងលក្ខខណ្ឌជីវិតនិងរស់រានបាន ...`

### 4.2 The `បន្លំ` question: the previous diagnosis is wrong

`បន្លំ` occurs 14 times in the corpus:

- **Chapter 7, p236/p236–237:** the definition of adaptation (`ការសម្របប្រួល ... ហៅថា បន្លំ`), plus examples of adaptive coloration and shape. This is the dominant biological use.
- **Chapter 6, p206:** `លក្ខណៈបន្លំនៃចំពុះបក្សី` — adaptive characteristics of bird beaks. Again adaptation, not camouflage.
- **Chapter 6, p236:** the same chapter-7 recap/definition.
- **Chapter 5, p189:** `ការបន្លំពីជនដៃថៃ` — counterfeiting/piracy, not a biological term.
- **Chapter 5, p190:** `សែនបន្លំឪប្រ៊ី` — an OCR-corrupted genetic-technology phrase, not camouflage.

Camouflage is expressed separately:

- `p239_009`: `មានពណ៌សម្បុរលាក់បំពួន` and `លាក់បំពួន`.
- `p200_008` describes cryptic coloration as an example of `បន្លាំ` (adaptation), not as a separate term.

Therefore:

- The model did **not** invent a camouflage definition.
- `បន្លំ` in q111 is the textbook’s own chapter-7 OCR/terminology variant for adaptation.
- The answer’s `ឬបន្លំ` is a terminology reconciliation, not a scientific conflation.
- The real terminology risk is that `បន្លំ` is nonstandard and ambiguous to students (and can mean “counterfeit” in another context), so the answer should ideally present the standard term `បន្ស៊ាំ` and mention the textbook variant only as a note, not as a co-equal synonym.

### 4.3 Page-level hit vs chunk-level evidence

This is the central retrieval finding:

| Gold page | Page in context? | Gold chunk in context? | What is actually in context |
|---|---|---|---|
| 202 | yes | no (`p201_012`, `p202_013` absent) | `p202_014` — variation and competition |
| 203 | yes | no (`p203_016` is competition; `p202_015` absent) | `p203_016` — competition |

The page-level metric `hit@5 = true` is technically correct and misleading for this question. The retrieval system found the right pages but not the right **passages**. The answer therefore had the definition (from p236) but not the mechanism (from p201–202).

This also explains why the citation score is 4 rather than 5: the footer includes p203-204 because it is a retrieved source, but the body cites p200 and p236. The expected-page overlap is 1/2 (p203 only), and validity is 1.0, giving `clamp(1 + 4 × (0.5×1.0 + 0.5×0.5)) = 4`. The citation score does not prove that the body used p203 evidence.

### 4.4 Why the answer looks the way it does

The context order is the key:

1. Four of the first five blocks are chapter 7 (`p237`, `p239`, `p236–237`, `p236`).
2. The chapter-7 definition is repeated in two overlapping chunks (`p236_001` and `p236_002`), increasing its salience.
3. The chapter-6 natural-selection definition is not present; the only `ជម្រើសដោយធម្មជាតិ` phrase is a recap in block 4.
4. The model produces a concise definition by copying the most salient definition sentence and paraphrasing the adjacent chapter-7 explanation.
5. The model does not add natural selection because the mechanism sentence is absent, and because the prompt/answer style favors a direct definition over a synthesized mechanism.

This is a **generation-selection + context-ordering** failure, not a hallucination or a wrong-chapter definition error.

---

## 5. Verified root cause

| Candidate cause | Verdict | Evidence |
|---|---|---|
| Retrieval failure | **Partial** | Page-level hit@5 is true; chunk-level gold evidence is missing. `p201_012`/`p202_013` absent; `p202_014`/`p203_016` present. |
| Wrong chapter or lesson context | **Contributing** | Top 4 of 5 blocks are chapter 7; answer copies p236. But chapter 7’s definition is the same concept and is textbook-canonical. |
| Missing supporting evidence | **Yes, for the mechanism** | The natural-selection definition sentence is not in context. The adaptation definition itself is present. |
| Question interpretation | **Mostly correct** | The model answers “what is adaptation?” correctly. The gold additionally requires the mechanism; that is an expectation mismatch, not a misinterpretation. |
| Multi-part question splitting | **Not applicable** | Single question, one query. |
| Generation/prompt behavior | **Primary proximate cause** | The model copies the top-ranked definition and does not synthesize the natural-selection mechanism, even though a recap cue exists in block 4. |
| Khmer terminology ambiguity | **Contributing** | `បន្សំ` (question) → `បន្ស៊ាំ` (query); corpus uses `បន្ស៊ាំ`, `បន្លាំ`, `បន្លំ`; `បន្លំ` also means “counterfeit” elsewhere. |
| OCR/textbook parsing | **Contributing** | Chapter 7 text is visibly garbled (`បន្លំ`, `កូន`, `យយ៉ាង`, etc.); chapter 6 p200 uses `បន្លាំ`. |
| Evaluation rubric limitation | **Strong artifact** | Correctness is literal concept coverage. 1/2 coverage → 3/5, regardless of definitional correctness. Faithfulness is 5 and invalid citations are 0. |

**Verified root-cause statement:**

q111 fails as a *complete conceptual answer* because the model anchors on the top-ranked chapter-7 definition and never states the chapter-6 natural-selection mechanism. The mechanism’s exact evidence chunk was missed at the chunk level even though its page was nominally retrieved. The score of 3/5 is then produced by a keyword-coverage rubric that cannot distinguish “definition correct but mechanism omitted” from “definition wrong.” The previous “camouflage conflation” claim is rejected: the textbook itself uses `បន្លំ` for adaptation, and camouflage is `លាក់បំពួន` on p239.

**Confidence:** high for the evidence and for rejecting the camouflage diagnosis; medium-high for treating the missing mechanism as a genuine failure (the question is a definition question, so the gold’s second concept is stricter than the literal question); high that the 3/5 is not a measure of scientific correctness.

---

## 6. Secondary failure analysis

The table below separates content quality from the score. “Artifact” means the answer is substantially correct but the rubric/alias/format penalized it. “Genuine” means the answer itself is incomplete, evasive, or misleading.

### 6.1 q56 — rice grain

- **Question:** `តើអង្ករសំរូបដែលយើងបរិភោគជាផ្នែកណារបស់រុក្ខជាតិ?`
- **Gold:** concept `គ្រាប់`; pages 12, 18.
- **Answer:** `អង្ករសំរូប ... គឺជាផ្នែក អង់ដូស្ពែម (ឬ អាល់ប៊ុយមែន) របស់គ្រាប់ស្រូវ ...`
- **Textbook:** p17–18 defines `អង់ដូស្ពែម` as the embryo’s stored food and `អាល់ប៊ុយមែន` as the food-storing cell mass.
- **Assessment:** correct. Milled rice is mostly endosperm; the answer also names the seed. Scores: correctness 5, completeness 4, helpfulness 3. Helpfulness 3 is a brevity/structure artifact (reasoning branch wants ≥2 structural lines or ≥350 characters; this is one short paragraph).
- **Classification:** no genuine error; helpfulness artifact.

### 6.2 q58 — xylem vs phloem

- **Question:** `តើស៊ីឡែមនិងដូអែមខុសគ្នាដូចម្តេច?`
- **Gold:** `ស៊ីឡែម`, `ដូអែម`; pages 13, 23, 28, 29, 32, 40.
- **Answer:** a correct comparison of `ស៊ីឡែម` and `ផ្លូអែម`, including water/mineral transport versus organic-food transport, and structural details.
- **Textbook:** p13 uses `ផ្លូអែម`; p13–14 uses the OCR variant `ដូអែម` in one place. Both refer to phloem.
- **Assessment:** biologically correct and complete. Correctness 3 comes only from `concept_present('ដូអែម', body)` being false; the answer uses the standard spelling `ផ្លូអែម`. This is a gold-spelling artifact.
- **Classification:** no genuine error; terminology/alias artifact.

### 6.3 q65 — protein roles

- **Question:** `ពន្យល់ពីតួនាទីរបស់ប្រូតេអ៊ីនក្នុងសារពាង្គកាយ`
- **Gold:** `ប្រូតេអ៊ីន`, `តួនាទី`; pages 122, 127, 128, 130, 134.
- **Answer:** six correct roles — enzyme/catalyst, structural, movement, defense, hormonal, transport — with examples and citations to pp. 130–131.
- **Assessment:** correct and comprehensive. The answer says `មាននាទី` rather than the noun `តួនាទី`, so coverage is 0.5 and correctness 3. This is a pure lexical artifact. Terminology 4 follows the same coverage formula.
- **Classification:** no genuine error; lexical artifact.

### 6.4 q68 — parent-to-child genetic information

- **Question:** `ពន្យល់ពីរបៀបដែលព័ត៌មានសេនេទិចត្រូវបានបញ្ជូនពីមេទៅកូន`
- **Gold:** `សេនេទិច`, `ADN`; pages 149, 150.
- **Answer:** parent-to-child transmission via gametes, DNA replication, daughter cells receiving DNA, and maintenance across cell generations.
- **Textbook:** p149 states that parents always transmit their hereditary characteristics to offspring, whether sexual or asexual reproduction; p150 introduces DNA as the carrier of genetic information.
- **Assessment:** substantively correct. The first bullet is almost verbatim p149. Citation 4 because the answer cites p149 but not p150; helpfulness 3 because the process branch does not find two structural step markers. Both are rubric artifacts/minor omissions, not scientific errors.
- **Classification:** minor completeness/citation artifact; no genuine scientific error.

### 6.5 q87 — three quiz questions

- **Question:** `ចូរបង្កើតសំណួរសាកល្បង 3 អំពីពពួក និងសហគមន៍`
- **Gold:** `ពពួក`, `សហគមន៍`; pages 227, 228, 229, 235, 243.
- **Answer:** three valid questions — definitions of population/community; methods and causes of population-size change; types of relationships in a community.
- **Assessment:** fulfills the request. Helpfulness 3 because the `quiz` branch requires the literal pattern `សំណួរទី\s*\d+` at least three times; the answer simply lists three questions. This is a formatting artifact.
- **Classification:** no genuine error; format artifact.

### 6.6 q94 — goiter prevention

- **Question:** `តើគេអាចបង្ការជំងឺពកកបានដោយរបៀបណា?`
- **Gold:** `បង្ការ`, `ពកក`, `អ៊ីយ៉ូត`, `អំបិល`, `អាហារសមុទ្រ`; page 109.
- **Answer:** eat iodine-rich food, especially seafood, as a good iodine source; cites p109.
- **Textbook:** p109 says goiter can be prevented by eating food containing iodine, and that `គ្រិន`/seafood are good iodine sources. It does **not** mention iodized salt in the retrieved chunk.
- **Assessment:** textbook-faithful. Coverage 0.8 because `អំបិល` is missing. A corpus-wide search found no chunk where `អំបិល` co-occurs with `អ៊ីយ៉ូត`; the gold’s iodized-salt concept is external/general knowledge, not textbook-supported. The answer should not be penalized for not inventing it. (In general biology, iodized salt is indeed the main public-health measure, but this system is constrained to the supplied context.)
- **Classification:** no generation error; gold over-specification / context-coverage mismatch. The typo `គ្រឿន` mirrors the textbook’s OCR `គ្រិន`.

### 6.7 q96 — mango: dicot or monocot?

- **Question:** `តើស្វាយជារុក្ខជាតិឌីកូទីលេដូន ឬ រុក្ខជាតិម៉ូណូកូទីលេដូន?`
- **Gold:** `ស្វាយ`, `ឌីកូទីលេដូន`, `កូទីលេដុង`, `ទ្រនុងបែកខ្នែង`, `ឫសកែវ`; pages 12, 19.
- **Answer:** mango is an angiosperm; “the document does not explicitly say whether mango is mono- or dicot”; then lists dicot traits (vascular bundles in a ring, branching leaf veins) and contrasts them with monocot traits (scattered bundles, parallel veins). It never says “mango is a dicot.”
- **Textbook:** p6 says pine is a gymnosperm and mango is an angiosperm. p12/p19 define monocot/dicot traits and provide a comparison table: two cotyledons, branching veins, ring-arranged vascular bundles, taproot for dicots.
- **Assessment:** the model’s factual statement that the document does not explicitly label mango is true. But the task is an application question: the textbook gives diagnostic traits, and the expected answer is an inference. The answer lists the relevant traits but refuses to commit, so it fails the user’s binary question. It also omits the cotyledon count and taproot. This is a genuine **decisiveness/application** failure, not a factual misconception. The score 3/3/5/3/4/5/5 and coverage 0.4 reflect both the missing conclusion and the missing keywords; `ទ្រនុងបែកមែក` is a synonym of the gold `ទ្រនុងបែកខ្នែង`, so part of the coverage loss is lexical.
- **Classification:** genuine failure (application/decisiveness); not a factual error.

### 6.8 Additional low-score controls

These were not in the requested list, but they are important because they are the two lowest correctness rows in the 45-question set.

**q78 — definition of a gene**

- Gold concept: `ហ្សែន`; page 174.
- Answer: `សែនគឺជាអង្គធាតុមួយរបស់ ADN ដែលផ្ទុកព័ត៌មានសេនេទិច ...`
- The answer is substantively correct (gene = DNA segment carrying genetic information for a protein/trait). It uses `សែន`, the query alias produced by the gene-alias expansion (`ហ្សែន -> សែន`). The evaluator’s `CONCEPT_ALIASES` does not include `ហ្សែន: ['ហ្សែន', 'សែន']`, so coverage is 0.0 and correctness is 1.
- **Classification:** pure alias artifact. This is the clearest example of the evaluator penalizing a correct answer. It should not be treated as an answer-quality failure.

**q86 — three quiz questions about water absorption**

- Gold concept: `ស្រូបទឹក`; pages 26, 27, 40.
- Answer: three valid questions about water absorption, using `ស្រូបយកទឹក` and Khmer numerals `១. ២. ៣.`.
- `concept_present('ស្រូបទឹក', ...)` is false because the answer inserts `យក`; coverage 0.0, correctness 1. The quiz-format branch also does not recognize the numbering.
- **Classification:** pure lexical/format artifact.

**q55 — pine pollen process**

- Gold: `លំអង`, `លំអងផ្កា`; page 9.
- Answer: correct, detailed pine pollination/fertilization process. It contains `គ្រាប់លំអង` but not `លំអងផ្កា`, so coverage is 0.5 and correctness 3.
- **Classification:** minor terminology/coverage artifact; content is correct.

**q93 — iodine deficiency consequences**

- Gold: `អ៊ីយ៉ូត`, `ទីរ៉ូអ៊ីត`, `ទីរ៉ុកស៊ីន`, `ពកក`, `TSH`; page 109.
- Answer: content-correct explanation of the TSH/goiter mechanism, but one long run-on sentence with OCR-garbled words (`អ៊ីប៉ូភីសមុខត្រូវបានភ្លេចឱ្យផលិត`). Clarity 2.
- **Classification:** genuine clarity/format issue; not a content error.

---

## 7. Genuine failures vs rubric artifacts

### 7.1 Genuine answer failures

| Case | Genuine issue | Severity | Evidence |
|---|---|---|---|
| q111 | Missing natural-selection mechanism; chapter-7 paraphrase can imply directed/Lamarckian adaptation; ambiguous `បន្លំ` presented as a co-equal synonym | Moderate | Gold requires `ជម្រើសដោយធម្មជាតិ`; answer never states it; p201_012 definition absent from context |
| q96 | Does not answer the binary question; hedges that the document “does not specify”; lists dicot traits but does not apply them; omits cotyledon count and taproot | Moderate | Gold expects dicot classification; p19 table provides the traits; answer never says `ស្វាយជាឌីកូទីលេដូន` |
| q93 | Clarity only: long run-on sentence with garbled OCR wording | Minor | Content concepts all present; clarity 2 |

No other requested case contains a substantive scientific error.

### 7.2 Rubric/measurement artifacts

| Case | Score symptom | Actual cause |
|---|---|---|
| q78 | Correctness 1, coverage 0.0 | Answer uses query alias `សែន`; gold uses `ហ្សែន`; evaluator has no alias |
| q86 | Correctness 1, coverage 0.0 | Answer uses `ស្រូបយកទឹក`; gold uses `ស្រូបទឹក`; quiz numbering not recognized |
| q58 | Correctness 3, coverage 0.5 | Answer uses standard `ផ្លូអែម`; gold uses OCR variant `ដូអែម` |
| q65 | Correctness 3, coverage 0.5 | Answer uses `មាននាទី`; gold keyword `តួនាទី` |
| q56 | Helpfulness 3 | Correct one-paragraph answer; reasoning branch wants ≥2 structural lines or ≥350 chars |
| q68 | Citation 4, helpfulness 3 | Answer cites p149 but not p150; process branch does not find two step markers |
| q87 | Helpfulness 3 | Three valid questions, but no literal `សំណួរទី 1/2/3` labels |
| q94 | Correctness 4, coverage 0.8 | Gold `អំបិល` is not in the textbook chunk and does not co-occur with `អ៊ីយ៉ូត` anywhere in the corpus |
| q55 | Correctness 3, coverage 0.5 | Correct answer; gold `លំអងផ្កា` absent |
| q111 | Correctness 3, coverage 0.5 | One gold concept missing; definition itself correct; faithfulness 5 |

### 7.3 Why the scores behave this way

The scoring code (`scripts/evaluation/evaluate_answers.py`) is transparent:

- `concept_present(concept, body_l)` checks literal substring presence after lowercase/LaTeX folding.
- `coverage = found / expected_concepts`.
- `correctness = clamp(1 + 4 × coverage)`.
- `completeness = clamp(1 + 4 × (0.7 × coverage + 0.3 × length_part))`.
- `terminology = clamp(1 + 4 × (0.5 × (1 − banned_hits) + 0.5 × coverage))`.
- `citation` uses `cite_pages(rec['answer'])`, which includes the footer, and compares against `retrieved_pages` and `expected_pages`.
- `helpfulness` is rule-based by question type (e.g., quiz requires `សំណួរទី n`; process requires step words; comparison requires `ដូចគ្នា`/`ខុសគ្នា`).

`CONCEPT_ALIASES` contains only a small set (`gymnosperm`, `សំណល់`, `វិវត្តន៍`, `ចំណងប៉ុបទីត`, `ជម្រើសដោយធម្មជាតិ`, `ARNm`). It has an explicit comment that the stale form `បន្សំ` must not match `បន្ស៊ាំ` so q111 keeps failing. That is a deliberate benchmark choice, but it means:

- Correctness is a **keyword-coverage proxy**, not a scientific-correctness judge.
- Correct answers that use a synonym, alias, OCR variant, or different word form receive 1–3.
- The lowest scores in the set are not the worst answers; q78 and q86 are correct answers with alias mismatches.

This is the single most important measurement finding of Phase 3.

---

## 8. Ranked recommendations

Ranked by expected benefit-to-risk for future unseen Grade 12 Biology questions. None of these are implemented in this phase.

### P0 — Fix measurement integrity before optimizing answers

**Root cause addressed:** keyword coverage, missing aliases, OCR variants, and gold concepts not grounded in the corpus.

**Proposed change:**

- Expand `CONCEPT_ALIASES` with corpus-verified variants:
  - `ហ្សែន`: `ហ្សែន`, `សែន`
  - `ស្រូបទឹក`: `ស្រូបទឹក`, `ស្រូបយកទឹក`
  - `ដូអែម`: `ដូអែម`, `ផ្លូអែម`
  - `តួនាទី`: `តួនាទី`, `នាទី`
  - `បន្ស៊ាំ`: `បន្ស៊ាំ`, `បន្លាំ`, `បន្លំ` (with care; see P3)
  - `ទ្រនុងបែកខ្នែង`: `ទ្រនុងបែកខ្នែង`, `ទ្រនុងបែកមែក`
- Add a `support_level` note to gold concepts: `direct` (literal textbook statement), `variant` (OCR/synonym), `inference` (requires reasoning), `external` (not in corpus). This is documentation, not a label change.
- Keep the old strict scoring available as a frozen comparator so v3.1 numbers remain comparable.

**Files potentially affected:** `scripts/evaluation/evaluate_answers.py` (evaluator only), `data/evaluation/gold_questions_v2.json` (audit annotations only, no concept changes in this phase), `docs/`.

**Expected benefit:** q78, q86, q58, q65 become correctly scored; the score table stops conflating “correct but different wording” with “wrong.” This is necessary before using correctness to prioritize answer improvements.

**Regression risk:** over-crediting wrong answers if aliases are too broad; benchmark comparability changes. Mitigate with negative controls and dual reporting (strict vs alias-aware).

**How to test:** re-score the stored 45 answers with no retrieval/generation changes; verify q78/q86/q58/q65 improve; verify q111 remains 3/5 (or document the change); verify known-wrong negative controls do not improve.

**Gemini regeneration required:** **No** — this is a stored-answer re-score.

### P1 — Require mechanism/application synthesis in generated answers

**Root cause addressed:** q111 omits natural selection; q96 does not apply dicot traits to mango.

**Proposed change:** add a small, general instruction to the generation prompt (not a q111/q96 special case):

- For **definition** questions: give the definition, then one sentence on **how/why** it arises or what it does, if the context supports it.
- For **application/classification** questions: state the classification/answer **first**, then justify it with the textbook traits.
- For **process** questions: use explicit ordered steps.
- Never invent evidence; if the context lacks the mechanism, say what the context supports rather than filling the gap with general knowledge.

**Files potentially affected:** `app/prompt.py` (system/feature prompt text). No retrieval changes.

**Expected benefit:** q111 would be pushed to mention natural selection when the recap is present; q96 would be pushed to commit to “dicot” and list the traits. Generalizes to unseen definition/application questions.

**Regression risk:** longer answers, more tokens/latency, potential over-generation or hallucination, format drift on comparison/summary questions. Keep the instruction narrow (definition/application only) and test on a fixed sample.

**How to test:** regenerate only a small validation set (q111, q96, plus 5 controls: q56, q58, q65, q68, q87) with the new prompt; require no new invalid citations, faithfulness ≥ 4.5, and no regression in the controls. Do not run the full 45 until the small set passes.

**Gemini regeneration required:** **Yes, for the small validation sample only.**

### P2 — Chunk-level evidence diversity in retrieval

**Root cause addressed:** page-level hit@5 can be true while the definition/mechanism chunk is absent.

**Proposed change:** after reranking, deduplicate overlapping chunks from the same page/lesson and ensure the context includes at least one chunk per top-ranked page/lesson, or add a lightweight query-expansion cue for definition/mechanism terms. Avoid changing TOP_K, RERANKER_TOP_K, threshold, embeddings, or Chroma.

**Files potentially affected:** `app/retrieval.py`, `app/config.py` (only if a new non-threshold constant is needed).

**Expected benefit:** q111’s context would include `p201_012`/`p202_013`; future definition questions would get the exact defining passage, not just an adjacent passage.

**Regression risk:** any retrieval change can move the frozen R@1/R@3/R@5/MRR and false-abstention numbers; deduplication can remove useful context; chapter diversity can dilute relevance. This is the highest-risk recommendation.

**How to test:** measure the frozen retrieval metrics on the 125-row set; require R@5 = 1.000, false abstention 0/116, OOS 9/9, and no material MRR regression; then regenerate the small validation set.

**Gemini regeneration required:** **Yes, for validation** (retrieval changes affect context).

### P3 — Context-aware terminology normalization for retrieval and scoring

**Root cause addressed:** OCR variants (`បន្សំ`, `បន្ស៊ាំ`, `បន្លាំ`, `បន្លំ`; `ដូអែម`/`ផ្លូអែម`; `ហ្សែន`/`សែន`) and the `បន្លំ` ambiguity.

**Proposed change:** create a small shared variant map used for **query expansion and evaluator aliases**, not for rewriting biological answers. Make `បន្លំ` context-sensitive: adaptation in chapter 6/7 biology text; “counterfeit” in the chapter-5 biotechnology text. Do not globally replace `បន្លំ` in generated output.

**Files potentially affected:** a new small `app/terms.py` or `data/glossary/` entry; `app/retrieval.py` for query expansion; `scripts/evaluation/evaluate_answers.py` for aliases.

**Expected benefit:** better recall/ranking for OCR-corrupted questions; fewer false rubric failures; clearer terminology in answers.

**Regression risk:** false expansions and over-normalization; `បន្លំ` has a legitimate non-biology sense. Requires context/chapter guards and tests.

**How to test:** unit tests for each variant; retrieval metrics on the frozen set; spot-check that `បន្លំ` in chapter 5 is not rewritten to adaptation.

**Gemini regeneration required:** **No** for scoring; **yes** for retrieval validation if query expansion changes retrieval.

### P4 — Output structure for quiz/process questions

**Root cause addressed:** q87/q86 quiz-format helpfulness; q68 process-step helpfulness.

**Proposed change:** when the user explicitly asks for a quiz or a process, use explicit labels (`សំណួរទី 1`, `ជំហានទី 1`, etc.) and keep the requested number of items. Do not impose this on definition/comparison answers.

**Files potentially affected:** `app/prompt.py`.

**Expected benefit:** better helpfulness/clarity and easier student use; fewer format artifacts.

**Regression risk:** rigid formatting; unnecessary verbosity; may conflict with the “concise” style.

**How to test:** small validation set (q86, q87, q68, q55), plus a definition control; require no content regression.

**Gemini regeneration required:** **Yes, for validation.**

### P5 — Benchmark/gold audit (documentation only)

**Root cause addressed:** q94’s `អំបិល` is not in the corpus; q111’s gold requires a mechanism for a definition question; q96 requires an inference the textbook does not state explicitly.

**Proposed change:** annotate each gold concept with its support level and evidence page/chunk. Do not change gold labels in this phase. Use the annotations to decide whether a future benchmark revision is justified.

**Files potentially affected:** `data/evaluation/gold_questions_v2.json` (future, with approval), `docs/`.

**Expected benefit:** valid measurement and fewer false “failures.”

**Regression risk:** changing gold labels would break comparability; keep annotations separate from labels.

**How to test:** review the 45 gold rows; confirm each concept is either directly supported, a documented variant, an intended inference, or explicitly marked external.

**Gemini regeneration required:** **No.**

---

## 9. Regression risks

| Change | Main risk | Mitigation |
|---|---|---|
| Alias-aware scoring (P0) | Over-credits wrong answers; v3.1 numbers no longer directly comparable | Keep strict and alias-aware scores side by side; negative controls; manual spot-check |
| Prompt mechanism/application rule (P1) | Longer answers, token/latency cost, hallucination, format drift | Narrow scope (definition/application/process only); small validation set; require citations and faithfulness check |
| Chunk-level retrieval diversity (P2) | Frozen retrieval metrics move; useful context removed; false abstention changes | Re-baseline R@1/R@3/R@5/MRR, false abstention, OOS; do not change TOP_K/threshold; compare contexts before/after |
| Terminology expansion (P3) | False normalization; `បន្លំ` ambiguity | Context/chapter guards; unit tests; no answer rewriting |
| Quiz/process formatting (P4) | Rigid or verbose answers | Only when the user asks for quiz/process; controls |
| Gold audit (P5) | Benchmark comparability | Annotate, do not change labels; version the benchmark |

No code, retrieval, gold, prompt, or model changes were made in this phase, so no regression was introduced by this diagnosis.

---

## 10. Proposed acceptance criteria for the next implementation phase

### Measurement (P0)

- Re-score the stored 45 answers with the alias-aware evaluator, with **no** retrieval/generation changes.
- q78, q86, q58, q65 must no longer be reported as correctness failures solely because of aliases/variants.
- q111 must remain documented as a genuine mechanism gap (not silently “fixed” by aliases alone).
- Negative controls (deliberately wrong answers) must not gain correctness credit.
- Report both strict and alias-aware scores; do not overwrite the v3.1 baseline.

### Generation (P1)

- On a fixed small validation set (q111, q96, q56, q58, q65, q68, q87):
  - q111 mentions `ជម្រើសដោយធម្មជាតិ` and explains selection without inventing evidence.
  - q96 explicitly states that mango is a dicot and supports it with at least two textbook traits (cotyledons, branching veins, ring vascular bundles, taproot).
  - The five controls do not regress in correctness/completeness/faithfulness.
- No new invalid citations; citation integrity remains 0 invalid rows; faithfulness ≥ 4.5.
- No hardcoded q111/q96 strings or question IDs in production logic.

### Retrieval (P2, only if pursued)

- Frozen retrieval metrics do not fall below the accepted baseline: R@1 = 0.655, R@3 = 0.888, R@5 = 1.000, MRR = 0.785; false abstention 0/116; OOS abstention 9/9.
- q111’s context includes `p201_012` or `p202_013` (the natural-selection definition) without removing the chapter-6 definition evidence.
- No changes to TOP_K, RERANKER_TOP_K, embeddings, reranker, chunking, corpus, Chroma, threshold 0.08, or the Gemini model pool.

### General

- All existing suites pass: citation integrity 84 checks, evaluation harness 80 checks, RAG fallback 26/26.
- Gold labels remain unchanged unless separately approved.
- Any prompt change is validated on stored contexts first; full 45-question regeneration only after the small validation set passes.
- The “camouflage conflation” diagnosis is removed from the working record; future reports should describe q111 as “missing natural-selection mechanism + chunk-level evidence miss + keyword-scoring artifact.”

---

## Appendix — Evidence index

| Claim | Source |
|---|---|
| q111 question, query, gold concepts/pages/note | `answer_evaluations_v3_1_citation.json`, `gold_questions_v2.json` |
| q111 retrieval ranks/scores | `retrieval_v3_1_results.json` row `111:0` |
| q111 12 context blocks and chunk IDs | `answer_evaluations_v3_1_citation.json` + `biology_chunks.json` text matching |
| p236 adaptation definition (`បន្លំ`) | `p236_001`, `p236_002` |
| p201–202 natural-selection definition | `p201_012` |
| p202 variation/competition | `p202_014` |
| p203–204 competition | `p203_016` |
| p200 `បន្លាំ` definition | `p200_008` |
| p206 `លក្ខណៈបន្លំនៃចំពុះបក្សី` | `p206_023` |
| p189 `ការបន្លំពីជនដៃថៃ` | `p189_030` |
| p239 camouflage `លាក់បំពួន` | `p239_009` |
| q94 iodine/seafood, no iodized salt | `p109_020`; corpus-wide `អំបិល` + `អ៊ីយ៉ូត` search |
| q96 mango as angiosperm; dicot traits | `p006_001`; `p012_001`; `p019_018` |
| q56 endosperm/albumen | `p017_013` |
| q58 xylem/phloem spellings | `p013_003`, `p013_004`, `p013_005` |
| q65 protein roles | `p130`–`p131` chunks |
| q68 parent-to-child inheritance | `p149_001`, `p150_001` |
| Scoring formulas | `scripts/evaluation/evaluate_answers.py` |
| v3 q111 baseline | `answer_evaluations_v3.json` |
