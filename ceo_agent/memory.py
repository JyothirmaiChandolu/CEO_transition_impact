"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Defines memory containers for per-company agent state and persistent batch progress tracking across runs.
"""

import json
import os
from typing import Optional

AGENT_BATCH_PROGRESS_FILE = "sec_ceo_data/agent_batch_progress.json"


class AgentMemory:
    """Holds everything the agent needs for one company run."""

    def __init__(self, ticker: str, cik: str, company_name: str):
        self.ticker = ticker
        self.cik = cik
        self.company_name = company_name
        self.messages: list = []        # Full OpenAI message history
        self.final_timeline: list = []  # Written by finalize_timeline tool

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, msg) -> None:
        """Append an OpenAI ChatCompletionMessage to history."""
        entry: dict = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            entry["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
        self.messages.append(entry)

    _MAX_TOOL_RESULT_CHARS = 2500

    def add_tool_result(self, tool_call_id: str, name: str, content: str) -> None:
        if len(content) > self._MAX_TOOL_RESULT_CHARS:
            content = content[:self._MAX_TOOL_RESULT_CHARS] + "\n...[truncated]"
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": name,
            "content": content,
        })


class BatchProgress:
    """Read/write the agent batch progress file."""

    def __init__(self, path: str = AGENT_BATCH_PROGRESS_FILE):
        self.path = path

    def read(self) -> int:
        if os.path.exists(self.path):
            try:
                with open(self.path) as f:
                    return json.load(f).get("next_index", 0)
            except Exception:
                pass
        return 0

    def write(self, next_index: int, total: int) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump({"next_index": next_index, "total_tickers": total}, f, indent=2)
