"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Main processing loop — iterates all companies and CEO entries, fetches filings, extracts reasons, and writes results back to JSON.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from .fetcher import fetch_item_502
from .extractor import extract_reason_and_classification, UNKNOWN
from .logger import log_summary


def _load_json(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_json(data: list, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _already_processed(entry: dict) -> bool:
    """Skip entries that already have a non-empty reason."""
    return bool(entry.get("reason")) and entry.get("exit_classification") in (
        "voluntary", "involuntary", "unknown"
    )


def process_batch(
    input_path: str,
    output_path: str,
    model: str,
    logger: logging.Logger,
    limit: Optional[int] = None,
) -> None:
    """
    Process all companies in the input JSON file.

    For each CEO entry that has a validation_url:
      1. Fetch the SEC filing and extract Item 5.02 text.
      2. Call LLM to get reason + exit_classification.
      3. Write reason and exit_classification back to the entry.

    Saves the updated JSON to output_path after every company (crash-safe).
    """
    logger.info(f"Input  : {input_path}")
    logger.info(f"Output : {output_path}")
    logger.info(f"Model  : {model}")
    if limit:
        logger.info(f"Limit  : {limit} companies")

    data = _load_json(input_path)
    logger.info(f"Loaded {len(data)} companies from {input_path}")

    # Counters
    total_companies  = 0
    total_ceos       = 0
    skipped_no_url   = 0
    skipped_existing = 0
    errors           = 0
    total_in_tokens  = 0
    total_out_tokens = 0

    companies_to_process = data[:limit] if limit else data

    for company in companies_to_process:
        ticker       = company.get("ticker", "???")
        company_name = company.get("company_name", ticker)
        ceo_timeline = company.get("ceo_timeline", [])
        total_companies += 1

        logger.info(f"── {ticker} ({company_name}) — {len(ceo_timeline)} CEO entries")

        # URL cache: avoid fetching the same filing URL twice within one company
        filing_cache: dict[str, str] = {}

        for entry in ceo_timeline:
            ceo_name  = entry.get("name", "Unknown")
            end_date  = entry.get("end_date", "")
            url       = (entry.get("validation_url") or "").strip()
            total_ceos += 1

            # Skip if already processed
            if _already_processed(entry):
                skipped_existing += 1
                logger.debug(f"[{ticker}] {ceo_name[:30]} | SKIP: already processed")
                continue

            # Skip if no URL
            if not url:
                skipped_no_url += 1
                entry["reason"] = "No validation URL available."
                entry["exit_classification"] = UNKNOWN
                logger.debug(f"[{ticker}] {ceo_name[:30]} | SKIP: no validation URL")
                continue

            # Fetch filing (use cache if same URL seen before in this company)
            if url in filing_cache:
                filing_text = filing_cache[url]
                logger.debug(f"[{ticker}] {ceo_name[:30]} | CACHE HIT: {url}")
            else:
                filing_text = fetch_item_502(url, logger, ticker=ticker, ceo_name=ceo_name)
                filing_cache[url] = filing_text

            # Extract reason + classification
            reason, classification, in_tok, out_tok = extract_reason_and_classification(
                filing_text=filing_text,
                ceo_name=ceo_name,
                transition_date=end_date,
                company_name=company_name,
                model=model,
                logger=logger,
                ticker=ticker,
            )

            if in_tok == 0 and out_tok == 0 and "LLM_ERROR" not in reason:
                # Filing text was empty — not an LLM error, just no content
                pass
            elif "LLM_ERROR" in reason:
                errors += 1

            total_in_tokens  += in_tok
            total_out_tokens += out_tok

            entry["reason"] = reason
            entry["exit_classification"] = classification

            logger.info(
                f"[{ticker}] {ceo_name[:30]:<30} | "
                f"{classification:<12} | "
                f"in={in_tok:>5} out={out_tok:>4} | "
                f"{reason[:60]}"
            )

        # Save after every company (crash-safe incremental writes)
        _save_json(data, output_path)
        logger.debug(f"[{ticker}] saved incremental output to {output_path}")

    log_summary(
        logger=logger,
        total=total_companies,
        processed=total_ceos - skipped_no_url - skipped_existing,
        skipped=skipped_no_url + skipped_existing,
        errors=errors,
        total_input_tokens=total_in_tokens,
        total_output_tokens=total_out_tokens,
        model=model,
    )

    logger.info(f"Final output written to: {output_path}")
