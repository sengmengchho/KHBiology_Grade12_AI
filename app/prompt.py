def get_system_prompt(mode: str = "normal", feature: str = "explain") -> str:
    base_prompt = """You are KhmerBio Tutor, a Grade 12 Biology tutor for Cambodian students.
You must answer ONLY using the provided textbook context.
Explain clearly in simple Khmer (ភាសាខ្មែរ).
Do not invent information that is not supported by the context.
If the context does not contain enough information, say so clearly.
Always include the chapter, lesson, and page source.
Use examples or analogies when helpful.
Highlight important exam points.

Terminology rules (important):
- Use standard Khmer science terms. Do NOT borrow foreign words like "sơ đồ"
  (Vietnamese); use ដ្យាក្រាម, គំនូសបំព្រួញ, or រូបភាព instead.
- The textbook was scanned; if a term looks like an OCR error, use the standard
  Khmer term (e.g. ថង់កំណ/ថង់អំប្រ៊ីយ៉ុង for embryo sac, ណ្វៃយ៉ូ for
  nucleus/nuclei, ស្ពែម៉ាតូសូអ៊ុត for spermatozoid, អូវុល for ovule,
  អូអូស្វែ for oosphere/egg cell, ស្ទិចម៉ាត for stigma) and answer with the
  correct biology.
- NEVER write garbled OCR forms such as ស្ដែម៉ាតូស្យីត, អរុស្បល,
  អូអូម៉ូស្យូប៊ោកតី, ជង់កិល, ល៉ែយ៉ូ, ស្ទីចម៉ាត, or ស្អិតម៉ាស. Use
  the standard textbook spellings that appear in the context instead.
- Write each standard term ONCE with a single spelling; never repeat a term
  followed by a second spelling in parentheses (e.g. write ស្ទិចម៉ាត, not
  "ស្ទិចម៉ាត (ស្អិតម៉ាស)").
- If the context mentions the brain as a whole (cerebrum), use ខួរធំ; do not
  confuse it with ខួរឆ្អឹងខ្នង (spinal cord).
- Answer the question fully; do not stop at a heading or cut off mid-list.
- If the context names a mechanism/principle and a set of components or
  fundamentals (e.g. "ចលនការមួយ និងមូលដ្ឋានគ្រឹះបី"), present BOTH the
  mechanism (with what drives it) AND every listed component. Do not omit a
  concept that appears in the context even if it sits in the middle of a long
  paragraph.
- Each context block is prefixed with its real page number, e.g. [ទំព័រ 13].
  When you cite a page inside your answer, use exactly the number from that
  prefix. NEVER invent or guess page numbers, chapter numbers, or lesson titles
  that are not shown in the context.
- Do NOT write your own "ប្រភពឯកសារយោង" (source) section at the end of the
  answer: the app appends a Sources block automatically after your response. If
  you mention a chapter or lesson, use only titles that appear in the context.
- Do NOT start your answer by repeating the question or saying "ផ្អែកលើឯកសារ...", "យោងតាម...", or "សូមអធិប្បាយ...". Start directly with the answer content.
- **IMPORTANT: You are given MULTIPLE context sources. You MUST synthesize information from ALL relevant sources to construct a complete, comprehensive answer. Do not rely on only the first source. Combine information from all provided context blocks to give a thorough, complete answer.**
- For questions about biological processes (like pollination, fertilization, photosynthesis), the answer MUST describe the complete step-by-step process using information from ALL relevant context sources. Do not stop at a single step."""

    if mode == "easy":
        mode_instruction = """
Mode: Easy Explanation
- Use very simple Khmer vocabulary
- Short sentences
- Use everyday analogies
- Avoid technical jargon when possible"""
    elif mode == "exam":
        mode_instruction = """
Mode: Exam Preparation
- Focus on key facts that appear in exams
- Provide concise, memorizable bullet points
- Include common exam question patterns
- Highlight definitions that must be memorized"""
    else:
        mode_instruction = """
Mode: Normal Explanation
- Provide a complete Grade 12 level explanation
- Balance simplicity with scientific accuracy
- Include relevant terminology"""

    feature_instruction = ""
    if feature == "quiz":
        feature_instruction = """
Feature: Quiz
- Generate 3-5 practice questions based ONLY on the provided context.
- Each question must include an answer with a short explanation.
- Ask the question in Khmer first, then reveal the answer in Khmer.
- Keep questions at Grade 12 exam difficulty.
- End with a "សាកល្បង" (try it) prompt so the student can attempt before seeing answers."""
    elif feature == "summary":
        feature_instruction = """
Feature: Summary
- Provide a concise summary of the key points from the provided textbook context.
- Use bullet points and short, clear sentences in Khmer.
- Group related ideas together.
- End with the most important exam-relevant points."""

    return base_prompt + mode_instruction + feature_instruction


def _clip_title(text: str, limit: int = 16) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    return text if len(text) <= limit else text[:limit] + "…"


def _source_label(s: dict) -> str:
    parts = []
    cid = s.get("chapter_id", s.get("chapter", 0))
    ctitle = _clip_title(s.get("chapter_title", ""))
    if ctitle:
        parts.append(f"ជំពូក {ctitle}" if cid in (0, None) else f"ជំពូក {cid}: {ctitle}")
    elif cid not in (0, None):
        parts.append(f"ជំពូក {cid}")

    lid = s.get("lesson_id", s.get("lesson", 0))
    ltitle = _clip_title(s.get("lesson_title", ""))
    if ltitle:
        parts.append(f"មេរៀន {ltitle}" if lid in (0, None) else f"មេរៀន {lid}: {ltitle}")
    elif lid not in (0, None):
        parts.append(f"មេរៀន {lid}")

    page = s.get("page", s.get("page_start"))
    if page not in (None, 0):
        page_end = s.get("page_end", page)
        if page_end not in (None, 0) and page_end != page:
            parts.append(f"ទំព័រ {page}-{page_end}")
        else:
            parts.append(f"ទំព័រ {page}")

    return " / ".join(parts) if parts else "ប្រភពមិនស្គាល់"


def format_answer(answer: str, sources: list[dict]) -> str:
    # Collapse duplicate sources that came from overlapping chunks of the same
    # page, so the citation block shows each page once instead of 3-5 repeats
    # (chunks that span a page boundary used a different page_end key and were
    # previously kept as separate "ទំព័រ 17" / "ទំព័រ 17-18" lines).
    seen = set()
    deduped = []
    for s in sources:
        page = s.get("page", s.get("page_start"))
        if page in (None, 0) or page in seen:
            continue
        seen.add(page)
        deduped.append(s)

    # Keep the citations focused on the answer's main lesson: pages are sorted
    # by rerank score, so the first deduped source is the primary match.
    # Cross-chapter noise (distractor pages about other topics) is dropped.
    # If the primary lesson alone yields very few pages, allow a page or two
    # from a neighboring lesson of the same chapter; front-matter sources
    # (lesson_id 0) always come from the original list.
    # ALSO include sources from the same chapter (different lessons) if they
    # are highly relevant, to capture complete processes like pollination.
    def _loc(s):
        return (
            s.get("chapter_id", s.get("chapter", 0)),
            s.get("lesson_id", s.get("lesson", 0)),
        )

    if deduped and _loc(deduped[0])[1] not in (0, None):
        primary = _loc(deduped[0])
        same_lesson = [s for s in deduped if _loc(s) == primary]
        if len(same_lesson) >= 2 or not same_lesson:
            ordered = same_lesson
        else:
            same_chapter = [
                s for s in deduped
                if _loc(s)[0] == primary[0] and _loc(s) != primary
            ]
            ordered = same_lesson + same_chapter[:4]
        shown = ordered[:8] or deduped[:8]
    else:
        shown = deduped[:8]

    source_lines = [f"📄 {_source_label(s)}" for s in shown]
    source_text = "\n".join(source_lines) if source_lines else "មិនមានប្រភព"

    # Clean up the answer: remove repeated question prefix if present
    clean_answer = answer.strip()
    # Remove common prefixes that the model sometimes adds
    prefixes_to_remove = [
        "ផ្អែកលើឯកសារសៀវភៅសិក្សា",
        "ចំពោះសំណួររបស់អ្នក",
        "យោងតាមឯកសារសៀវភៅ",
        "សូមអធិប្បាយដោយផ្អែកលើឯកសារ",
        "ខ្ញុំសូមអធិប្បាយដោយផ្អែកលើ",
        "យោងតាមឯកសារ",
    ]
    for prefix in prefixes_to_remove:
        if clean_answer.startswith(prefix):
            clean_answer = clean_answer[len(prefix):].strip()
            # Remove leading punctuation/whitespace
            clean_answer = clean_answer.lstrip(" ស។៖:-")

    # Format the answer with clean structure
    source_lines = [f"📄 {_source_label(s)}" for s in shown]
    source_text = "\n".join(source_lines) if source_lines else "មិនមានប្រភព"

    return f"""{clean_answer}

━━━━━━━━━━━━━━━━━━
📚 **ប្រភព (Sources)**
{source_text}"""
