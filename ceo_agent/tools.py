"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Implements tool functions (SEC EDGAR, web search, Wikipedia) and OpenAI function-calling schemas used by the CEO agent.
"""

import re
import time
import json
import requests
from urllib.parse import quote
from typing import Optional

from . import llm
from . import utils

_SEC_HEADERS = {
    "User-Agent": "CEOResearch jyothirmai@mhktechinc.com",
    "Accept-Encoding": "gzip, deflate",
}
_session = requests.Session()
_session.headers.update(_SEC_HEADERS)


# ── Private SEC helpers ──────────────────────────────────────────────────────

def _sec_get(url: str, host: Optional[str] = None) -> Optional[requests.Response]:
    time.sleep(0.15)
    try:
        headers = dict(_SEC_HEADERS)
        if host:
            headers["Host"] = host
        r = _session.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        return r
    except Exception:
        return None


def _download_filing(url: str) -> Optional[str]:
    try:
        r = _session.get(url, timeout=30, stream=True)
        r.raise_for_status()
        content = ""
        for chunk in r.iter_content(chunk_size=16384, decode_unicode=True):
            if chunk:
                content += chunk
                if len(content) > 2_000_000:
                    break
        return content
    except Exception:
        return None


def _build_filing_url(cik: str, accession: str, document: str) -> str:
    acc_clean = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{acc_clean}/{document}"


def _parse_filing_entries(data: dict, cik: str) -> list:
    result = []
    forms = data.get("form", [])
    dates = data.get("filingDate", [])
    accessions = data.get("accessionNumber", [])
    docs = data.get("primaryDocument", [])
    items_list = data.get("items", [])
    for i, form in enumerate(forms):
        if form in ("8-K", "8-K/A"):
            result.append({
                "form": form,
                "date": dates[i] if i < len(dates) else None,
                "accession": accessions[i] if i < len(accessions) else None,
                "document": docs[i] if i < len(docs) else None,
                "items": items_list[i] if i < len(items_list) else "",
                "cik": cik,
            })
    return result


def _collect_8k_filings(data: dict, cik: str) -> list:
    filings = _parse_filing_entries(data.get("filings", {}).get("recent", {}), cik)
    for file_info in data.get("filings", {}).get("files", []):
        fname = file_info.get("name")
        if fname:
            resp = _sec_get(f"https://data.sec.gov/submissions/{fname}", host="data.sec.gov")
            if resp:
                try:
                    filings.extend(_parse_filing_entries(resp.json(), cik))
                except Exception:
                    pass
    return sorted(filings, key=lambda x: x.get("date", ""))


def _extract_ceo_change_via_llm(
    item_text: str, filing_date: str, company_name: str
) -> Optional[dict]:
    """Use GPT-4o-mini to parse Item 5.02 text into a structured dict."""
    prompt = f"""Analyze this Item 5.02 section from an 8-K filing for "{company_name}" (filed {filing_date}).

Extract ONLY company-level Chief Executive Officer (CEO) changes.
Ignore: CFO, COO, President (unless also CEO), division CEO, subsidiary CEO.

TEXT:
\"\"\"
{item_text[:8000]}
\"\"\"

Respond with JSON only — no other text:
{{
  "has_ceo_change": true or false,
  "new_ceo_name": "Full Name" or null,
  "new_ceo_date": "YYYY-MM-DD" or null,
  "departing_ceo_name": "Full Name" or null,
  "departing_ceo_date": "YYYY-MM-DD" or null,
  "served_since": "YYYY-MM-DD or YYYY" or null
}}

Rules:
- Full names only (First + Last), no honorifics
- Prefer the explicit effective date from the text over the filing date {filing_date}
- Use filing date {filing_date} only if no effective date is stated in the text
- served_since = when the departing CEO first became CEO, if mentioned"""

    response = llm.extract(prompt)
    try:
        m = re.search(r'\{.*\}', response, re.DOTALL)
        if not m:
            return None
        result = json.loads(m.group(0))
        if not result.get("has_ceo_change"):
            return None
        # Sanity check: at least one significant word from either name must appear in the text.
        # Use any word >= 4 chars (catches partial/middle-name matches, not just last names).
        text_lower = item_text.lower()
        for field in ("new_ceo_name", "departing_ceo_name"):
            name = result.get(field) or ""
            if not name or len(name) < 4:
                continue
            for word in name.split():
                if len(word) >= 4 and word.lower().rstrip('.') in text_lower:
                    return result
        # No name word found in text — reject to avoid hallucinations
        return None
    except (json.JSONDecodeError, KeyError):
        return None


# ── Tool: fetch_sec_8k ───────────────────────────────────────────────────────

def fetch_sec_8k(cik: str, company_name: str, ticker: str) -> str:
    """Fetch and parse all 8-K Item 5.02 CEO-change filings. Returns a human-readable summary."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = _sec_get(url, host="data.sec.gov")
    if not resp:
        return "ERROR: Could not fetch SEC submissions data."

    data = resp.json()
    # Update company name from SEC if it differs
    sec_name = data.get("name", company_name)
    all_filings = _collect_8k_filings(data, cik)

    ceo_changes = []
    scanned = 0
    for filing in all_filings:
        if (filing.get("date") or "") < "2000-01-01":
            continue

        # Pre-filter: skip if items field exists and doesn't mention 5.02
        items_field = filing.get("items", "").lower()
        if items_field and "5.02" not in items_field:
            continue

        filing_url = _build_filing_url(cik, filing["accession"], filing["document"])
        content = _download_filing(filing_url)
        if not content or len(content) < 500:
            continue

        # Quick text-level pre-filter (faster than full parse)
        norm = re.sub(r'<[^>]+>', ' ', content.lower())
        norm = norm.replace('&nbsp;', ' ').replace('&#160;', ' ')
        norm = re.sub(r'\s+', ' ', norm)
        if not (("5.02" in norm or "item 5.02" in norm) and
                ("chief executive officer" in norm or
                 "principal executive officer" in norm or
                 " ceo" in norm)):
            continue

        item_text = utils.extract_item_502(content)
        if not item_text:
            continue

        scanned += 1
        change = _extract_ceo_change_via_llm(item_text, filing["date"], sec_name)
        if change:
            change["filing_date"] = filing["date"]
            change["filing_url"] = filing_url
            ceo_changes.append(change)

    if not ceo_changes:
        return (
            f"Company (SEC name): {sec_name}\n"
            f"Scanned {scanned} CEO-related 8-K filing(s). No CEO changes found in Item 5.02."
        )

    lines = [
        f"Company (SEC name): {sec_name}",
        f"Found {len(ceo_changes)} CEO transition(s) in 8-K filings:\n",
    ]
    for c in ceo_changes:
        lines.append(f"Filing date: {c['filing_date']}")
        if c.get("new_ceo_name"):
            lines.append(f"  New CEO    : {c['new_ceo_name']} (effective: {c.get('new_ceo_date')})")
        if c.get("departing_ceo_name"):
            lines.append(
                f"  Departed   : {c['departing_ceo_name']} "
                f"(effective: {c.get('departing_ceo_date')}, "
                f"served since: {c.get('served_since')})"
            )
        lines.append(f"  URL        : {c['filing_url']}")
        lines.append("")

    return "\n".join(lines)


# ── Tool: fetch_annual_filing ────────────────────────────────────────────────

def _extract_exec_section(text: str) -> str:
    """Pull the executive-officers or CEO section from a 10-K / DEF 14A.

    Strategy:
    1. Find ALL occurrences of "chief executive officer" in the document.
    2. Pick the occurrence inside a table/list of executives (identified by a
       nearby age number pattern like '  51  ' or 'Age' column header).
    3. Return a 5000-char window centred on that hit.
    4. If no such occurrence, fall back to the first "executive officers"
       section heading and widen the window to 12000 chars.
    """
    text_lower = text.lower()

    # Step 1: find all "chief executive officer" positions
    ceo_positions = []
    pos = 0
    while True:
        idx = text_lower.find("chief executive officer", pos)
        if idx == -1:
            break
        ceo_positions.append(idx)
        pos = idx + 1

    # Step 2: prefer a hit that has a nearby age indicator (executive table row)
    for idx in ceo_positions:
        window = text[max(0, idx - 1500): idx + 2000]
        # Typical executive table has " 45 " or " 52 " or "Age" near CEO title
        if re.search(r'\b(Age|\d{2})\b', window):
            start = max(0, idx - 1500)
            return text[start: start + 5000]

    # Step 3: any CEO mention — return wide window
    if ceo_positions:
        idx = ceo_positions[0]
        start = max(0, idx - 500)
        return text[start: start + 5000]

    # Step 4: fall back to "executive officers" section header with wider window
    section_kws = [
        "executive officers of the registrant",
        "information about our executive officers",
        "executive officers and directors",
        "executive officers",
        "principal executive officer",
    ]
    for kw in section_kws:
        idx = text_lower.find(kw)
        if idx != -1:
            start = max(0, idx - 200)
            return text[start: start + 12000]

    # Last resort: middle third of the document
    mid = len(text) // 3
    return text[mid: mid + 6000]


def fetch_annual_filing(cik: str, company_name: str) -> str:
    """Fetch the most recent 10-K or DEF 14A and extract the current CEO's name."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = _sec_get(url, host="data.sec.gov")
    if not resp:
        return "ERROR: Could not fetch SEC submissions data."

    data = resp.json()
    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    docs = recent.get("primaryDocument", [])

    # Include 20-F (foreign annual report) and 40-F (Canadian) alongside domestic forms
    ANNUAL_FORMS = ("10-K", "10-K/A", "DEF 14A", "20-F", "40-F")

    for i, form in enumerate(forms):
        if form not in ANNUAL_FORMS:
            continue
        accession = accessions[i] if i < len(accessions) else None
        document = docs[i] if i < len(docs) else None
        filing_date = dates[i] if i < len(dates) else None
        if not accession or not document:
            continue

        filing_url = _build_filing_url(cik, accession, document)
        time.sleep(0.12)
        content = _download_filing(filing_url)
        if not content or len(content) < 500:
            continue

        text = utils.clean_html(content)
        # Extract executive section — do NOT naively truncate to :8000
        exec_section = _extract_exec_section(text)

        prompt = f"""This is a {form} SEC filing for "{company_name}" (filed {filing_date}).

Find the name of the Chief Executive Officer (CEO) of {company_name}.
Look in: officer/director tables, "Executive Officers" section, signature block, cover page.

TEXT:
\"\"\"{exec_section}\"\"\"

Return ONLY the CEO's full name (First Last), no honorifics. If not found, return "NOT_FOUND"."""

        response = llm.extract(prompt).strip()
        if "NOT_FOUND" in response.upper() or len(response) > 80:
            continue

        name = utils.extract_name_from_response(response)
        if not name:
            continue

        return (
            f"Current CEO from {form} (filed {filing_date}): {name}\n"
            f"Source URL: {filing_url}"
        )

    return "Could not identify current CEO from annual filings."


# ── Tool: search_web ─────────────────────────────────────────────────────────

_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _search_duckduckgo(query: str) -> list[str]:
    """Try DuckDuckGo HTML search. Returns list of formatted result strings, or []."""
    url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
    for attempt in range(2):
        if attempt:
            time.sleep(8)
        try:
            resp = _session.get(url, timeout=15, headers={"User-Agent": _BROWSER_UA})
        except Exception:
            return []
        if resp.status_code != 200:
            continue
        text = resp.text
        snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', text, re.DOTALL)
        titles   = re.findall(r'result__title[^>]*>.*?<a[^>]*>(.*?)</a>', text, re.DOTALL)
        urls_f   = re.findall(r'class="result__url"[^>]*>(.*?)</(?:a|span)>', text, re.DOTALL)
        results = []
        for i, snippet in enumerate(snippets[:8]):
            clean_s = re.sub(r'<[^>]+>', '', snippet).strip()
            title   = re.sub(r'<[^>]+>', '', titles[i]).strip() if i < len(titles) else ""
            r_url   = re.sub(r'<[^>]+>', '', urls_f[i]).strip() if i < len(urls_f) else ""
            if clean_s:
                results.append(f"[{i+1}] {title}\n{r_url}\n{clean_s}")
        if results:
            return results
    return []


def _search_google_news(query: str) -> list[str]:
    """Fallback: Google News RSS — reliable and free."""
    try:
        r = _session.get(
            f"https://news.google.com/rss/search?q={quote(query)}&hl=en-US&gl=US&ceid=US:en",
            headers={"User-Agent": _BROWSER_UA},
            timeout=10,
        )
        if r.status_code != 200:
            return []
        titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>', r.text)
        links  = re.findall(r'<link>(https?://[^<]+)</link>', r.text)
        results = []
        for i, (t1, t2) in enumerate(titles[2:8]):  # skip feed title entries
            title = (t1 or t2).strip()
            link  = links[i] if i < len(links) else ""
            if title:
                results.append(f"[{i+1}] {title}\n{link}")
        return results
    except Exception:
        return []


def search_web(query: str) -> str:
    """Search the web for CEO information.

    Tries DuckDuckGo first; falls back to Google News RSS if DuckDuckGo is
    rate-limited (returns HTTP 202 bot-check page).
    """
    results = _search_duckduckgo(query)
    if not results:
        results = _search_google_news(query)
    time.sleep(0.3)
    if not results:
        return "No search results found."
    return "\n\n".join(results)


# ── Tool: search_sec_filings ─────────────────────────────────────────────────

def search_sec_filings(company_name: str, cik: str) -> str:
    """Search SEC EDGAR full-text index for proxy statements (DEF 14A) and 10-Ks
    that mention the CEO of this company.  Returns a list of filing URLs to fetch.
    Most reliable when web search fails or when 8-K Item 5.02 data is sparse.
    """
    cik_int = str(int(cik.lstrip("0") or "0"))
    results_out = []

    # Priority order: proxy first, then annual report (domestic and foreign)
    for form in ("DEF 14A", "10-K", "20-F", "40-F"):
        try:
            resp = _sec_get(
                f"https://data.sec.gov/submissions/CIK{cik}.json",
                host="data.sec.gov",
            )
            if not resp:
                continue
            data = resp.json()
            recent = data.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            dates = recent.get("filingDate", [])
            accessions = recent.get("accessionNumber", [])
            docs = recent.get("primaryDocument", [])
            for i, f in enumerate(forms):
                if f == form and i < len(accessions) and i < len(docs):
                    url = _build_filing_url(cik, accessions[i], docs[i])
                    results_out.append(
                        f"[{form}] {dates[i] if i < len(dates) else '?'}  {url}"
                    )
                    if len(results_out) >= 3:
                        break
            if results_out:
                break
        except Exception:
            continue

    if not results_out:
        return f"No DEF 14A or 10-K filings found for CIK {cik}."

    header = (
        f"Found SEC annual/proxy filings for {company_name} (CIK {cik_int}).\n"
        f"Call fetch_webpage on these URLs to extract the CEO name:\n\n"
    )
    return header + "\n".join(results_out)


# ── Tool: fetch_webpage ──────────────────────────────────────────────────────

def fetch_webpage(url: str, company_name: str = "") -> str:
    """Fetch a webpage and return cleaned text, focused on CEO-relevant sections."""
    try:
        # SEC URLs require the registered SEC User-Agent; all others use the browser UA
        is_sec = "sec.gov" in url
        headers = _SEC_HEADERS if is_sec else {"User-Agent": _BROWSER_UA}
        resp = _session.get(url, timeout=20, headers=headers)
        resp.raise_for_status()
    except Exception as e:
        return f"ERROR fetching {url}: {e}"

    text = utils.clean_html(resp.text)

    if len(text) <= 5000:
        return text

    # Extract CEO-relevant sections for long pages
    kws = ["chief executive officer", "ceo", "president", "appointed", "resigned",
           "founded", "succeeded", "named as ceo", "stepped down"]
    text_lower = text.lower()
    seen_starts: set = set()
    sections = []
    for kw in kws:
        pos = 0
        while len(sections) < 12:
            idx = text_lower.find(kw, pos)
            if idx == -1:
                break
            start = max(0, idx - 300)
            bucket = start // 400
            if bucket not in seen_starts:
                seen_starts.add(bucket)
                sections.append(text[start: min(len(text), idx + 900)])
            pos = idx + len(kw)

    if sections:
        header = f"[CEO-relevant excerpts from {url}]\n\n"
        return header + "\n---\n".join(sections[:8])

    return text[:5000]


# ── Tool: finalize_timeline ──────────────────────────────────────────────────

def finalize_timeline(timeline_json: str) -> str:
    """Validate the supplied JSON array and signal completion."""
    try:
        timeline = json.loads(timeline_json)
    except json.JSONDecodeError as e:
        return f"ERROR: Invalid JSON — {e}. Fix the JSON and call finalize_timeline again."

    if not isinstance(timeline, list):
        return "ERROR: timeline_json must be a JSON array (list), not an object."

    issues = []
    for i, entry in enumerate(timeline):
        if not isinstance(entry, dict):
            issues.append(f"Entry {i}: not a dict")
            continue
        name = entry.get("name", "")
        if not utils.is_valid_ceo_name(name):
            issues.append(f"Entry {i}: invalid or missing name '{name}'")
        if "start_date" not in entry:
            issues.append(f"Entry {i}: missing 'start_date'")
        if "end_date" not in entry:
            issues.append(f"Entry {i}: missing 'end_date'")
        if "source" not in entry:
            issues.append(f"Entry {i}: missing 'source'")

    if issues:
        return (
            "VALIDATION_ERRORS — fix these and call finalize_timeline again:\n"
            + "\n".join(f"  - {issue}" for issue in issues)
        )

    return f"FINALIZED: {len(timeline)} CEO entry/entries accepted."


# ── OpenAI Tool Schemas ──────────────────────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "fetch_sec_8k",
            "description": (
                "Fetch all SEC 8-K Item 5.02 CEO-change filings for a company. "
                "This is the most authoritative source — always call this first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cik": {"type": "string", "description": "10-digit zero-padded SEC CIK"},
                    "company_name": {"type": "string"},
                    "ticker": {"type": "string"},
                },
                "required": ["cik", "company_name", "ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_annual_filing",
            "description": (
                "Fetch the most recent 10-K or DEF 14A and extract the current CEO. "
                "Use when 8-K data is missing or as a last resort."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cik": {"type": "string", "description": "10-digit zero-padded SEC CIK"},
                    "company_name": {"type": "string"},
                },
                "required": ["cik", "company_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": (
                "Search the web (DuckDuckGo) for CEO information. "
                "Use for: missing start dates, pre-2004 CEO history, gaps in the timeline."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query, e.g. 'John Smith CEO Acme Corp appointed date'",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_webpage",
            "description": (
                "Fetch and read a specific webpage (Wikipedia, news article, company page) "
                "to extract CEO history details. Use URLs returned by search_web."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Full URL to fetch"},
                    "company_name": {
                        "type": "string",
                        "description": "Company name (used to focus extraction)",
                    },
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_sec_filings",
            "description": (
                "Search SEC EDGAR for DEF 14A proxy statements and 10-K annual filings "
                "for this company. Use when fetch_sec_8k found no CEO changes and "
                "web search is unavailable or returned nothing. "
                "Returns filing URLs — call fetch_webpage on them to read the CEO name."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string"},
                    "cik": {"type": "string", "description": "10-digit zero-padded CIK"},
                },
                "required": ["company_name", "cik"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finalize_timeline",
            "description": (
                "Submit the completed CEO timeline. Call this when you have all available "
                "information. The argument must be a valid JSON array."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "timeline_json": {
                        "type": "string",
                        "description": (
                            'JSON array: [{"name": "First Last", "start_date": "YYYY-MM-DD", '
                            '"end_date": "YYYY-MM-DD or Present", "source": "8-K|Web search|...", '
                            '"validation_url": "https://..."}]'
                        ),
                    },
                },
                "required": ["timeline_json"],
            },
        },
    },
]


# ── Dispatcher ───────────────────────────────────────────────────────────────

def dispatch(
    tool_name: str,
    arguments: dict,
    cik: str,
    company_name: str,
    ticker: str,
) -> str:
    """Route a tool call to the correct implementation."""
    if tool_name == "fetch_sec_8k":
        return fetch_sec_8k(
            cik=arguments.get("cik", cik),
            company_name=arguments.get("company_name", company_name),
            ticker=arguments.get("ticker", ticker),
        )
    if tool_name == "fetch_annual_filing":
        return fetch_annual_filing(
            cik=arguments.get("cik", cik),
            company_name=arguments.get("company_name", company_name),
        )
    if tool_name == "search_web":
        return search_web(query=arguments["query"])
    if tool_name == "fetch_webpage":
        return fetch_webpage(
            url=arguments["url"],
            company_name=arguments.get("company_name", company_name),
        )
    if tool_name == "search_sec_filings":
        return search_sec_filings(
            company_name=arguments.get("company_name", company_name),
            cik=arguments.get("cik", cik),
        )
    if tool_name == "finalize_timeline":
        return finalize_timeline(timeline_json=arguments["timeline_json"])
    return f"Unknown tool: {tool_name}"
