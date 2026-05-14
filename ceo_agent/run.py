"""
CLI entry point for the CEO agent.

Usage:
  python -m ceo_agent.run           # interactive mode selector
  python -m ceo_agent.run batch     # run the next 100-company batch
  python -m ceo_agent.run test      # run first 2 companies
  python -m ceo_agent.run AAPL,MSFT # run specific tickers

Output files:
  sec_ceo_data/agent_batch_NNN.json
  sec_ceo_data/agent_batch_NNN.csv
  sec_ceo_data/agent_batch_NNN_progress.json  (rolling save, for resume)
"""

import csv
import json
import os
import sys
import time
from datetime import datetime
from typing import Optional

import pandas as pd

from .agent import CEOAgent
from .memory import BatchProgress

RUSSELL2000_CSV = "output.csv"
BATCH_SIZE = 100

_INDICES_CONFIG: dict = {}
_progress = BatchProgress()  # overridden inside main() per-index


def _load_indices_config() -> dict:
    global _INDICES_CONFIG
    if not _INDICES_CONFIG:
        cfg_path = "data/indices_config.json"
        if os.path.exists(cfg_path):
            with open(cfg_path) as f:
                _INDICES_CONFIG = json.load(f)
    return _INDICES_CONFIG


# ── Data loading ─────────────────────────────────────────────────────────────

def load_tickers(csv_path: str) -> list[tuple[str, str]]:
    """Return list of (ticker, cik) pairs that have a valid CIK."""
    df = pd.read_csv(csv_path, dtype=str)
    pairs = []
    for _, row in df.iterrows():
        ticker = str(row.get("ticker", "")).upper().strip()
        cik = str(row.get("cik", "")).strip()
        if ticker and cik and cik != "nan":
            # Ensure zero-padded to 10 digits
            cik = cik.zfill(10)
            pairs.append((ticker, cik))
    return pairs


# ── Saving helpers ────────────────────────────────────────────────────────────

def _save_results(results: list, batch_num: Optional[int], timestamp: str,
                  ceo_data_dir: str = "sec_ceo_data") -> tuple[str, str]:
    os.makedirs(ceo_data_dir, exist_ok=True)
    if batch_num is not None:
        json_file = f"{ceo_data_dir}/agent_batch_{batch_num:03d}.json"
        csv_file = f"{ceo_data_dir}/agent_batch_{batch_num:03d}.csv"
    else:
        json_file = f"{ceo_data_dir}/agent_{timestamp}.json"
        csv_file = f"{ceo_data_dir}/agent_{timestamp}.csv"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    rows = []
    for r in results:
        for ceo in r.get("ceo_timeline", []):
            rows.append({
                "Ticker": r["ticker"],
                "Company Name": r.get("company_name", ""),
                "CEO Name": ceo.get("name", ""),
                "Start Date": ceo.get("start_date", ""),
                "End Date": ceo.get("end_date", ""),
                "Source": ceo.get("source", ""),
                "Validation URL": ceo.get("validation_url", ""),
            })
    pd.DataFrame(rows).to_csv(csv_file, index=False)
    return json_file, csv_file


def _rolling_save(results: list, batch_num: Optional[int],
                  ceo_data_dir: str = "sec_ceo_data") -> None:
    os.makedirs(ceo_data_dir, exist_ok=True)
    if batch_num is not None:
        path = f"{ceo_data_dir}/agent_batch_{batch_num:03d}_progress.json"
    else:
        path = f"{ceo_data_dir}/agent_progress.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def _load_partial(batch_num: Optional[int], ceo_data_dir: str = "sec_ceo_data") -> list:
    if batch_num is None:
        return []
    path = f"{ceo_data_dir}/agent_batch_{batch_num:03d}_progress.json"
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


# ── Main ─────────────────────────────────────────────────────────────────────

def _sync_batch_to_timeline(batch_file: str, timeline_file: str) -> None:
    """Merge user-edited agent_batch_001.json into ceo_timeline_batch_001.json.

    For each company in batch_file that also exists in timeline_file:
    - Replace the timeline entry with the batch entry (batch is considered authoritative).
    Companies in timeline_file that are NOT in batch_file are left unchanged.
    """
    if not os.path.exists(batch_file):
        print(f"ERROR: {batch_file} not found")
        return
    if not os.path.exists(timeline_file):
        print(f"ERROR: {timeline_file} not found")
        return

    with open(batch_file, encoding="utf-8") as f:
        batch = json.load(f)
    with open(timeline_file, encoding="utf-8") as f:
        timeline = json.load(f)

    batch_by_ticker = {c["ticker"]: c for c in batch}
    updated = 0
    for i, entry in enumerate(timeline):
        t = entry["ticker"]
        if t in batch_by_ticker:
            # Preserve company_name from ceo_timeline if it's more informative
            old_name = entry.get("company_name", "")
            new_entry = dict(batch_by_ticker[t])
            if old_name and old_name != t and (not new_entry.get("company_name") or new_entry.get("company_name") == t):
                new_entry["company_name"] = old_name
            if timeline[i] != new_entry:
                timeline[i] = new_entry
                updated += 1

    with open(timeline_file, "w", encoding="utf-8") as f:
        json.dump(timeline, f, indent=2, ensure_ascii=False)
    print(f"Synced {updated} companies from {batch_file} → {timeline_file}")


def _retry_empty(batch_file: str) -> None:
    """Re-run the agent for companies with empty ceo_timeline in batch_file, in-place."""
    if not os.path.exists(batch_file):
        print(f"ERROR: {batch_file} not found")
        return

    with open(batch_file, encoding="utf-8") as f:
        data = json.load(f)

    all_pairs = load_tickers(RUSSELL2000_CSV)
    ticker_map = {t: c for t, c in all_pairs}

    empty = [(i, entry) for i, entry in enumerate(data) if not entry.get("ceo_timeline")]
    if not empty:
        print("No empty companies found in batch file.")
        return

    print(f"\nFound {len(empty)} companies with empty ceo_timeline:")
    for _, entry in empty:
        print(f"  {entry['ticker']}")

    agent = CEOAgent()
    for idx, (list_idx, entry) in enumerate(empty):
        ticker = entry["ticker"]
        cik = entry.get("cik") or ticker_map.get(ticker, "")
        company_name = entry.get("company_name") or ticker
        if not cik:
            print(f"\n  SKIP {ticker}: no CIK")
            continue

        print(f"\n{'#'*70}")
        print(f"[{idx+1}/{len(empty)}] RETRY: {ticker}  CIK={cik}")
        print(f"{'#'*70}")

        try:
            timeline = agent.run_company(ticker=ticker, cik=cik, company_name=company_name)
            data[list_idx]["ceo_timeline"] = timeline
            print(f"   {ticker}: {len(timeline)} CEO(s) found after retry")
            for ceo in timeline:
                print(f"     {ceo.get('name','?'):35} {ceo.get('start_date','?')} → {ceo.get('end_date','?')}")
        except Exception as e:
            print(f"   ERROR on {ticker}: {e}")
            import traceback
            traceback.print_exc()

        # Save after each company
        with open(batch_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        time.sleep(1)

    still_empty = [e["ticker"] for e in data if not e.get("ceo_timeline")]
    print(f"\nDone. Still empty: {still_empty or 'none'}")


def _rebuild_companies_json(ceo_data_dir: str = "sec_ceo_data", out_file: str = "data/companies.json") -> None:
    """Regenerate companies.json from all agent_batch_*.json files.

    Batches are merged in order (001, 002, ...). Later batches don't override
    earlier ones for the same ticker (first-seen wins), except agent_batch_001
    is always authoritative (user may have manually edited it).
    Also merges any extra companies from ceo_timeline_batch_001.json.
    """
    import glob
    timeline_file = f"{ceo_data_dir}/ceo_timeline_batch_001.json"

    # Collect all batch files sorted by number
    batch_files = sorted(glob.glob(f"{ceo_data_dir}/agent_batch_[0-9][0-9][0-9].json"))
    if not batch_files:
        print("No agent_batch_*.json files found.")
        return

    # Merge batches: batch_001 is authoritative, others add new tickers
    seen: dict = {}
    all_items: list = []
    for bf in batch_files:
        with open(bf, encoding="utf-8") as f:
            batch_data = json.load(f)
        print(f"  Loading {bf}: {len(batch_data)} companies")
        for item in batch_data:
            t = item["ticker"]
            if t not in seen:
                seen[t] = True
                all_items.append(item)
            elif bf.endswith("agent_batch_001.json"):
                # batch_001 is authoritative — replace if already seen from timeline
                for i, existing in enumerate(all_items):
                    if existing["ticker"] == t:
                        all_items[i] = item
                        break

    # Add companies from ceo_timeline_batch_001 not in any batch file
    if os.path.exists(timeline_file):
        with open(timeline_file, encoding="utf-8") as f:
            timeline_data = json.load(f)
        for item in timeline_data:
            if item["ticker"] not in seen:
                seen[item["ticker"]] = True
                all_items.append(item)

    # Preserve existing sector data
    existing_sectors: dict = {}
    if os.path.exists(out_file):
        try:
            with open(out_file, encoding="utf-8") as f:
                existing = json.load(f)
            for c in existing.get("companies", []):
                if c.get("sector") and c["sector"] != "Unknown":
                    existing_sectors[c["ticker"]] = c["sector"]
        except Exception:
            pass

    companies = []
    for item in all_items:
        ticker = item["ticker"]
        company_name = item.get("company_name") or ticker
        sector = existing_sectors.get(ticker, "Unknown")
        transitions = []
        timeline = item.get("ceo_timeline", [])
        for i in range(len(timeline) - 1):
            cur = timeline[i]
            nxt = timeline[i + 1]
            transitions.append({
                "previousCEO": cur.get("name", "Unknown"),
                "newCEO": nxt.get("name", "Unknown"),
                "transitionDate": nxt.get("start_date") or cur.get("end_date") or "",
                "startDate": nxt.get("start_date") or "",
                "endDate": nxt.get("end_date") or "Present",
            })
        companies.append({
            "ticker": ticker,
            "name": company_name,
            "sector": sector,
            "transitions": transitions,
        })

    total_transitions = sum(len(c["transitions"]) for c in companies)
    companies_with = sum(1 for c in companies if c["transitions"])

    result = {
        "totalCompanies": len(companies),
        "companiesWithTransitions": companies_with,
        "totalTransitions": total_transitions,
        "dateRange": "1996-2026",
        "companies": companies,
    }
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Rebuilt {out_file}: {len(companies)} companies, {total_transitions} transitions")


def _lookup_company_name(cik: str) -> str:
    """Look up the official company name from SEC EDGAR submissions API."""
    try:
        import requests as _req
        r = _req.get(
            f"https://data.sec.gov/submissions/CIK{cik}.json",
            headers={"User-Agent": "CEOResearch jyothirmai@mhktechinc.com"},
            timeout=10,
        )
        if r.status_code == 200:
            return r.json().get("name", "") or ""
    except Exception:
        pass
    return ""


def main() -> None:
    # ── Parse --index flag (e.g. --index sp500) ──────────────────────────────
    argv = [a for a in sys.argv[1:] if a not in ("--index",)]
    index_key = "russell2000"
    if "--index" in sys.argv:
        idx_pos = sys.argv.index("--index")
        if idx_pos + 1 < len(sys.argv):
            index_key = sys.argv[idx_pos + 1].lower().strip()
            # Remove --index and its value from argv for the rest of arg parsing
            argv = [a for a in sys.argv[1:] if a not in ("--index", index_key)]

    # ── Parse --batch-num N (explicit batch, skips shared progress file) ─────
    explicit_batch_num: Optional[int] = None
    if "--batch-num" in sys.argv:
        bn_pos = sys.argv.index("--batch-num")
        if bn_pos + 1 < len(sys.argv):
            try:
                explicit_batch_num = int(sys.argv[bn_pos + 1])
            except ValueError:
                pass
            argv = [a for a in argv if a not in ("--batch-num", sys.argv[bn_pos + 1])]

    # Load index config
    cfg = _load_indices_config()
    if cfg and index_key in cfg:
        idx_cfg = cfg[index_key]
        tickers_csv = idx_cfg.get("tickers_csv", RUSSELL2000_CSV)
        ceo_data_dir = idx_cfg.get("ceo_data_dir", "sec_ceo_data")
        companies_file = idx_cfg.get("companies_file", "data/companies.json")
        index_name = idx_cfg.get("name", index_key)
    else:
        tickers_csv = RUSSELL2000_CSV
        ceo_data_dir = "sec_ceo_data"
        companies_file = "data/companies.json"
        index_name = index_key

    progress = BatchProgress(path=f"{ceo_data_dir}/agent_batch_progress.json")

    print("=" * 70)
    print(f"CEO AGENT — OpenAI GPT-4o + SEC 8-K + Web Search")
    print(f"Index: {index_name}  |  Period: 2000-present")
    print("=" * 70)

    os.makedirs(ceo_data_dir, exist_ok=True)

    # Parse CLI argument (first non-flag arg)
    arg = argv[0].strip().lower() if argv else ""

    # Sync mode: merge agent_batch_001 edits into ceo_timeline_batch_001
    if arg == "sync":
        _sync_batch_to_timeline(
            f"{ceo_data_dir}/agent_batch_001.json",
            f"{ceo_data_dir}/ceo_timeline_batch_001.json",
        )
        return

    # Rebuild mode: regenerate companies.json from all batch files
    if arg == "rebuild":
        _rebuild_companies_json(ceo_data_dir=ceo_data_dir, out_file=companies_file)
        return

    # Retry mode: re-run empty companies in a specific batch file then rebuild
    if arg == "retry":
        batch_arg = argv[1].strip().zfill(3) if len(argv) > 1 else "001"
        batch_file = f"{ceo_data_dir}/agent_batch_{batch_arg}.json"
        _retry_empty(batch_file)
        if batch_arg == "001":
            print(f"\nAuto-syncing to {ceo_data_dir}/ceo_timeline_batch_001.json...")
            _sync_batch_to_timeline(
                f"{ceo_data_dir}/agent_batch_001.json",
                f"{ceo_data_dir}/ceo_timeline_batch_001.json",
            )
        _rebuild_companies_json(ceo_data_dir=ceo_data_dir, out_file=companies_file)
        return

    print(f"\nLoading tickers from {tickers_csv}...")
    all_pairs = load_tickers(tickers_csv)
    print(f"Loaded {len(all_pairs)} tickers with CIK.")

    # Determine next_index: explicit --batch-num overrides shared progress file
    if explicit_batch_num is not None:
        next_index = (explicit_batch_num - 1) * BATCH_SIZE
    else:
        next_index = progress.read()
    batch_num_default = next_index // BATCH_SIZE + 1
    batch_pairs = all_pairs[next_index: next_index + BATCH_SIZE]

    if arg in ("batch", "5"):
        if not batch_pairs:
            print(f"All batches complete. Delete {ceo_data_dir}/agent_batch_progress.json to restart.")
            return
        pairs = batch_pairs
        batch_num = batch_num_default
    elif arg in ("test", "1"):
        pairs = all_pairs[:2]
        batch_num = None
    elif arg in ("small", "2"):
        pairs = all_pairs[:5]
        batch_num = None
    elif arg in ("ten", "3"):
        pairs = all_pairs[:10]
        batch_num = None
    elif arg in ("medium", "4"):
        pairs = all_pairs[:25]
        batch_num = None
    elif "," in arg or (arg and arg.upper() == arg):
        # Comma-separated tickers or single uppercase ticker
        raw = sys.argv[1].upper().replace(" ", "")
        requested = [t.strip() for t in raw.split(",") if t.strip()]
        ticker_map = {t: c for t, c in all_pairs}
        pairs = [(t, ticker_map[t]) for t in requested if t in ticker_map]
        missing = [t for t in requested if t not in ticker_map]
        if missing:
            print(f"WARNING: tickers not found in {tickers_csv}: {missing}")
        if not pairs:
            print("No valid tickers to process.")
            return
        batch_num = None
    else:
        # Interactive
        print(f"\nSELECT MODE:")
        print(f"1. Test    (first 2 companies)")
        print(f"2. Small   (first 5 companies)")
        print(f"3. Ten     (first 10 companies)")
        print(f"4. Medium  (first 25 companies)")
        if batch_pairs:
            print(f"5. Batch   (batch {batch_num_default}: companies "
                  f"{next_index+1}–{next_index+len(batch_pairs)} of {len(all_pairs)})")
        else:
            print(f"5. Batch   (ALL COMPLETE)")
        print(f"6. Custom  (enter tickers)")
        choice = input("\nChoice (1-6): ").strip()

        if choice == "6":
            raw = input("Enter tickers (comma-separated): ").strip().upper()
            requested = [t.strip() for t in raw.split(",") if t.strip()]
            ticker_map = {t: c for t, c in all_pairs}
            pairs = [(t, ticker_map[t]) for t in requested if t in ticker_map]
            batch_num = None
        elif choice == "5":
            if not batch_pairs:
                print("All batches complete.")
                return
            pairs = batch_pairs
            batch_num = batch_num_default
        elif choice == "4":
            pairs = all_pairs[:25]
            batch_num = None
        elif choice == "3":
            pairs = all_pairs[:10]
            batch_num = None
        elif choice == "2":
            pairs = all_pairs[:5]
            batch_num = None
        else:
            pairs = all_pairs[:2]
            batch_num = None

    # Save full batch size before resume filtering (used for progress advance)
    full_batch_size = len(pairs)

    # Resume within-batch
    already_done = _load_partial(batch_num, ceo_data_dir=ceo_data_dir)
    if already_done:
        done_tickers = {r["ticker"] for r in already_done}
        remaining = [(t, c) for t, c in pairs if t not in done_tickers]
        print(f"\nResuming batch {batch_num}: {len(already_done)} done, {len(remaining)} remaining")
        pairs = remaining
    else:
        remaining = pairs

    # If batch is already fully complete, advance pointer and exit
    if batch_num is not None and len(pairs) == 0 and already_done:
        print(f"\nBatch {batch_num} already complete. Advancing to next batch.")
        progress.write(next_index + full_batch_size, len(all_pairs))
        print(f"Rebuilding {companies_file}...")
        _rebuild_companies_json(ceo_data_dir=ceo_data_dir, out_file=companies_file)
        print(f"Run again to start batch {batch_num + 1}.")
        return

    print(f"\nWill process {len(pairs)} companies")
    tickers_preview = [t for t, _ in pairs[:15]]
    print(f"Companies: {', '.join(tickers_preview)}{'...' if len(pairs) > 15 else ''}")

    if not argv:  # interactive mode (no CLI args)
        confirm = input("\nContinue? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Cancelled.")
            return

    agent = CEOAgent()
    results = list(already_done)
    start_time = datetime.now()
    timestamp = start_time.strftime("%Y%m%d_%H%M%S")

    for i, (ticker, cik) in enumerate(pairs):
        if i > 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            avg = elapsed / i
            eta = avg * (len(pairs) - i)
            print(f"\n   Progress: {i}/{len(pairs)} | ~{eta/60:.1f} min remaining")

        print(f"\n{'#'*70}")
        print(f"[{i+1}/{len(pairs)}] {ticker}  CIK={cik}")
        print(f"{'#'*70}")

        try:
            company_name = _lookup_company_name(cik) or ticker
            timeline = agent.run_company(ticker=ticker, cik=cik, company_name=company_name)

            result = {
                "ticker": ticker,
                "cik": cik,
                "company_name": company_name,
                "ceo_timeline": timeline,
            }
            results.append(result)
            _rolling_save(results, batch_num, ceo_data_dir=ceo_data_dir)

            # Print mini-summary
            print(f"\n   {ticker}: {len(timeline)} CEO(s) found")
            for ceo in timeline:
                print(f"     {ceo.get('name','?'):30} {ceo.get('start_date','?')} → {ceo.get('end_date','?')}")

            time.sleep(1)
        except Exception as e:
            print(f"\n   ERROR processing {ticker}: {e}")
            import traceback
            traceback.print_exc()

    # Save final results
    json_file, csv_file = _save_results(results, batch_num, timestamp, ceo_data_dir=ceo_data_dir)

    # Advance batch pointer — skip if --batch-num was used (parallel mode: no shared pointer)
    if batch_num is not None:
        if explicit_batch_num is None:
            progress.write(next_index + full_batch_size, len(all_pairs))
        # Auto-rebuild companies.json after each named batch
        print(f"\nRebuilding {companies_file}...")
        _rebuild_companies_json(ceo_data_dir=ceo_data_dir, out_file=companies_file)

    elapsed = (datetime.now() - start_time).total_seconds()
    total_ceos = sum(len(r.get("ceo_timeline", [])) for r in results)

    print(f"\n{'='*70}")
    print(f"DONE")
    print(f"{'='*70}")
    print(f"Time      : {elapsed/60:.1f} minutes")
    print(f"Companies : {len(results)}")
    print(f"CEOs found: {total_ceos}")
    print(f"\nOutput:")
    print(f"  CSV : {csv_file}")
    print(f"  JSON: {json_file}")
    print(f"\n{'─'*70}")
    print(f"{'Ticker':<8} {'CEOs':<6} {'First CEO':<30} {'Last CEO'}")
    print(f"{'─'*70}")
    for r in results:
        tl = r.get("ceo_timeline", [])
        first = tl[0]["name"] if tl else "—"
        last = tl[-1]["name"] if tl else "—"
        print(f"{r['ticker']:<8} {len(tl):<6} {first[:29]:<30} {last}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
