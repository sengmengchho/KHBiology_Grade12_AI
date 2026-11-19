import time

from app.config import (
    LLM_PROVIDER, OPENAI_API_KEY, GOOGLE_API_KEY,
    OLLAMA_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS,
    GOOGLE_MODEL_POOL,
)
from app.prompt import get_system_prompt, format_answer


# Shown only when Gemini refuses the retrieved context (safety block) or
# returns an empty candidate even after the reduced-context retry. This keeps
# the app usable instead of surfacing a raw [GEN_FAILED: ...] string.
GENERATION_FALLBACK_MESSAGE = (
    "សូមអភ័យទោស! ខ្ញុំមិនអាចបង្កើតចម្លើយពីខ្លឹមសារដែលបានរកឃើញបានទេ។ "
    "សូមព្យាយាមសួរឡើងវិញដោយប្រើពាក្យផ្សេង ឬសួរសំណួរផ្សេង។"
)
_FALLBACK_CONTEXT_BLOCKS = 3
_TRANSIENT_MARKERS = ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE")
_BLOCKED_MARKERS = (
    "PROHIBITED_CONTENT", "SAFETY", "BLOCKED", "blocked", "finish_reason",
)


def _build_user_prompt(question: str, context: str) -> str:
    return f"""TEXTBOOK CONTEXT:
{context}

STUDENT QUESTION:
{question}

Please answer the question using only the provided textbook context. Answer in Khmer."""


def _is_transient_error(err: Exception) -> bool:
    msg = str(err)
    return any(marker in msg for marker in _TRANSIENT_MARKERS)


def _is_blocked_error(err: Exception) -> bool:
    msg = str(err)
    return any(marker in msg for marker in _BLOCKED_MARKERS)


def _reduce_context(context: str, max_blocks: int = _FALLBACK_CONTEXT_BLOCKS) -> str:
    """Keep only the first few retrieved page blocks.

    app/main.py joins one block per retrieved chunk with a blank line. A long
    context can trip Gemini's safety filter even when each chunk is harmless;
    retrying with the top three blocks usually gets a usable answer.
    """
    blocks = [b for b in context.split("\n\n") if b.strip()]
    return "\n\n".join(blocks[:max_blocks])


def _generate_google(question: str, context: str, system_prompt: str) -> str:
    user_prompt = _build_user_prompt(question, context)
    try:
        out = _call_google(system_prompt, user_prompt)
        if out and out.strip():
            return out
    except Exception as err:  # noqa: BLE001
        if _is_transient_error(err):
            return _call_google_rotate(system_prompt, user_prompt)
        if not _is_blocked_error(err):
            raise

    # Blocked or empty candidate: retry with progressively smaller contexts.
    # The top block often still contains the direct definition even when lower
    # blocks add reproductive/anatomy terms that trip the safety filter.
    # Do not rotate through the whole model pool on a safety block; every model
    # sees the same text and would fail the same way.
    tried = {context}
    for max_blocks in (_FALLBACK_CONTEXT_BLOCKS, 1):
        reduced = _reduce_context(context, max_blocks)
        if not reduced or reduced in tried:
            continue
        tried.add(reduced)
        reduced_prompt = _build_user_prompt(question, reduced)
        try:
            out = _call_google(system_prompt, reduced_prompt)
            if out and out.strip():
                return out
        except Exception as err:  # noqa: BLE001
            if _is_transient_error(err):
                return _call_google_rotate(system_prompt, reduced_prompt)
            if not _is_blocked_error(err):
                raise
    return GENERATION_FALLBACK_MESSAGE


def generate_answer(question: str, context: str, mode: str = "normal", feature: str = "explain") -> str:
    system_prompt = get_system_prompt(mode, feature)

    if LLM_PROVIDER == "openai":
        return _call_openai(system_prompt, _build_user_prompt(question, context))
    elif LLM_PROVIDER == "google":
        return _generate_google(question, context, system_prompt)
    else:
        return _call_ollama(system_prompt, _build_user_prompt(question, context))


def _call_openai(system_prompt: str, user_prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


def _call_google(system_prompt: str, user_prompt: str, model: str = LLM_MODEL) -> str:
    from google.genai import Client
    from google.genai import types

    client = Client(api_key=GOOGLE_API_KEY)
    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=LLM_TEMPERATURE,
            max_output_tokens=LLM_MAX_TOKENS,
        ),
    )
    return response.text


def _call_google_rotate(system_prompt: str, user_prompt: str) -> str:
    """Try the primary Gemini model, then rotate through the model pool.
    Skips models that hit quota (429), are unavailable (503), or return an
    empty / implausibly short response (a known failure of the lite models)."""
    models = [m.strip() for m in GOOGLE_MODEL_POOL if m.strip()]
    if LLM_MODEL not in models:
        models.insert(0, LLM_MODEL)
    seen_output = None
    for model in models:
        try:
            out = _call_google(system_prompt, user_prompt, model)
            if out and len(out.strip()) >= 80:
                return out
            time.sleep(1)  # model returned nothing useful; try next
        except Exception as err:  # noqa: BLE001
            msg = str(err)
            if "429" not in msg and "RESOURCE_EXHAUSTED" not in msg \
                    and "503" not in msg and "UNAVAILABLE" not in msg:
                raise
            time.sleep(1)
    # One more pass accepting any short output rather than failing outright.
    for model in models:
        try:
            out = _call_google(system_prompt, user_prompt, model)
            if out:
                return out
        except Exception:  # noqa: BLE001
            continue
    raise RuntimeError("All Gemini models exhausted quota or unavailable.")


def _call_ollama(system_prompt: str, user_prompt: str) -> str:
    import requests
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        },
    )
    return response.json()["message"]["content"]
