"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: OpenAI client wrapper providing two-tier model access: GPT-4o for reasoning and GPT-4o-mini for fast extraction.
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage
from dotenv import load_dotenv

load_dotenv()

MODEL_STRONG = "gpt-4o"
MODEL_FAST = "gpt-4o-mini"

_client: Optional[OpenAI] = None

# Token log file — written next to sec_ceo_data/ by default, overridable at runtime.
_TOKEN_LOG_PATH: Optional[str] = None


def set_token_log_path(path: str) -> None:
    global _TOKEN_LOG_PATH
    _TOKEN_LOG_PATH = path


def _log_usage(model: str, input_tokens: int, output_tokens: int) -> None:
    log_path = _TOKEN_LOG_PATH or os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "sec_ceo_data", "token_usage.jsonl"
    )
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(record) + "\n")


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found. Add it to your .env file:\n"
                "  OPENAI_API_KEY=sk-..."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def chat(
    messages: list,
    tools: Optional[list] = None,
    model: str = MODEL_STRONG,
) -> ChatCompletionMessage:
    """Call OpenAI chat completions. Returns the raw message object."""
    client = _get_client()
    kwargs: dict = {"model": model, "messages": messages, "temperature": 0.0}
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    response = client.chat.completions.create(**kwargs)
    if response.usage:
        _log_usage(model, response.usage.prompt_tokens, response.usage.completion_tokens)
    return response.choices[0].message


def extract(
    prompt: str,
    system: Optional[str] = None,
    model: str = MODEL_FAST,
) -> str:
    """Cheap single-turn extraction. Returns the text content."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    msg = chat(messages, model=model)
    return (msg.content or "").strip()
