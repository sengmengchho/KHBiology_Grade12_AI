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
  nucleus/nuclei) and answer with the correct biology.
- Answer the question fully; do not stop at a heading or cut off mid-list."""

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
        parts.append(f"ទំព័រ {page}")

    return " / ".join(parts) if parts else "ប្រភពមិនស្គាល់"


def format_answer(answer: str, sources: list[dict]) -> str:
    # Collapse duplicate sources that came from overlapping chunks of the same
    # page, so the citation block shows each page once instead of 3-5 repeats.
    seen = set()
    deduped = []
    for s in sources:
        page = s.get("page", s.get("page_start"))
        key = f"{page}-{s.get('chapter_id', s.get('chapter', 0))}-{s.get('lesson_id', s.get('lesson', 0))}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(s)
    source_lines = [f"- {_source_label(s)}" for s in deduped]
    source_text = "\n".join(source_lines) if source_lines else "- (មិនមាន)"
    return f"""{answer}

---
📖 **ប្រភព (Sources):**
{source_text}"""
