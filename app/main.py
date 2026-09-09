import streamlit as st
from app.config import EMBEDDING_MODEL, VECTOR_DB_DIR, RETRIEVAL_SCORE_THRESHOLD, NOT_FOUND_MESSAGE
from app.retrieval import get_embedding_model, get_vector_db, get_reranker, retrieve, rerank_with_context
from app.rag import generate_answer
from app.prompt import format_answer

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
    formatted answer. Raises on failure so the caller can show an error."""
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


if "messages" not in st.session_state:
    st.session_state.messages = []

st.session_state.setdefault("last_question", None)

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
                final_answer = _answer(q, mode, feature)
                st.markdown(final_answer)
            except Exception as err:  # noqa: BLE001
                st.error(f"⚠️ មានបញ្ហាក្នុងការឆ្លើយតប៖ {err}")
                final_answer = None
    if final_answer:
        st.session_state.messages.append({"role": "assistant", "content": final_answer})

# --- User input ---
if question := st.chat_input("សួស្តី! សួរសំណួរជីវវិទ្យារបស់អ្នក..."):
    st.session_state.last_question = question
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    try:
        with st.chat_message("assistant"):
            with st.spinner("កំពុងស្វែងរកក្នុងមេរៀន..."):
                final_answer = _answer(question, mode, feature)
            st.markdown(final_answer)
    except Exception as err:  # noqa: BLE001
        st.error(f"⚠️ មានបញ្ហាក្នុងការឆ្លើយតប៖ {err}")
        final_answer = None

    if final_answer:
        st.session_state.messages.append({"role": "assistant", "content": final_answer})
