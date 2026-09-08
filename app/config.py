import os
from dotenv import load_dotenv

load_dotenv()

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
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))

# --- Embeddings ---
EMBEDDING_MODEL = "BAAI/bge-m3"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# --- Retrieval ---
TOP_K = 20
RERANKER_TOP_K = 5

# --- System Language ---
DEFAULT_LANGUAGE = "km"
