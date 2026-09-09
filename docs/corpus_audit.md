# Corpus Audit Report (2026-09-09)

## Summary: PASS

The final corpus is complete, clean, and internally consistent.

## 1. Page Completeness

| Check | Result |
|---|---|
| Total pages in raw extraction | 257 / 257 |
| Missing pages | 0 |
| Duplicate page records | 0 |
| Empty-text pages | 0 |
| Pages with <20 chars | 0 |
| Cleaned records | 257 (unique, pages 0-256) |

## 2. Chapter / Lesson Detection

- **8 chapters** detected across the full textbook.
- Chapter distribution (pages):
  - Ch1: 23 (2 TOC/unauthored + lesson1: 8 + lesson2: 13)
  - Ch2: 36 (lesson1: 15 + lesson2: 21)
  - Ch3: 62 (lesson1: 20 + lesson2: 21 + lesson3: 21)
  - Ch4: 30 (lesson1: 6 + lesson2: 10 + lesson3: 14)
  - Ch5: 50 (lesson1: 14 + lesson2: 16 + lesson3: 20)
  - Ch6: 30 (lesson1: 12 + lesson2: 6 + lesson3: 12)
  - Ch7: 16 (lesson1: 6 + lesson2: 9 + lesson3: 1)
  - Ch8: 6 (lesson1: 2 + lesson2: 4)
- Pages 0-3 (cover, copyright, committee, preface) have no chapter/lesson, as expected.

**Note:** Some pages 211, 229-230, 247-248, 251-252, 253-254 are question-bank/review pages that reference an earlier chapter in their header (e.g., "សំណួរនិងលំហាត់ជំពូកទី 2"). They are tagged to the chapter they reference, which is actually correct for retrieval.

**Known minor issue (not blocking):** Chapter titles captured by `parse_lessons.py` are often verbose/garbled (they include trailing question or diagram-caption text) rather than a clean short chapter name. This affects the `chapter_title` metadata display in citations but does not affect retrieval quality (retrieval uses chunk text embeddings, not titles).

## 3. Chunk Validity

| Check | Result |
|---|---|
| Total chunks | 1093 |
| Unique chunk_ids | 1093 (no duplicates) |
| Empty-text chunks | 0 |
| Chunks with page metadata | 1093 (all) |
| Chunks with chapter metadata | 1086 (7 TOC chunks lack chapter) |
| Chunks with lesson metadata | 1082 (11 lack lesson) |
| Distinct pages covered | 257 / 257 |
| Pages with NO chunk | 0 |
| Sizes | min=23, max=3274, avg=342 chars |

Chunk distribution by chapter:
- None/TOC: 7
- Ch1: 89, Ch2: 159, Ch3: 280, Ch4: 118, Ch5: 214, Ch6: 127, Ch7: 73, Ch8: 26

## 4. Vector Database

- Chroma collection "biology" rebuilt with **1093 chunks** (up from 834).
- BGE-M3 embeddings, cosine space.
- Retrieval re-validated on 5 Khmer test queries — all return relevant results.

## Conclusion

The corpus is ready for evaluation. The only cosmetic issue is verbose chapter titles; this is noted and can be refined later without rebuilding the vector DB.
