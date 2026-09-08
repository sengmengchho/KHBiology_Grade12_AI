from app.config import (
    LLM_PROVIDER, OPENAI_API_KEY, GOOGLE_API_KEY,
    OLLAMA_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS,
)
from app.prompt import get_system_prompt, format_answer


def generate_answer(question: str, context: str, mode: str = "normal") -> str:
    system_prompt = get_system_prompt(mode)

    user_prompt = f"""TEXTBOOK CONTEXT:
{context}

STUDENT QUESTION:
{question}

Please answer the question using only the provided textbook context. Answer in Khmer."""

    if LLM_PROVIDER == "openai":
        return _call_openai(system_prompt, user_prompt)
    elif LLM_PROVIDER == "google":
        return _call_google(system_prompt, user_prompt)
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


def _call_google(system_prompt: str, user_prompt: str) -> str:
    from google.genai import Client
    from google.genai import types

    client = Client(api_key=GOOGLE_API_KEY)
    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=LLM_TEMPERATURE,
            max_output_tokens=LLM_MAX_TOKENS,
        ),
    )
    return response.text


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
