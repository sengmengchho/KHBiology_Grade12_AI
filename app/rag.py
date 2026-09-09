import time

from app.config import (
    LLM_PROVIDER, OPENAI_API_KEY, GOOGLE_API_KEY,
    OLLAMA_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS,
    GOOGLE_MODEL_POOL,
)
from app.prompt import get_system_prompt, format_answer


def generate_answer(question: str, context: str, mode: str = "normal", feature: str = "explain") -> str:
    system_prompt = get_system_prompt(mode, feature)

    user_prompt = f"""TEXTBOOK CONTEXT:
{context}

STUDENT QUESTION:
{question}

Please answer the question using only the provided textbook context. Answer in Khmer."""

    if LLM_PROVIDER == "openai":
        return _call_openai(system_prompt, user_prompt)
    elif LLM_PROVIDER == "google":
        try:
            return _call_google(system_prompt, user_prompt)
        except Exception as err:  # noqa: BLE001
            msg = str(err)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                return _call_google_rotate(system_prompt, user_prompt)
            raise
    else:
        return _call_ollama(system_prompt, user_prompt)


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
