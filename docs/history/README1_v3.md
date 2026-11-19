# Khmer Biology AI Tutor — Work Log (Detailed)

## Project Context

RAG-based tutor for Grade 12 Cambodian Biology (Khmer):
- **Retrieval:** `BAAI/bge-m3` embeddings + ChromaDB (`vector_db/`), reranked by `BAAI/bge-reranker-v2-m3`.
- **Generation:** Google Gemini (`gemini-3.6-flash`, rotates through a pool on quota/traffic errors).
- **Hallucination guard:** abstains (returns NOT_FOUND) if the best rerank score < 0.08.
- **Terms:** OCR-scanned textbook; verified garbled terms are mapped back to the official key spelling by two fix lists. The lists are kept aligned for each verified pair; full parity is still an audit item (347 OCR entries vs 325 query entries).

---

## I. OCR / Terminology Corrections (the main ongoing work)

### How it works
Every student query is normalized in two places so it matches the cleaned corpus:
1. `scripts/clean_text.py` → `OCR_FIXES` list, applied at corpus-build time (`apply_ocr_fixes`).
2. `app/utils.py` → `QUERY_FIXES` list, applied to the live question (`normalize_query`).

Both lists are **300+ entries**. The five latest stale-form pairs are kept byte-in-sync; full parity remains an audit item (347 OCR entries vs 325 query entries).

### Corrections added, round by round (from official Grading-Key evaluation)

| # | Topic (Chapter/Lesson) | Concrete fixes |
|---|------------------------|----------------|
| 1 | **Reflex arc / neuron types** (Ch.3 L.1) | `វិញ្ញាណទទួល→ធ្មួលវិញ្ញាណ`, `ផ្ដួល→ធ្មួល`, `ណឺរ៉ូនតភ្ជាគ់→ណឺរ៉ូនភ្ជាគ់`, `ធួលត្រចៀក→ធ្មួលត្រចៀក`, `សូររោទ៍→សូរសំឡេងរោទ៍` |
| 2 | **Neuron classification** (Ch.3 L.1) | `ឯកប្ដួល/ឯកប៉ូល→ឯកបូឡា`, `ទ្វេប្ដួល/ទ្វេប៉ូល→ទ្វេបូឡា`, `ពហុប្ដួល/ពហុប៉ូល→ពហុបូឡា`, `ភាពពន្លាយស៊ីតូប្លាស→ភាពពន្លយស៊ីតូប្លាស` |
| 3 | **Protein types** (Ch.4 L.1) | Globular (ស្វ៊ែរូល) vs Fibrous (សរសៃ) classification |
| 4 | **Vision / eye** (Ch.3 L.2) | `កញ្ចក់ភ្នែក`, `កែវនេត្រ`, `ករនេ`, optic nerve `សរសៃប្រសាទអុបទិក` |
| 5 | **Fossils / molds** (Ch.6) | Fossil cast vs mold distinction |
| 6 | **Pancreas / blood sugar** (Ch.3 L.3) | Insulin (កោសិកាបេតា) vs Glucagon (កោសិកាអាល់ហ្វា) antagonism |
| 7 | **Pituitary gland** (Ch.3 L.3) | Anterior: GH, PRL, MSH, TSH, ACTH, FSH/LH; Posterior: ADH (អង់ទីឌីអ៊ុយរេទិច), Oxytocin |
| 8 | **Ear / cochlea** (Ch.3 L.2) | `បំពង់រាងគូទខ្យង→បំពង់រាងកងធ្នូទងខ្យល់`, `អាំងពុលស៊ីប្រសាទ→អាំងភ្លុចប្រសាទ`, `រលកសូ→រលកសូរ`, `លឺ→ឮ` |
| 9 | **Tripeptide / peptide bond** (Ch.4 L.1) | `ទ្រីប៉ិបទិត/ទ្រីប៉េបទីត→ទ្រីប៉ិបទីត`, `ក្រុមកាបុកស៊ីល→បណ្តុំកាបុកស៊ីល`, `ក្រុមអាមីន→បណ្តុំអាមីន` |
| 10 | **Flower parts** (Ch.1 L.2) | Sepal `ស្លឹកផ្កា`, Petal `ស្លឹកឆ្នូត`, Stamen (សរសៃលំអង + កេសរប្រុស), Carpel/stigma/style/ovary |
| 11 | **Angiosperm classification** (Ch.1 L.2) | Monocot (1 cotyledon) vs Dicot (2 cotyledons) features |
| 12 | **Dicot root** (Ch.1 L.2) | Xylem, Phloem, Pericycle (បរិកឺនែរូស), taproot |
| 13 | **Leaf anatomy** (Ch.1 L.2) | Palisade (ប៉ឺលីសាដ), spongy mesophyll, stomata, cuticle (គុយទីគុល) |
| 14 | **Pollination** (Ch.1 L.2) | `ប្លោកលំអង`, `គ្រាប់លំអង`, flower sex types |
| 15 | **DNA vs RNA** (Ch.5 L.2) | Sugars `ស្ករដេអុកស៊ីរីបូស`/`ស្កររីបូស`, bases `បាសអ៊ុយរ៉ាស៊ីល`/`បាសទីមីន`, `អាស៊ីតនុយក្លេអ៊ិច`, double vs single strand |
| 16 | **Griffith experiment** (Ch.5 L.1) | S/R strains, Pneumococcus, transformation |
| 17 | **Translation** (Ch.4 L.1) | Stop codons UAA/UAG/UGA (បញ្ឈប់), peptide bond formation on ribosome |
| 18 | **Enzymes & temperature** (Ch.4) | Optimal temp, denaturation, Q10 |
| 19 | **Amino acids** | `អាឡានីន`, `គ្លីស៊ីន`, dipeptide `ឌីប៉ិបទីត` |
| 20 | **Natural selection** (Ch.6) | `ជ្រើសរើសធម្មជាតិ` |
| 21 | **Stigma** (Ch.1 L.2) | `ស្ទិចម៉ាតគឺជាផ្កំពូល→ស្ទិចម៉ាតគឺជាផ្នែកកំពូល`, `ស្ទិចម៉ាតជាផ្នែកកំពូល→ស្ទិចម៉ាត គឺជាផ្នែកកំពូល` |
| 22 | **Adaptation vs Combination** (Ch.6 L.1) | `តើបន្សំជាអ្វី→តើបន្ស៊ាំជាអ្វី`, `លក្ខណៈបន្សំ→លក្ខណៈបន្ស៊ាំ`, `សត្វរ៉ាព(សត្វស៊ីគេ)→ប្រេដាទ័រ(សត្វស៊ីគេ)`, `យំឡេង→បន្លឺសំឡេង` |

### Safety rule enforced for every entry
The fix pairs are applied with plain `str.replace()`, so a `bad` form must NEVER be a prefix of a legitimate longer word. This led to one special-cased fix (see bug #2 below): `រលកសូ` → `រលកសូរ` had to be moved out of the list into a guarded regex so it can't corrupt the already-correct `រលកសូរ`.

---

## II. Answer-Format Improvements

### 1. Quiz answers are now collapsible (st.expander)
- **Before:** the model emitted `<details>` HTML, which Streamlit does not render — students saw answers immediately.
- **After:**
  - `app/prompt.py` quiz instruction now demands the exact plain-markdown format:
    ```
    **សំណួរទី X: [Question]**
    **ចម្លើយ:** [Answer with explanation + page ref]
    ```
    and explicitly forbids `<details>`.
  - `app/main.py` gained `_render_quiz_answer()`, which splits the answer on `សំណួរទី X:` markers and draws each question inside an `st.expander` titled with the question — answer hidden until the student clicks.

### 2. Comparison questions MUST have both sections
- `app/prompt.py` contains a **CRITICAL FOR COMPARISON QUESTIONS** instruction: answers to `ប្រៀបធៀប A និង B` must include **both** `លក្ខណៈដូចគ្នា` (similarities) and `លក្ខណៈខុសគ្នា` (differences), each as bullet points, following the official Ground-Truth-Key style.
- The same requirement was added to the **summary** feature.

---

## III. Bugs Found & Fixed

### Bug 1 — Ginkgo / neuron spelling inconsistency in `utils.py`
- `scripts/clean_text.py` used the correct `ឯកបូឡា`, `ទ្វេបូឡា`, `ពហុបូឡា`, `ស៊ីតូប្លាស`, but `app/utils.py` had accidentally been written with `គ` instead of `ប` (`ឯកគូឡា`, `ទ្វេគូឡា`, `ពហុគូឡា`, `ស៊ីតូគ្លាស`) plus corrupted keys (`ពហុគ្ដួល`, `ពហុគ៉ូល`).
- **Fix:** rewrote the neuron block in `utils.py` to mirror `clean_text.py` exactly. Verified both neuron blocks are now byte-identical.

### Bug 2 — `រលកសូរ` (sound wave) corruption
- The pair `("រលកសូ", "រលកសូរ")` is applied with `text.replace()`, which matches inside the already-correct `រលកសូរ` → produced `រលកសូររ` (extra រ). Violates the "no legitimate term matches any key" contract.
- Discovered by the new smoke test while checking `រលកសូរ និង សូររោទ៍`.
- **Fix:** removed the pair from both lists; replaced it with a lookahead-guarded regex `រលកសូ(?!រ)` → `រលកសូរ` in `normalize_query` (utils.py) and `apply_ocr_fixes` (clean_text.py). Corpus was checked: has 0 corrupted `រលកសូររ`.

### Bug 3 — Gemini 503 crashes instead of rotating
- `app/rag.py` `generate_answer()` only caught `429`/`RESOURCE_EXHAUSTED` and rotated to the model pool; a **503 UNAVAILABLE** (high demand) propagated and crashed the app.
- Actually hit live during testing (503 on the quiz run).
- **Fix:** added `503` / `UNAVAILABLE` to the rotation trigger in `generate_answer`, matching the handling already present inside `_call_google_rotate`.

### Bug 4 — Exam-question prefix markers causing abstains (NOT_FOUND)
- `_split_questions()` in `app/main.py` kept the leading marker in the retrieved text: `I. តើ...`, `II. ក. តើ...`, `ក. ...`, `1. ...`.
- Because the marker prefixes the question, rerank scores dropped below the 0.08 abstain threshold:
  - Stigma: `0.13` (bare) → `0.07` (with `I.`) → NOT_FOUND.
  - Adaptation: `0.082` (bare) → `0.045` (with `ក.`) → NOT_FOUND.
- **Fix:** added `_strip_lead_markers()` + `_LEAD_MARKER_RE` (roman numerals `IVX`, Khmer sub-question consonants `ក-អ`, digits) applied to every extracted segment before retrieval, looping until no marker remains.
- **Verified end-to-end** (real embed + rerank + Gemini):
  - `I. តើស្ទិចម៉ាតគឺជាអ្វី?` now answers: «ស្ទិចម៉ាត គឺជាផ្នែកកំពូលនៃកញ្ចុំកេសរញី... ទំហំធំ សភាពស្អិត... ទទួលគ្រាប់លំអង» [ទំព័រ 14, 15].
  - `II. ក. តើបន្ស៊ាំជាអ្វី?` now answers with the official definition incl. scoring keywords «រស់រានមានជីវិត និងបន្តពូជ» + predator/prey adaptations.

---

## IV. Test Suite Added

### `scripts/smoke_test.py` (fast, no heavy models)
- 14 checks, all green:
  - Query normalization: neuron (`ពហុប៉ូល→ពហុបូឡា`), sound-wave guard, adaptation terminology (`បន្សំ→បន្ស៊ាំ`, `រ៉ាព→ប្រេដាទ័រ`, `យំឡេង→បន្លឺសំឡេង`).
  - Marker stripping: `II. ក.`, `I.`, `ក.`, `1.`, and a control with no marker.
  - Quiz-format parser replication.

### `scripts/e2e_format_test.py` (real pipeline + Gemini)
- Comparison query `ចូរប្រៀបធៀប ADN និង ARNm` → top rerank **0.961**, answer contains BOTH លក្ខណៈដូចគ្នា and លក្ខណៈខុសគ្នា → PASS.
- Quiz query → 4 questions (`សំណួរទី 1..4`), all with ចម្លើយ, **no** `<details>` → PASS.

### `scripts/ui_expander_test.py` (Streamlit AppTest)
- App boots cleanly (sidebar radio present).
- `_render_quiz_answer` renders each quiz question as an `st.expander` → 2 quiz expanders with correct titles → PASS.

---

## V. Verification Commands
```
python -m py_compile scripts/clean_text.py app/utils.py app/prompt.py app/main.py app/config.py app/rag.py
python scripts/smoke_test.py            # -> ALL PASS
python scripts/e2e_format_test.py       # -> ALL PASS (needs Gemini API + models)
python scripts/ui_expander_test.py      # -> ALL PASS
```

---

## VI. v3 Corpus + Retrieval Rebuild (completed 2026-10-23)

This section records the full v3 process and its results. The detailed report is
`docs/system_accuracy_evaluation_v3.md`; the artifacts are listed in §VI.9.

### VI.1 Code and evaluation-harness changes

- Moved the Khmer sub-question splitter into `app/utils.py`:
  `_LEAD_MARKER_RE`, `_ROMAN_TOP_RE`, `_KHMER_SEQUENCE`, `_KHMER_INLINE_RE`,
  `strip_lead_markers`, `_split_khmer_subquestions`, `split_questions`.
  `app/main.py` now imports the shared splitter; `scripts/eval_common.py`
  re-exports it. The app and evaluator therefore split questions the same way.
- Added `GOLD_LABEL_CORRECTIONS` to `scripts/build_gold_v2.py`. The v3 gold set
  now has eight page-label corrections (q23, q109, q119, q53, q62, q69, q83,
  q89), with evidence and reasons recorded in
  `data/evaluation/gold_label_changes_v3.json`.
- Added `--tag` and `--ids` to `scripts/evaluate_retrieval_v2.py`:
  - `--tag v3` writes `retrieval_v3_results.json` and `retrieval_v3_summary.txt`;
  - the default remains v2, so historical v2 results are not overwritten;
  - `--ids` refreshes selected question IDs in an existing resumable run.
- Added `scripts/validate_corpus_v3.py`, which writes
  `data/evaluation/corpus_validation_v3.json`.
- Added `scripts/smoke_retrieval_v3.py`, which runs the real query/rerank path on
  the known regression cases and writes `data/evaluation/retrieval_smoke_v3.json`.
- Updated `scripts/build_vector_db.py` to store `page_start` and `page_end` in
  Chroma metadata. The existing collection was also patched in place with
  `collection.update`, so its 609 chunks now have page ranges without
  re-embedding.
- Expanded `scripts/test_eval_harness.py` with splitter, OCR-sync, normalizer,
  gold-label, metric, and scoring checks.
- Wrote `docs/system_accuracy_evaluation_v3.md`.

### VI.2 Corpus rebuild process

Commands used:

```powershell
$env:PYTHONIOENCODING="utf-8"
.\.venv\Scripts\python.exe -X utf8 scripts\clean_text.py
.\.venv\Scripts\python.exe -X utf8 scripts\parse_lessons.py
.\.venv\Scripts\python.exe -X utf8 scripts\chunk_text.py
.\.venv\Scripts\python.exe -X utf8 scripts\validate_corpus_v3.py
```

Results:

| stage | result |
|---|---|
| Cleaned corpus | 257 pages; 333,066 → 329,653 characters (1.0% removed); `data/processed/biology_cleaned.json` |
| Structured dataset | 257 pages; 8 chapters; `data/processed/biology_structured.json` |
| Chunks | **609 chunks** (expected ~610); min 23 / max 3,274 / average 626 characters; `data/processed/biology_chunks.json` |
| Page coverage | all 257 pages covered; `missing_pages=[]`; chunk IDs unique |
| Chunk distribution | `{1:49, 2:102, 3:135, 4:70, 5:106, 6:77, 7:40, 8:30}` |
| Stale OCR forms | **0** in pages and chunks; legitimate `បន្សំ` (“combination”) preserved |
| Validation | **PASS**; report at `data/evaluation/corpus_validation_v3.json` |
| Lesson metadata | **84/609 chunks have no `lesson_id`**, across 29 pages. Includes front matter/chapter intros and genuine content pages (ch2 pp39–58, ch4 pp137–148, ch6 p215). Root cause: running headers use Thai `น` in `មេរៀน`, which `LESSON_ID_RE` / `_LESSON_META_RE` do not match. |

The five newly synced OCR pairs were applied at corpus-build time:

- `ស្ទីចម៉ាត` → `ស្ទិចម៉ាត`
- `ស្អិតម៉ាស` → `ស្ទិចម៉ាត`
- `បន្សុំ` → `បន្ស៊ាំ`
- `លក្ខណៈ បន្សំ` → `លក្ខណៈបន្សាំ`
- `ជំងឺហមារីក` → `ជំងឺមហារីក`

Post-rebuild canonical counts: `ស្ទិចម៉ាត` 14 pages/15 chunks, `បន្ស៊ាំ` 9/13,
`បន្សំ` 7/9, `មហារីក` 4/5.

### VI.3 Vector DB rebuild and page-range fix

- Collection `biology`: **609 chunks**.
- `build_vector_db.py` now writes `page`, `page_start`, and `page_end`.
- Existing collection metadata was updated in place; no re-embedding was needed.
- Verified chunk `p164_008`: page 164, page_start 164, page_end 165.
- The page-range fix changed evaluation correctly:
  - q24 now passes because retrieved chunks `p164_007`/`p164_008` span p165.
  - q115.1 now passes for the same reason.
  - q115.0 still fails; q115 remains a strict failure.
  - q111 retrieval now passes in the full v3 run.

### VI.4 Gold-label audit and corrections

The full v3 run exposed five additional errors. These were corrected only after
checking the source pages:

| question | old pages | new pages | evidence |
|---|---|---|---|
| q53 | 196, 197, 209 | **6, 12** | p6: gymnosperm seeds are naked/no protective coat; p12: angiosperm seeds are protected by fruit/shell. Old pages are unrelated chapters 6–7. |
| q62 | 60 | **65, 70** | p65: nerve fibres carry electrical signals; p70: synaptic neurotransmitter transmission. p60 is the lesson overview. |
| q69 | 165 | **153, 154, 156** | p153: nucleotide components; p154: four nucleotide types; p156: DNA base pairing. p165 is the ARN lesson. |
| q83 | 246 | **247** | p247 explicitly defines `ខ្សែអាហារ`; p246 is lesson objectives. |
| q89 | 246, 247, 248, 256 | **77** | p77 is the chapter 3 nervous-system summary; old pages are chapter 8 food-chain/energy pages. |

Earlier v3 corrections retained: q23 → 157/158/159, q109 → 15/16/17,
q119 → 122/126/127.

q68 was **not** re-labelled: p149 is the chapter introduction that frames the
question, but p150 is the ADN lesson page; retrieval returns p149 and misses
p150. It remains a genuine near-miss.

The five corrected rows (q53, q62, q69, q83, q89) were refreshed with:

```powershell
$env:PYTHONPATH="D:\Khmer Biology AI Tutor"
.\.venv\Scripts\python.exe -X utf8 scripts\evaluate_retrieval_v2.py --tag v3 --ids 53,62,69,83,89
```

### VI.5 Full v3 retrieval results

Full set: **125 rows**, 116 in-scope rows, 9 out-of-scope rows, 110 in-scope
questions.

| metric | embed | rerank | real pipeline |
|---|---:|---:|---:|
| Recall@1 | 0.560 | 0.629 | **0.629** |
| Recall@3 | 0.845 | 0.853 | **0.853** |
| Recall@5 | 0.922 | 0.957 | **0.957** |
| MRR | 0.715 | 0.756 | **0.756** |

Per-question (multi-part strict): strict hit@5 **0.955**, any-part hit@5
**0.964**.

| abstention check | result |
|---|---:|
| Out-of-scope abstained | **9/9 = 1.000** |
| In-scope false abstain | **2/116 = 0.017** |

`real` equals `rerank` because `rerank_with_context` neighbour expansion is
still a no-op with the current defaults.

#### By chapter (real pipeline)

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

#### By question type (real pipeline)

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

### VI.6 v2 sample baseline and same-question comparison

The v2 sample file has 69 saved rows, but only 62 IDs are in
`meta.selected_ids`; q6/q7 are two stray rows outside that selection. The
same-ID v2 baseline is therefore 67 rows / 58 in-scope, not 69/60. v3 adds one
q115 sub-question, giving 68 rows / 59 in-scope for the same IDs.

| subset | rows / in-scope | real R@1 | real R@3 | real R@5 | MRR | strict hit@5 |
|---|---:|---:|---:|---:|---:|---:|
| v2, selected IDs | 67 / 58 | 0.672 | 0.862 | 0.897 | 0.778 | 0.887 |
| v3, same IDs | 68 / 59 | 0.712 | 0.932 | **0.983** | **0.828** | **0.981** |
| v2, excluding q115 | 66 / 57 | 0.684 | 0.877 | 0.912 | 0.791 | 0.904 |
| v3, excluding q115 | 66 / 57 | 0.719 | 0.947 | **1.000** | **0.837** | **1.000** |

On the same questions, v3 improves Recall@5 by about 8.6 points and MRR by about
5 points. Excluding q115, v3 reaches Recall@5 1.000 on this subset.

The v2 report’s 0.900/0.761 figures were computed over all 69 saved rows,
including q6/q7; they are not a strict same-ID baseline.

### VI.7 Remaining v3 failures and false abstentions

Five in-scope rows still miss Recall@5:

| question | chapter | expected pages | top 5 retrieved | top score | note |
|---|---:|---|---|---:|---|
| q55.0 | 1 | 9 | 15, 15, 23, 17, 226 | 0.1722 | Pine pollen process on p9; diagram-heavy page missed. |
| q56.0 | 1 | 12, 18 | 5, 20, 255, 21, 31 | 0.0319 | Rice-grain reasoning; `អង្ករ` absent from corpus. Also false abstain. |
| q68.0 | 5 | 150 | 149, 160, 180, 160, 162 | 0.7929 | p149 is chapter intro; p150 ADN lesson is absent from top 5. |
| q84.0 | 5 | 150, 165 | 174, 174, 190, 161, 160 | 0.8925 | Quiz-generation prompt; p174 summary retrieved, p165 ARN absent. |
| q115.0 | 5 | 150, 165 | 163, 159, 160, 152, 156 | 0.8054 | ADN sub-question; p150 around rank 6. q115.1 passes, but q115 is strict failure. |

Two in-scope false abstentions remain:

- q56.0: top score 0.0319, below 0.08; also an R@5 miss.
- q78.0: top score 0.0248; hit@5 is true, but the threshold rejects it. Query
  uses `ហ្សែន` while the corpus uses `សែន`; no alias exists yet. Expected pages
  are also broad (150/155/160/165/175) while the actual gene definition is on
  p174. This needs terminology + label work, not a threshold change.

### VI.8 Answer quality and blockers

No answer v3 evaluation was run. The answer baseline remains the v2 20-question
run:

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

- q1 remains blocked: full assembled context triggers Gemini
  `PROHIBITED_CONTENT`; individual chunks pass. Primary 3.6/3.5 returned 429.
  All models empty → `[GEN_FAILED: All Gemini models exhausted quota or unavailable.]`.
- q111 retrieval now passes, but its answer was not re-generated; the v2 answer
  score (~3.43) is still the last answer-level evidence.
- q115’s v2 citation was weak (pp. 164/170/174 instead of 150/165). Chroma now
  has page ranges and `format_answer` can render `page-page_end`, but the
  context label in `app/main.py` still uses only the primary `page`, and the
  citation dedupe keys on `page`; a chunk spanning 164–165 may therefore still
  be cited as p164.
- **84/609 chunks have no `lesson_id`, and `_answer` filters them out**
  (`app/main.py`: `if m.get("lesson_id")`). The 84 chunks span 29 pages,
  including genuine content pages (ch2 pp39–58, ch4 pp137–148, ch6 p215).
  Their headers contain Thai `น` in `មេរៀน`, which the parser’s lesson regex
  does not match. Fixing this requires a parser change plus corpus/vector DB
  rebuild and re-evaluation; it is not a retrieval-parameter change.
- `rerank_with_context` is still a no-op (`selected = indexed[:12]` equals
  `max_total=12`).
- Broader OCR parity remains open: 347 OCR fixes vs 325 query fixes; only the
  five latest stale-form pairs were synced.
- No retrieval parameters, prompts, chunk size, model pool, or the 0.08
  threshold were changed.

### VI.9 v3 artifacts and reproduction

Artifacts:

- `docs/system_accuracy_evaluation_v3.md`
- `data/evaluation/gold_questions_v2.json`
- `data/evaluation/gold_label_changes_v3.json`
- `data/evaluation/corpus_validation_v3.json`
- `data/evaluation/retrieval_smoke_v3.json`
- `data/evaluation/retrieval_v3_results.json`
- `data/evaluation/retrieval_v3_summary.txt`
- `data/processed/biology_cleaned.json`
- `data/processed/biology_structured.json`
- `data/processed/biology_chunks.json`

Reproduce the v3 evaluation:

```powershell
$env:PYTHONIOENCODING="utf-8"
$env:PYTHONPATH="D:\Khmer Biology AI Tutor"

.\.venv\Scripts\python.exe -X utf8 scripts\build_gold_v2.py
.\.venv\Scripts\python.exe -X utf8 scripts\validate_corpus_v3.py
.\.venv\Scripts\python.exe -X utf8 scripts\smoke_retrieval_v3.py
.\.venv\Scripts\python.exe -X utf8 scripts\evaluate_retrieval_v2.py --tag v3 --fresh
.\.venv\Scripts\python.exe -X utf8 scripts\test_eval_harness.py
```

To refresh only rows whose labels changed:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts\evaluate_retrieval_v2.py --tag v3 --ids 53,62,69,83,89
```

## VII. Current Status and Next Actions

Completed in v3: corpus rebuild, OCR sync, 609-chunk validation, vector DB page
ranges, full 119-question retrieval evaluation, eight gold-label corrections,
q24/q111 retrieval fixes, and the v3 report.

Remaining work, in priority order:

1. Decide whether to run an answer evaluation v3; if yes, first decide the q1
   `PROHIBITED_CONTENT` fallback (fewer chunks or a friendly blocked response).
2. Investigate q78’s `ហ្សែន`/`សែន` normalisation with corrected gene labels
   (p174), rather than changing the 0.08 threshold.
3. Review q84/q115 multi-part/quiz labels; q115 currently shares one gold page
   set for both sub-questions.
4. Decide whether to fix the 84 no-`lesson_id` chunks: `_answer` filters them,
   and their headers use Thai `น` in `មេរៀน`; a parser fix requires a corpus +
   vector DB rebuild and re-evaluation. Also decide whether to use page ranges
   in the context label/citation dedupe, not just the primary `page`.
5. Clean temporary diagnostics: `_inspect_pages.txt`, `_full_pages.txt`,
   `_stale.txt`, `scripts\_inspect.py`, and
   `data/evaluation/retrieval_v3_run.err.log`.
6. Broader OCR list parity and the `rerank_with_context` no-op remain open and
   require before/after evidence before changing.

> **Superseded:** §VIII records the v3.1 work. The v3 status above is kept for
> history; current retrieval and answer results are in §VIII.

---

## VIII. v3.1 Parser Fix and Retrieval Completion (2026-10-25)

The v3.1 pass started from a corpus-parser defect, not from a retrieval
parameter change. It fixed that defect, corrected five gold labels only after
page-level evidence review, added three query-level fixes, and made the
generation fallback safe. The detailed report is
`docs/system_accuracy_evaluation_v3_1.md`; the per-failure evidence is
`docs/failure_analysis_v3_1.md`.

### VIII.1 Root cause: Thai `ន` in `មេរៀន` headers

Some running headers use Thai `ន` (`U+0E19`) instead of Khmer `ន` (`U+1793`)
in `មេរៀន`. The old lesson regex accepted only the Khmer character, so 84 of
609 chunks had no `lesson_id`. `app/main.py::_answer()` filters out chunks
without a `lesson_id`, so legitimate lesson content was silently removed from
the generation context.

`scripts/parse_lessons.py` now uses:

```python
_LESSON_WORD = r"មេរៀ[\u1793\u0e19]"
```

and a `CHAPTER_OPEN_RE` guard so a chapter opening such as
`ជំពូក 5 ព័ត៌មានសេនេទិច...` is not mistaken for a lesson header. Regression
tests cover the Thai header, the Khmer header, and the chapter opening.

The corpus was rebuilt from the 257 cleaned pages:

| stage | v3 | v3.1 |
|---|---:|---:|
| Chunks | 609 | **567** |
| Chunks without `lesson_id` | 84 across 29 pages | **25 across 12 pages** |
| Chapter distribution | `{1:49, 2:102, 3:135, 4:70, 5:106, 6:77, 7:40, 8:30}` | `{1:49, 2:75, 3:135, 4:56, 5:106, 6:76, 7:40, 8:30}` |

Every remaining no-`lesson_id` chunk was inspected and is front matter or a
chapter introduction, not lesson content. The pre-fix corpus is archived at
`data/processed/archive_v3/`. The active Chroma collection was rebuilt from
the 567-chunk corpus; embeddings, reranker, chunk size/overlap, `TOP_K`,
`RERANKER_TOP_K`, the 0.08 threshold, prompts, and the model pool were not
changed.

### VIII.2 Validation

| check | result |
|---|---|
| `scripts/validate_corpus_v3.py` | **PASS** — 257 pages, 8 chapters, 567 chunks, all pages covered, unique IDs, page ranges correct |
| `scripts/smoke_retrieval_v3.py` | **PASS** |
| Stale OCR forms | 0; legitimate `បន្សំ` preserved |
| `p164_008` metadata | page 164, range 164–165 |

### VIII.3 Gold corrections (five, all evidence-backed)

The v3.1 run exposed labels that pointed at lesson openers or omitted the
page that actually answers the question. Each change was made only after
reading the source page; the quotes and reasons are in
`data/evaluation/gold_label_changes_v3_1.json`, and the changes are
reproducible with `scripts/update_gold_v3_1.py`.

| id | old pages | new pages | evidence |
|---|---|---|---|
| q68 | 150 | **149, 150** | p149 states that parents transmit inherited traits to offspring; p150 is only the ADN lesson opener. |
| q78 | 150, 155, 160, 165, 175 | **174** | p174 gives the exact gene definition; p175 only asks it as an exercise; the others cover ADN/ARN. |
| q84 | 150, 165 | **150, 160, 165** | p160 is the ADN lesson summary needed for an ADN/ARN quiz; p165 lists the ARN types. |
| q86 | 26 | **26, 27, 40** | p26 lists objectives; p27 teaches root-hair absorption; p40 restates it in the summary. |
| q115 | 150, 165 (shared) | **[[150,160], [164,165]]** | Part 0 is ADN (p150/p160); part 1 is ARN types (p164/p165). |

For q115, `scripts/eval_common.py` gained
`expected_pages_for_part()` and `expected_pages_for_question()`, wired into
both the retrieval and answer evaluators. Questions without per-part gold
keep the shared list.

### VIII.4 Query-level fixes

| id | fix | why |
|---|---|---|
| q55 | topic expansion `ស្រល់ → ស៊ីមណូស្ពែម កោន` | The corpus calls pine a gymnosperm and its reproductive structure a cone; the student's word alone was outranked by flowering-plant pages. |
| q56 | topic expansion `អង្ករសំរូប → គ្រាប់ស្រូវ អាល់ប៊ុយមែន អង់ដូស្ពែម` | `អង្ករ`/`សំរូប` do not occur in the corpus; the textbook terms for the rice grain, albumen, and endosperm do. |
| q78 | alias `ហ្សែន → សែន` | Exam papers use `ហ្សែន`; the definition page and most of the textbook use `សែន`. |

The q55 expansion also affects q3 and q52. Both were rerun: q3 improved from
p9 rank 2 to rank 1, and q52 stayed at p6 rank 1. The q56 expansion affects
only q56; the q78 alias affects only q78.

### VIII.5 Final retrieval results

Full set: 125 rows, 116 in-scope rows, 9 out-of-scope rows, 110 in-scope
questions.

| metric | v3 | v3.1 pre-fix | v3.1 post-fix |
|---|---:|---:|---:|
| Recall@1 | 0.629 | 0.638 | **0.655** |
| Recall@3 | 0.853 | 0.853 | **0.888** |
| Recall@5 | 0.957 | 0.948 | **1.000** |
| MRR | 0.756 | 0.760 | **0.785** |
| Strict hit@5 | 0.955 | 0.945 | **1.000** |
| Any-part hit@5 | 0.964 | 0.955 | **1.000** |
| In-scope false abstain | 2/116 | 2/116 | **0/116** |
| Out-of-scope abstention | 9/9 | 9/9 | **9/9** |

All eight chapters now have Recall@5 = 1.000 and zero false abstentions.
Chapter 5 improved most in MRR (0.635 → 0.717), with the largest label-related
gains from q78, q84, and q115; chapter 1 rose from 0.796 to 0.840 as q3 moved
to rank 1 and q56 stopped abstaining.

The six pre-fix R@5 failures (q55, q56, q68, q84, q86, q115), the q78 false
abstain, and the q1 generation failure are analyzed one by one in
`docs/failure_analysis_v3_1.md`. q86 is the one new v3.1 regression: the
parser changed the chunk boundaries, the old `[26]` label pointed at a lesson
opener that fell to rank 7, and the label was corrected to `[26,27,40]`. The
regression is disclosed in the report rather than hidden by the rebuild.

### VIII.6 Generation fallback (q1)

q1 (`តើស៊ីមណូស្ពែមជាអ្វី?`) retrieved p6 correctly, but the assembled context
also contained p8–p10 reproductive terms that made Gemini return
`PROHIBITED_CONTENT`; the old top-3 retry still included them and ended in
`[GEN_FAILED: ...]`.

`app/rag.py::_generate_google()` now retries blocked or empty candidates with
progressively smaller contexts: full → top 3 → top 1. If all fail, it returns
`GENERATION_FALLBACK_MESSAGE`, a friendly Khmer message. The normal path and
the 429/503 model rotation are unchanged. `scripts/test_rag_fallback.py`
covers the paths with 26 checks; q1 now answers from p6 with overall 4.86 and
no fallback.

### VIII.7 Answer evaluation

A 45-question stratified sample was run: 41 in-scope + 4 out-of-scope, all
eight content chapters, all question types, and every fixed retrieval case
(q1, q3, q52, q55, q56, q68, q78, q84, q86, q115).

Outputs:

- `data/evaluation/answer_evaluations_v3.json`
- `data/evaluation/answer_evaluation_v3_summary.txt`
- `data/evaluation/answer_review_v3.csv` (blank `teacher_*` columns and
  `teacher_notes` for manual grading)

<!-- V31_ANSWER_METRICS -->

The seven rubric dimensions are automated proxies, not a substitute for
teacher review.

### VIII.8 Tests

| test | result |
|---|---|
| `python scripts/test_eval_harness.py` | **PASS** (parser, splitter, query expansion, per-part gold, scoring, fallback scoring) |
| `python scripts/test_rag_fallback.py` | **PASS** (26/26) |
| `python scripts/validate_corpus_v3.py` | **PASS** |
| `python scripts/smoke_retrieval_v3.py` | **PASS** |

No test failures were left unresolved.

### VIII.9 Residual limitations

- q55, q84, and q86 pass R@5 but not R@3; the correct page is rank 4–5.
- q78 passes R@3 but not R@1; the lesson opener p162 outranks the definition
  page p174.
- q68's gold p149 is a chapter opener without `lesson_id`; the app's context
  filter drops it. Retrieval is correct, but the generator may not see the
  exact sentence. Changing the filter risks adding front-matter noise to
  other questions, so it is documented rather than changed.
- q56's expansion depends on the textbook's `អាល់ប៊ុយមែន`/`អង់ដូស្ពែម`
  vocabulary; a future corpus revision must update it.
- The answer rubric is automated; teacher review is still required before
  making claims about pedagogical quality.
- Broader OCR-list parity (347 OCR entries vs 325 query entries) and the
  `rerank_with_context` no-op remain open and need before/after evidence.

### VIII.10 v3.1 artifacts

| file | purpose |
|---|---|
| `docs/system_accuracy_evaluation_v3_1.md` | final v3.1 report |
| `docs/failure_analysis_v3_1.md` | per-failure evidence and fixes |
| `data/evaluation/retrieval_v3_1_results.json` | post-fix rows and aggregate |
| `data/evaluation/retrieval_v3_1_summary.txt` | post-fix summary |
| `data/evaluation/archive_v3_1_prefix/` | pre-fix v3.1 baseline |
| `data/evaluation/gold_label_changes_v3_1.json` | five gold changes with evidence |
| `data/evaluation/v31_evidence_dump.txt` | page/chunk evidence for the failures |
| `data/evaluation/q56_variant_experiment*.txt` | q56 vocabulary-bridge tests |
| `data/evaluation/query_variant_experiment.txt` | q55/q56/q68 query-variant tests |
| `scripts/update_gold_v3_1.py` | reproducible gold corrections |
| `scripts/test_eval_harness.py` | parser/query/gold/scoring tests |
| `scripts/test_rag_fallback.py` | generation fallback tests |

Reproduce the v3.1 retrieval result:

```powershell
$env:PYTHONIOENCODING="utf-8"
$env:PYTHONPATH="D:\Khmer Biology AI Tutor"

.\.venv\Scripts\python.exe -X utf8 scripts\parse_lessons.py
.\.venv\Scripts\python.exe -X utf8 scripts\chunk_text.py
.\.venv\Scripts\python.exe -X utf8 scripts\build_vector_db.py
.\.venv\Scripts\python.exe -X utf8 scripts\validate_corpus_v3.py
.\.venv\Scripts\python.exe -X utf8 scripts\smoke_retrieval_v3.py
.\.venv\Scripts\python.exe -X utf8 scripts\evaluate_retrieval_v2.py --tag v3_1 --fresh
.\.venv\Scripts\python.exe -X utf8 scripts\evaluate_retrieval_v2.py --tag v3_1 --ids 3,52,55,56,68,78,84,86,115
```