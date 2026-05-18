"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Fetches SEC 8-K filings from validation URLs and extracts the Item 5.02 text section.
"""

import re
import time
import logging
import requests
from typing import Optional
from urllib.parse import urljoin, urlparse

from ceo_agent.utils import clean_html, extract_item_502

_HEADERS = {
    "User-Agent": "CEOReasonResearch jyothirmai@mhktechinc.com",
    "Accept-Encoding": "gzip, deflate",
}
_SESSION = requests.Session()
_SESSION.headers.update(_HEADERS)

_REQUEST_DELAY = 0.2   # seconds between SEC requests


def _get(url: str, timeout: int = 30) -> Optional[requests.Response]:
    time.sleep(_REQUEST_DELAY)
    try:
        r = _SESSION.get(url, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception:
        return None


def _is_index_page(url: str, html: str) -> bool:
    """Return True if this looks like an EDGAR filing index page, not the document itself."""
    return (
        "Archives/edgar" in url
        and ("-index.htm" in url.lower() or "index.htm" in url.lower())
    ) or (
        '<table' in html.lower()
        and 'filing summary' in html.lower()
    )


def _resolve_8k_document(index_url: str, html: str) -> Optional[str]:
    """
    Given an EDGAR index page HTML, find the URL of the actual 8-K document.
    Looks for .htm links that are not the index itself.
    """
    # Find all href links to .htm files
    links = re.findall(r'href=["\']([^"\']+\.htm[l]?)["\']', html, re.IGNORECASE)
    base = index_url.rsplit("/", 1)[0] + "/"

    for link in links:
        lower = link.lower()
        # Skip index pages and exhibits
        if "index" in lower or "ex" in lower.split("/")[-1][:3]:
            continue
        full = urljoin(base, link)
        return full

    # Fallback: first .htm that isn't the index itself
    for link in links:
        if "index" not in link.lower():
            full = urljoin(base, link)
            return full

    return None


def fetch_item_502(url: str, logger: logging.Logger, ticker: str = "", ceo_name: str = "") -> str:
    """
    Fetch a validation URL and return the Item 5.02 text.
    Returns empty string on failure.

    Steps:
      1. Fetch the URL.
      2. If it's an index page, resolve the actual 8-K document URL and fetch that.
      3. Extract the Item 5.02 section from the raw HTML.
      4. If no Item 5.02 section found, return the full cleaned text (truncated).
    """
    tag = f"[{ticker}] {ceo_name[:25]}"

    if not url or not url.startswith("http"):
        logger.debug(f"{tag} | fetch_item_502 | SKIP: no valid URL")
        return ""

    logger.debug(f"{tag} | fetch_item_502 | fetching {url}")
    resp = _get(url)
    if resp is None:
        logger.warning(f"{tag} | fetch_item_502 | FAILED to fetch {url}")
        return ""

    html = resp.text
    logger.debug(f"{tag} | fetch_item_502 | fetched {len(html):,} chars from {url}")

    # If we landed on an index page, resolve the real document
    if _is_index_page(url, html):
        doc_url = _resolve_8k_document(url, html)
        if doc_url:
            logger.debug(f"{tag} | fetch_item_502 | resolved document URL: {doc_url}")
            resp2 = _get(doc_url)
            if resp2:
                html = resp2.text
                logger.debug(f"{tag} | fetch_item_502 | fetched document: {len(html):,} chars")
            else:
                logger.warning(f"{tag} | fetch_item_502 | failed to fetch resolved doc {doc_url}")
        else:
            logger.warning(f"{tag} | fetch_item_502 | could not resolve document from index")

    # Extract Item 5.02
    section = extract_item_502(html)
    if section:
        # Trim to avoid flooding the LLM context
        trimmed = section[:6000]
        logger.debug(f"{tag} | fetch_item_502 | extracted Item 5.02 ({len(section):,} chars, trimmed to {len(trimmed):,})")
        return trimmed

    # Fallback: return cleaned full text, trimmed
    fallback = clean_html(html)[:4000]
    logger.debug(f"{tag} | fetch_item_502 | no Item 5.02 found; using full text fallback ({len(fallback):,} chars)")
    return fallback
