"""
Memory containers for the agent.

AgentMemory  — per-company working state (message history, final result).
BatchProgress — persists batch index across runs.
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

    def add_tool_result(self, tool_call_id: str, name: str, content: str) -> None:
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
