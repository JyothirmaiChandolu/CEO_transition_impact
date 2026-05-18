"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Pure utility functions for HTML cleaning, date normalization, and text processing shared across the agent package.
"""

import re
from datetime import datetime
from typing import Optional


# ── HTML / Text Cleaning ─────────────────────────────────────────────────────

def clean_html(html: str) -> str:
    """Remove HTML tags, scripts, styles and normalize whitespace."""
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'\.mw-parser-output[^}]*\}', ' ', text)
    text = re.sub(r'@media[^}]*\{[^}]*\}', ' ', text, flags=re.DOTALL)
    text = re.sub(r'<br\s*/?\s*>|</p>|</div>|</tr>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    text = text.replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#8217;', "'")
    text = text.replace('&rsquo;', "'").replace('&ldquo;', '"').replace('&rdquo;', '"')
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'[^\S\n]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()


def extract_item_502(content: str) -> Optional[str]:
    """Extract Item 5.02 section from 8-K filing content."""
    text = clean_html(content)

    patterns = [
        r'(Item\s*5\.0*2\b.*?)(?=Item\s*\d+\.\d+|\Z)',
        r'(ITEM\s*5\.0*2\b.*?)(?=ITEM\s*\d+\.\d+|\Z)',
        r'(Section\s*5\s*[-–—:]\s*Item\s*5\.0*2\b.*?)(?=Section\s*\d+|Item\s*\d+\.\d+|\Z)',
        r'(Item\s*5\.0*2\s*\([a-z]\).*?)(?=Item\s*\d+\.\d+|\Z)',
        r'(Item\s*5\.0*2\s+Departure.*?)(?=Item\s*\d+\.\d+|ITEM\s*\d+|\Z)',
        r'(Item\s*5[\.\s\xa0]+0*2\b.*?)(?=Item\s*\d+\.\d+|\Z)',
        r'(Item\s*6\b[^0-9].*?(?:Chief Executive|CEO).*?)(?=Item\s*\d+|\Z)',
        r'(5\.0*2\s*[-–—:.]?\s*Departure.*?)(?=\d+\.\d+\s*[-–—:.]?\s*[A-Z]|\Z)',
    ]

    for pattern in patterns:
        best = ""
        for m in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
            s = m.group(1).strip()
            if len(s) > len(best):
                best = s
        if len(best) > 100:
            return best[:12000]

    # Fallback: keyword window
    text_lower = text.lower()
    ceo_kws = ['chief executive officer', 'principal executive officer']
    action_kws = ['appoint', 'resign', 'depart', 'succeed', 'elect',
                  'terminat', 'step down', 'retire', 'named', 'promoted']
    if any(k in text_lower for k in ceo_kws) and any(k in text_lower for k in action_kws):
        for kw in ceo_kws:
            idx = text_lower.find(kw)
            if idx != -1:
                return text[max(0, idx - 2000):min(len(text), idx + 5000)]

    return None


# ── Date Normalization ────────────────────────────────────────────────────────

def normalize_date(date_str: str) -> str:
    """Normalize any date string to YYYY-MM-DD."""
    if not date_str or date_str in ("null", "None", "Present"):
        return date_str or ""

    date_str = date_str.strip()

    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    if re.match(r'^\d{4}-\d{2}$', date_str):
        return f"{date_str}-01"
    if re.match(r'^\d{4}$', date_str):
        return f"{date_str}-01-01"

    for fmt in ['%B %d, %Y', '%b %d, %Y', '%m/%d/%Y', '%d %B %Y', '%B %Y']:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue

    return date_str


def sort_key(date_str: Optional[str]) -> str:
    """Sortable key for a date string, placing missing/unknown dates first."""
    if not date_str or date_str.startswith(("Before", "Unknown")):
        return "0000-00-00"
    if len(date_str) == 4:
        return f"{date_str}-01-01"
    return date_str


# ── Name Utilities ────────────────────────────────────────────────────────────

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
    'liz': 'elizabeth', 'elizabeth': 'elizabeth',
}

_GENERIC_COMPANY_WORDS = frozenset({
    "inc", "corp", "corporation", "co", "ltd", "llc", "plc", "company",
    "group", "holdings", "international", "industries", "services",
    "solutions", "technologies", "technology", "the", "of", "and", "or",
    "trust", "fund", "partners", "capital", "management", "financial",
})


def names_match(name1: str, name2: str) -> bool:
    """Return True if two name strings refer to the same person."""
    if not name1 or not name2:
        return False

    n1, n2 = name1.lower().strip(), name2.lower().strip()
    if n1 == n2:
        return True

    for pfx in ('dr.', 'dr ', 'mr.', 'mr ', 'ms.', 'ms '):
        if n1.startswith(pfx):
            n1 = n1[len(pfx):].strip()
        if n2.startswith(pfx):
            n2 = n2[len(pfx):].strip()

    p1, p2 = n1.split(), n2.split()
    if not p1 or not p2:
        return False
    if p1[-1] != p2[-1]:
        return False

    f1, f2 = p1[0], p2[0]
    if f1 == f2:
        return True
    if f1[0] == f2[0]:
        return True
    if NICKNAMES.get(f1, f1) == NICKNAMES.get(f2, f2):
        return True

    # Middle-name variant: "Frank Carsten Thiel" vs "Carsten Thiel"
    nl1, nl2 = set(p1[:-1]), set(p2[:-1])
    if nl1 and nl2 and (nl1.issubset(nl2) or nl2.issubset(nl1)):
        return True

    return False


def is_valid_ceo_name(name: str) -> bool:
    """Return False for incomplete names like 'Mr. Vasquez' or single words."""
    if not name or len(name) < 4:
        return False
    cleaned = re.sub(r'^(Mr\.|Ms\.|Dr\.|Mrs\.|Prof\.)\s+', '', name.strip(), flags=re.IGNORECASE)
    return len(cleaned.split()) >= 2


def extract_name_from_response(response: str) -> Optional[str]:
    """Pull a clean CEO name from an LLM response, filtering out prose leakage."""
    if not response:
        return None

    _PROSE = ('the ', ' is ', ' was ', ' has ', ' who ', ' of the ', ' at ', ' for ',
              'ceo', 'chief', 'officer', 'however', 'based on', 'according')

    for line in response.strip().split('\n'):
        candidate = line.strip().strip('"\'').strip()
        if not candidate or len(candidate) > 60:
            continue
        if any(p in candidate.lower() for p in _PROSE):
            continue
        if is_valid_ceo_name(candidate):
            return candidate

    m = re.match(r'^([A-Z][a-zA-Z.\-]+(?:\s+[A-Z][a-zA-Z.\-]+){1,3})', response.strip())
    if m:
        candidate = m.group(1).strip()
        if is_valid_ceo_name(candidate):
            return candidate

    return None


def page_matches_company(page_title: str, company_name: str) -> bool:
    """Check that a Wikipedia page title plausibly belongs to this company."""
    title_words = set(re.findall(r'\b\w+\b', page_title.lower()))
    name_words = re.findall(r'\b\w+\b', company_name.lower())
    distinctive = [w for w in name_words
                   if w not in _GENERIC_COMPANY_WORDS and len(w) > 2]
    if not distinctive:
        return True
    matches = sum(1 for w in distinctive if w in title_words)
    return matches >= min(2, len(distinctive))
