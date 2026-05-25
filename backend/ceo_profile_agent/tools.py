"""
Tool implementations and OpenAI function schemas for the CEO profile agent.

CRITICAL: Image bytes are NEVER passed to the LLM.
image_search() returns only text metadata: URL string, source domain, page title,
and whether the CEO's name appears in that text. The LLM reasons about trust
purely from text signals.
"""

import asyncio
import json
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "CEOAnalysisTool/1.0 (research@mhktechinc.com)"}

# Domains whose images are more likely to be identity-verified
_TRUSTED_DOMAINS = [
    "wikipedia.org", "wikimedia.org",
    "bloomberg.com", "forbes.com", "reuters.com", "apnews.com",
    "businesswire.com", "prnewswire.com", "globenewswire.com",
    "wsj.com", "ft.com", "cnbc.com", "fortune.com",
    "ir.", "investor.", "newsroom.", "about.", "press.",
]


async def wikipedia_search(name: str, company: str) -> dict:
    """
    Search Wikipedia for the CEO. Returns text metadata only.
    image_url is a URL string — the image itself is never fetched or sent to the LLM.
    """
    queries = [
        f"{name} CEO {company}",
        f"{name} {company}",
        name,
    ]
    bio = image_url = url = page_title = None

    async with httpx.AsyncClient(timeout=10, headers=_HEADERS) as client:
        for q in queries:
            try:
                r = await client.get("https://en.wikipedia.org/w/api.php", params={
                    "action": "query", "list": "search",
                    "srsearch": q, "format": "json", "srlimit": 3,
                })
                results = r.json().get("query", {}).get("search", [])
                if results:
                    last = name.split()[-1].lower()
                    best = next((x for x in results if last in x["title"].lower()), results[0])
                    page_title = best["title"]
                    break
            except Exception:
                continue

        if page_title:
            try:
                pr = await client.get("https://en.wikipedia.org/w/api.php", params={
                    "action": "query", "titles": page_title,
                    "prop": "extracts|pageimages|info",
                    "exintro": True, "explaintext": True,
                    "pithumbsize": 800, "pilicense": "any",
                    "inprop": "url", "format": "json",
                })
                pages = pr.json().get("query", {}).get("pages", {})
                page = next(iter(pages.values()), {})
                raw = page.get("extract", "") or ""
                cut = raw.rfind(". ", 0, 1200)
                bio = raw[:cut + 1] if cut != -1 and len(raw) > 1200 else (raw or None)
                image_url = page.get("thumbnail", {}).get("source") if page.get("thumbnail") else None
                url = page.get("fullurl")
            except Exception as e:
                logger.warning(f"Wikipedia page fetch failed for '{name}': {e}")

    return {
        "found": bool(bio or image_url),
        "page_title": page_title,
        "bio": bio,
        "image_url": image_url,   # URL string only — never the image bytes
        "source_url": url,
        "image_source": "wikipedia" if image_url else None,
    }


async def image_search(name: str, company: str, query: str = "") -> list[dict]:
    """
    DDG image search. Returns text metadata ONLY — no image bytes, no image content.
    Each item: {image_url, source_domain, page_title, page_url, name_in_title, trusted_source}
    The LLM sees only these text fields to decide which image to use.
    """
    queries = [
        query or f"{name} CEO {company} official headshot",
        f"{name} {company} executive portrait",
        f'"{name}" CEO official photo',
    ]
    out: list[dict] = []
    last = name.split()[-1].lower()
    first = name.split()[0].lower()
    slug = name.lower().replace(" ", "-")

    # Require BOTH first+last name to appear, or the full slug — prevents false positives
    # from partial surname/firstname matches (e.g. "Florin" matching "Florin Popa")
    def _full_name_match(text: str) -> bool:
        t = text.lower()
        return (last in t and first in t) or slug in t

    try:
        try:
            from ddgs import DDGS  # type: ignore[import]
        except ImportError:
            from duckduckgo_search import DDGS  # type: ignore[import]
        for q in queries:
            raw = await asyncio.to_thread(lambda q=q: list(DDGS().images(q, max_results=15)))
            for img in raw:
                img_url = img.get("image", "")
                if not img_url:
                    continue
                page_url = img.get("url", "").lower()
                title = img.get("title", "").lower()
                img_lower = img_url.lower()
                name_in_page = _full_name_match(title) or _full_name_match(page_url) or _full_name_match(img_lower)
                trusted = any(d in page_url for d in _TRUSTED_DOMAINS)
                has_ext = any(img_lower.endswith(e) for e in (".jpg", ".jpeg", ".png", ".webp"))
                # Only include if full name confirmed OR from trusted domain
                if name_in_page or trusted:
                    out.append({
                        "image_url": img_url,
                        "source_domain": img.get("source", ""),
                        "page_title": img.get("title", ""),
                        "page_url": img.get("url", ""),
                        "name_in_title": name_in_page,
                        "trusted_source": trusted,
                        "has_valid_ext": has_ext,
                    })
            if len(out) >= 8:
                break
    except Exception as e:
        logger.warning(f"DDG image search failed for '{name}': {e}")

    # Best first: name-in-title + trusted > name-in-title > trusted
    out.sort(key=lambda x: (not x["name_in_title"], not x["trusted_source"], not x["has_valid_ext"]))
    return out[:6]


async def validate_url(url: str) -> dict:
    """HTTP HEAD check — confirms the URL resolves and content-type is image/*."""
    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True, headers=_HEADERS) as client:
            r = await client.head(url)
            ct = r.headers.get("content-type", "")
            return {"ok": r.status_code < 400 and "image" in ct, "status": r.status_code, "content_type": ct}
    except Exception as e:
        return {"ok": False, "status": None, "content_type": None, "error": str(e)}


# ── OpenAI function schemas ──────────────────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "wikipedia_search",
            "description": (
                "Search Wikipedia for the CEO. Returns bio text, image URL (as a string), "
                "and Wikipedia page URL. Wikipedia images are identity-verified — always try this first. "
                "The image URL is a plain string; do NOT treat it as image data."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name":    {"type": "string", "description": "Full CEO name"},
                    "company": {"type": "string", "description": "Company name"},
                },
                "required": ["name", "company"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "image_search",
            "description": (
                "Search DuckDuckGo for CEO headshots. Returns a list of candidates with TEXT METADATA only: "
                "image_url (string), source_domain, page_title, name_in_title (bool), trusted_source (bool). "
                "You NEVER see the actual image. Use name_in_title and trusted_source to pick the safest option. "
                "Only call this if wikipedia_search returned no image."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name":    {"type": "string"},
                    "company": {"type": "string"},
                    "query":   {"type": "string", "description": "Optional custom search query"},
                },
                "required": ["name", "company"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_url",
            "description": (
                "HTTP HEAD request to verify an image URL actually resolves and returns image content. "
                "Call this before finalizing any image URL from image_search (not needed for Wikipedia — those are pre-verified)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Image URL to validate"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finalize_profile",
            "description": "Submit the final result. Call this when you have found (or confirmed you cannot find) a verified image and bio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_url":   {"type": "string",  "description": "Verified headshot URL, or empty string if none found"},
                    "bio":         {"type": "string",  "description": "Short biography text, or empty string"},
                    "source_url":  {"type": "string",  "description": "Wikipedia or source page URL"},
                    "image_source": {"type": "string", "description": "wikipedia | duckduckgo | none"},
                },
                "required": ["image_url", "bio", "source_url", "image_source"],
            },
        },
    },
]


def dispatch(tool_name: str, args: dict, name: str, company: str) -> str:
    """Synchronous dispatcher — called inside asyncio.to_thread so uses asyncio.run()."""
    if tool_name == "wikipedia_search":
        result = asyncio.run(wikipedia_search(args.get("name", name), args.get("company", company)))
        return json.dumps(result)
    if tool_name == "image_search":
        result = asyncio.run(image_search(args.get("name", name), args.get("company", company), args.get("query", "")))
        return json.dumps(result)
    if tool_name == "validate_url":
        result = asyncio.run(validate_url(args["url"]))
        return json.dumps(result)
    if tool_name == "finalize_profile":
        return f"FINALIZED:{json.dumps(args)}"
    return f"Unknown tool: {tool_name}"
