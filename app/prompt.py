import re


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
- For questions about biological processes (like pollination, fertilization, photosynthesis), the answer MUST describe the complete step-by-step process using information from ALL relevant context sources. Do not stop at a single step.
- **CRITICAL FOR COMPARISON QUESTIONS: When the question asks to compare two things (e.g. "ប្រៀបធៀប A និង B", "ចូរប្រៀបធៀប..."), you MUST structure your answer with TWO clear sections: 'លក្ខណៈដូចគ្នា' (Similarities) AND 'លក្ខណៈខុសគ្នា' (Differences). Both sections must be present with bullet points. Do not omit either section. Use the Ground Truth Key format from the textbook."""

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
- Format EACH question-answer pair EXACTLY as follows (use this exact format):

**សំណួរទី X: [Question text]**

**ចម្លើយ:** [Answer text with explanation and page reference]

- Do NOT use <details> HTML tags. Use the format above.
- Keep questions at Grade 12 exam difficulty.
- End with a "សាកល្បង" (try it) prompt so the student can attempt before seeing answers."""
    elif feature == "summary":
        feature_instruction = """
Feature: Summary
- Provide a concise summary of the key points from the provided textbook context.
- Use bullet points and short, clear sentences in Khmer.
- Group related ideas together.
- End with the most important exam-relevant points.
- For comparison topics, use the Ground Truth Key format: 'លក្ខណៈដូចគ្នា' AND 'លក្ខណៈខុសគ្នា' sections."""

    return base_prompt + mode_instruction + feature_instruction


def _clip_title(text: str, limit: int = 16) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    return text if len(text) <= limit else text[:limit] + "…"


PAGE_MARKER = "ទំព័រ"
FRONT_MATTER_LAST_PAGE = 4
MAX_CITATION_SOURCES = 8

# Khmer digits are normalized only inside citation tokens.  This makes
# page-number conversion explicit rather than relying on int()'s Unicode
# behavior, and never rewrites biological prose outside a "ទំព័រ ..." group.
KHMER_DIGITS = str.maketrans("០១២៣៤៥៦៧៨៩", "0123456789")


def normalize_khmer_digits(text: str) -> str:
    """Translate Khmer digits to ASCII; every other character is unchanged."""
    if not text:
        return text or ""
    return text.translate(KHMER_DIGITS)


# A citation group is "ទំព័រ" followed by one or more page numbers/ranges
# separated by commas or "និង".  The group stops at the first character that
# is not part of a page token, so prose and punctuation are left untouched.
_CITATION_GROUP_RE = re.compile(
    PAGE_MARKER
    + r"\s*((?:\d+(?:\s*-\s*\d+)?)"
    + r"(?:\s*(?:,|និង)\s*\d+(?:\s*-\s*\d+)?)*)"
)
_PAGE_TOKEN_RE = re.compile(r"(\d+)(?:\s*-\s*(\d+))?")


def _as_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _page_bounds(source: dict):
    """Return the chunk's inclusive page range, or (None, None) if unusable."""
    start = _as_int(source.get("page_start"))
    if start in (None, 0):
        start = _as_int(source.get("page"))
    end = _as_int(source.get("page_end"))
    if start in (None, 0):
        return None, None
    if end in (None, 0):
        end = start
    if end < start:
        start, end = end, start
    return start, end


def format_page_range(start, end=None) -> str:
    """Render 164/164 as "164" and 164/165 as "164-165"."""
    start = _as_int(start)
    end = _as_int(end)
    if start in (None, 0):
        return ""
    if end in (None, 0):
        end = start
    if end < start:
        start, end = end, start
    return str(start) if end == start else f"{start}-{end}"


def page_range_label(source: dict) -> str:
    start, end = _page_bounds(source)
    if start is None:
        return ""
    return format_page_range(start, end)


def source_page_ranges(sources) -> list[tuple[int, int]]:
    """Deduplicated inclusive ranges from context metadata, in input order."""
    ranges = []
    seen = set()
    for source in sources:
        start, end = _page_bounds(source)
        if start is None:
            continue
        key = (start, end)
        if key in seen:
            continue
        seen.add(key)
        ranges.append(key)
    return ranges


def allowed_pages_from_sources(sources) -> set[int]:
    pages = set()
    for start, end in source_page_ranges(sources):
        pages.update(range(start, end + 1))
    return pages


def parse_page_citations(text: str) -> list[tuple[int, int]]:
    """Parse every page/range in every "ទំព័រ ..." citation group.

    Khmer digits inside the captured citation group are normalized to ASCII
    before token parsing; surrounding text is not modified.
    """
    citations = []
    if not text:
        return citations
    for group in _CITATION_GROUP_RE.finditer(text):
        normalized = normalize_khmer_digits(group.group(1))
        for token in _PAGE_TOKEN_RE.finditer(normalized):
            start = int(token.group(1))
            end = int(token.group(2)) if token.group(2) else start
            if end < start:
                start, end = end, start
            citations.append((start, end))
    return citations


def _format_page_runs(pages) -> list[str]:
    """Compress [164, 165, 170] into ["164-165", "170"]."""
    if not pages:
        return []
    ordered = sorted(set(pages))
    runs = []
    start = prev = ordered[0]
    for page in ordered[1:]:
        if page == prev + 1:
            prev = page
            continue
        runs.append(str(start) if start == prev else f"{start}-{prev}")
        start = prev = page
    runs.append(str(start) if start == prev else f"{start}-{prev}")
    return runs


def sanitize_page_citations(text: str, allowed_pages) -> str:
    """Remove page tokens not represented in the supplied context.

    Only citation tokens are changed.  Answer wording, facts, and structure are
    left untouched.  A partially supported list keeps its supported pages.
    """
    if not text:
        return text or ""
    allowed = set(allowed_pages or ())

    def replace_group(match):
        supported = []
        # Normalize only the citation group, never the surrounding answer.
        normalized = normalize_khmer_digits(match.group(1))
        for token in _PAGE_TOKEN_RE.finditer(normalized):
            start = int(token.group(1))
            end = int(token.group(2)) if token.group(2) else start
            if end < start:
                start, end = end, start
            supported.extend(p for p in range(start, end + 1) if p in allowed)
        if not supported:
            return ""
        return f"{PAGE_MARKER} {', '.join(_format_page_runs(supported))}"

    cleaned = _CITATION_GROUP_RE.sub(replace_group, text)
    # A fully unsupported group can leave "[]" or "()" behind.
    cleaned = re.sub(r"[\[\(]\s*[\]\)]", "", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"[ \t]+([,;:។.!?])", r"\1", cleaned)
    cleaned = re.sub(r"([,;:])\s*([។.!?])", r"\2", cleaned)
    cleaned = re.sub(r"[ \t]*\n[ \t]*", "\n", cleaned)
    return cleaned.strip()


def is_context_source(source: dict) -> bool:
    """Keep real lesson chunks and chapter openers; drop only front matter.

    The corpus stores p0-p4 (copyright/TOC) and the p5/p25/... chapter openers
    with lesson_id=0.  The openers contain answerable textbook content, so they
    must remain eligible; only the front matter should be excluded.
    """
    if source.get("lesson_id"):
        return True
    start, _ = _page_bounds(source)
    return start is not None and start > FRONT_MATTER_LAST_PAGE


def select_citation_sources(answer: str, sources, max_sources=MAX_CITATION_SOURCES):
    """Choose footer sources from context chunks, deterministically.

    Body-cited pages are mapped back to the context chunks that contain them;
    those chunks come first.  Remaining slots are filled with the top context
    chunks in rerank/context order.  No gold labels or external knowledge are
    used.
    """
    deduped = []
    seen = set()
    for source in sources:
        start, end = _page_bounds(source)
        if start is None:
            continue
        key = (start, end)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(source)

    selected = []
    selected_keys = set()
    covered = set()

    for cite_start, cite_end in parse_page_citations(answer):
        candidates = []
        for source in deduped:
            start, end = _page_bounds(source)
            if start is None or end < cite_start or start > cite_end:
                continue
            candidates.append((source, start, end))
        if not candidates:
            continue
        # Prefer a chunk that covers the whole cited range; otherwise use the
        # first intersecting chunk in context order.
        chosen = next(
            (
                (source, start, end)
                for source, start, end in candidates
                if start <= cite_start and end >= cite_end
            ),
            candidates[0],
        )
        source, start, end = chosen
        key = (start, end)
        pages = set(range(start, end + 1))
        if key in selected_keys or pages <= covered:
            continue
        selected.append(source)
        selected_keys.add(key)
        covered.update(pages)
        if len(selected) >= max_sources:
            break

    for source in deduped:
        if len(selected) >= max_sources:
            break
        start, end = _page_bounds(source)
        key = (start, end)
        if key in selected_keys:
            continue
        selected.append(source)
        selected_keys.add(key)

    return selected[:max_sources]


def _strip_existing_footer(answer: str) -> str:
    """Make format_answer idempotent and keep citation parsing body-only."""
    text = (answer or "").strip()
    marker = "📚"
    idx = text.find(marker)
    if idx != -1:
        text = text[:idx].rstrip()
        text = re.sub(r"\n\s*━{3,}\s*$", "", text).rstrip()
    return text


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

    page_label = page_range_label(s)
    if page_label:
        parts.append(f"ទំព័រ {page_label}")

    return " / ".join(parts) if parts else "ប្រភពមិនស្គាល់"


def format_answer(answer: str, sources: list[dict]) -> str:
    body = _strip_existing_footer(answer)
    body = sanitize_page_citations(body, allowed_pages_from_sources(sources))
    shown = select_citation_sources(body, sources)

    source_lines = [f"📄 {_source_label(s)}" for s in shown]
    source_text = "\n".join(source_lines) if source_lines else "មិនមានប្រភព"

    # Clean up the answer: remove repeated question prefix if present
    clean_answer = body.strip()
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

    return f"""{clean_answer}

━━━━━━━━━━━━━━━━━━
📚 **ប្រភព (Sources)**
{source_text}"""
