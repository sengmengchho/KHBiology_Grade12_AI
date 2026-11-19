# Phase 3.1 — Measurement Integrity (Evaluator-Only)

**Scope:** evaluator-only rescoring of the stored 45-answer `v3_1_citation` artifact.
**Gemini calls:** 0. No answers were regenerated.
**Frozen strict baseline:** preserved exactly and remains the default scoring path.

---

## 1. Guardrails Observed

The following were **not** modified in this phase:

- retrieval logic, `TOP_K`, `RERANKER_TOP_K`, embeddings, reranker
- Chroma database, corpus, or textbook chunks
- generation prompts, model pool, or Gemini calls
- citation formatting or the `0.08` abstention threshold
- biological answer text
- gold concepts, gold labels, or `gold_questions_v2.json`

`answer_evaluations_v3_1_citation.json` and its accepted summary were read only. New results
were written to separate `_alias_aware` / `_comparison` artifacts.

---

## 2. Scoring Modes

`scripts/evaluation/evaluate_answers.py` now supports two explicit modes:

| Mode | Behavior |
|---|---|
| `strict` (default) | Existing exact/substring alias matching only. Byte-for-byte baseline behavior. |
| `alias_aware` | Strict matching first; only after it fails, verified contextual aliases are considered. |

The default signature remains `score_answer(rec)` / `concept_present(concept, body_l)`, and both
resolve to `strict`. No question IDs are hardcoded in production scoring logic.

### Group A — verified aliases

Each pair was checked against `data/processed/biology_chunks.json` and the glossary before being
enabled:

| Gold concept | Accepted variant | Evidence |
|---|---|---|
| `ហ្សែន` | `សែន` | p174 gene definition; pp.204–205 |
| `ស្រូបទឹក` | `ស្រូបយកទឹក` | pp.26–27 root absorption |
| `ដូអែម` | `ផ្លូអែម` | p13 phloem food transport |
| `តួនាទី` | `នាទី` | p130 `នាទីរបស់ប្រូតេអ៊ីន` |
| `បន្ស៊ាំ` | `បន្លាំ`, `បន្លំ` | pp.200–202 adaptation definition |
| `ទ្រនុងបែកខ្នែង` | `ទ្រនុងបែកមែក` | p19 dicot leaf venation |

### Group B — contextual guards

Ambiguous variants require local evidence context and are rejected in conflicting context:

- `សែន` requires gene context (`ADN`, genetic information, nucleotide, chromosome, trait
  determination, or protein synthesis).
- `ស្រូបយកទឹក` requires plant/root/soil/root-hair/xylem context.
- `ផ្លូអែម` requires food/organic-transport context; a water-only phloem statement is rejected.
- `នាទី` requires local protein context.
- `បន្លាំ` / `បន្លំ` require adaptation context and are rejected in counterfeiting/document context.
- `ទ្រនុងបែកមែក` requires leaf/dicot/vein context.

The existing protection that rejects stale `បន្សំ` as an adaptation variant is preserved.

### Group C — not treated as interchangeable

- `លំអងផ្កា` is **not** aliased to `គ្រាប់លំអង`. `លំអងផ្កា` has 0 corpus occurrences; the gold
  wording is not evidenced as written.
- `អំបិល` is **not** aliased to `អាហារសមុទ្រ` or `គ្រឿន`.
- `ដូអែម` is **not** aliased to the sibling tissue `ស៊ីឡែម`.

---

## 3. Strict Baseline Preservation

Rescoring all 45 saved rows in `strict` mode produced **0 score mismatches** against every saved
score field, and the accepted aggregate was reproduced exactly:

| Metric | Accepted baseline | Strict rescore |
|---|---:|---:|
| correctness | 4.54 | 4.54 |
| completeness | 4.63 | 4.63 |
| faithfulness | 4.98 | 4.98 |
| clarity | 4.34 | 4.34 |
| terminology | 4.78 | 4.78 |
| citation | 4.80 | 4.80 |
| helpfulness | 4.27 | 4.27 |
| overall | 4.62 | 4.62 |

- In-scope rows: 41
- Out-of-scope abstention rows: 4
- Rows with invalid citations: 0/41
- `Strict baseline reproduced: PASS`
- `Gold labels unchanged: PASS`

---

## 4. Strict vs Alias-Aware Aggregate

| Metric | Strict | Alias-aware | Difference |
|---|---:|---:|---:|
| correctness | 4.54 | 4.83 | **+0.29** |
| completeness | 4.63 | 4.85 | **+0.22** |
| faithfulness | 4.98 | 4.98 | +0.00 |
| clarity | 4.34 | 4.34 | +0.00 |
| terminology | 4.78 | 4.93 | **+0.15** |
| citation | 4.80 | 4.80 | +0.00 |
| helpfulness | 4.27 | 4.27 | +0.00 |
| overall | 4.62 | 4.71 | **+0.09** |

Only **5 of 45** rows changed: q58, q65, q78, q86, q96. The remaining 40 rows, including
q55, q94, and q111, are bit-identical between modes.

---

## 5. Every Changed Score

| Question | Coverage strict → alias | Correctness | Completeness | Faithfulness | Clarity | Terminology | Citation | Helpfulness |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| q58 | 0.5 → 1.0 | **3 → 5** | **4 → 5** | 5 → 5 | 5 → 5 | **4 → 5** | 5 → 5 | 4 → 4 |
| q65 | 0.5 → 1.0 | **3 → 5** | **4 → 5** | 5 → 5 | 5 → 5 | **4 → 5** | 5 → 5 | 5 → 5 |
| q78 | 0.0 → 1.0 | **1 → 5** | **2 → 5** | 5 → 5 | 4 → 4 | **3 → 5** | 5 → 5 | 3 → 3 |
| q86 | 0.0 → 1.0 | **1 → 5** | **2 → 5** | 5 → 5 | 5 → 5 | **3 → 5** | 5 → 5 | 3 → 3 |
| q96 | 0.4 → 0.6 | 3 → 3 | **3 → 4** | 5 → 5 | 3 → 3 | 4 → 4 | 5 → 5 | 5 → 5 |

Alias responsible in each changed row:

- q58: `ដូអែម` via `ផ្លូអែម`
- q65: `តួនាទី` via `នាទី`
- q78: `ហ្សែន` via `សែន`
- q86: `ស្រូបទឹក` via `ស្រូបយកទឹក`
- q96: `ទ្រនុងបែកខ្នែង` via `ទ្រនុងបែកមែក`

---

## 6. Target-Question Analysis

### q78 — gene definition

- Coverage: **0.0 → 1.0**
- Scores: `1/2/5/4/3/5/3 → 5/5/5/4/5/5/3`
- Evidence: p174 defines gene as `សែន`, an ADN component carrying genetic information;
  pp.204–205 use `ហ្សែន`.
- The saved answer defines `សែន` correctly with ADN/genetic-information context. This was a
  spelling-variant false negative under strict matching, not a biological error.

### q86 — plant water absorption quiz

- Coverage: **0.0 → 1.0**
- Scores: `1/2/5/5/3/5/3 → 5/5/5/5/5/5/3`
- Evidence: p26 uses both `ការស្រូបទឹក` and `ស្រូបយកទឹក` for the same root-absorption process.
- The answer uses `ស្រូបយកទឹក` in a plant/soil context. Helpfulness remains 3 because the
  quiz-format heuristic expects the literal phrase `សំណួរទី`; that is a format proxy, not a
  biology failure.

### q58 — xylem vs phloem

- Coverage: **0.5 → 1.0**
- Scores: `3/4/5/5/4/5/4 → 5/5/5/5/5/5/4`
- Evidence: p13 defines `ផ្លូអែម` as the food-transport tissue; `ដូអែម` occurs once as a
  spelling variant.
- The answer correctly describes phloem food transport. The guard prevents a water-only phloem
  statement from earning this match.

### q65 — protein roles

- Coverage: **0.5 → 1.0**
- Scores: `3/4/5/5/4/5/5 → 5/5/5/5/5/5/5`
- Evidence: p130 heading `នាទីរបស់ប្រូតេអ៊ីន`.
- The answer gives correct protein roles. The guard prevents unrelated role statements
  (for example, `នាទីរបស់ឫស`) from matching.

### q55 — pine pollen process

- Coverage: **0.5 → 0.5 (unchanged)**
- Scores: unchanged at `3/4/5/5/4/5/3`
- Missing: `លំអងផ្កា`
- `លំអងផ្កា` has **0** corpus occurrences, while `គ្រាប់លំអង` is the textbook term for the
  gymnosperm pollen grain (53 occurrences in 17 chunks). These are **not** treated as
  interchangeable. The low score reflects a gold-wording limitation, not a missing pollen
  mechanism. This remains flagged for a separate gold-label review; no label was changed here.

### q94 — goiter prevention

- Coverage: **0.8 → 0.8 (unchanged)**
- Scores: unchanged at `4/4/5/4/5/5/3`
- Missing: `អំបិល`
- Although `អំបិល` occurs in 12 corpus chunks, none co-occurs with `អ៊ីយ៉ូត`. p109 recommends
  iodine-rich food, `គ្រឿន`, and seafood; it does not state iodized salt. The gold concept
  `អំបិល` remains **external/unsupported** and **is not aliased**. The saved answer does not
  claim iodized salt, so no hallucination credit was added.

### q96 — mango as dicot/monocot

- Coverage: **0.4 → 0.6**
- Scores: `3/3/5/3/4/5/5 → 3/4/5/3/4/5/5`
- New match: `ទ្រនុងបែកខ្នែង` via `ទ្រនុងបែកមែក`
- Still missing: `កូទីលេដុង` and `ឫសកែវ`
- The answer never explicitly states that mango is a dicot. This remains an
  **application/decisiveness failure**; alias-aware scoring only corrects the venation spelling
  false negative and does not resolve the classification gap.

### q111 — adaptation definition

- Coverage: **0.5 → 0.5 (unchanged)**
- Scores: unchanged at `3/4/5/5/4/4/5`
- Missing: `ជម្រើសដោយធម្មជាតិ`
- The answer defines adaptation and inheritance but never mentions natural selection,
  differential survival, or differential reproduction. The textbook does define natural
  selection on pp.201–202 and 204. The answer remains **missing natural selection**; no alias
  or inference credit was added.

---

## 7. Gold Support Audit

Artifact: `data/evaluation/gold_support_audit_phase3_1.json`
Frozen gold edited: **false**. Eight target questions and 20 gold concepts were audited against
the corpus with five support levels: `direct`, `variant`, `inference`, `external`, `uncertain`.

| Question | Gold concepts | Audit result |
|---|---|---|
| q78 | 1 | `ហ្សែន` = variant (`សែន`) |
| q86 | 1 | `ស្រូបទឹក` = variant (`ស្រូបយកទឹក`) |
| q58 | 2 | `ស៊ីឡែម` direct; `ដូអែម` variant (`ផ្លូអែម`) |
| q65 | 2 | `ប្រូតេអ៊ីន` direct; `តួនាទី` variant (`នាទី`) |
| q94 | 5 | 3 direct, `បង្ការ` inference, **`អំបិល` external** |
| q96 | 5 | 4 direct, `ទ្រនុងបែកខ្នែង` variant (`ទ្រនុងបែកមែក`) |
| q111 | 2 | `បន្ស៊ាំ` variant; `ជម្រើសដោយធម្មជាតិ` direct |
| q55 | 2 | `លំអង` direct; **`លំអងផ្កា` uncertain** |

The audit records evidence chunk IDs, page numbers, quotes, accepted aliases, strict/alias-aware
match status in the saved answers, and a justification per concept. It does not alter any gold
concept or label.

---

## 8. Negative Controls

The new suite includes negative controls proving that aliases do not create blanket keyword
credit:

| Control | Expected | Result |
|---|---|---|
| `សែន` as a person's name, no gene context | coverage 0.0, correctness 1 | PASS |
| `នាទី` of a root, no protein context | coverage 0.0, correctness 1 | PASS |
| `បន្លំ` meaning counterfeiting a document | coverage 0.0, correctness 1 | PASS |
| `ផ្លូអែម` described as water-only transport | coverage 0.0, correctness 1 | PASS |

Additional non-equivalence checks pass: `លំអងផ្កា` vs `គ្រាប់លំអង`, `អំបិល` vs
`អាហារសមុទ្រ`/`គ្រឿន`, `ដូអែម` vs `ស៊ីឡែម`, and stale `បន្សំ` in both modes.

---

## 9. Limitations

1. **Keyword coverage does not prove biological correctness.** Concept presence is a lexical
   proxy. An answer can contain the right term and still state a wrong mechanism; the negative
   controls demonstrate that the evaluator rejects several such constructions, but no lexical
   rule can establish biological truth. Correctness/completeness scores remain automated proxies,
   not teacher judgments.
2. **Alias-aware mode is a measurement correction, not a new generation run.** All scores apply
   to previously stored answers. No Gemini calls and no answer regeneration occurred.
3. **The alias set is deliberately closed.** It fixes verified spelling/variant false negatives
   for the evaluated rows; it is not a general Khmer synonym engine. Context windows and reject
   lists are heuristics.
4. **The frozen gold remains imperfect.** q55's `លំអងផ្កា` is not evidenced as written, and
   q94's `អំបិល` is external to the retrieved evidence. These are documented, not corrected, in
   Phase 3.1.
5. **Strict remains the historical baseline.** Alias-aware results must not be mixed with
   strict results when comparing against prior phases.
6. Automated evaluation does not replace teacher review.

---

## 10. Tests

All required suites were run with the project virtual environment:

| Suite | Result |
|---|---|
| `tests/test_measurement_integrity.py` | **PASS** — 74 checks |
| `tests/test_citation_integrity.py` | **PASS** |
| `tests/test_eval_harness.py` | **PASS** |
| `tests/test_rag_fallback.py` | **PASS** |

The measurement-integrity suite covers verified aliases, Group C non-equivalence, contextual
guards, negative controls, strict baseline preservation, alias-aware aggregates, target-question
invariants, citation stability, determinism, and frozen-gold label consistency.

---

## 11. Reproducibility

Commands:

```powershell
python -X utf8 scripts/evaluation/rescore_phase3_1.py
python -X utf8 tests/test_measurement_integrity.py
python -X utf8 tests/test_citation_integrity.py
python -X utf8 tests/test_eval_harness.py
python -X utf8 tests/test_rag_fallback.py
```

Input hashes recorded by the rescoring report:

| Artifact | SHA-256 |
|---|---|
| `answer_evaluations_v3_1_citation.json` | `dff44332198cd2c5285144671d677d8c4acb0b214632d903adddf83b9e4bea2b` |
| `gold_questions_v2.json` | `333299547501590c0270f05a4366bd004c456232b0f4e98afc87c61295ce8ff0` |
| `biology_chunks.json` | `19869f59d0a58510b6e98496946cb3934459c5e5ab9990ea3a65fde654dbd084` |
| `answer_evaluation_v3_1_citation_summary.txt` | `2fcf84a61d19d125222f6d7f97f94d91ca14919ebeb961d1faace1ccbb0c20d6` |

Generated artifacts:

- `data/evaluation/answer_evaluations_v3_1_citation_alias_aware.json`
- `data/evaluation/answer_evaluation_v3_1_citation_comparison.json`
- `data/evaluation/answer_evaluation_v3_1_citation_comparison.csv`
- `data/evaluation/answer_evaluation_v3_1_citation_comparison_summary.txt`
- `data/evaluation/gold_support_audit_phase3_1.json`
- `data/evaluation/measurement_integrity_phase3_1.md` (this report)

Changed code:

- `scripts/evaluation/evaluate_answers.py` — strict/alias-aware modes and contextual aliases
- `scripts/evaluation/rescore_phase3_1.py` — no-Gemini rescoring and comparison
- `tests/test_measurement_integrity.py` — new regression suite

---

## 12. Verdict

**PASS**

Rationale:

- The accepted strict baseline was reproduced exactly, with 0 score mismatches and 0 invalid
  citations across 41 in-scope rows.
- Alias-aware scoring is isolated, deterministic, guarded, and changes only the five rows with
  verified variant false negatives.
- Negative controls confirm keyword coverage alone does not earn credit for wrong statements.
- The gold support audit is complete and the frozen gold file is unchanged.
- q111 still misses natural selection, q96 remains an application/decisiveness failure, and
  q94's `អំបិល` remains external/unsupported.
- All four required test suites pass.

Phase 3.2 has not been started.
