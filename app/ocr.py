"""OCR a student-uploaded question image using Google Gemini multimodal.

Used by the Streamlit app so students can photograph a Biology question (or
a lesson excerpt) and have it turned into text, which is then answered by the
normal RAG pipeline. Mirrors the model-pool rotation in app/rag.py.
"""

import time

from google.genai import Client
from google.genai import types

from app.config import GOOGLE_API_KEY, GOOGLE_MODEL_POOL, LLM_MODEL
from app.utils import normalize_query

QUESTION_OCR_PROMPT = (
    "This image contains a Khmer Biology question or a textbook lesson that a "
    "student wants explained. Transcribe the relevant text exactly as written."
    "\n- If it is a question, transcribe the question(s) in full."
    "\n- If it is a lesson or textbook excerpt, transcribe the main headings "
    "and body text."
    "\nKeep Khmer text and any science terms as-is (fix only obvious "
    "misspellings). Output only the plain transcription, no commentary."
)


def _transcribe(client, img_bytes: bytes, mime_type: str, model: str) -> str:
    resp = client.models.generate_content(
        model=model,
        contents=[
            QUESTION_OCR_PROMPT,
            types.Part.from_bytes(data=img_bytes, mime_type=mime_type),
        ],
    )
    return (resp.text or "").strip()


def ocr_question_image(img_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Transcribe an uploaded question image into plain text.

    Tries the primary Gemini model first, then rotates through the model pool
    on quota (429) / unavailability (503) errors or empty results — the same
    strategy as app/rag.py::_call_google_rotate.
    """
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is not set in .env")
    client = Client(api_key=GOOGLE_API_KEY)
    models = [m.strip() for m in GOOGLE_MODEL_POOL if m.strip()]
    if LLM_MODEL not in models:
        models.insert(0, LLM_MODEL)
    for model in models:
        try:
            out = _transcribe(client, img_bytes, mime_type, model)
            if out:
                return normalize_query(out)
        except Exception as err:  # noqa: BLE001
            msg = str(err)
            if "429" not in msg and "RESOURCE_EXHAUSTED" not in msg \
                    and "503" not in msg and "UNAVAILABLE" not in msg:
                raise
            time.sleep(1)
    raise RuntimeError("All Gemini models exhausted quota or unavailable for OCR.")