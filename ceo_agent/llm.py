"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: AWS Bedrock client using Amazon Nova models via the Bedrock Converse API.
"""

import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

MODEL_STRONG = "amazon.nova-lite-v1:0"
MODEL_FAST   = "amazon.nova-micro-v1:0"

_client = None
_TOKEN_LOG_PATH: Optional[str] = None
_RUN_LOG_PATH:   Optional[str] = None
_request_counter: int = 0


# ── Mock message class (matches OpenAI interface used by agent.py) ────────────

class _FunctionCall:
    def __init__(self, name: str, arguments: str):
        self.name = name
        self.arguments = arguments

class _ToolCall:
    def __init__(self, id: str, name: str, arguments: str):
        self.id   = id
        self.type = "function"
        self.function = _FunctionCall(name, arguments)

class _Message:
    def __init__(self, content: Optional[str], tool_calls: Optional[list]):
        self.role       = "assistant"
        self.content    = content
        self.tool_calls = tool_calls or None


# ── Logging ───────────────────────────────────────────────────────────────────

def _get_run_log_path() -> str:
    global _RUN_LOG_PATH
    if _RUN_LOG_PATH is None:
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        run_id = str(uuid.uuid4())
        _RUN_LOG_PATH = os.path.join(logs_dir, f"{run_id}.log")
        with open(_RUN_LOG_PATH, "w") as f:
            f.write(
                f"=== CEO Agent Run  |  {datetime.now(timezone.utc).isoformat()}"
                f"  |  strong={MODEL_STRONG}  fast={MODEL_FAST} ===\n\n"
            )
        print(f"   [log] {_RUN_LOG_PATH}")
    return _RUN_LOG_PATH


def _write_log(entry: dict) -> None:
    ts   = entry.get("ts", "")[-8:][:8]   # HH:MM:SS from ISO timestamp
    req  = entry.get("req", "")
    evt  = entry.get("event", "")

    if evt == "request":
        tools   = ", ".join(entry.get("available_tools", [])) or "none"
        preview = entry.get("last_message_preview", "")[:120].replace("\n", " ")
        line = (
            f"[{ts}] REQUEST #{req}  →  {entry['model']}\n"
            f"         Context: {entry['messages_in_context']} messages in context\n"
            f"         Tools available: {tools}\n"
            f"         Last msg ({entry.get('last_message_role','?')}): {preview}\n"
        )
    elif evt == "response":
        line = (
            f"[{ts}] RESPONSE #{req}  ←  ({entry.get('elapsed_s', '?')}s)\n"
            f"         Tokens: {entry.get('input_tokens', 0)} in → {entry.get('output_tokens', 0)} out"
            f"  |  Stop: {entry.get('stop_reason', '?')}\n"
            f"         Action: {entry.get('action', '?')}\n"
            f"         Preview: {str(entry.get('action_preview', ''))[:120].replace(chr(10), ' ')}\n"
        )
    elif evt == "throttle":
        line = (
            f"[{ts}] THROTTLED #{req}  —  attempt {entry.get('attempt')}/5"
            f"  |  waiting {entry.get('wait_s')}s\n"
        )
    elif evt == "error":
        line = (
            f"[{ts}] ERROR #{req}  —  {str(entry.get('error', ''))[:200]}\n"
        )
    else:
        line = f"[{ts}] {evt.upper()}  {entry}\n"

    with open(_get_run_log_path(), "a") as f:
        f.write(line + "\n")


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


# ── Bedrock client ────────────────────────────────────────────────────────────

def _get_client():
    global _client
    if _client is None:
        region = os.getenv("AWS_REGION", "us-east-1")
        _client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
    return _client


# ── Format converters: OpenAI ↔ Bedrock ──────────────────────────────────────

def _to_bedrock_messages(messages: list) -> tuple[list, list]:
    """Convert OpenAI-format messages to Bedrock Converse format.
    Returns (system_blocks, conversation_messages).
    """
    system_blocks = []
    bedrock_msgs  = []

    for msg in messages:
        role    = msg["role"]
        content = msg.get("content") or ""

        if role == "system":
            if content:
                system_blocks.append({"text": content})

        elif role == "user":
            bedrock_msgs.append({
                "role": "user",
                "content": [{"text": content}],
            })

        elif role == "assistant":
            blocks = []
            if content:
                blocks.append({"text": content})
            for tc in (msg.get("tool_calls") or []):
                try:
                    input_data = json.loads(tc["function"]["arguments"])
                except (json.JSONDecodeError, KeyError):
                    input_data = {}
                blocks.append({
                    "toolUse": {
                        "toolUseId": tc["id"],
                        "name":      tc["function"]["name"],
                        "input":     input_data,
                    }
                })
            if blocks:
                bedrock_msgs.append({"role": "assistant", "content": blocks})

        elif role == "tool":
            # Bedrock: tool results go in a user-role message
            result_block = {
                "toolResult": {
                    "toolUseId": msg.get("tool_call_id", ""),
                    "content":   [{"text": content}],
                }
            }
            if bedrock_msgs and bedrock_msgs[-1]["role"] == "user":
                bedrock_msgs[-1]["content"].append(result_block)
            else:
                bedrock_msgs.append({"role": "user", "content": [result_block]})

    return system_blocks, bedrock_msgs


def _to_bedrock_tools(tools: list) -> dict:
    return {
        "tools": [
            {
                "toolSpec": {
                    "name":        t["function"]["name"],
                    "description": t["function"].get("description", ""),
                    "inputSchema": {"json": t["function"].get("parameters", {})},
                }
            }
            for t in tools
        ]
    }


def _from_bedrock_response(response: dict) -> _Message:
    blocks     = response.get("output", {}).get("message", {}).get("content", [])
    text_parts = []
    tool_calls = []

    for block in blocks:
        if "text" in block:
            text_parts.append(block["text"])
        elif "toolUse" in block:
            tu = block["toolUse"]
            tool_calls.append(_ToolCall(
                id=tu["toolUseId"],
                name=tu["name"],
                arguments=json.dumps(tu.get("input", {})),
            ))

    return _Message(
        content    = "\n".join(text_parts) if text_parts else None,
        tool_calls = tool_calls if tool_calls else None,
    )


# ── Public API (same interface as before) ─────────────────────────────────────

def chat(
    messages: list,
    tools: Optional[list] = None,
    model: str = MODEL_STRONG,
) -> _Message:
    global _request_counter
    _request_counter += 1
    req_num = _request_counter

    system_blocks, bedrock_msgs = _to_bedrock_messages(messages)

    kwargs: dict = {
        "modelId":        model,
        "messages":       bedrock_msgs,
        "inferenceConfig": {"temperature": 0.0},
    }
    if system_blocks:
        kwargs["system"] = system_blocks
    if tools:
        kwargs["toolConfig"] = _to_bedrock_tools(tools)

    last_msg     = messages[-1] if messages else {}
    last_preview = str(last_msg.get("content") or "")[:200]
    tool_names   = [t["function"]["name"] for t in (tools or [])]

    _write_log({
        "event":               "request",
        "req":                 req_num,
        "ts":                  datetime.now(timezone.utc).isoformat(),
        "model":               model,
        "messages_in_context": len(messages),
        "available_tools":     tool_names,
        "last_message_role":   last_msg.get("role", "?"),
        "last_message_preview": last_preview,
    })
    print(f"   [llm #{req_num}] → {model}  ({len(messages)} msgs in context)")

    for attempt in range(5):
        try:
            t0       = time.time()
            response = _get_client().converse(**kwargs)
            elapsed  = round(time.time() - t0, 2)

            usage         = response.get("usage", {})
            input_tokens  = usage.get("inputTokens",  0)
            output_tokens = usage.get("outputTokens", 0)

            msg = _from_bedrock_response(response)

            if msg.tool_calls:
                action         = f"tool_call → {msg.tool_calls[0].function.name}"
                action_preview = msg.tool_calls[0].function.arguments[:200]
            else:
                action         = "text_response"
                action_preview = (msg.content or "")[:200]

            _write_log({
                "event":         "response",
                "req":           req_num,
                "ts":            datetime.now(timezone.utc).isoformat(),
                "elapsed_s":     elapsed,
                "input_tokens":  input_tokens,
                "output_tokens": output_tokens,
                "stop_reason":   response.get("stopReason", ""),
                "action":        action,
                "action_preview": action_preview,
            })
            print(f"   [llm #{req_num}] ← {action}  ({input_tokens}→{output_tokens} tokens, {elapsed}s)")

            _log_usage(model, input_tokens, output_tokens)
            return msg

        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code in ("ThrottlingException", "ServiceUnavailableException", "ModelNotReadyException"):
                delay = 30 * (attempt + 1)
                _write_log({"event": "throttle", "req": req_num, "attempt": attempt + 1, "wait_s": delay})
                print(f"   [llm #{req_num}] throttled — waiting {delay}s (attempt {attempt + 1}/5)...")
                time.sleep(delay)
            elif code == "ModelErrorException":
                # Nova model occasionally produces a malformed toolUse block; short retry usually clears it
                delay = 5 * (attempt + 1)
                _write_log({"event": "throttle", "req": req_num, "attempt": attempt + 1, "wait_s": delay,
                            "ts": datetime.now(timezone.utc).isoformat()})
                print(f"   [llm #{req_num}] ModelErrorException (malformed toolUse) — retrying in {delay}s (attempt {attempt + 1}/5)...")
                time.sleep(delay)
            else:
                _write_log({"event": "error", "req": req_num, "error": str(e)})
                raise

    raise RuntimeError("Failed after 5 retries due to ModelErrorException or throttling")


def extract(
    prompt: str,
    system: Optional[str] = None,
    model: str = MODEL_FAST,
) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    msg = chat(messages, model=model)
    return (msg.content or "").strip()
