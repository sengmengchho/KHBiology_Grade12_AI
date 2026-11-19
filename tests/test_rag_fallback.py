"""Regression tests for the Gemini generation fallback.

Run:  python -X utf8 tests/test_rag_fallback.py
"""

import os
import sys
from unittest.mock import patch

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import app.rag as rag  # noqa: E402

CTX = "\n\n".join(
    f"[ទំព័រ {page}] ខ្លឹមសារសាកល្បងទំព័រ {page}" for page in (1, 2, 3, 4, 5)
)


def check(name, cond):
    if not cond:
        raise AssertionError(name)
    print(f"  PASS {name}")


def _blocked(*_args, **_kwargs):
    raise RuntimeError("PROHIBITED_CONTENT: candidate blocked by safety filter")


def _quota(*_args, **_kwargs):
    raise RuntimeError("429 RESOURCE_EXHAUSTED")


def _unavailable(*_args, **_kwargs):
    raise RuntimeError("503 UNAVAILABLE")


def test_normal():
    with patch.object(rag, "LLM_PROVIDER", "google"), \
            patch.object(rag, "_call_google", return_value="ក" * 100) as call, \
            patch.object(rag, "_call_google_rotate") as rotate:
        out = rag.generate_answer("តើ ADN ជាអ្វី?", CTX)
    check("normal returns model output", out == "ក" * 100)
    check("normal calls primary once", call.call_count == 1)
    check("normal does not rotate", rotate.call_count == 0)


def test_quota_rotates():
    with patch.object(rag, "LLM_PROVIDER", "google"), \
            patch.object(rag, "_call_google", side_effect=_quota), \
            patch.object(rag, "_call_google_rotate", return_value="rotated") as rotate:
        out = rag.generate_answer("សំណួរ", CTX)
    check("429 rotates to model pool", out == "rotated")
    check("429 rotation called once", rotate.call_count == 1)


def test_unavailable_rotates():
    with patch.object(rag, "LLM_PROVIDER", "google"), \
            patch.object(rag, "_call_google", side_effect=_unavailable), \
            patch.object(rag, "_call_google_rotate", return_value="rotated") as rotate:
        out = rag.generate_answer("សំណួរ", CTX)
    check("503 rotates to model pool", out == "rotated")
    check("503 rotation called once", rotate.call_count == 1)


def test_blocked_then_reduced_succeeds():
    prompts = []

    def fake_call(system_prompt, user_prompt, model=None):
        prompts.append(user_prompt)
        if len(prompts) == 1:
            raise RuntimeError("PROHIBITED_CONTENT")
        return "ចម្លើយខ្លី"

    with patch.object(rag, "LLM_PROVIDER", "google"), \
            patch.object(rag, "_call_google", side_effect=fake_call), \
            patch.object(rag, "_call_google_rotate") as rotate:
        out = rag.generate_answer("សំណួរ", CTX)
    check("blocked retries reduced context", out == "ចម្លើយខ្លី")
    check("blocked does not rotate", rotate.call_count == 0)
    check("reduced prompt keeps three blocks", prompts[1].count("[ទំព័រ") == 3)
    check("reduced prompt drops later blocks", "[ទំព័រ 4]" not in prompts[1])


def test_blocked_twice_returns_friendly_message():
    with patch.object(rag, "LLM_PROVIDER", "google"), \
            patch.object(rag, "_call_google", side_effect=_blocked) as call, \
            patch.object(rag, "_call_google_rotate") as rotate:
        out = rag.generate_answer("សំណួរ", CTX)
    check("blocked twice returns fallback message", out == rag.GENERATION_FALLBACK_MESSAGE)
    check("blocked twice tries full, three, one block", call.call_count == 3)
    check("blocked twice does not rotate", rotate.call_count == 0)
    check("fallback is Khmer and not a GEN_FAILED string",
          "សូមអភ័យទោស" in out and "[GEN_FAILED" not in out)


def test_blocked_top3_then_top1_succeeds():
    prompts = []

    def fake_call(system_prompt, user_prompt, model=None):
        prompts.append(user_prompt)
        if len(prompts) <= 2:
            raise RuntimeError("PROHIBITED_CONTENT")
        return "ចម្លើយពីប្លុកដំបូង"

    with patch.object(rag, "LLM_PROVIDER", "google"), \
            patch.object(rag, "_call_google", side_effect=fake_call), \
            patch.object(rag, "_call_google_rotate") as rotate:
        out = rag.generate_answer("សំណួរ", CTX)
    check("top-3 block falls back to top-1", out == "ចម្លើយពីប្លុកដំបូង")
    check("top-3 then top-1 uses three calls", len(prompts) == 3)
    check("top-1 prompt keeps one block", prompts[2].count("[ទំព័រ") == 1)
    check("top-1 prompt drops the second block", "[ទំព័រ 2]" not in prompts[2])
    check("top-1 fallback does not rotate", rotate.call_count == 0)


def test_empty_then_reduced_succeeds():
    calls = []

    def fake_call(system_prompt, user_prompt, model=None):
        calls.append(user_prompt)
        return "" if len(calls) == 1 else "ចម្លើយពីបរិបទខ្លី"

    with patch.object(rag, "LLM_PROVIDER", "google"), \
            patch.object(rag, "_call_google", side_effect=fake_call):
        out = rag.generate_answer("សំណួរ", CTX)
    check("empty retries reduced context", out == "ចម្លើយពីបរិបទខ្លី")
    check("empty retry uses three blocks", calls[1].count("[ទំព័រ") == 3)


def test_empty_twice_returns_friendly_message():
    with patch.object(rag, "LLM_PROVIDER", "google"), \
            patch.object(rag, "_call_google", return_value="") as call:
        out = rag.generate_answer("សំណួរ", CTX)
    check("empty twice returns fallback message", out == rag.GENERATION_FALLBACK_MESSAGE)
    check("empty twice tries full, three, one block", call.call_count == 3)


def test_single_block_context_returns_friendly_message():
    one_block = "[ទំព័រ 1] ខ្លឹមសារតែមួយ"
    with patch.object(rag, "LLM_PROVIDER", "google"), \
            patch.object(rag, "_call_google", return_value="") as call:
        out = rag.generate_answer("សំណួរ", one_block)
    check("single-block empty returns fallback", out == rag.GENERATION_FALLBACK_MESSAGE)
    check("single-block empty tries once", call.call_count == 1)


def main():
    print("RAG fallback tests")
    test_normal()
    test_quota_rotates()
    test_unavailable_rotates()
    test_blocked_then_reduced_succeeds()
    test_blocked_twice_returns_friendly_message()
    test_blocked_top3_then_top1_succeeds()
    test_empty_then_reduced_succeeds()
    test_empty_twice_returns_friendly_message()
    test_single_block_context_returns_friendly_message()
    print("All RAG fallback tests passed.")


if __name__ == "__main__":
    main()
