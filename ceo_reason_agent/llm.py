"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: LLM wrapper for the CEO reason agent — returns content plus raw token usage so the caller can log and accumulate costs.
"""

import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

MODEL = "gpt-4o-mini"   # default; override via run.py --model

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found. Add it to your .env file.")
        _client = OpenAI(api_key=api_key)
    return _client


def call(
    messages: list[dict],
    model: str = MODEL,
    temperature: float = 0.0,
) -> tuple[str, int, int]:
    """
    Call the LLM and return (content, input_tokens, output_tokens).
    Never raises — returns ("", 0, 0) on error.
    """
    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        content = (resp.choices[0].message.content or "").strip()
        usage = resp.usage
        in_tok = usage.prompt_tokens if usage else 0
        out_tok = usage.completion_tokens if usage else 0
        return content, in_tok, out_tok
    except Exception as exc:
        return f"LLM_ERROR: {exc}", 0, 0
