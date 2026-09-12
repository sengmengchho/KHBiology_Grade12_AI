# Khmer Biology AI Tutor — Work Log

## What I Have Done

### 1. Applied All OCR Corrections from Evaluation Feedback
**Files updated:**
- `scripts/clean_text.py` — `OCR_FIXES` list (+80 entries)
- `app/utils.py` — `QUERY_FIXES` list (+80 entries)

**Key corrections added:**
- **Reflex arc / neuron types**: `វិញ្ញាណទទួល→ធ្មួលវិញ្ញាណ`, `ផ្ដួល→ធ្មួល`, `ណឺរ៉ូនតភ្ជាប់→ណឺរ៉ូនភ្ជាប់`
- **Reflex arc pathway**: `ធួលត្រចៀក→ធ្មួលត្រចៀក`, `សូរសម្លេង→សូរសំឡេង`, `តាមបណ្ដោយ→តាមបណ្តោយ`
- **Hormone types**: Peptide (`ប៉ិបទីត`) vs Steroid (`ស្តេរ៉ូអ៊ីត`)
- **Adrenal gland**: Cortex (`ករតិចអាដ្រិណាល់`), Medulla (`មេឌុយឡា`)
- **Natural selection**, **Cornea/eye**, **Pollination**, **Leaf anatomy**, **Monocot/Dicot**, **Enzyme temperature**, **Protein synthesis**, **Griffith experiment**, **Dicot root**, **DNA/RNA**

### 2. Fixed Quiz Feature — Collapsible Answers
**Problem**: Model used `<details>` HTML tags which Streamlit doesn't render; answers were visible immediately.

**Solution:**
- Updated `app/prompt.py` quiz instruction to generate structured markdown:
  ```
  **សំណួរទី X: [Question]**
  **ចម្លើយ:** [Answer with explanation]
  ```
- Added `_render_quiz_answer()` in `app/main.py` that parses this format and renders each question as a **Streamlit `st.expander`** — answers hidden until clicked.

### 3. Comparison Question Format Enforcement
**File:** `app/prompt.py`
- Added explicit instruction: "CRITICAL FOR COMPARISON QUESTIONS... MUST structure answer with TWO clear sections: 'លក្ខណៈដូចគ្នា' AND 'លក្ខណៈខុសគ្នា'. Both sections must be present with bullet points."

### 4. Verification
- All Python files pass syntax check (`python -m py_compile`)

---

## What I Will Do Next

1. **Test the quiz feature end-to-end** — Run the Streamlit app and verify expanders work correctly
2. **Validate comparison question outputs** — Ensure both similarity/difference sections appear
3. **Run retrieval quality tests** — Check that new OCR fixes improve chunk retrieval for garbled queries
4. **Optional: Add more OCR fixes** if evaluation reveals additional gaps
5. **Optional: Fine-tune prompt for exam mode** — Make bullet points more concise/memorizable