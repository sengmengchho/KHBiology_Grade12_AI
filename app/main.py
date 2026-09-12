import re

import streamlit as st
from app.config import EMBEDDING_MODEL, VECTOR_DB_DIR, RETRIEVAL_SCORE_THRESHOLD, NOT_FOUND_MESSAGE
from app.retrieval import get_embedding_model, get_vector_db, get_reranker, retrieve, rerank_with_context
from app.rag import generate_answer
from app.prompt import format_answer
from app.ocr import ocr_question_image
from app.utils import expand_query, normalize_query


def _render_quiz_answer(answer: str, feature: str) -> None:
    """Render quiz answers with collapsible expanders for each question."""
    if feature != "quiz":
        st.markdown(answer)
        return

    # Parse the quiz format: **សំណួរទី X: ...** followed by **ចម្លើយ:** ...
    # Split by question markers
    question_pattern = re.compile(r'(\*\*សំណួរទី\s*\d+\s*:\s*.+?\*\*)')
    parts = question_pattern.split(answer)

    # parts[0] might be intro text, then alternating: question, content, question, content...
    if len(parts) <= 1:
        st.markdown(answer)
        return

    # Check if there's intro text before first question
    intro = parts[0].strip()
    if intro:
        st.markdown(intro)

    # Process question-answer pairs
    for i in range(1, len(parts), 2):
        if i >= len(parts):
            break
        question_header = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""

        # Extract question number from header
        q_match = re.search(r'សំណួរទី\s*(\d+)', question_header)
        q_num = q_match.group(1) if q_match else str((i + 1) // 2)

        # Split content into answer part
        # The content should start with **ចម្លើយ:**
        answer_match = re.match(r'\*\*ចម្លើយ:\*\*\s*(.+)', content, re.DOTALL)
        if answer_match:
            answer_text = answer_match.group(1).strip()
            # Render question as expander header, answer inside
            with st.expander(f"**សំណួរទី {q_num}:** {question_header.replace('**', '').replace(f'សំណួរទី {q_num}:', '').strip()}"):
                st.markdown(f"**ចម្លើយ:** {answer_text}")
        else:
            # Fallback: just render as markdown
            st.markdown(f"{question_header}\n\n{content}")

    # Check for trailing content after last question
    if len(parts) % 2 == 0:
        trailing = parts[-1].strip()
        if trailing:
            st.markdown(trailing)

st.set_page_config(page_title="KhmerBio Tutor", page_icon="🧬", layout="centered")

st.title("🧬 KhmerBio Tutor")
st.caption("AI ជំនួយការសិស្សវិទ្យាល័យទី ១២ មុខវិទ្យាជីវវិទ្យា")


@st.cache_resource(show_spinner="កំពុងផ្ទុកម៉ូដែល...")
def _get_embedding_model():
    return get_embedding_model()


@st.cache_resource(show_spinner="កំពុងផ្ទុកម៉ូដែល...")
def _get_reranker():
    return get_reranker()


@st.cache_resource
def _get_vector_db():
    return get_vector_db()


def _answer(question: str, mode: str, feature: str) -> str:
    """Run the full retrieval + rerank + generate pipeline and return the
    formatted answer. Raises on failure so the caller can show an error.

    The query is expanded (term fixes + definition rewrite) here so it reaches
    retrieval, reranking, and generation in the most retrievable form; the
    displayed chat message keeps the student's own (term-fixed) wording."""
    question = expand_query(question)
    embedding_model = _get_embedding_model()
    vector_db = _get_vector_db()
    reranker = _get_reranker()

    results = retrieve(question, embedding_model, vector_db)
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    reranked_docs, reranked_sources, reranked_scores = rerank_with_context(
        question, documents, metadatas, reranker
    )

    top_score = reranked_scores[0] if reranked_scores else 0.0
    if not reranked_docs or top_score < RETRIEVAL_SCORE_THRESHOLD:
        return NOT_FOUND_MESSAGE

    # Drop front-matter / running-header chunks (no lesson_id, stored as 0) so
    # TOC pages do not pollute the answer or its citation list.
    kept = [
        (d, m) for d, m in zip(reranked_docs, reranked_sources)
        if m.get("lesson_id")
    ]
    kept = kept or [(reranked_docs[0], reranked_sources[0])]  # never empty

    # Label each block with its real page so the model can cite accurately
    # instead of guessing page numbers.
    context = "\n\n".join(
        f"[ទំព័រ {m.get('page')}] {d}" for d, m in kept
    )
    answer = generate_answer(question, context, mode, feature)
    return format_answer(answer, [m for _d, m in kept])


_QUESTION_END_RE = re.compile(r"[?\u17d5\uff1f\u061f]")
_MARK_CHARS = "\u17d5\uff1f\u061f?"
# Generic prompt fragments that should be merged with previous question
_GENERIC_PROMPT_RE = re.compile(r"^\s*(ចូរ|ព្រោះ|ពន្យល់|ពណ៌នា|វាមាន)")
# Roman numeral question markers (I., II., III., IV., V., VI., etc.)
_ROMAN_RE = re.compile(r"^[IVX]{1,6}[.។]\s*")


def _split_questions(text: str) -> list[str]:
    """Split a multi-part exam-style message into individual questions.

    Only splits on TOP-LEVEL question markers (I., II., III., IV., V., VI., etc.).
    Keeps sub-questions (ក., ខ., គ.) together with their parent question.
    """
    # First, normalize the text: ensure spaces around roman numeral markers
    # e.g., "I.ដូច..." -> "I. ដូច..."
    text = re.sub(r'([IVX]{1,6})[.។](?=\S)', r'\1. ', text)
    
    # Find all TOP-LEVEL question markers (I., II., III., IV., V., VI., etc.)
    # These are roman numerals followed by . or ។ at the start of text or after whitespace/period
    top_level_pattern = re.compile(r'(?:^|(?<=[។\s]))([IVX]{1,6})[.។]\s*')
    
    markers = list(top_level_pattern.finditer(text))
    
    if not markers:
        # No top-level markers found, treat as single question
        cleaned = text.strip()
        return [cleaned] if cleaned else []
    
    # Split text by top-level markers
    questions = []
    for i, m in enumerate(markers):
        start = m.start()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        question_text = text[start:end].strip()
        if question_text:
            questions.append(question_text)
    
    return questions if questions else [text.strip()]


def _is_generic_fragment(seg: str) -> bool:
    """True for short prompt fragments like "ចូរពន្យល់?" / "ព្រោះអ្វី?"."""
    if len(seg.strip(_MARK_CHARS + " ")) > 25:
        return False
    return _GENERIC_PROMPT_RE.match(seg) is not None


def _answer_multi(question: str, mode: str, feature: str) -> str:
    """Answer possibly several sub-questions, each with its own retrieval.

    The question is normalized first so OCR-style garbled terms (including the
    common ខួរឆ្អឹង-for-ខួរធំ typo) are rewritten to the canonical textbook
    spellings before retrieval."""
    question = normalize_query(question)
    parts = _split_questions(question)
    if len(parts) == 1:
        return _answer(parts[0], mode, feature)
    blocks = []
    for i, q in enumerate(parts, 1):
        blocks.append(f"**{i}. {q}**\n\n{_answer(q, mode, feature)}")
    return "\n\n---\n\n".join(blocks)


if "messages" not in st.session_state:
    st.session_state.messages = []

st.session_state.setdefault("last_question", None)
st.session_state.setdefault("ocr_draft", "")


def _process_question(question: str, mode: str, feature: str) -> None:
    """Append the student question to the chat and show the grounded answer."""
    question = normalize_query(question)
    st.session_state.last_question = question
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    try:
        with st.chat_message("assistant"):
            with st.spinner("កំពុងស្វែងរកក្នុងមេរៀន..."):
                final_answer = _answer_multi(question, mode, feature)
            _render_quiz_answer(final_answer, feature)
    except Exception as err:  # noqa: BLE001
        st.error(f"⚠️ មានបញ្ហាក្នុងការឆ្លើយតប៖ {err}")
        final_answer = None

    if final_answer:
        st.session_state.messages.append({"role": "assistant", "content": final_answer})

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ របៀបប្រើប្រាស់")

    mode = st.selectbox(
        "របៀបឆ្លើយតប",
        ["normal", "easy", "exam"],
        format_func=lambda x: {
            "normal": "📖 ធម្មតា (Normal)",
            "easy": "🟢 ងាយៗ (Easy)",
            "exam": "🎯 ប្រឡង (Exam)",
        }[x],
    )

    feature = st.radio(
        "មុខងារ",
        ["explain", "quiz", "summary"],
        format_func=lambda x: {
            "explain": "💬 ឆ្លើយសំណួរ",
            "quiz": "❓ សាកល្បង",
            "summary": "📝 សង្ខេប",
        }[x],
    )

    # Re-use the previous question with the currently selected mode/feature,
    # so the student does not have to retype it to switch styles.
    last_q = st.session_state.last_question
    if last_q:
        st.divider()
        st.caption("📌 សំណួរមុន")
        st.caption(last_q[:120] + ("…" if len(last_q) > 120 else ""))
        reanswer_clicked = st.button(
            "↻ ឆ្លើយម្តងទៀត (របៀប/មុខងារបច្ចុប្បន្ន)",
            use_container_width=True,
        )
    else:
        reanswer_clicked = False

    if st.button("🗑️ សម្អាតសន្ទនា"):
        st.session_state.messages = []
        st.session_state.last_question = None
        st.rerun()

    st.divider()
    with st.expander("📷 សំណួរពីរូបភាព"):
        st.caption("ថតរូបសំណួរ ឬលើករូបភាពសំណួរមក រួចអានដោយ AI")
        uploaded = st.file_uploader(
            "រូបភាពសំណួរ (JPG/PNG)", type=["jpg", "jpeg", "png"]
        )
        if uploaded is not None:
            st.image(uploaded, caption="រូបភាពដែលបានជ្រើស", width=220)
        if uploaded is not None and st.button(
            "🔍 អានសំណួរពីរូបភាព", use_container_width=True
        ):
            with st.spinner("កំពុងអានសំណួរពីរូបភាព..."):
                try:
                    q_text = ocr_question_image(
                        uploaded.getvalue(), uploaded.type or "image/jpeg"
                    )
                except Exception as err:  # noqa: BLE001
                    st.error(f"⚠️ បរាជ័យក្នុងការអានរូបភាព៖ {err}")
                    q_text = None
            if q_text:
                st.session_state.ocr_draft = q_text
                st.success("អានរួច! សូមពិនិត្យ និងកែសំណួរ រួចចុច «ផ្ញើសំណួរនេះ»")
        draft = st.text_area(
            "សំណួរដែលបានអាន (កែបាន)", key="ocr_draft", height=120
        )
        draft = (draft or "").strip()
        send_img = st.button(
            "📨 ផ្ញើសំណួរនេះ", use_container_width=True, disabled=not draft
        )

# --- Display chat history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Answer the previous question again in the current mode/feature ---
if reanswer_clicked:
    q = st.session_state.last_question
    with st.chat_message("assistant"):
        with st.spinner("កំពុងឆ្លើយតប (សំណួរមុន)..."):
            try:
                final_answer = _answer_multi(q, mode, feature)
                _render_quiz_answer(final_answer, feature)
            except Exception as err:  # noqa: BLE001
                st.error(f"⚠️ មានបញ្ហាក្នុងការឆ្លើយតប៖ {err}")
                final_answer = None
    if final_answer:
        st.session_state.messages.append({"role": "assistant", "content": final_answer})

# --- Send the OCR'd image question, if requested ---
if send_img:
    _process_question(draft, mode, feature)
    st.session_state.ocr_draft = ""

# --- User input ---
if question := st.chat_input("សួស្តី! សួរសំណួរជីវវិទ្យារបស់អ្នក..."):
    _process_question(question, mode, feature)
