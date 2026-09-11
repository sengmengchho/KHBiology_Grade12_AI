# KhmerBio Tutor — Training Progress Log

## Summary
Grounded RAG system for Grade 12 Khmer Biology. Retrieval pipeline: normalize/expand query → embedding retrieve (top-30) → rerank (top-8, BGE-reranker-v2-m3) → threshold (0.08) → generate (Gemini) → format citations. Corpus: 610 chunks from Grade 12 textbook (Chapters 1–8), embedded with BGE-M3.

---

## Completed Training Batches (8 rounds, 40 questions)

| Batch | Questions | Topics Covered | Key Fixes |
|-------|-----------|----------------|-----------|
| **1** | 5 | Double fertilization, Cerebrum, Iodine/Goiter, Dicots, Griffith | Initial OCR term normalization (`QUERY_FIXES`, `normalize_query`) |
| **2** | 4 | ADN info carrier, Retina, Polyploidy, Flower/Angiosperm | Definition query expansion (`_expand_definition`) |
| **3** | 5 (re-train) | Same as Batch 1 + fixes | Stigma residue removal, citation dedup, spermatozoid spelling (ស្ពែម៉ាតូសូអ៊ុត) |
| **4** | 6 | Nerve impulse, Amino acids, ADN replication, ARN polymerase, Ear balance, Fossils | R-group variants (រ៉ូម៉ាគាល់) |
| **5** | 4 | Parathyroid, Pancreas, Stomach, Nervous systems | Image 2 OCR fixes (insulin/glucagon/cephalization) |
| **6** | 5 | Leaf tissue, Amino acid/dipeptide, Monocot/Dicot, Enzyme temp, Translation stop | Image artifacts, temperature spacing, stop codons |
| **7** | 4 | Parathyroid, Pancreas, Sweat gland, Nervous systems | Image 2 OCR fixes (ត្រពេញ→ក្រពេញ, អូមូន→អរម៉ូន, etc.) |
| **8** | 6 | Pollination, Neurons, Cornea, Hormone comparison, Adrenal, Natural selection | Image 3 OCR fixes + improved question splitting (I–VI) |

**Total:** 8 batches, 40 questions, all retrieval scores >0.08, 610 chunks, 610 re-embeddings per round.

---

## Key Technical Achievements

### OCR Error Correction (30+ mappings)
- `ត្រពេញ` → `ក្រពេញ` (gland)
- `អូមូន` → `អរម៉ូន` (hormone)
- `ផ្វូស្បាត` → `ផូស្វាត` (phosphate)
- `ស្វីកុដជាតិ` → `ស្លឹករុក្ខជាតិ` (plant leaves)
- `រ៉ូម៉ាគាល់់` → `រ៉ាឌីកាល់` (R-group)
- `ឌីប៉ុបទីត` → `ឌីប៉ិបទីត` (dipeptide)
- `កូដុងឈប់` → `កូដុងស្តុប` (stop codon)
- `សត្វកត់ផ្ដៀងកង` / `កណ្តុរ` → `សត្វឥតឆ្អឹងកង` (invertebrate)
- `ម៉ូលេគុល` → `ម៉ូណូកូទីលេដូន` (monocot)
- `ឌីគូម៉ូលេគុល` → `ឌីកូទីលេដូន` (dicot)
- `ស្ពែម៉ាតូសូអ៊ីត` → `ស្ពែម៉ាតូសូអ៊ុត` (spermatozoid)

### Query Processing Improvements
- **Definition rewriting**: `ចូរឱ្យនិយមន័យ X` → `តើXជាអ្វី?` (clean noun phrases only)
- **Cerebrum rule**: `ខួរឆ្អឹង` → `ខួរធំ` (unless followed by `ខ្នង`)
- **Follow-up merge**: `វាមាននាទីអ្វី?` merges with parent question
- **Roman numeral splitting**: Clean I–VI separation with sub-question merge

### Citation Quality
- Dedup by page only (collapses page-range overlaps)
- Primary-lesson filtering (drops cross-chapter noise)
- Cap at 6 source lines

### Prompt Rules
- Canonical terminology enforcement (NEVER-list for garbled OCR forms)
- No parenthetical double-spelling (e.g., `ស្ទិចម៉ាត (ស្អិតម៉ាស)`)
- Spermatozoid canonical: `ស្ពែម៉ាតូសូអ៊ុត` (matches textbook fig. p18/19 + official key)

---

## Files Modified

| File | Purpose |
|------|---------|
| `app/utils.py` | `QUERY_FIXES` (30+ entries), `normalize_query()`, `expand_query()` |
| `app/main.py` | `_answer()`, `_answer_multi()`, `_process_question()`, `_split_questions()` — term expansion + multi-question splitting |
| `app/prompt.py` | System prompt (canonical terms, NEVER-list, no-parenthetical rule), `format_answer()` dedup + primary-lesson filter |
| `app/ocr.py` | Uses shared `normalize_query()` |
| `scripts/clean_text.py` | `OCR_FIXES` (30+ mappings across all batches) |

---

## Next Steps

1. **Expand evaluation set** — Run automated evaluation on 30+ questions (Ch1–8) using `scripts/evaluate_answers.py`; track concept coverage & page recall.
2. **Add remaining term gaps** — Scan retrieval failures for missing normalizations (specific hormone names, enzyme names, plant tissue terms).
3. **Hardening** — Add regression tests for critical term normalizations; CI for pipeline regen.
4. **Optional UX** — Streamlit chat history export; quiz mode scoring.

---

## Commands for Re-running Pipeline

```powershell
# Full corpus regeneration (after clean_text.py OCR_FIXES changes)
$env:PYTHONIOENCODING='utf-8'
python scripts/clean_text.py
python scripts/parse_lessons.py
python scripts/chunk_text.py
python scripts/build_vector_db.py   # ~6 min on CPU (610 chunks)

# Retrieval smoke test
python scripts/test_retrieval.py

# Full evaluation (uses GOOGLE_API_KEY)
python scripts/evaluate_answers.py --sample 20
```