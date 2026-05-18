"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Fetches SEC EDGAR CIK numbers for a list of stock tickers and writes the results to an output CSV.
"""

import re
import sys
import pandas as pd
import requests


SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
EDGAR_CIK_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=&dateb=&owner=include&count=1"
EDGAR_SEARCH_URL = "https://www.sec.gov/cgi-bin/browse-edgar?company={ticker}&CIK=&type=&dateb=&owner=include&count=10&search_text=&action=getcompany"
HEADERS = {"User-Agent": "jyothirmai@mhktechinc.com"}


def fetch_sec_ticker_map() -> dict[str, int]:
    """Download SEC's full ticker→CIK mapping in one request."""
    response = requests.get(SEC_TICKERS_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    data = response.json()
    return {entry["ticker"].upper(): entry["cik_str"] for entry in data.values()}


def _parse_cik_from_url(url: str) -> int | None:
    match = re.search(r"CIK=(\d+)", url)
    if match:
        cik = int(match.group(1))
        return cik if cik != 0 else None
    return None


def lookup_cik_by_ticker_field(ticker: str) -> int | None:
    """Query EDGAR using ticker as CIK field; works when EDGAR recognizes the ticker directly."""
    response = requests.get(EDGAR_CIK_URL.format(ticker=ticker), headers=HEADERS, timeout=15)
    return _parse_cik_from_url(response.url)


def scrape_cik_from_edgar_search(ticker: str) -> int | None:
    """Scrape EDGAR company-name search results for the ticker."""
    response = requests.get(EDGAR_SEARCH_URL.format(ticker=ticker), headers=HEADERS, timeout=15)

    # Single match: EDGAR redirects directly to the company page
    cik = _parse_cik_from_url(response.url)
    if cik:
        return cik

    # Multiple matches: parse the first company link from the results table.
    # Links look like: action=getcompany&amp;CIK=0000123456&amp;
    match = re.search(r"getcompany&amp;CIK=(\d{10})", response.text)
    if match:
        return int(match.group(1))

    return None


def pad_cik(cik: int | None) -> str | None:
    return str(cik).zfill(10) if cik is not None else None


def main(input_path: str, output_path: str) -> None:
    tickers_df = pd.read_csv(input_path)
    if "ticker" not in tickers_df.columns:
        sys.exit("Input CSV must have a 'ticker' column.")

    tickers = tickers_df["ticker"].str.upper().str.strip().tolist()

    print("Fetching SEC ticker data...")
    sec_map = fetch_sec_ticker_map()

    rows = []
    missing = []
    for ticker in tickers:
        cik = sec_map.get(ticker)
        if cik is None:
            missing.append(ticker)
        rows.append({"ticker": ticker, "cik": cik})

    if missing:
        print(f"Trying EDGAR fallbacks for {len(missing)} missing tickers...")
        cik_index = {row["ticker"]: i for i, row in enumerate(rows)}
        for ticker in missing:
            cik = lookup_cik_by_ticker_field(ticker) or scrape_cik_from_edgar_search(ticker)
            rows[cik_index[ticker]]["cik"] = cik
            status = f"found: {cik}" if cik else "not found"
            print(f"  {ticker}: {status}")

    for row in rows:
        row["cik"] = pad_cik(row["cik"])

    result_df = pd.DataFrame(rows)
    matched = result_df["cik"].notna().sum()
    total = len(result_df)

    result_df.to_csv(output_path, index=False)

    print(f"Matched: {matched}/{total} tickers")
    still_missing = result_df[result_df["cik"].isna()]["ticker"].tolist()
    if still_missing:
        print(f"Not found: {still_missing}")
    print(f"Output saved to: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python get_cik.py <input_csv> <output_csv>")
    main(sys.argv[1], sys.argv[2])
