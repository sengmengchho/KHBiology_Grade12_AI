import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
EXTRACTED_DIR = os.path.join(DATA_DIR, "extracted")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
GLOSSARY_DIR = os.path.join(DATA_DIR, "glossary")
VECTOR_DB_DIR = os.path.join(BASE_DIR, "vector_db")

# --- LLM ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
# Raised from 2048 so long explain/exam answers (with an "Exam Tips" section)
# are not cut off mid-sentence by the generation limit.
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))

# Rotation pool of Google Gemini models to spread free-tier daily quota.
# The primary model (LLM_MODEL) is used first; if it returns a quota
# error, the caller tries the next model in this list.
GOOGLE_MODEL_POOL = os.getenv(
    "GOOGLE_MODEL_POOL",
    "gemini-3.6-flash,gemini-3.5-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-flash-lite-latest,gemini-3.8-flash,gemini-3.7-flash",
).split(",")

# --- Embeddings ---
EMBEDDING_MODEL = "BAAI/bge-m3"
# Larger chunks keep multi-part sections (e.g. ឫស/ដើម/ស្លឹក) coherent so a
# whole-section question still matches enough context. 800 chars ≈ 1/2 page.
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

# --- Retrieval ---
# Fetch more initial candidates so topic-specific chunks on different pages
# are not crowded out of the reranker by repeated/boilerplate chunks.
TOP_K = 30
# Keep more reranked chunks so the LLM sees the full section (roots+stem+leaf)
# instead of only the single best-match fragment.
RERANKER_TOP_K = 12

# --- Hallucination protection ---
# If the best reranked chunk scores below this threshold, the app abstains
# instead of answering, to avoid inventing information not in the textbook.
RETRIEVAL_SCORE_THRESHOLD = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.08"))

NOT_FOUND_MESSAGE = (
    "សូមទោស! ខ្ញុំមិនបានរកឃើញព័ត៌មានគ្រប់គ្រាន់ក្នុងសៀវភៅសិក្សាដើម្បីឆ្លើយសំណួរនេះទេ។ "
    "សូមសួរសំណួរដែលទាក់ទងនឹងមេរៀនក្នុងសៀវភៅជីវវិទ្យាថ្នាក់ទី១២។"
)

# --- System Language ---
DEFAULT_LANGUAGE = "km"
