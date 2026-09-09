import streamlit as st
from app.config import EMBEDDING_MODEL, VECTOR_DB_DIR, RETRIEVAL_SCORE_THRESHOLD, NOT_FOUND_MESSAGE
from app.retrieval import get_embedding_model, get_vector_db, get_reranker, retrieve, rerank_with_scores
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


if "messages" not in st.session_state:
    st.session_state.messages = []

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

    if st.button("🗑️ សម្អាតសន្ទនា"):
        st.session_state.messages = []
        st.rerun()

# --- Display chat history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- User input ---
if question := st.chat_input("សួស្តី! សួរសំណួរជីវវិទ្យារបស់អ្នក..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    try:
        with st.chat_message("assistant"):
            with st.spinner("កំពុងស្វែងរកក្នុងមេរៀន..."):
                embedding_model = _get_embedding_model()
                vector_db = _get_vector_db()
                reranker = _get_reranker()

                results = retrieve(question, embedding_model, vector_db)
                documents = results["documents"][0]
                metadatas = results["metadatas"][0]

                reranked_docs, reranked_sources, reranked_scores = rerank_with_scores(
                    question, documents, metadatas, reranker
                )

                context = "\n\n".join(reranked_docs)
                top_score = reranked_scores[0] if reranked_scores else 0.0
            with st.spinner("កំពុងឆ្លើយតប..."):
                if not reranked_docs or top_score < RETRIEVAL_SCORE_THRESHOLD:
                    final_answer = NOT_FOUND_MESSAGE
                else:
                    answer = generate_answer(question, context, mode, feature)
                    final_answer = format_answer(answer, reranked_sources)
                st.markdown(final_answer)
    except Exception as err:  # noqa: BLE001
        st.error(f"⚠️ មានបញ្ហាក្នុងការឆ្លើយតប៖ {err}")
        final_answer = None

    if final_answer:
        st.session_state.messages.append({"role": "assistant", "content": final_answer})
