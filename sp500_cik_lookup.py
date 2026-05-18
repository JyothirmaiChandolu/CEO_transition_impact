#!/usr/bin/env python3
"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Looks up SEC EDGAR CIK numbers for S&P 500 tickers incrementally and writes the results to sp500_output.csv.
"""

import csv
import glob
import logging
import os
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_FILE = "sp500_output.csv"
RATE_LIMIT = 0.1  # seconds between requests
HEADERS = {"User-Agent": "CEOResearch jyothirmai@mhktechinc.com"}

# Tickers whose EDGAR symbol differs from their market symbol
TICKER_ALIASES: dict[str, list[str]] = {
    "BRKB":  ["BRK-B", "BRK.B", "BRKB"],
    "BFB":   ["BF-B",  "BF.B",  "BFB"],
    "GOOG":  ["GOOGL", "GOOG"],
    "GEHC":  ["GEHC"],
    "GEV":   ["GEV"],
    "GE":    ["GE"],
}


def find_latest_sp500_csv() -> str:
    files = sorted(glob.glob("sp500_tickers_*.csv"), reverse=True)
    if not files:
        raise FileNotFoundError(
            "No sp500_tickers_*.csv found. Run sp500_data.py first."
        )
    logger.info("Using tickers file: %s", files[0])
    return files[0]


def load_tickers(csv_path: str) -> list[str]:
    tickers = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = row.get("ticker", "").strip().upper()
            if t:
                tickers.append(t)
    return tickers


def load_existing_output() -> dict[str, str]:
    """Return {ticker: cik} for already-found tickers."""
    if not os.path.exists(OUTPUT_FILE):
        return {}
    result = {}
    with open(OUTPUT_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = row.get("ticker", "").strip().upper()
            c = row.get("cik", "").strip()
            if t and c:
                result[t] = c
    logger.info("Loaded %d existing tickers from %s", len(result), OUTPUT_FILE)
    return result


def lookup_cik(ticker: str) -> str | None:
    """
    Look up CIK via SEC EDGAR company search atom feed.
    Returns zero-padded 10-digit CIK string, or None if not found.
    """
    url = (
        "https://www.sec.gov/cgi-bin/browse-edgar"
        f"?action=getcompany&company=&CIK={ticker}"
        "&type=8-K&dateb=&owner=include&count=1&output=atom"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            logger.warning("HTTP %s for ticker %s", resp.status_code, ticker)
            return None

        text = resp.text
        # The atom feed contains <company-info> with <cik> element
        # e.g. <cik>0001234567</cik>
        import re
        m = re.search(r"<cik>(\d+)</cik>", text)
        if m:
            cik = m.group(1).zfill(10)
            return cik

        # Fallback: look for CIK in the company href
        m2 = re.search(r"/cgi-bin/browse-edgar\?action=getcompany&CIK=(\d+)", text)
        if m2:
            cik = m2.group(1).zfill(10)
            return cik

        logger.warning("No CIK found for ticker %s", ticker)
        return None
    except Exception as e:
        logger.warning("Request error for ticker %s: %s", ticker, e)
        return None


def write_output(results: dict[str, str]) -> None:
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ticker", "cik"])
        for ticker in sorted(results.keys()):
            writer.writerow([ticker, results[ticker]])


def fetch_sec_company_tickers() -> dict[str, str]:
    """
    Download SEC's full company_tickers.json and return a ticker→CIK mapping.
    This covers nearly every public company and is the most reliable fallback.
    """
    url = "https://www.sec.gov/files/company_tickers.json"
    logger.info("Downloading SEC company_tickers.json...")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # Format: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "..."}, ...}
        mapping: dict[str, str] = {}
        for entry in data.values():
            t = str(entry.get("ticker", "")).upper().strip()
            c = str(entry.get("cik_str", "")).zfill(10)
            if t and c:
                mapping[t] = c
        logger.info("Loaded %d tickers from SEC company_tickers.json", len(mapping))
        return mapping
    except Exception as e:
        logger.error("Failed to download company_tickers.json: %s", e)
        return {}


def retry_missing(tickers: list[str], results: dict[str, str]) -> dict[str, str]:
    """Try to resolve missing tickers using SEC's full company_tickers.json."""
    sec_map = fetch_sec_company_tickers()
    if not sec_map:
        logger.error("Cannot retry — SEC mapping unavailable.")
        return results

    resolved = 0
    still_missing = []
    for ticker in tickers:
        # Try the ticker as-is first
        candidates = [ticker] + TICKER_ALIASES.get(ticker, [])
        cik = None
        for candidate in candidates:
            if candidate in sec_map:
                cik = sec_map[candidate]
                break
        if cik:
            results[ticker] = cik
            logger.info("  FOUND  %s -> CIK %s", ticker, cik)
            resolved += 1
        else:
            # Last resort: atom feed with a small delay
            cik = lookup_cik(ticker)
            if cik:
                results[ticker] = cik
                logger.info("  ATOM   %s -> CIK %s", ticker, cik)
                resolved += 1
            else:
                still_missing.append(ticker)
                logger.warning("  MISS   %s -> still not found", ticker)
            time.sleep(RATE_LIMIT)

    logger.info("Retry resolved %d/%d. Still missing: %s", resolved, len(tickers), still_missing)
    return results


def main() -> None:
    import sys
    retry_mode = "--retry" in sys.argv

    tickers_file = find_latest_sp500_csv()
    all_tickers = load_tickers(tickers_file)
    logger.info("Found %d tickers in %s", len(all_tickers), tickers_file)

    results = load_existing_output()
    already_done = set(results.keys())

    if retry_mode:
        missing = [t for t in all_tickers if t not in already_done]
        logger.info("Retry mode: %d tickers to resolve", len(missing))
        results = retry_missing(missing, results)
    else:
        remaining = [t for t in all_tickers if t not in already_done]
        logger.info("%d tickers already resolved, %d remaining", len(already_done), len(remaining))

        for i, ticker in enumerate(remaining):
            cik = lookup_cik(ticker)
            if cik:
                results[ticker] = cik
                logger.info("[%d/%d] %s -> CIK %s", i + 1, len(remaining), ticker, cik)
            else:
                logger.warning("[%d/%d] %s -> no CIK found, skipping", i + 1, len(remaining), ticker)

            if (i + 1) % 10 == 0:
                write_output(results)

            time.sleep(RATE_LIMIT)

    write_output(results)
    total_missing = len([t for t in all_tickers if t not in results])
    logger.info("Done. Wrote %d tickers to %s (%d still missing)", len(results), OUTPUT_FILE, total_missing)


if __name__ == "__main__":
    main()
