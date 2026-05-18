"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: LLM-based extraction of CEO transition reasons and voluntary/involuntary classification from SEC 8-K filing text.
"""

import json
import logging
import re
from typing import Optional

from . import llm
from .logger import log_llm_call

# ── Classification labels ─────────────────────────────────────────────────────
VOLUNTARY   = "voluntary"
INVOLUNTARY = "involuntary"
UNKNOWN     = "unknown"

_SYSTEM_PROMPT = """\
You are an expert SEC filing analyst. Your task is to read an SEC 8-K filing \
(Item 5.02 — Departure of Directors or Certain Officers; Election of Directors; \
Appointment of Certain Officers) and extract:

1. reason   — A concise 1-2 sentence explanation of WHY the CEO transition \
happened (e.g., "CEO retired after 10 years; CFO appointed as successor", \
"Board terminated CEO following performance review", \
"CEO resigned to pursue other opportunities; COO named interim CEO").

2. exit_classification — Classify the departing CEO's exit:
   - "voluntary"   : retirement, planned succession, stepping down to chairman/
                     advisory role, resignation to pursue other opportunities, \
                     health reasons stated voluntarily.
   - "involuntary" : fired, terminated, forced resignation, removed by board, \
                     mutual separation with unusual severance, \
                     "mutual agreement" departures with no stated reason.
   - "unknown"     : insufficient information to determine.

Return ONLY valid JSON (no markdown, no explanation):
{"reason": "...", "exit_classification": "voluntary|involuntary|unknown"}
"""

_USER_TEMPLATE = """\
Company   : {company_name}
CEO Name  : {ceo_name}
Transition Date: {transition_date}

--- Filing Text (Item 5.02) ---
{filing_text}
--- End of Filing Text ---

Extract the reason for the CEO transition and classify the exit type.
"""


def extract_reason_and_classification(
    filing_text: str,
    ceo_name: str,
    transition_date: str,
    company_name: str,
    model: str,
    logger: logging.Logger,
    ticker: str = "",
) -> tuple[str, str, int, int]:
    """
    Call the LLM to extract reason + exit_classification from filing text.

    Returns:
        (reason, exit_classification, input_tokens, output_tokens)
    """
    tag = f"[{ticker}] {ceo_name[:25]}"

    if not filing_text.strip():
        logger.debug(f"{tag} | extractor | SKIP: empty filing text")
        return "No filing text available.", UNKNOWN, 0, 0

    user_msg = _USER_TEMPLATE.format(
        company_name=company_name,
        ceo_name=ceo_name,
        transition_date=transition_date or "Unknown",
        filing_text=filing_text,
    )

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user",   "content": user_msg},
    ]

    logger.debug(f"{tag} | extractor | calling LLM (model={model}, text_len={len(filing_text):,})")
    content, in_tok, out_tok = llm.call(messages, model=model)

    log_llm_call(
        logger=logger,
        step=f"extract reason [{ticker}] {ceo_name[:20]}",
        model=model,
        input_tokens=in_tok,
        output_tokens=out_tok,
        extra=f"filing_chars={len(filing_text):,}",
    )

    if content.startswith("LLM_ERROR"):
        logger.error(f"{tag} | extractor | LLM error: {content}")
        return "LLM error during extraction.", UNKNOWN, in_tok, out_tok

    reason, classification = _parse_llm_output(content, logger, tag)
    logger.debug(f"{tag} | extractor | result: classification={classification!r}, reason={reason[:80]!r}")

    return reason, classification, in_tok, out_tok


def _parse_llm_output(content: str, logger: logging.Logger, tag: str) -> tuple[str, str]:
    """Parse JSON from LLM response. Falls back to regex extraction if JSON is malformed."""
    # Strip possible markdown fences
    cleaned = re.sub(r"^```(?:json)?\s*", "", content.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
        reason = str(data.get("reason", "")).strip() or "Not specified."
        raw_cls = str(data.get("exit_classification", "")).strip().lower()
        classification = _normalize_classification(raw_cls)
        return reason, classification
    except json.JSONDecodeError:
        logger.warning(f"{tag} | extractor | JSON parse failed, trying regex fallback")

    # Regex fallback
    reason_m = re.search(r'"reason"\s*:\s*"([^"]+)"', cleaned)
    cls_m    = re.search(r'"exit_classification"\s*:\s*"([^"]+)"', cleaned)

    reason = reason_m.group(1).strip() if reason_m else "Could not parse reason."
    raw_cls = cls_m.group(1).strip().lower() if cls_m else "unknown"
    return reason, _normalize_classification(raw_cls)


def _normalize_classification(raw: str) -> str:
    if raw in (VOLUNTARY, "retire", "retirement", "resigned voluntarily", "planned"):
        return VOLUNTARY
    if raw in (INVOLUNTARY, "fired", "terminated", "forced", "removed"):
        return INVOLUNTARY
    if VOLUNTARY in raw:
        return VOLUNTARY
    if INVOLUNTARY in raw or "fired" in raw or "terminat" in raw:
        return INVOLUNTARY
    return UNKNOWN
