"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Extracts CEO transition history using a two-tier approach: SEC EDGAR 8-K filings for exact dates and Wikipedia scraping as fallback.
"""

import requests
import time
import json
import re
import os
import csv
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import anthropic
from dotenv import load_dotenv

load_dotenv()

RUSSELL2000_CSV = "output.csv"
BATCH_SIZE = 100
BATCH_PROGRESS_FILE = "sec_ceo_data/batch_progress.json"

SEC_HEADERS = {
    "User-Agent": "CEOResearch nagamanimhk@gmail.com",
    "Accept-Encoding": "gzip, deflate",
}

CLAUDE_MODEL_MAIN = "claude-sonnet-4-5-20250929"  # Tier 1: 8-K (needs accuracy)
CLAUDE_MODEL_CHEAP = "claude-haiku-4-5-20251001"  # Tier 2: cheaper for Wikipedia extraction
START_YEAR = 2000


class CEOExtractor:
    """2-Tier CEO data extraction: 8-K → Wikipedia scraping."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(SEC_HEADERS)
        self.cik_cache = {}
        self.client = None
        self._init_claude()

    def _init_claude(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in .env file")
        self.client = anthropic.Anthropic(api_key=api_key)
        print(f"Claude API ready (Tier1: {CLAUDE_MODEL_MAIN}, Tier2: {CLAUDE_MODEL_CHEAP})")

    def query_claude(self, prompt: str, max_tokens: int = 1024, use_cheap: bool = False) -> Optional[str]:
        model = CLAUDE_MODEL_CHEAP if use_cheap else CLAUDE_MODEL_MAIN
        try:
            message = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"      Claude API error: {e}")
            return None

    def _sec_request(self, url: str, host: str = None) -> Optional[requests.Response]:
        """Make a rate-limited SEC request."""
        time.sleep(0.15)
        try:
            headers = dict(SEC_HEADERS)
            if host:
                headers["Host"] = host
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"      SEC request error: {url[:80]}... -> {e}")
            return None

    # ══════════════════════════════════════════════════
    # STEP 1: Ticker → CIK
    # ══════════════════════════════════════════════════
    def get_cik(self, ticker: str) -> Optional[str]:
        ticker_upper = ticker.upper().replace(".", "-")
        if ticker_upper in self.cik_cache:
            return self.cik_cache[ticker_upper]

        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            response = self._sec_request(url)
            if not response:
                return None
            data = response.json()

            for entry in data.values():
                t = entry.get("ticker", "").upper()
                cik = str(entry.get("cik_str", "")).zfill(10)
                self.cik_cache[t] = cik

            # Try with and without dot/dash
            return (self.cik_cache.get(ticker.upper()) or
                    self.cik_cache.get(ticker.upper().replace(".", "-")) or
                    self.cik_cache.get(ticker.upper().replace("-", ".")))
        except Exception as e:
            print(f"   Error fetching CIK: {e}")
            return None

    # ══════════════════════════════════════════════════
    # STEP 2: CIK → ALL 8-K Filings (2000+)
    # ══════════════════════════════════════════════════
    def get_all_8k_filings(self, cik: str) -> Tuple[str, List[Dict]]:
        company_name = "Unknown"
        all_8k = []

        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        response = self._sec_request(url, host="data.sec.gov")
        if not response:
            return company_name, []

        data = response.json()
        company_name = data.get("name", "Unknown")

        # Recent filings
        recent = data.get("filings", {}).get("recent", {})
        all_8k.extend(self._extract_8k_entries(recent, cik))

        # Archived filings (older)
        files = data.get("filings", {}).get("files", [])
        for file_info in files:
            file_name = file_info.get("name")
            if file_name:
                archive_url = f"https://data.sec.gov/submissions/{file_name}"
                archive_resp = self._sec_request(archive_url, host="data.sec.gov")
                if archive_resp:
                    try:
                        archive_data = archive_resp.json()
                        all_8k.extend(self._extract_8k_entries(archive_data, cik))
                    except Exception:
                        pass

        # Filter: only 2000+ and sort oldest first
        all_8k = [f for f in all_8k if f.get("date", "") >= f"{START_YEAR}-01-01"]
        all_8k.sort(key=lambda x: x.get("date", ""))
        return company_name, all_8k

    def _extract_8k_entries(self, data: Dict, cik: str) -> List[Dict]:
        filings = []
        forms = data.get("form", [])
        dates = data.get("filingDate", [])
        accessions = data.get("accessionNumber", [])
        primary_docs = data.get("primaryDocument", [])
        items_list = data.get("items", [])

        for i, form in enumerate(forms):
            if form in ("8-K", "8-K/A"):
                # Pre-filter by items field if available
                items = items_list[i] if i < len(items_list) else ""
                filings.append({
                    "form": form,
                    "date": dates[i] if i < len(dates) else None,
                    "accession": accessions[i] if i < len(accessions) else None,
                    "document": primary_docs[i] if i < len(primary_docs) else None,
                    "items": items,
                    "cik": cik,
                })
        return filings

    # ══════════════════════════════════════════════════
    # STEP 3: Download & Clean Filing Content
    # ══════════════════════════════════════════════════
    def build_filing_url(self, cik: str, accession: str, document: str) -> str:
        acc_clean = accession.replace("-", "")
        return f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{acc_clean}/{document}"

    def build_index_url(self, cik: str, accession: str) -> str:
        acc_clean = accession.replace("-", "")
        return f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{acc_clean}/"

    def download_filing(self, url: str, max_size: int = 2_000_000) -> Optional[str]:
        try:
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            content = ""
            for chunk in response.iter_content(chunk_size=16384, decode_unicode=True):
                if chunk:
                    content += chunk
                    if len(content) > max_size:
                        break
            return content
        except Exception:
            return None

    def clean_html(self, html: str) -> str:
        """Remove HTML tags, scripts, styles and normalize whitespace."""
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        # Remove Wikipedia CSS noise (mw-parser-output rules that leak into text)
        text = re.sub(r'\.mw-parser-output[^}]*\}', ' ', text)
        text = re.sub(r'@media[^}]*\{[^}]*\}', ' ', text, flags=re.DOTALL)
        # Replace <br>, <p>, <div> with newlines for better text extraction
        text = re.sub(r'<br\s*/?\s*>|</p>|</div>|</tr>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        # Clean entities
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
        text = text.replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&quot;', '"').replace('&#8217;', "'")
        text = text.replace('&rsquo;', "'").replace('&ldquo;', '"').replace('&rdquo;', '"')
        # Decode numeric HTML entities (&#147; &#148; etc.)
        text = re.sub(r'&#\d+;', ' ', text)
        text = re.sub(r'&[a-zA-Z]+;', ' ', text)  # catch any remaining HTML entities
        # Normalize whitespace but keep newlines
        text = re.sub(r'[^\S\n]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()

    def extract_item_502(self, content: str) -> Optional[str]:
        """Extract Item 5.02 section from 8-K filing. Handles multiple formats."""
        text = self.clean_html(content)

        # Multiple regex patterns for different 8-K formats (ordered by specificity)
        patterns = [
            # Standard: Item 5.02 ... next Item X.XX
            r'(Item\s*5\.0*2\b.*?)(?=Item\s*\d+\.\d+|\Z)',
            # ALL CAPS header: ITEM 5.02 ... next ITEM
            r'(ITEM\s*5\.0*2\b.*?)(?=ITEM\s*\d+\.\d+|\Z)',
            # Section header: "Section 5 - Item 5.02"
            r'(Section\s*5\s*[-–—:]\s*Item\s*5\.0*2\b.*?)(?=Section\s*\d+|Item\s*\d+\.\d+|\Z)',
            # Parenthetical format: "Item 5.02(b)" or "Item 5.02(e)"
            r'(Item\s*5\.0*2\s*\([a-z]\).*?)(?=Item\s*\d+\.\d+|\Z)',
            # Bold/underline cleaned: "Item 5.02 Departure of Directors..."
            r'(Item\s*5\.0*2\s+Departure.*?)(?=Item\s*\d+\.\d+|ITEM\s*\d+|\Z)',
            # Non-breaking space: "Item\xa05.02"
            r'(Item\s*5[\.\s\xa0]+0*2\b.*?)(?=Item\s*\d+\.\d+|\Z)',
            # Old pre-2004 format: Item 6 (Changes in Registrant's Officers)
            r'(Item\s*6\b[^0-9].*?(?:Chief Executive|CEO).*?)(?=Item\s*\d+|\Z)',
            # "5.02" alone as a section number (some filings use just the number)
            r'(5\.0*2\s*[-–—:.]?\s*Departure.*?)(?=\d+\.\d+\s*[-–—:.]?\s*[A-Z]|\Z)',
        ]

        for pattern in patterns:
            # Find ALL matches and pick the longest (skip TOC entries)
            best_section = ""
            for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
                section = match.group(1).strip()
                if len(section) > len(best_section):
                    best_section = section
            if len(best_section) > 100:  # Must have meaningful content
                return best_section[:12000]

        # Fallback: look for CEO change keywords in the whole text
        text_lower = text.lower()
        ceo_keywords = ['chief executive officer', 'principal executive officer']
        action_keywords = ['appoint', 'resign', 'depart', 'succeed', 'elect',
                          'terminat', 'step down', 'retire', 'named', 'promoted']

        has_ceo = any(k in text_lower for k in ceo_keywords)
        has_action = any(k in text_lower for k in action_keywords)

        if has_ceo and has_action:
            # Return a generous window around the first CEO mention
            for kw in ceo_keywords:
                idx = text_lower.find(kw)
                if idx != -1:
                    start = max(0, idx - 2000)
                    end = min(len(text), idx + 5000)
                    return text[start:end]

        return None

    # ══════════════════════════════════════════════════
    # TIER 1: Extract CEO from 8-K Item 5.02
    # ══════════════════════════════════════════════════
    def extract_ceo_from_8k(self, item_text: str, filing_date: str,
                            company_name: str) -> Optional[Dict]:
        """Send Item 5.02 text to Claude to extract CEO change details."""

        prompt = f"""You are analyzing an Item 5.02 section from an 8-K filing for "{company_name}" filed on {filing_date}.

TASK: Extract ONLY Chief Executive Officer (CEO) changes for the ENTIRE company.

TEXT:
\"\"\"
{item_text[:10000]}
\"\"\"

RULES:
1. ONLY extract if the person holds the title "Chief Executive Officer" or "Principal Executive Officer" of THE ENTIRE COMPANY
2. DO NOT extract: CFO, COO, President (unless also CEO), VP, Director, Division CEO, Regional CEO, Group CEO, subsidiary CEO
3. Extract the EXACT effective date mentioned in the text (not the filing date). Look for phrases like "effective [date]", "commencing [date]", "beginning [date]", "as of [date]"
4. If only a filing date is available and no effective date is explicitly stated, use "{filing_date}" as the date
5. For departing CEO: look for resignation date, termination date, "will step down on [date]"
6. For new CEO: look for appointment date, "will assume the role on [date]", "effective [date]"
7. If the text mentions the departing CEO "has served as CEO since [year/date]", extract that as their start information
8. Names MUST be full names (First + Last). Do NOT use honorifics (Mr., Dr., Ms., Mrs.). If you can only find a last name or a title + last name, return null for that name field.

Respond ONLY with this exact JSON format:
{{
  "has_ceo_change": true or false,
  "change_type": "appointment" or "departure" or "transition" or "none",
  "new_ceo": {{
    "name": "Full Name" or null,
    "effective_date": "YYYY-MM-DD" or null
  }},
  "departing_ceo": {{
    "name": "Full Name" or null,
    "effective_date": "YYYY-MM-DD" or null,
    "served_since": "YYYY-MM-DD or YYYY" or null
  }}
}}

Respond with ONLY the JSON, no other text."""

        response_text = self.query_claude(prompt, max_tokens=500)
        if not response_text:
            return None

        # Parse JSON
        json_text = re.sub(r'```json\s*|\s*```', '', response_text)
        json_match = re.search(r'\{.*\}', json_text, re.DOTALL)
        if not json_match:
            return None

        try:
            result = json.loads(json_match.group(0))
            if not result.get("has_ceo_change"):
                return None

            # Validate: at least one CEO name must be in the text
            text_lower = item_text.lower()
            new_name = result.get("new_ceo", {}).get("name") or ""
            old_name = result.get("departing_ceo", {}).get("name") or ""

            has_valid_name = False
            if new_name and len(new_name) >= 3:
                # Check last name appears in text
                last_name = new_name.split()[-1].lower()
                if last_name in text_lower:
                    has_valid_name = True
            if old_name and len(old_name) >= 3:
                last_name = old_name.split()[-1].lower()
                if last_name in text_lower:
                    has_valid_name = True

            if not has_valid_name:
                return None

            return result
        except json.JSONDecodeError:
            return None

    # ══════════════════════════════════════════════════
    # TIER 2: Wikipedia SCRAPING (actual web scrape)
    # ══════════════════════════════════════════════════
    def get_wikipedia_ceo_data(self, ticker: str, company_name: str) -> List[Dict]:
        """Fallback: SCRAPE Wikipedia page for CEO history."""
        print(f"   [TIER 2] Scraping Wikipedia...")

        # Clean company name for Wikipedia search
        clean_name = company_name.replace(",", "").replace("/", " ").strip()
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        # Short name without suffixes
        short_name = company_name.replace(" Inc.", "").replace(" Inc", "")
        short_name = short_name.replace(" Corp.", "").replace(" Corp", "")
        short_name = short_name.replace(" plc", "").replace(",", "").replace("/", " ").strip()
        short_name = re.sub(r'\s+', ' ', short_name).strip()

        # Try multiple search strategies to find the right company page
        search_queries = [
            clean_name,                           # "Apple Inc." (full name first!)
            f"{clean_name} company",              # "Apple Inc. company"
            short_name,                           # "Apple"
            f"{short_name} company",              # "Apple company"
            f"{short_name} corporation",          # "Apple corporation"
            f"{ticker} company",                  # "AAPL company"
        ]

        page_title = None
        for query in search_queries:
            wiki_search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={requests.utils.quote(query)}&format=json&srlimit=5"
            try:
                resp = self.session.get(wiki_search_url, timeout=15)
                resp.raise_for_status()
                search_results = resp.json().get("query", {}).get("search", [])
            except Exception as e:
                print(f"      Wikipedia search failed for '{query}': {e}")
                continue

            if not search_results:
                continue

            # Pick the best result - prefer pages that don't contain "list of", "merger", "acquisition"
            # AND whose title actually matches the company name (guards against wrong-company pages)
            skip_words = ['list of', 'merger', 'acquisition', 'category:', 'template:']
            for sr in search_results:
                title_lower = sr["title"].lower()
                if (not any(sw in title_lower for sw in skip_words) and
                        self._page_matches_company(sr["title"], company_name)):
                    page_title = sr["title"]
                    break

            if page_title:
                break

        if not page_title:
            print(f"      No matching Wikipedia page found for {clean_name} (all results failed company validation)")
            return []

        if not page_title:
            print(f"      No Wikipedia page found for {clean_name}")
            return []
        wiki_page_url = f"https://en.wikipedia.org/w/api.php?action=parse&page={requests.utils.quote(page_title)}&prop=text&format=json"
        try:
            resp = self.session.get(wiki_page_url, timeout=30)
            resp.raise_for_status()
            html_content = resp.json().get("parse", {}).get("text", {}).get("*", "")
        except Exception as e:
            print(f"      Wikipedia page fetch failed: {e}")
            return []

        if not html_content:
            return []

        wiki_url = f"https://en.wikipedia.org/wiki/{requests.utils.quote(page_title.replace(' ', '_'))}"
        print(f"      Scraped: {wiki_url}")

        # Step 3: Clean HTML and extract CEO-related text
        text = self.clean_html(html_content)

        # Find sections with CEO info
        ceo_sections = []
        text_lower = text.lower()
        for keyword in ['chief executive officer', 'ceo', 'key people', 'leadership', 'history']:
            idx = 0
            count = 0
            while count < 5:
                pos = text_lower.find(keyword, idx)
                if pos == -1:
                    break
                start = max(0, pos - 1000)
                end = min(len(text), pos + 2000)
                ceo_sections.append(text[start:end])
                idx = pos + len(keyword)
                count += 1

        if not ceo_sections:
            print(f"      No CEO info found on Wikipedia page")
            return []

        combined = "\n---SECTION---\n".join(ceo_sections[:6])

        # Step 4: Send scraped text to Claude for structured extraction
        prompt = f"""I scraped the Wikipedia page for "{page_title}" (ticker: {ticker}).

Here are the relevant sections mentioning CEO/leadership:

\"\"\"
{combined[:12000]}
\"\"\"

From this SCRAPED TEXT ONLY, extract every person who served as Chief Executive Officer (CEO) of {clean_name} who was serving at any point from year 2000 to present (include CEOs who started BEFORE 2000 if they were still CEO in 2000 or later - use their REAL start date).

RULES:
- ONLY extract data that is ACTUALLY in the text above
- Do NOT make up dates or names that aren't in the text
- For each CEO: full name, exact start date as CEO, exact end date as CEO
- Use YYYY-MM-DD format. If only year mentioned, use YYYY-01-01. If only month+year, use YYYY-MM-01.
- If still current CEO, end_date = "Present"
- ONLY company-level CEO, not division/regional

Respond ONLY with JSON:
{{
  "ceos": [
    {{"name": "Full Name", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD or Present"}}
  ],
  "wikipedia_url": "{wiki_url}"
}}"""

        response_text = self.query_claude(prompt, max_tokens=1000, use_cheap=True)
        if not response_text:
            return []

        json_text = re.sub(r'```json\s*|\s*```', '', response_text)
        json_match = re.search(r'\{.*\}', json_text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                ceos = result.get("ceos", [])
                # Attach wiki URL to each CEO
                for c in ceos:
                    c["wiki_url"] = wiki_url
                return ceos
            except json.JSONDecodeError:
                return []
        return []

    # ══════════════════════════════════════════════════
    # TIER 2B: Wikipedia lookup for individual CEO start date
    # ══════════════════════════════════════════════════
    def get_ceo_start_from_wikipedia(self, ceo_name: str, company_name: str) -> Optional[str]:
        """Search Wikipedia for a CEO's exact start date. Tries CEO's personal page first, then company page."""
        print(f"      [WIKI LOOKUP] Searching Wikipedia for {ceo_name} start date at {company_name}...")

        clean_ceo = re.sub(r'\b(Dr\.|Mr\.|Mrs\.|Ms\.)\s*', '', ceo_name).strip()
        clean_company = company_name.replace(",", "").replace("/", " ").strip()
        clean_company = re.sub(r'\s+', ' ', clean_company).strip()
        short_company = clean_company.replace(" Inc.", "").replace(" Inc", "")
        short_company = short_company.replace(" Corp.", "").replace(" Corp", "")
        short_company = short_company.replace(" plc", "").replace(" LABORATORIES", "").strip()

        # Try multiple Wikipedia pages: CEO's personal page, then company page
        pages_to_try = []

        # --- Find CEO's personal Wikipedia page ---
        ceo_search_queries = [
            clean_ceo,
            f"{clean_ceo} CEO",
            f"{clean_ceo} businessman",
            f"{clean_ceo} {short_company}",
        ]
        ceo_parts = clean_ceo.lower().split()
        # Remove middle initials for matching (e.g., "Bruce R. Chizen" -> match "bruce" and "chizen")
        ceo_first = ceo_parts[0] if ceo_parts else ""
        ceo_last = ceo_parts[-1] if len(ceo_parts) >= 2 else ""
        # Build set of possible first names using nicknames (e.g., "jeffrey" -> also match "jeff")
        first_name_variants = {ceo_first}
        canonical = self.NICKNAMES.get(ceo_first)
        if canonical:
            for nick, canon in self.NICKNAMES.items():
                if canon == canonical:
                    first_name_variants.add(nick)

        for query in ceo_search_queries:
            wiki_search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={requests.utils.quote(query)}&format=json&srlimit=5"
            try:
                resp = self.session.get(wiki_search_url, timeout=15)
                resp.raise_for_status()
                search_results = resp.json().get("query", {}).get("search", [])
            except Exception as e:
                print(f"      Wikipedia search failed for '{query}': {e}")
                continue

            for sr in search_results:
                title_lower = sr["title"].lower()
                # Match last name + any variant of first name in title
                if ceo_last and ceo_last in title_lower:
                    if any(variant in title_lower for variant in first_name_variants):
                        pages_to_try.append(("ceo_page", sr["title"]))
                        break

            if pages_to_try:
                break

        # --- Also add the company Wikipedia page ---
        company_search_queries = [clean_company, f"{clean_company} company", short_company]
        for query in company_search_queries:
            wiki_search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={requests.utils.quote(query)}&format=json&srlimit=3"
            try:
                resp = self.session.get(wiki_search_url, timeout=15)
                resp.raise_for_status()
                results = resp.json().get("query", {}).get("search", [])
                for sr in results:
                    title_lower = sr["title"].lower()
                    if (not any(sw in title_lower for sw in ['list of', 'merger', 'acquisition']) and
                            self._page_matches_company(sr["title"], clean_company)):
                        pages_to_try.append(("company_page", sr["title"]))
                        break
                if len(pages_to_try) > (1 if pages_to_try else 0):
                    break
            except Exception:
                continue

        if not pages_to_try:
            print(f"      No Wikipedia pages found for {clean_ceo} or {clean_company}")
            return None

        # Try each page to find the start date
        for page_type, page_title in pages_to_try:
            wiki_page_url = f"https://en.wikipedia.org/w/api.php?action=parse&page={requests.utils.quote(page_title)}&prop=text&format=json"
            try:
                resp = self.session.get(wiki_page_url, timeout=30)
                resp.raise_for_status()
                html_content = resp.json().get("parse", {}).get("text", {}).get("*", "")
            except Exception as e:
                print(f"      Wikipedia page fetch failed for {page_title}: {e}")
                continue

            if not html_content:
                continue

            wiki_url = f"https://en.wikipedia.org/wiki/{requests.utils.quote(page_title.replace(' ', '_'))}"
            print(f"      Scraped ({page_type}): {wiki_url}")

            text = self.clean_html(html_content)

            # Send the full page text (truncated) — keyword snippets miss context
            # Also include targeted sections for CEO-specific info
            full_text = text[:6000]

            text_lower = text.lower()
            extra_sections = []
            for keyword in ['chief executive officer', 'ceo', 'succeeded', 'appointed', 'named']:
                pos = text_lower.find(keyword)
                if pos >= 0:
                    start = max(0, pos - 300)
                    end = min(len(text), pos + 1000)
                    snippet = text[start:end]
                    if snippet not in full_text:
                        extra_sections.append(snippet)

            combined = full_text
            if extra_sections:
                combined += "\n\n---ADDITIONAL SECTIONS---\n" + "\n---\n".join(extra_sections[:3])

            prompt = f"""I scraped the Wikipedia page for "{page_title}".

Here are relevant sections:

\"\"\"
{combined[:8000]}
\"\"\"

Question: When did {clean_ceo} specifically become CEO (Chief Executive Officer) of {clean_company} (also known as {short_company})?

RULES:
- ONLY use information that is ACTUALLY in the text above
- Do NOT make up dates
- Look for when this person specifically held the CEO title - phrases like "became CEO", "named CEO", "appointed CEO", "CEO from", "CEO of X from YEAR to YEAR", "president and CEO since"
- If the person is described as BOTH the founder AND CEO of the company, and a founding date/year is mentioned, then that is when they became CEO. Return that date.
- If a specific date like "January 5, 2000" is mentioned, return "2000-01-05"
- If only a month and year like "December 2007" is mentioned, return "2007-12-01"
- If only a year like "2000" is mentioned, return "2000" (just the year is OK)
- If the text truly does not mention when this person became CEO, respond with "NOT_FOUND"

Respond with ONLY the date (e.g. "2007-12-01" or "2000") or "NOT_FOUND". Nothing else."""

            response_text = self.query_claude(prompt, max_tokens=100, use_cheap=True)
            if not response_text:
                continue

            response_text = response_text.strip().strip('"').strip()
            if "NOT_FOUND" in response_text.upper() or len(response_text) > 20:
                print(f"      Start date not found on {page_type} for {clean_ceo}")
                continue

            if re.match(r'^\d{4}(-\d{2}(-\d{2})?)?$', response_text):
                print(f"      Found start date: {response_text} (from {page_type})")
                return response_text

            print(f"      Invalid date format: {response_text}")

        print(f"      Could not find start date on Wikipedia, trying web search...")

        # ── Web search fallback using DuckDuckGo ──
        return self._web_search_ceo_start(clean_ceo, clean_company, short_company)

    def _web_search_ceo_start(self, ceo_name: str, company_name: str, short_company: str) -> Optional[str]:
        """Search the web (DuckDuckGo) for CEO start date when Wikipedia fails."""
        search_queries = [
            f"{ceo_name} became CEO of {short_company} date",
            f"{ceo_name} appointed CEO {short_company} when",
            f"when did {ceo_name} become CEO of {short_company}",
        ]

        all_snippets = []
        for query in search_queries:
            try:
                url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
                resp = self.session.get(url, timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                })
                if resp.status_code != 200:
                    continue

                # Extract search result snippets
                text = resp.text
                snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', text, re.DOTALL)
                if not snippets:
                    # Try alternate format
                    snippets = re.findall(r'class="result__snippet">(.*?)</(?:a|span)>', text, re.DOTALL)

                for s in snippets[:5]:
                    clean = re.sub(r'<[^>]+>', '', s).strip()
                    if clean:
                        all_snippets.append(clean)

                time.sleep(0.3)
            except Exception as e:
                print(f"      Web search failed for '{query}': {e}")
                continue

            if all_snippets:
                break

        if not all_snippets:
            print(f"      No web search results found for {ceo_name}")
            return None

        combined_snippets = "\n".join(all_snippets[:8])
        print(f"      [WEB] Found {len(all_snippets)} search snippets, asking Claude...")

        prompt = f"""From these web search results about {ceo_name} and {company_name}:

\"\"\"{combined_snippets}\"\"\"

Question: When did {ceo_name} become CEO of {company_name} (also known as {short_company})?

RULES:
- Use dates from the search results above
- Look for: "became CEO in", "appointed CEO", "named CEO", "CEO since", "CEO from YEAR"
- If the person is described as BOTH the founder AND CEO of the company, and a founding year is mentioned (e.g. "founded Amazon in 1994"), then that founding year is when they became CEO. Return that year.
- Return the date in YYYY-MM-DD format. If only year, return YYYY. If month+year, return YYYY-MM-01.
- If no date is found at all, respond "NOT_FOUND"

Respond with ONLY the date or "NOT_FOUND"."""

        response_text = self.query_claude(prompt, max_tokens=100, use_cheap=True)
        if not response_text:
            return None

        response_text = response_text.strip().strip('"').strip()
        if "NOT_FOUND" in response_text.upper() or len(response_text) > 20:
            print(f"      Web search: start date not found for {ceo_name}")
            return None

        if re.match(r'^\d{4}(-\d{2}(-\d{2})?)?$', response_text):
            print(f"      [WEB] Found start date: {response_text}")
            return response_text

        print(f"      Web search: invalid date format: {response_text}")
        return None

    def _get_company_formation_date(self, ticker: str, company_name: str) -> Optional[str]:
        """Search Wikipedia for when the company was formed/founded/spun off."""
        print(f"      [WIKI] Checking if {company_name} was formed after 2000...")

        clean_name = company_name.replace(",", "").replace("/", " ").strip()
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        short_name = clean_name.replace(" Inc.", "").replace(" Inc", "")
        short_name = short_name.replace(" Corp.", "").replace(" Corp", "")
        short_name = short_name.replace(" plc", "").replace(" LABORATORIES", "").strip()

        # Search Wikipedia for the company
        search_queries = [clean_name, f"{clean_name} company", short_name]
        page_title = None
        for query in search_queries:
            wiki_search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={requests.utils.quote(query)}&format=json&srlimit=3"
            try:
                resp = self.session.get(wiki_search_url, timeout=15)
                resp.raise_for_status()
                results = resp.json().get("query", {}).get("search", [])
                for sr in results:
                    title_lower = sr["title"].lower()
                    if not any(sw in title_lower for sw in ['list of', 'merger', 'acquisition']):
                        page_title = sr["title"]
                        break
                if page_title:
                    break
            except Exception:
                continue

        if not page_title:
            return None

        wiki_page_url = f"https://en.wikipedia.org/w/api.php?action=parse&page={requests.utils.quote(page_title)}&prop=text&format=json"
        try:
            resp = self.session.get(wiki_page_url, timeout=30)
            resp.raise_for_status()
            html_content = resp.json().get("parse", {}).get("text", {}).get("*", "")
        except Exception:
            return None

        if not html_content:
            return None

        text = self.clean_html(html_content)
        text_lower = text.lower()

        # Look for formation/founding/spinoff info
        relevant_sections = []
        for keyword in ['founded', 'formed', 'spun off', 'spinoff', 'spin-off', 'incorporated', 'established']:
            pos = text_lower.find(keyword)
            if pos != -1:
                start = max(0, pos - 300)
                end = min(len(text), pos + 500)
                relevant_sections.append(text[start:end])

        if not relevant_sections:
            return None

        combined = "\n---\n".join(relevant_sections[:4])

        prompt = f"""From this Wikipedia text about {clean_name}:

\"\"\"{combined[:4000]}\"\"\"

When was {clean_name} founded, formed, or spun off as a separate company?
Give ONLY the date in YYYY-MM-DD format (use 01 for unknown day/month).
If the company existed before 2000, respond "BEFORE_2000".
If not found, respond "NOT_FOUND"."""

        response_text = self.query_claude(prompt, max_tokens=50, use_cheap=True)
        if not response_text:
            return None

        response_text = response_text.strip().strip('"').strip()
        if "BEFORE_2000" in response_text:
            return None
        if "NOT_FOUND" in response_text:
            return None
        if re.match(r'^\d{4}(-\d{2}(-\d{2})?)?$', response_text):
            normalized = self._normalize_date(response_text)
            print(f"      Company formation date: {normalized}")
            return normalized
        return None

    # ══════════════════════════════════════════════════
    # TIER 3: Extract current CEO from latest 10-K / DEF 14A
    # ══════════════════════════════════════════════════
    def get_ceo_from_sec_filing(self, cik: str, company_name: str) -> Optional[Dict]:
        """Last resort when 8-K and Wikipedia both fail.
        Fetches the most recent 10-K or DEF 14A and asks Claude for the current CEO."""
        print(f"   [TIER 3] Looking for current CEO in most recent annual SEC filing...")

        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        response = self._sec_request(url, host="data.sec.gov")
        if not response:
            return None

        data = response.json()
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])

        for i, form in enumerate(forms):
            if form not in ("10-K", "DEF 14A", "10-K/A"):
                continue

            accession = accessions[i] if i < len(accessions) else None
            document = primary_docs[i] if i < len(primary_docs) else None
            filing_date = dates[i] if i < len(dates) else None
            if not accession or not document:
                continue

            filing_url = self.build_filing_url(cik, accession, document)
            time.sleep(0.12)
            content = self.download_filing(filing_url)
            if not content or len(content) < 500:
                continue

            text = self.clean_html(content)

            prompt = f"""You are reading a {form} SEC filing for "{company_name}" (filed {filing_date}).

Find the name of the person serving as Chief Executive Officer (CEO) of {company_name}.

Look in: officer/director tables, "Executive Officers" section, signature block, cover page.

TEXT:
\"\"\"{text[:10000]}\"\"\"

Rules:
- Return ONLY the CEO's full name (First Last). No honorifics (Mr., Dr., etc.).
- Company-level CEO only — not division or subsidiary CEO.
- If you cannot identify the CEO with confidence, respond "NOT_FOUND".

Respond with ONLY the name or "NOT_FOUND"."""

            response_text = self.query_claude(prompt, max_tokens=80, use_cheap=True)
            if not response_text:
                continue

            if "NOT_FOUND" in response_text.upper():
                continue
            name = self._extract_name_from_response(response_text)
            if not name:
                continue

            print(f"      [TIER 3] Found CEO: {name} (from {form} filed {filing_date})")
            return {
                "name": name,
                "start_date": None,
                "end_date": "Present",
                "validation_url": filing_url,
                "source": f"SEC {form}",
            }

        print(f"      [TIER 3] Could not identify CEO from annual filings")
        return None

    # ══════════════════════════════════════════════════
    # MAIN: Process Company with 3-Tier Fallback
    # ══════════════════════════════════════════════════
    def process_company(self, ticker: str) -> Dict:
        print(f"\n{'='*70}")
        print(f"COMPANY: {ticker}")
        print(f"{'='*70}")

        result = {
            "ticker": ticker,
            "company_name": "",
            "ceo_timeline": [],
            "data_sources": []
        }

        # Step 1: Get CIK
        cik = self.get_cik(ticker)
        if not cik:
            print(f"   CIK not found for {ticker}")
            return result
        print(f"   CIK: {cik}")

        # Step 2: Fetch ALL 8-K filings (2000+)
        print(f"   Fetching 8-K filings (2000-present)...")
        company_name, filings = self.get_all_8k_filings(cik)
        result["company_name"] = company_name

        if not filings:
            print(f"   No 8-K filings found since 2000")
        else:
            print(f"   Company: {company_name}")
            print(f"   Total 8-K filings (2000+): {len(filings)}")
            if filings:
                print(f"   Date range: {filings[0]['date']} to {filings[-1]['date']}")

        # ── TIER 1: Extract CEO changes from 8-K Item 5.02 ──
        print(f"\n   [TIER 1] Scanning 8-K filings for Item 5.02 CEO changes...")
        ceo_changes = []

        for idx, filing in enumerate(filings):
            if idx % 50 == 0 and idx > 0:
                print(f"   Scanning: {idx}/{len(filings)} filings...")

            # Pre-filter using items field from SEC metadata
            items_field = filing.get("items", "").lower()
            has_502_hint = "5.02" in items_field if items_field else True  # If no items field, check anyway

            if not has_502_hint:
                continue

            filing_url = self.build_filing_url(
                filing['cik'], filing['accession'], filing['document']
            )
            time.sleep(0.12)
            content = self.download_filing(filing_url)

            if not content or len(content) < 500:
                continue

            # Quick pre-filter on raw content (handles HTML entities, varied spacing)
            content_lower = content.lower()
            # Normalize HTML entities for matching
            content_norm = content_lower.replace('&nbsp;', ' ').replace('&#160;', ' ').replace('\xa0', ' ')
            content_norm = re.sub(r'<[^>]+>', ' ', content_norm)  # strip tags for matching
            content_norm = re.sub(r'\s+', ' ', content_norm)

            has_502 = ('item 5.02' in content_norm or 'item 5.2' in content_norm or
                       '5.02' in content_norm)
            has_ceo = ('chief executive officer' in content_norm or
                       'principal executive officer' in content_norm or
                       'ceo' in content_norm)

            if not (has_502 and has_ceo):
                continue

            # Extract Item 5.02 section
            item_text = self.extract_item_502(content)
            if not item_text:
                continue

            # Check if this section is about CEO (not just mentions CEO in passing)
            # Normalize whitespace for matching (CEO title can span lines)
            item_lower = item_text.lower()
            item_normalized = re.sub(r'\s+', ' ', item_lower)
            if ('chief executive officer' not in item_normalized and
                'principal executive officer' not in item_normalized and
                'ceo' not in item_normalized):
                continue

            # Skip non-company-level CEOs
            skip_terms = ['division chief executive', 'regional chief executive',
                          'group chief executive', 'subsidiary', 'unit chief executive']
            if any(term in item_lower for term in skip_terms):
                # Only skip if no company-level CEO mention
                ceo_idx = item_lower.find('chief executive officer')
                if ceo_idx != -1:
                    context = item_lower[max(0, ceo_idx-100):ceo_idx+100]
                    if any(t in context for t in skip_terms):
                        continue

            print(f"   [{idx+1}/{len(filings)}] {filing['date']} - CEO-related 8-K found, analyzing...")

            ceo_data = self.extract_ceo_from_8k(item_text, filing['date'], company_name)

            if ceo_data:
                change_entry = {
                    "filing_date": filing['date'],
                    "filing_url": filing_url,
                    "data": ceo_data,
                    "source": "8-K"
                }
                ceo_changes.append(change_entry)

                new_ceo = ceo_data.get("new_ceo", {})
                old_ceo = ceo_data.get("departing_ceo", {})
                if new_ceo and new_ceo.get("name"):
                    print(f"      -> NEW CEO: {new_ceo['name']} (effective: {new_ceo.get('effective_date')})")
                if old_ceo and old_ceo.get("name"):
                    print(f"      <- OLD CEO: {old_ceo['name']} (departed: {old_ceo.get('effective_date')})")

        print(f"\n   [TIER 1] Found {len(ceo_changes)} CEO changes from 8-K filings")

        # ── Build initial timeline from 8-K data ──
        timeline = self._build_timeline_from_8k(ceo_changes)

        # ── TIER 2: Always scrape Wikipedia to fill gaps ──
        # Wikipedia helps with: missing CEOs, null start dates, pre-2004 data,
        # and cases where 8-K didn't capture a CEO transition
        wiki_data = self.get_wikipedia_ceo_data(ticker, company_name)
        if wiki_data:
            timeline = self._merge_wiki_data(timeline, wiki_data, company_name)
            result["data_sources"].append("Wikipedia (scraped)")

        if ceo_changes:
            result["data_sources"].append("8-K")

        # If first CEO still starts well after 2000, check if company was formed after 2000
        # (e.g., ABBV spun off from ABT in 2013 - no CEO before that)
        if timeline:
            first_sd = timeline[0].get("start_date") or ""
            first_sd_norm = self._normalize_date(first_sd) if first_sd and first_sd not in ("Unknown", "None") else ""
            if first_sd_norm and first_sd_norm > "2002-01-01":
                formation_date = self._get_company_formation_date(ticker, company_name)
                if formation_date and formation_date > "2000-01-01":
                    timeline[0]["note"] = f"Company formed/spun off on {formation_date}. No prior CEO exists."
                    print(f"   NOTE: {company_name} was formed on {formation_date}, no CEO before that.")

        # ── Deduplicate: merge entries for the same person ──
        deduped = []
        for ceo in timeline:
            merged = False
            for existing in deduped:
                if self._names_match(existing["name"], ceo["name"]):
                    # Merge: keep earliest start, latest end, prefer 8-K source
                    sd_e = existing.get("start_date") or ""
                    sd_c = ceo.get("start_date") or ""
                    if sd_c and (not sd_e or sd_e.startswith("Unknown") or
                                 (sd_c < sd_e and not sd_c.startswith("Unknown"))):
                        existing["start_date"] = sd_c
                    ed_e = existing.get("end_date") or ""
                    ed_c = ceo.get("end_date") or ""
                    if ed_c == "Present":
                        existing["end_date"] = "Present"
                    elif ed_c and (not ed_e or ed_e == "Unknown" or
                                   (ed_c > ed_e and ed_e != "Present")):
                        existing["end_date"] = ed_c
                    # Prefer 8-K source and longer name
                    if ceo.get("source") == "8-K" and existing.get("source") != "8-K":
                        existing["source"] = "8-K"
                        existing["validation_url"] = ceo.get("validation_url")
                    if len(ceo["name"]) > len(existing["name"]):
                        existing["name"] = ceo["name"]
                    merged = True
                    break
            if not merged:
                deduped.append(ceo)
        timeline = deduped

        # ── Final cleanup ──
        today_str = datetime.now().strftime("%Y-%m-%d")

        # Remove CEOs whose entire tenure ended before 2000
        timeline = [c for c in timeline
                    if not c.get("end_date") or c["end_date"] == "Present" or c["end_date"] >= "2000-01-01"]

        # Remove future CEOs whose start_date is after today
        timeline = [c for c in timeline
                    if not c.get("start_date") or c["start_date"] <= today_str
                    or c["start_date"] in ("Unknown", "None")]

        # If last CEO has a future end_date, set to Present (they're still CEO today)
        if timeline:
            last_end = timeline[-1].get("end_date") or ""
            if last_end and last_end != "Present" and last_end > today_str:
                timeline[-1]["end_date"] = "Present"

        # Sort by start date
        def _sk(x):
            sd = x.get("start_date") or ""
            if not sd or sd.startswith("Before") or sd.startswith("Unknown"):
                return "0000-00-00"
            return sd if len(sd) > 4 else f"{sd}-01-01"
        timeline.sort(key=_sk)

        # Fix end dates: each CEO ends when next one starts
        # Also fix overlapping dates (e.g., CEO A ends 2004-12-31 but CEO B starts 2004-01-01)
        for i in range(len(timeline)):
            if i + 1 < len(timeline):
                next_start = timeline[i+1].get("start_date")
                if not next_start or next_start.startswith("Before"):
                    continue
                curr_end = timeline[i].get("end_date") or ""
                # If no end date, or end date is "Present", or end date overlaps with next start
                if not curr_end or curr_end == "Present" or curr_end > next_start:
                    timeline[i]["end_date"] = next_start

        # Keep real start dates - no clamping to 2000-01-01
        # If a CEO became CEO in 1997, we show 1997 as start_date

        # Fix any remaining null/unknown start dates:
        # Search Wikipedia for actual CEO start date before falling back
        for i, ceo in enumerate(timeline):
            if not ceo.get("start_date") or ceo["start_date"] in ("Unknown", "None"):
                # Try to find actual start date from CEO's Wikipedia page
                wiki_date = self.get_ceo_start_from_wikipedia(ceo["name"], company_name)
                if wiki_date:
                    ceo["start_date"] = self._normalize_date(wiki_date)
                    ceo["note"] = "Start date from CEO's Wikipedia page"
                elif i > 0:
                    prev_end = timeline[i-1].get("end_date")
                    if prev_end and prev_end not in ("Present", "Unknown"):
                        ceo["start_date"] = prev_end
                        ceo["note"] = "Start date not found; set to previous CEO's end date"

        # Normalize all dates to YYYY-MM-DD one final time
        for ceo in timeline:
            if ceo.get("start_date") and ceo["start_date"] not in ("Unknown", "None", ""):
                ceo["start_date"] = self._normalize_date(ceo["start_date"])
            if ceo.get("end_date") and ceo["end_date"] not in ("Present", "Unknown", "None", ""):
                ceo["end_date"] = self._normalize_date(ceo["end_date"])

        # Chronological sanity check: clear any end_date that precedes start_date
        for ceo in timeline:
            start = ceo.get("start_date") or ""
            end = ceo.get("end_date") or ""
            if (start and end
                    and end not in ("Present", "Unknown", "None", "")
                    and start not in ("Unknown", "None", "")
                    and end < start):
                print(f"   WARNING: {ceo['name']} has end_date ({end}) before start_date ({start})"
                      f" — clearing invalid end_date")
                ceo["end_date"] = None

        # Final end-date fill: ensure every non-last CEO has an end date
        for i in range(len(timeline) - 1):
            curr_end = timeline[i].get("end_date") or ""
            if not curr_end or curr_end in ("", "Unknown", "None"):
                next_start = timeline[i + 1].get("start_date") or ""
                if next_start and next_start not in ("Unknown", "None", ""):
                    timeline[i]["end_date"] = next_start

        # Gap detection: warn if consecutive CEOs have a gap > 1 year (possible missing CEO)
        for i in range(len(timeline) - 1):
            curr_end = timeline[i].get("end_date") or ""
            next_start = timeline[i + 1].get("start_date") or ""
            if (curr_end and next_start and
                    curr_end not in ("Present", "Unknown", "None") and
                    next_start not in ("Unknown", "None") and
                    next_start > curr_end):
                try:
                    gap_years = int(next_start[:4]) - int(curr_end[:4])
                    if gap_years > 1:
                        print(f"   WARNING: {gap_years}-year CEO gap detected between "
                              f"{timeline[i]['name']} (ended {curr_end}) and "
                              f"{timeline[i+1]['name']} (started {next_start}) — possible missing CEO")
                except ValueError:
                    pass

        # Tier 3: if still empty after 8-K + Wikipedia, pull CEO from annual filing
        if not timeline:
            print(f"\n   [TIER 3] No CEO found from 8-K or Wikipedia — trying annual SEC filing...")
            fallback = self.get_ceo_from_sec_filing(cik, company_name)
            if fallback:
                timeline = [fallback]
                result["data_sources"].append(f"SEC {fallback['source'].replace('SEC ', '')}")

        # Set last CEO's end_date to Present
        if timeline:
            timeline[-1]["end_date"] = "Present"

        result["ceo_timeline"] = timeline

        # Print summary
        print(f"\n   {'─'*50}")
        print(f"   CEO TIMELINE: {ticker} ({company_name})")
        print(f"   Sources: {', '.join(result['data_sources']) if result['data_sources'] else 'None'}")
        print(f"   {'─'*50}")
        if timeline:
            for ceo in timeline:
                print(f"\n   CEO          : {ceo['name']}")
                print(f"   Start Date   : {ceo['start_date']}")
                print(f"   End Date     : {ceo['end_date']}")
                print(f"   Source       : {ceo.get('source', 'N/A')}")
                print(f"   Validation   : {ceo.get('validation_url', 'N/A')}")
        else:
            print(f"\n   No CEO data found from any source")

        return result

    def _find_existing_key(self, ceo_map: Dict, name: str) -> Optional[str]:
        """Find existing key in ceo_map that matches name (fuzzy)."""
        for key in ceo_map:
            if self._names_match(key, name):
                return key
        return None

    def _build_timeline_from_8k(self, ceo_changes: List[Dict]) -> List[Dict]:
        """Build CEO timeline from 8-K extracted changes."""
        ceo_map = {}  # name -> {start, end, url, source}

        for change in ceo_changes:
            data = change["data"]
            filing_url = change["filing_url"]

            new_ceo = data.get("new_ceo", {}) or {}
            old_ceo = data.get("departing_ceo", {}) or {}

            new_name = (new_ceo.get("name") or "").strip()
            old_name = (old_ceo.get("name") or "").strip()

            # Skip invalid names (null placeholders, single words, honorific-only like "Mr. Vasquez")
            if new_name and (new_name.lower() in ["null", "none", "n/a"] or
                             not self._is_valid_ceo_name(new_name)):
                new_name = ""
            if old_name and (old_name.lower() in ["null", "none", "n/a"] or
                             not self._is_valid_ceo_name(old_name)):
                old_name = ""

            # Process departing CEO
            if old_name:
                end_date = old_ceo.get("effective_date")
                served_since = old_ceo.get("served_since")

                existing_key = self._find_existing_key(ceo_map, old_name)
                if existing_key is None:
                    ceo_map[old_name] = {
                        "name": old_name,
                        "start_date": served_since if served_since else None,
                        "end_date": end_date,
                        "validation_url": filing_url,
                        "source": "8-K",
                    }
                else:
                    if end_date and not ceo_map[existing_key].get("end_date"):
                        ceo_map[existing_key]["end_date"] = end_date
                    if served_since and (not ceo_map[existing_key].get("start_date") or
                                         (ceo_map[existing_key]["start_date"] or "").startswith("Before")):
                        ceo_map[existing_key]["start_date"] = served_since
                    # Keep the longer (more complete) name
                    if len(old_name) > len(ceo_map[existing_key]["name"]):
                        ceo_map[existing_key]["name"] = old_name

            # Process new CEO
            if new_name:
                start_date = new_ceo.get("effective_date")

                existing_key = self._find_existing_key(ceo_map, new_name)
                if existing_key is None:
                    ceo_map[new_name] = {
                        "name": new_name,
                        "start_date": start_date,
                        "end_date": None,
                        "validation_url": filing_url,
                        "source": "8-K",
                    }
                else:
                    # Update start date if earlier
                    if start_date:
                        existing = ceo_map[existing_key].get("start_date")
                        if not existing or (existing or "").startswith("Before") or start_date < existing:
                            ceo_map[existing_key]["start_date"] = start_date
                            ceo_map[existing_key]["validation_url"] = filing_url
                    # Keep the longer (more complete) name
                    if len(new_name) > len(ceo_map[existing_key]["name"]):
                        ceo_map[existing_key]["name"] = new_name

        # Convert to list, normalize all dates to YYYY-MM-DD
        timeline = list(ceo_map.values())
        for ceo in timeline:
            if ceo.get("start_date") and ceo["start_date"] not in ("Unknown", "None"):
                ceo["start_date"] = self._normalize_date(ceo["start_date"])
            if ceo.get("end_date") and ceo["end_date"] not in ("Present", "Unknown", "None"):
                ceo["end_date"] = self._normalize_date(ceo["end_date"])

        # Sort by start_date, putting None/Before at the beginning
        def sort_key(x):
            sd = x.get("start_date") or ""
            if not sd or sd.startswith("Before") or sd.startswith("Unknown"):
                return "0000-00-00"
            # Handle YYYY format
            if len(sd) == 4:
                return f"{sd}-01-01"
            return sd

        timeline.sort(key=sort_key)

        # Fill in end dates: each CEO ends when next starts
        for i in range(len(timeline)):
            if i + 1 < len(timeline) and not timeline[i].get("end_date"):
                next_start = timeline[i + 1].get("start_date")
                if next_start and not next_start.startswith("Before"):
                    timeline[i]["end_date"] = next_start

        return timeline

    def _merge_wiki_data(self, timeline: List[Dict], wiki_data: List[Dict],
                         company_name: str) -> List[Dict]:
        """Merge Wikipedia SCRAPED data for any remaining gaps."""
        if not wiki_data:
            return timeline

        for wiki_ceo in wiki_data:
            name = wiki_ceo.get("name", "")
            start = wiki_ceo.get("start_date", "")
            end = wiki_ceo.get("end_date", "")
            wiki_url = wiki_ceo.get("wiki_url", f"https://en.wikipedia.org/wiki/{company_name.replace(' ', '_')}")

            if not name:
                continue

            # Skip if entire tenure is before 2000
            norm_end = self._normalize_date(end) if end and end != "Present" else None
            if norm_end and norm_end < "2000-01-01":
                continue

            found = False
            for ceo in timeline:
                if self._names_match(ceo["name"], name):
                    found = True
                    existing_sd = ceo.get("start_date") or ""
                    # Fill in start_date ONLY if 8-K doesn't have it
                    if start and (not existing_sd or
                                  existing_sd.startswith("Before") or
                                  existing_sd.startswith("Unknown")):
                        ceo["start_date"] = self._normalize_date(start)
                        if ceo.get("source") != "8-K":
                            ceo["source"] = "Wikipedia (scraped)"
                            ceo["validation_url"] = wiki_url
                    # Fill end_date ONLY if 8-K doesn't have it
                    # (8-K source means the end_date came from a real filing)
                    existing_ed = ceo.get("end_date") or ""
                    if end and end != "Present" and (not existing_ed or
                                                      existing_ed.startswith("Unknown")):
                        # Only use wiki end_date if this CEO has no 8-K end_date
                        if ceo.get("source") != "8-K":
                            ceo["end_date"] = self._normalize_date(end)
                    break

            if not found:
                timeline.append({
                    "name": name,
                    "start_date": self._normalize_date(start) if start else "Unknown",
                    "end_date": self._normalize_date(end) if end and end != "Present" else None,
                    "validation_url": wiki_url,
                    "source": "Wikipedia (scraped)",
                })

        # Re-sort and fix end dates
        timeline.sort(key=lambda x: self._sort_date(x.get("start_date")))
        for i in range(len(timeline)):
            if i + 1 < len(timeline) and not timeline[i].get("end_date"):
                next_start = timeline[i + 1].get("start_date")
                if next_start and next_start not in ("Unknown", "Present"):
                    timeline[i]["end_date"] = next_start

        return timeline

    _GENERIC_COMPANY_WORDS = frozenset({
        "inc", "corp", "corporation", "co", "ltd", "llc", "plc", "company",
        "group", "holdings", "international", "industries", "services",
        "solutions", "technologies", "technology", "the", "of", "and", "or",
        "trust", "fund", "partners", "capital", "management", "financial",
    })

    def _page_matches_company(self, page_title: str, company_name: str) -> bool:
        """Return True if the Wikipedia page title plausibly belongs to this company.

        Requires at least 2 distinctive words to match when 2+ exist, preventing
        false positives like 'Abacus Group' matching 'Abacus Global Management',
        or 'Calico' matching 'Aardvark Therapeutics'.
        """
        title_words = set(re.findall(r'\b\w+\b', page_title.lower()))
        name_words = re.findall(r'\b\w+\b', company_name.lower())
        distinctive = [w for w in name_words
                       if w not in self._GENERIC_COMPANY_WORDS and len(w) > 2]
        if not distinctive:
            return True  # Nothing distinctive to check against
        matches = sum(1 for w in distinctive if w in title_words)
        required = min(2, len(distinctive))  # Need ≥2 matches when 2+ distinctive words exist
        return matches >= required

    def _is_valid_ceo_name(self, name: str) -> bool:
        """Return False for incomplete names like 'Mr. Vasquez' or single-word names."""
        if not name or len(name) < 4:
            return False
        # Strip honorifics to count real name parts
        cleaned = re.sub(r'^(Mr\.|Ms\.|Dr\.|Mrs\.|Prof\.)\s+', '', name.strip(), flags=re.IGNORECASE)
        parts = cleaned.split()
        return len(parts) >= 2  # Must have at least first + last name

    def _extract_name_from_response(self, response: str) -> Optional[str]:
        """Extract a CEO name from a Claude response, guarding against chain-of-thought leakage.

        Claude sometimes writes prose reasoning instead of just the name. This method
        tries each line, then falls back to a leading capitalised-word pattern.
        """
        if not response:
            return None

        # Markers that mean the line is prose, not a name
        _PROSE = ('the ', ' is ', ' was ', ' has ', ' who ', ' of the ', ' at ', ' for ',
                  'ceo', 'chief', 'officer', 'however', 'based on', 'according')

        for line in response.strip().split('\n'):
            candidate = line.strip().strip('"\'').strip()
            if not candidate or len(candidate) > 60:
                continue
            low = candidate.lower()
            if any(p in low for p in _PROSE):
                continue
            if self._is_valid_ceo_name(candidate):
                return candidate

        # Fallback: grab leading run of Title-Case words
        match = re.match(r'^([A-Z][a-zA-Z\.\-]+(?:\s+[A-Z][a-zA-Z\.\-]+){1,3})', response.strip())
        if match:
            candidate = match.group(1).strip()
            if self._is_valid_ceo_name(candidate):
                return candidate

        return None

    NICKNAMES = {
        'bob': 'robert', 'robert': 'robert', 'rob': 'robert',
        'bill': 'william', 'william': 'william', 'will': 'william',
        'jim': 'james', 'james': 'james', 'jimmy': 'james',
        'mike': 'michael', 'michael': 'michael',
        'dick': 'richard', 'richard': 'richard', 'rick': 'richard',
        'tom': 'thomas', 'thomas': 'thomas',
        'joe': 'joseph', 'joseph': 'joseph',
        'steve': 'steven', 'steven': 'steven', 'stephen': 'steven',
        'dave': 'david', 'david': 'david',
        'ed': 'edward', 'edward': 'edward', 'ted': 'edward',
        'dan': 'daniel', 'daniel': 'daniel',
        'tim': 'timothy', 'timothy': 'timothy',
        'jeff': 'jeffrey', 'jeffrey': 'jeffrey',
        'andy': 'andrew', 'andrew': 'andrew',
        'chris': 'christopher', 'christopher': 'christopher',
        'tony': 'anthony', 'anthony': 'anthony',
        'larry': 'lawrence', 'lawrence': 'lawrence',
        'chuck': 'charles', 'charles': 'charles',
        'lisa': 'lisa', 'liz': 'elizabeth', 'elizabeth': 'elizabeth',
    }

    def _names_match(self, name1: str, name2: str) -> bool:
        """Check if two CEO names refer to the same person."""
        if not name1 or not name2:
            return False

        n1 = name1.lower().strip()
        n2 = name2.lower().strip()
        if n1 == n2:
            return True

        # Remove prefixes like Dr., Mr.
        for pfx in ['dr.', 'dr ', 'mr.', 'mr ', 'ms.', 'ms ']:
            if n1.startswith(pfx): n1 = n1[len(pfx):].strip()
            if n2.startswith(pfx): n2 = n2[len(pfx):].strip()

        parts1 = n1.split()
        parts2 = n2.split()
        if not parts1 or not parts2:
            return False

        # Last names must match
        if parts1[-1] != parts2[-1]:
            return False

        first1 = parts1[0]
        first2 = parts2[0]

        # Exact first name match
        if first1 == first2:
            return True

        # Same first initial = likely same person (same last name already confirmed)
        if first1[0] == first2[0]:
            return True

        # Nickname check (Bob/Robert, Bill/William, etc.)
        canon1 = self.NICKNAMES.get(first1, first1)
        canon2 = self.NICKNAMES.get(first2, first2)
        if canon1 == canon2:
            return True

        # Middle-name variant: "Frank Carsten Thiel" vs "Carsten Thiel"
        # Check if all non-last parts of the shorter name appear in the longer name
        non_last1 = set(parts1[:-1])
        non_last2 = set(parts2[:-1])
        if non_last1 and non_last2:
            if non_last1.issubset(non_last2) or non_last2.issubset(non_last1):
                return True

        return False

    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to YYYY-MM-DD format."""
        if not date_str or date_str in ("null", "None", "Present"):
            return date_str or ""

        date_str = date_str.strip()

        # Already YYYY-MM-DD
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str

        # YYYY-MM
        if re.match(r'^\d{4}-\d{2}$', date_str):
            return f"{date_str}-01"

        # YYYY
        if re.match(r'^\d{4}$', date_str):
            return f"{date_str}-01-01"

        # Try parsing common formats
        for fmt in ['%B %d, %Y', '%b %d, %Y', '%m/%d/%Y', '%d %B %Y', '%B %Y']:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        return date_str

    def _sort_date(self, date_str: str) -> str:
        if not date_str or date_str.startswith("Before") or date_str.startswith("Unknown"):
            return "0000-00-00"
        if len(date_str) == 4:
            return f"{date_str}-01-01"
        return date_str

    def load_cik_map(self, csv_path: str) -> int:
        """Pre-populate CIK cache from output.csv (ticker, cik columns). Returns count loaded."""
        df = pd.read_csv(csv_path, dtype=str)
        count = 0
        for _, row in df.iterrows():
            ticker = str(row.get("ticker", "")).upper().strip()
            cik = str(row.get("cik", "")).strip()
            if ticker and cik and cik != "nan":
                self.cik_cache[ticker] = cik
                count += 1
        return count


def _load_russell2000_tickers(csv_path: str) -> List[str]:
    """Load tickers from output.csv, skipping rows with no CIK."""
    df = pd.read_csv(csv_path, dtype=str)
    tickers = []
    for _, row in df.iterrows():
        ticker = str(row.get("ticker", "")).upper().strip()
        cik = str(row.get("cik", "")).strip()
        if ticker and cik and cik != "nan":
            tickers.append(ticker)
    return tickers


def _read_batch_progress() -> int:
    """Return the next ticker index to process (0 if starting fresh)."""
    if os.path.exists(BATCH_PROGRESS_FILE):
        try:
            with open(BATCH_PROGRESS_FILE, "r") as f:
                return json.load(f).get("next_index", 0)
        except Exception:
            pass
    return 0


def _write_batch_progress(next_index: int, total: int) -> None:
    os.makedirs(os.path.dirname(BATCH_PROGRESS_FILE), exist_ok=True)
    with open(BATCH_PROGRESS_FILE, "w") as f:
        json.dump({"next_index": next_index, "total_tickers": total}, f, indent=2)


def _save_batch_results(all_results: list, batch_num: int) -> tuple[str, str]:
    """Save batch results to JSON + CSV. Returns (json_path, csv_path)."""
    json_file = f"sec_ceo_data/ceo_timeline_batch_{batch_num:03d}.json"
    csv_file = f"sec_ceo_data/ceo_timeline_batch_{batch_num:03d}.csv"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    rows = []
    for r in all_results:
        for ceo in r.get("ceo_timeline", []):
            rows.append({
                "Ticker": r["ticker"],
                "Company Name": r["company_name"],
                "CEO Name": ceo["name"],
                "Start Date": ceo.get("start_date", ""),
                "End Date": ceo.get("end_date", ""),
                "Source": ceo.get("source", ""),
                "Validation URL": ceo.get("validation_url", ""),
            })

    pd.DataFrame(rows).to_csv(csv_file, index=False)
    return json_file, csv_file


def main():
    import sys

    print("=" * 70)
    print("CEO HISTORY EXTRACTOR - 2-TIER APPROACH")
    print("Tier 1: SEC 8-K Item 5.02 | Tier 2: Wikipedia Scraping")
    print("Period: 2000 to present | Universe: Russell 2000")
    print("=" * 70)

    os.makedirs("sec_ceo_data", exist_ok=True)

    extractor = CEOExtractor()

    print(f"\nLoading Russell 2000 tickers from {RUSSELL2000_CSV}...")
    all_tickers = _load_russell2000_tickers(RUSSELL2000_CSV)
    loaded = extractor.load_cik_map(RUSSELL2000_CSV)
    print(f"Loaded {loaded} tickers with CIK from {RUSSELL2000_CSV}")

    next_index = _read_batch_progress()
    batch_num = next_index // BATCH_SIZE + 1
    batch_tickers = all_tickers[next_index: next_index + BATCH_SIZE]
    remaining_after = len(all_tickers) - next_index - len(batch_tickers)

    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        print(f"\nSELECT MODE:")
        print(f"1. Test     (first 2 companies)")
        print(f"2. Small    (first 5 companies)")
        print(f"3. Ten      (first 10 companies)")
        print(f"4. Medium   (first 25 companies)")
        if batch_tickers:
            print(f"5. Next Batch  (batch {batch_num}: companies {next_index+1}–{next_index+len(batch_tickers)} of {len(all_tickers)})")
        else:
            print(f"5. Next Batch  (ALL BATCHES COMPLETE)")
        print(f"6. Custom   (enter tickers)")
        choice = input("\nChoice (1-6): ").strip()

    if choice == "6":
        custom = input("Enter tickers (comma-separated): ").strip()
        tickers = [t.strip().upper() for t in custom.split(",") if t.strip()]
        batch_num = None  # custom run: don't update batch progress
    elif choice == "5":
        if not batch_tickers:
            print("All batches complete. Reset batch_progress.json to restart.")
            return
        tickers = batch_tickers
    elif choice == "4":
        tickers = all_tickers[:25]
        batch_num = None
    elif choice == "3":
        tickers = all_tickers[:10]
        batch_num = None
    elif choice == "2":
        tickers = all_tickers[:5]
        batch_num = None
    else:
        tickers = all_tickers[:2]
        batch_num = None

    # Resume within-batch: load any partial results already saved for this batch
    already_done = []
    if batch_num is not None:
        partial_file = f"sec_ceo_data/batch_{batch_num:03d}_progress.json"
        if os.path.exists(partial_file):
            try:
                with open(partial_file, "r", encoding="utf-8") as f:
                    already_done = json.load(f)
                done_tickers = {r["ticker"] for r in already_done}
                tickers = [t for t in tickers if t not in done_tickers]
                if already_done:
                    print(f"\n   Resuming batch {batch_num}: {len(already_done)} already done, "
                          f"{len(tickers)} remaining")
            except Exception:
                already_done = []

    print(f"\nWill process {len(tickers)} companies")
    print(f"Companies: {', '.join(tickers[:15])}{'...' if len(tickers) > 15 else ''}")

    if len(sys.argv) <= 1:
        confirm = input("\nContinue? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Cancelled")
            return

    all_results = list(already_done)
    start_time = datetime.now()

    for i, ticker in enumerate(tickers):
        if i > 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            avg_time = elapsed / i
            remaining = avg_time * (len(tickers) - i)
            print(f"\n   Progress: {i}/{len(tickers)} done | ~{remaining/60:.1f} min remaining")

        print(f"\n{'#'*70}")
        print(f"[{i+1}/{len(tickers)}] {ticker}")
        print(f"{'#'*70}")

        try:
            result = extractor.process_company(ticker)
            all_results.append(result)

            # Rolling save after each company (batch-scoped file)
            if batch_num is not None:
                with open(f"sec_ceo_data/batch_{batch_num:03d}_progress.json", "w", encoding="utf-8") as f:
                    json.dump(all_results, f, indent=2, ensure_ascii=False)
            else:
                with open("sec_ceo_data/progress.json", "w", encoding="utf-8") as f:
                    json.dump(all_results, f, indent=2, ensure_ascii=False)

            time.sleep(1)
        except Exception as e:
            print(f"\n   ERROR processing {ticker}: {e}")
            import traceback
            traceback.print_exc()

    # ── Save Final Results ──
    if batch_num is not None:
        json_file, csv_file = _save_batch_results(all_results, batch_num)
        # Advance progress pointer
        _write_batch_progress(next_index + len(tickers), len(all_tickers))
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = f"sec_ceo_data/ceo_timeline_{timestamp}.json"
        csv_file = f"sec_ceo_data/ceo_timeline_{timestamp}.csv"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        rows = []
        for r in all_results:
            for ceo in r.get("ceo_timeline", []):
                rows.append({
                    "Ticker": r["ticker"],
                    "Company Name": r["company_name"],
                    "CEO Name": ceo["name"],
                    "Start Date": ceo.get("start_date", ""),
                    "End Date": ceo.get("end_date", ""),
                    "Source": ceo.get("source", ""),
                    "Validation URL": ceo.get("validation_url", ""),
                })
        pd.DataFrame(rows).to_csv(csv_file, index=False)

    elapsed = (datetime.now() - start_time).total_seconds()
    total_ceos = sum(len(r.get("ceo_timeline", [])) for r in all_results)

    print(f"\n{'='*70}")
    print(f"BATCH {batch_num:03d} COMPLETE" if batch_num else "COMPLETE")
    print(f"{'='*70}")
    print(f"Time         : {elapsed/60:.1f} minutes")
    print(f"Companies    : {len(all_results)}")
    print(f"CEOs found   : {total_ceos}")
    if batch_num is not None:
        new_next = next_index + len(tickers)
        print(f"Progress     : {new_next}/{len(all_tickers)} total | {remaining_after} remaining")
    print(f"\nOutput Files:")
    print(f"  CSV : {csv_file}")
    print(f"  JSON: {json_file}")

    # Summary table
    print(f"\n{'─'*70}")
    print(f"{'Ticker':<8} {'Company':<25} {'CEOs':<5} {'Sources'}")
    print(f"{'─'*70}")
    for r in all_results:
        sources = ', '.join(r.get('data_sources', []))
        print(f"{r['ticker']:<8} {r['company_name'][:24]:<25} {len(r.get('ceo_timeline', [])):<5} {sources}")

    print(f"{'='*70}")
if __name__ == "__main__":
    main()