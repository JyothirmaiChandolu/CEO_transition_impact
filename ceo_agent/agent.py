"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Implements the CEOAgent using a ReAct loop with OpenAI function calling to iteratively extract CEO transition histories.
"""

import json
import re
from datetime import datetime
from typing import Optional

from . import llm
from . import tools as tool_module
from . import prompts
from . import utils
from . memory import AgentMemory

MAX_TURNS = 25

class CEOAgent:
    def run_company(self, ticker: str, cik: str, company_name: str) -> list:
        """Run the full ReAct loop for one company. Returns the cleaned CEO timeline."""
        memory = AgentMemory(ticker=ticker, cik=cik, company_name=company_name)
        memory.messages = [
            {"role": "system", "content": prompts.build_system_prompt(ticker, company_name)},
        ]
        memory.add_user(prompts.build_user_prompt(ticker, cik, company_name))

        for turn in range(1, MAX_TURNS + 1):
            try:
                msg = llm.chat(memory.messages, tools=tool_module.TOOL_SCHEMAS)
            except Exception as e:
                print(f"   [turn {turn}] LLM error after all retries: {e} — aborting agent loop")
                break
            memory.add_assistant(msg)

            if not msg.tool_calls:
                # Agent produced a text response with no tool calls — shouldn't happen normally
                print(f"   [turn {turn}] Agent stopped without calling finalize_timeline")
                break

            finalized = False
            for tc in msg.tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                print(f"   [turn {turn}] → {name}({', '.join(f'{k}={repr(v)[:40]}' for k, v in args.items())})")

                result = tool_module.dispatch(
                    tool_name=name,
                    arguments=args,
                    cik=cik,
                    company_name=company_name,
                    ticker=ticker,
                )

                memory.add_tool_result(tc.id, name, result)

                if name == "finalize_timeline" and result.startswith("FINALIZED:"):
                    try:
                        memory.final_timeline = json.loads(args.get("timeline_json", "[]"))
                    except json.JSONDecodeError:
                        memory.final_timeline = []
                    finalized = True

            if finalized:
                print(f"   Finalized after {turn} turn(s)")
                break
        else:
            print(f"   WARNING: reached MAX_TURNS ({MAX_TURNS}) without finalizing")

        timeline = _post_process(memory.final_timeline, company_name)

        # If the agent returned nothing at all, try a direct emergency lookup
        if not timeline:
            print(f"   [FALLBACK] Agent returned empty timeline — trying emergency lookup...")
            timeline = _emergency_ceo_lookup(ticker, cik, company_name)
            timeline = _post_process(timeline, company_name)

        # Deterministic fallback: fill null start_dates with previous CEO's end_date
        _fill_null_start_dates(timeline)

        return timeline


# ── Fallback helpers ─────────────────────────────────────────────────────────

def _emergency_ceo_lookup(ticker: str, cik: str, company_name: str) -> list:
    """Direct tool calls (no LLM loop) to find at least one CEO when the agent returned empty."""
    # Try to get real company name from SEC if we only have ticker
    real_name = company_name if company_name != ticker else None
    if not real_name:
        try:
            import requests
            r = requests.get(
                f"https://data.sec.gov/submissions/CIK{cik}.json",
                headers={"User-Agent": "CEOResearch jyothirmai@mhktechinc.com"},
                timeout=10,
            )
            if r.status_code == 200:
                real_name = r.json().get("name", "") or ""
        except Exception:
            pass
    search_name = real_name or company_name

    # Try annual filing first (most reliable for current CEO)
    result = tool_module.fetch_annual_filing(cik, search_name)
    if "ERROR" not in result and "Could not" not in result:
        name_m = re.search(r':\s+([A-Z][a-zA-Z\s.\-]+?)\s*\n', result)
        url_m = re.search(r'Source URL:\s*(\S+)', result)
        if name_m:
            name = name_m.group(1).strip()
            if utils.is_valid_ceo_name(name):
                print(f"   [FALLBACK] Annual filing found CEO: {name}")
                return [{
                    "name": name,
                    "start_date": None,
                    "end_date": "Present",
                    "source": "Annual filing",
                    "validation_url": url_m.group(1) if url_m else "",
                }]

    # Try web search with multiple query strategies
    queries = [
        f'"{search_name}" CEO appointed site:businesswire.com OR site:prnewswire.com',
        f"{search_name} CEO history leadership",
        f"{ticker} CEO current 2024 2025",
        f'"{search_name}" "chief executive officer" appointed',
    ]
    for query in queries:
        snippets = tool_module.search_web(query)
        if "No search results" in snippets or "Search error" in snippets:
            continue
        prompt = (
            f"From these web search results about {search_name} ({ticker}):\n\n"
            f"{snippets[:4000]}\n\n"
            f"What is the full name of the current or most recent CEO of {search_name}?\n"
            f"Return ONLY the full name (First Last) or NOT_FOUND."
        )
        response = llm.extract(prompt)
        name = utils.extract_name_from_response(response)
        if name:
            print(f"   [FALLBACK] Web search found CEO: {name}")
            # Try to find a URL in snippets
            url_m = re.search(r'https?://\S+', snippets)
            return [{
                "name": name,
                "start_date": None,
                "end_date": "Present",
                "source": "Web search",
                "validation_url": url_m.group(0) if url_m else "",
            }]

    print(f"   [FALLBACK] Could not find any CEO for {ticker}")
    return []


def _fill_null_start_dates(timeline: list) -> None:
    """Deterministic fallback: set null start_date to previous CEO's end_date.

    This handles the common case where an 8-K captures a departure but the
    original appointment predates our records. We know at minimum they started
    by the time the next CEO left (or when they themselves departed).
    """
    for i, ceo in enumerate(timeline):
        if ceo.get("start_date"):
            continue
        # Use previous CEO's end_date as the lower bound
        if i > 0:
            prev_end = timeline[i - 1].get("end_date") or ""
            if prev_end and prev_end not in ("Present", "Unknown", "None", ""):
                ceo["start_date"] = prev_end
                ceo["start_date_estimated"] = True
                print(f"   [FILL] {ceo['name']}: start_date estimated as {prev_end} (prev CEO's end_date)")


# ── Post-processing ──────────────────────────────────────────────────────────

def _post_process(timeline: list, company_name: str) -> list:
    """Sort, deduplicate, fix end dates, and run sanity checks on the agent's output."""
    if not timeline:
        return []

    today = datetime.now().strftime("%Y-%m-%d")

    # Normalize all dates
    for ceo in timeline:
        sd = ceo.get("start_date") or ""
        ed = ceo.get("end_date") or ""
        if sd and sd not in ("Unknown", "None", ""):
            ceo["start_date"] = utils.normalize_date(sd)
        if ed and ed not in ("Present", "Unknown", "None", ""):
            ceo["end_date"] = utils.normalize_date(ed)

    # Remove entries entirely before 2000 (end_date < 2000)
    timeline = [
        c for c in timeline
        if not c.get("end_date")
        or c["end_date"] in ("Present", "Unknown")
        or c["end_date"] >= "2000-01-01"
    ]

    # Remove future start dates (data error)
    timeline = [
        c for c in timeline
        if not c.get("start_date")
        or c["start_date"] in ("Unknown", "None")
        or c["start_date"] <= today
    ]

    # Deduplicate: merge entries for the same person
    deduped: list = []
    for ceo in timeline:
        merged = False
        for existing in deduped:
            if utils.names_match(existing["name"], ceo["name"]):
                _merge_into(existing, ceo)
                merged = True
                break
        if not merged:
            deduped.append(ceo)
    timeline = deduped

    # Sort by start_date
    timeline.sort(key=lambda x: utils.sort_key(x.get("start_date")))

    # Fix end dates: each non-last CEO ends when the next one starts
    for i in range(len(timeline) - 1):
        next_start = timeline[i + 1].get("start_date") or ""
        curr_end = timeline[i].get("end_date") or ""
        if next_start and next_start not in ("Unknown", "None"):
            if not curr_end or curr_end == "Present" or curr_end > next_start:
                timeline[i]["end_date"] = next_start

    # Last CEO is current
    if timeline:
        last_end = timeline[-1].get("end_date") or ""
        if not last_end or (last_end != "Present" and last_end > today):
            timeline[-1]["end_date"] = "Present"

    # Chronological sanity: clear end_date that precedes start_date
    for ceo in timeline:
        sd = ceo.get("start_date") or ""
        ed = ceo.get("end_date") or ""
        if (sd and ed
                and ed not in ("Present", "Unknown", "None", "")
                and sd not in ("Unknown", "None", "")
                and ed < sd):
            print(f"   WARNING: {ceo['name']} end_date ({ed}) < start_date ({sd}) — clearing")
            ceo["end_date"] = None

    # Gap detection (informational only)
    for i in range(len(timeline) - 1):
        ed = timeline[i].get("end_date") or ""
        ns = timeline[i + 1].get("start_date") or ""
        if (ed and ns
                and ed not in ("Present", "Unknown")
                and ns not in ("Unknown", "None")
                and ns > ed):
            try:
                gap = int(ns[:4]) - int(ed[:4])
                if gap > 1:
                    print(
                        f"   WARNING: {gap}-year gap between "
                        f"{timeline[i]['name']} (ended {ed}) and "
                        f"{timeline[i+1]['name']} (started {ns})"
                    )
            except ValueError:
                pass

    return timeline


def _merge_into(existing: dict, incoming: dict) -> None:
    """Merge incoming CEO entry into existing (same person, different source)."""
    sd_e = existing.get("start_date") or ""
    sd_i = incoming.get("start_date") or ""
    if sd_i and (not sd_e or sd_e.startswith("Unknown")
                 or (sd_i < sd_e and not sd_i.startswith("Unknown"))):
        existing["start_date"] = sd_i

    ed_e = existing.get("end_date") or ""
    ed_i = incoming.get("end_date") or ""
    if ed_i == "Present":
        existing["end_date"] = "Present"
    elif ed_i and (not ed_e or ed_e == "Unknown"
                   or (ed_i > ed_e and ed_e != "Present")):
        existing["end_date"] = ed_i

    # Prefer 8-K source; keep longer name
    if incoming.get("source") == "8-K" and existing.get("source") != "8-K":
        existing["source"] = "8-K"
        existing["validation_url"] = incoming.get("validation_url")
    if len(incoming.get("name", "")) > len(existing.get("name", "")):
        existing["name"] = incoming["name"]
