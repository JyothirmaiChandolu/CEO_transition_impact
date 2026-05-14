"""
Fetch company metadata for all tickers using yfinance.

Usage:
  python fetch_company_metadata.py                     # Russell 2000
  python fetch_company_metadata.py --index sp500       # S&P 500
  python fetch_company_metadata.py --force             # re-fetch everything
  python fetch_company_metadata.py AAPL,MSFT           # specific tickers
"""

import json
import os
import sys
import time

import pandas as pd
import yfinance as yf

# Defaults (overridden by --index)
INPUT_CSV = "output.csv"
OUTPUT_FILE = "data/company_metadata.json"
BATCH_SIZE = 50       # save progress every N tickers
SLEEP_BETWEEN = 0.3   # seconds between requests

FIELDS = {
    "longName":           "name",
    "sector":             "sector",
    "sectorDisp":         "sectorDisp",
    "industry":           "industry",
    "industryDisp":       "industryDisp",
    "country":            "country",
    "state":              "state",
    "city":               "city",
    "website":            "website",
    "fullTimeEmployees":  "employees",
    "marketCap":          "marketCap",
    "longBusinessSummary": "description",
    "exchange":           "exchange",
    "quoteType":          "quoteType",
    "currency":           "currency",
}


def load_tickers() -> list[str]:
    df = pd.read_csv(INPUT_CSV, dtype=str)
    return [str(row["ticker"]).upper().strip() for _, row in df.iterrows()
            if str(row.get("ticker", "")).strip()]


def load_existing() -> dict:
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save(data: dict) -> None:
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def fetch_one(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).info
        result = {}
        for yf_key, out_key in FIELDS.items():
            val = info.get(yf_key)
            if val is not None and val != "":
                result[out_key] = val
        # Prefer sectorDisp/industryDisp if available (cleaner display names)
        if result.get("sectorDisp"):
            result["sector"] = result.pop("sectorDisp")
        else:
            result.pop("sectorDisp", None)
        if result.get("industryDisp"):
            result["industry"] = result.pop("industryDisp")
        else:
            result.pop("industryDisp", None)
        return result
    except Exception as e:
        return {"error": str(e)}


def main() -> None:
    global INPUT_CSV, OUTPUT_FILE

    force = "--force" in sys.argv

    # --index support
    if "--index" in sys.argv:
        idx_pos = sys.argv.index("--index")
        if idx_pos + 1 < len(sys.argv):
            index_key = sys.argv[idx_pos + 1].lower().strip()
            cfg_path = "data/indices_config.json"
            if os.path.exists(cfg_path):
                with open(cfg_path) as f:
                    cfg = json.load(f)
                if index_key in cfg:
                    idx_cfg = cfg[index_key]
                    INPUT_CSV = idx_cfg.get("tickers_csv", INPUT_CSV)
                    OUTPUT_FILE = idx_cfg.get("metadata_file", OUTPUT_FILE)
                    print(f"Index: {idx_cfg.get('name', index_key)}")
                    print(f"Input: {INPUT_CSV}  →  Output: {OUTPUT_FILE}")

    # Specific tickers mode
    specific: list[str] = []
    for arg in sys.argv[1:]:
        if arg.startswith("--"):
            continue
        if "," in arg or arg.upper() == arg:
            specific = [t.strip() for t in arg.upper().split(",") if t.strip()]

    all_tickers = specific if specific else load_tickers()
    existing = {} if force else load_existing()

    to_fetch = [t for t in all_tickers if t not in existing]
    print(f"Total tickers : {len(all_tickers)}")
    print(f"Already fetched: {len(existing)}")
    print(f"To fetch now  : {len(to_fetch)}")

    if not to_fetch:
        print("Nothing to fetch. Use --force to re-fetch all.")
        return

    results = dict(existing)
    errors: list[str] = []

    for i, ticker in enumerate(to_fetch):
        meta = fetch_one(ticker)
        results[ticker] = meta

        name = meta.get("name", "")
        sector = meta.get("sector", "")
        err = meta.get("error", "")
        status = f"[{ticker}] {name[:30]:<30} {sector:<25}" if not err else f"[{ticker}] ERROR: {err[:60]}"
        print(f"  {i+1:4}/{len(to_fetch)}  {status}")

        if err:
            errors.append(ticker)

        if (i + 1) % BATCH_SIZE == 0:
            save(results)
            print(f"  --- saved {len(results)} records ---")

        time.sleep(SLEEP_BETWEEN)

    save(results)

    filled = sum(1 for v in results.values() if v.get("name") or v.get("sector"))
    print(f"\nDone.")
    print(f"  Total saved : {len(results)}")
    print(f"  With data   : {filled}")
    print(f"  Errors      : {len(errors)}")
    if errors:
        print(f"  Error tickers: {errors[:20]}{'...' if len(errors) > 20 else ''}")
    print(f"\nOutput: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
