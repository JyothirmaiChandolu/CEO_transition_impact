"""
CEO Profile Agent — ReAct loop with OpenAI function calling.

Finds a verified headshot URL and biography for a given CEO.

KEY CONSTRAINT: Images are never passed to the LLM.
The agent sees only text metadata (URL strings, source domains, page titles)
and reasons from that to pick the most trustworthy image.
"""

import asyncio
import json
import logging
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from . import cache as profile_cache
from . import tools as tool_module

logger = logging.getLogger(__name__)

MAX_TURNS = 6
MODEL = "gpt-4o-mini"

_SYSTEM_PROMPT = """\
You are a CEO profile researcher. Your job is to find a verified headshot photo URL
and a short biography for a specific CEO.

RULES — follow strictly:
1. Always call wikipedia_search first. Wikipedia images are identity-verified by editors
   and are the most trustworthy source.
2. If Wikipedia returns an image_url, use it directly — no need to call validate_url.
   Wikipedia images are pre-verified.
3. If Wikipedia has NO image, call image_search. You will receive text metadata only
   (URL string, page_title, source_domain, name_in_title flag).
   YOU NEVER SEE THE ACTUAL IMAGE CONTENT. Choose based on text signals:
   - name_in_title=true means the CEO's name appears in the page title or URL — strongly prefer these
   - trusted_source=true means the domain is a major news outlet or company IR page
   - Reject any candidate where name_in_title=false AND trusted_source=false
4. For any image_url from image_search (not Wikipedia), call validate_url before finalizing.
   If validate_url returns ok=false, try the next candidate or call image_search with a different query.
5. If you genuinely cannot find a verified image after trying, finalize with image_url="" and image_source="none".
6. Never use an image unless text evidence confirms it is of THIS specific CEO.
7. Call finalize_profile when done. Do not explain your reasoning — just call the tools.
"""


class CEOProfileAgent:
    def __init__(self):
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        self._client = OpenAI(api_key=api_key)

    def _chat(self, messages: list) -> object:
        resp = self._client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tool_module.TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=0.0,
        )
        return resp.choices[0].message

    def _run_sync(self, name: str, company: str, transition_date: str = "", sector: str = "") -> dict:
        """ReAct loop — synchronous (runs inside asyncio.to_thread from API)."""
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Find a verified headshot and biography for:\n"
                f"Name: {name}\n"
                f"Company: {company}\n"
                f"Transition date: {transition_date or 'unknown'}\n"
                f"Sector: {sector or 'unknown'}\n\n"
                "Start with wikipedia_search."
            )},
        ]

        final: Optional[dict] = None

        for turn in range(1, MAX_TURNS + 1):
            msg = self._chat(messages)

            # Add assistant message
            entry: dict = {"role": "assistant", "content": msg.content}
            if msg.tool_calls:
                entry["tool_calls"] = [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ]
            messages.append(entry)

            if not msg.tool_calls:
                logger.warning(f"[ProfileAgent] Turn {turn}: agent stopped without finalizing")
                break

            for tc in msg.tool_calls:
                tool_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                logger.info(f"[ProfileAgent] Turn {turn}: {tool_name}({list(args.keys())})")
                result_str = tool_module.dispatch(tool_name, args, name, company)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tool_name,
                    "content": result_str,
                })

                if tool_name == "finalize_profile" and result_str.startswith("FINALIZED:"):
                    try:
                        final = json.loads(result_str[len("FINALIZED:"):])
                    except json.JSONDecodeError:
                        final = {}
                    logger.info(f"[ProfileAgent] Finalized after {turn} turn(s) — image_source={final.get('image_source')}")
                    return final

        # Fallback if agent never called finalize_profile
        return {"image_url": "", "bio": "", "source_url": "", "image_source": "none"}

    async def run(self, name: str, company: str, transition_date: str = "", sector: str = "") -> dict:
        """Async entry point. Checks cache first, then runs the agent."""
        if not name or name in ("Unknown", "ERROR", "NOT FOUND"):
            return {"image_url": "", "bio": "", "source_url": "", "image_source": "none"}

        cached = profile_cache.get(name, company)
        if cached:
            return cached

        result = await asyncio.to_thread(self._run_sync, name, company, transition_date, sector)
        profile_cache.set(name, company, result)
        return result


# Module-level singleton — created lazily so missing OPENAI_API_KEY doesn't crash import
_agent_instance: Optional[CEOProfileAgent] = None


def get_agent() -> CEOProfileAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = CEOProfileAgent()
    return _agent_instance
