"""
Title: CEO performance analysis
Author: Jyothirmai Chandolu
Employee_id: 800342

Data Fetching Module
Fetches stock data from yfinance for Russell 2000 companies
"""
import json
import time
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)
logging.getLogger("yfinance").setLevel(logging.CRITICAL)  # silence yfinance noise; retries handle failures

PROJECT_ROOT = Path(__file__).parent.parent
_CONFIG_FILE = PROJECT_ROOT / "data" / "indices_config.json"

HISTORICAL_START = "1996-01-01"
BATCH_SIZE = 50   # reduced from 100 — smaller batches hit rate limits less often
BATCH_DELAY = 2   # seconds to sleep between batches


def load_index_config(index_key: str) -> dict:
    """Load path config for a given index key from indices_config.json.

    Returns a dict with absolute paths resolved from the project root:
        tickers_csv, raw_stock_dir, data_dir, companies_file, ...
    """
    with open(_CONFIG_FILE) as f:
        cfg = json.load(f)
    if index_key not in cfg:
        raise KeyError(f"Unknown index '{index_key}'. Available: {list(cfg)}")
    entry = cfg[index_key]
    return {k: str(PROJECT_ROOT / v) if isinstance(v, str) and "/" in v else v
            for k, v in entry.items()}


# Backwards-compatible module-level defaults — resolved from config at import time.
def _default_paths() -> tuple:
    try:
        cfg = load_index_config("russell2000")
        return cfg["tickers_csv"], cfg["raw_stock_dir"]
    except Exception:
        return "", ""

TICKERS_CSV, DATA_DIR = _default_paths()

_OHLCV_FIELDS = {"Open", "High", "Low", "Close", "Volume", "Adj Close"}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def load_tickers(csv_path: str = TICKERS_CSV) -> List[str]:
    """Load ticker symbols from the Russell 2000 CSV file."""
    df = pd.read_csv(csv_path)
    return df["ticker"].dropna().str.strip().tolist()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_raw(raw: pd.DataFrame, batch_tickers: List[str]) -> pd.DataFrame:
    """Convert yfinance download output into a normalized (date, ticker, ohlcv) DataFrame."""
    if raw.empty:
        return pd.DataFrame()

    records = []

    if isinstance(raw.columns, pd.MultiIndex):
        lvl0 = raw.columns.get_level_values(0).unique().tolist()

        if any(f in _OHLCV_FIELDS for f in lvl0):
            # Default multi-ticker layout: (field, ticker)
            available_tickers = raw.columns.get_level_values(1).unique().tolist()
            for ticker in available_tickers:
                try:
                    t_df = raw.xs(ticker, axis=1, level=1).dropna(how="all").reset_index()
                    t_df["ticker"] = ticker
                    records.append(t_df)
                except KeyError:
                    pass
        else:
            # group_by='ticker' layout: (ticker, field)
            for ticker in lvl0:
                try:
                    t_df = raw[ticker].dropna(how="all").reset_index()
                    t_df["ticker"] = ticker
                    records.append(t_df)
                except KeyError:
                    pass
    else:
        # Single-ticker download
        t_df = raw.dropna(how="all").reset_index()
        t_df["ticker"] = batch_tickers[0].upper() if batch_tickers else "UNKNOWN"
        records.append(t_df)

    if not records:
        return pd.DataFrame()

    df = pd.concat(records, ignore_index=True)
    df.columns = [str(c).lower() for c in df.columns]

    for dc in ("date", "datetime"):
        if dc in df.columns:
            df = df.rename(columns={dc: "date"})
            break

    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df["ticker"] = df["ticker"].str.upper()

    for col in ("open", "high", "low", "close", "adj close"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)
    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype(int)

    keep = ["date", "ticker", "open", "high", "low", "close", "volume"]
    return df[[c for c in keep if c in df.columns]].dropna(subset=["date", "ticker"])


def _fetch_batch(tickers: List[str], start: str, end_exclusive: str) -> pd.DataFrame:
    """Download one batch of tickers from yfinance and return a normalized DataFrame.

    Any ticker that fails in the batch is retried individually so one bad ticker
    cannot silently drop valid neighbours.
    """
    try:
        raw = yf.download(tickers, start=start, end=end_exclusive, progress=False)
        df = _parse_raw(raw, tickers)
    except Exception as e:
        logger.error(f"Batch download failed (first ticker: {tickers[0]}): {e}")
        df = pd.DataFrame()

    if len(tickers) == 1:
        return df

    # Find which tickers came back and retry the missing ones individually
    returned = set(df["ticker"].unique()) if not df.empty else set()
    missing = [t for t in tickers if t.upper() not in returned]

    if missing:
        logger.info(f"Retrying {len(missing)} tickers individually: {missing}")
        parts = [df] if not df.empty else []
        for t in missing:
            try:
                raw_t = yf.download(t, start=start, end=end_exclusive, progress=False)
                t_df = _parse_raw(raw_t, [t])
                if not t_df.empty:
                    parts.append(t_df)
            except Exception:
                pass
        df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()

    return df


def _save_by_date(df: pd.DataFrame, output_dir: str) -> None:
    """Partition df by date and save/merge into year/month/YYYY-MM-DD.csv files."""
    if df.empty:
        return

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    for date_val, group in df.groupby("date"):
        year  = date_val.strftime("%Y")
        month = date_val.strftime("%m")
        fname = date_val.strftime("%Y-%m-%d") + ".csv"

        dir_path = Path(output_dir) / year / month
        dir_path.mkdir(parents=True, exist_ok=True)
        file_path = dir_path / fname

        group_out = group.copy()
        group_out["date"] = group_out["date"].dt.strftime("%Y-%m-%d")

        if file_path.exists():
            existing = pd.read_csv(file_path)
            combined = (
                pd.concat([existing, group_out], ignore_index=True)
                .drop_duplicates(subset=["date", "ticker"])
            )
            combined.to_csv(file_path, index=False)
        else:
            group_out.to_csv(file_path, index=False)


# ---------------------------------------------------------------------------
# Public fetch functions
# ---------------------------------------------------------------------------

def fetch_date_range(
    start_date: str,
    end_date: str,
    output_dir: str = DATA_DIR,
    csv_path: str = TICKERS_CSV,
    batch_size: int = BATCH_SIZE,
) -> None:
    """
    Fetch and store stock data for all Russell 2000 tickers over a date range.

    Folder layout: output_dir/YYYY/MM/YYYY-MM-DD.csv
    Each CSV contains one row per ticker for that trading day.

    Args:
        start_date:  Start date inclusive, YYYY-MM-DD
        end_date:    End date inclusive, YYYY-MM-DD
        output_dir:  Root directory for output files
        csv_path:    Path to tickers CSV
        batch_size:  Number of tickers per yfinance batch request
    """
    tickers = load_tickers(csv_path)
    # yfinance end date is exclusive
    end_exclusive = (
        datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
    ).strftime("%Y-%m-%d")

    total_batches = (len(tickers) + batch_size - 1) // batch_size
    logger.info(
        f"Fetching {len(tickers)} tickers from {start_date} to {end_date} "
        f"in {total_batches} batches"
    )

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i : i + batch_size]
        batch_num = i // batch_size + 1
        logger.info(
            f"Batch {batch_num}/{total_batches}: "
            f"tickers {i + 1}–{min(i + batch_size, len(tickers))}"
        )
        df = _fetch_batch(batch, start_date, end_exclusive)
        if not df.empty:
            _save_by_date(df, output_dir)
        time.sleep(BATCH_DELAY)

    logger.info("Done.")


def fetch_historical(
    output_dir: str = DATA_DIR,
    csv_path: str = TICKERS_CSV,
    batch_size: int = BATCH_SIZE,
) -> None:
    """
    Fetch all available historical data from 1996-01-01 to today for all Russell 2000 tickers.

    Args:
        output_dir:  Root directory for output files
        csv_path:    Path to tickers CSV
        batch_size:  Number of tickers per yfinance batch request
    """
    today = datetime.now().strftime("%Y-%m-%d")
    fetch_date_range(HISTORICAL_START, today, output_dir, csv_path, batch_size)


def fetch_single_date(
    target_date: str,
    output_dir: str = DATA_DIR,
    csv_path: str = TICKERS_CSV,
    batch_size: int = BATCH_SIZE,
) -> None:
    """
    Fetch stock data for all Russell 2000 tickers on a specific date.

    Args:
        target_date: Date in YYYY-MM-DD format
        output_dir:  Root directory for output files
        csv_path:    Path to tickers CSV
        batch_size:  Number of tickers per yfinance batch request
    """
    fetch_date_range(target_date, target_date, output_dir, csv_path, batch_size)


def fetch_current(
    output_dir: str = DATA_DIR,
    csv_path: str = TICKERS_CSV,
    batch_size: int = BATCH_SIZE,
) -> None:
    """
    Fetch today's stock data for all Russell 2000 tickers.

    Args:
        output_dir:  Root directory for output files
        csv_path:    Path to tickers CSV
        batch_size:  Number of tickers per yfinance batch request
    """
    today = datetime.now().strftime("%Y-%m-%d")
    fetch_date_range(today, today, output_dir, csv_path, batch_size)


# ---------------------------------------------------------------------------
# Legacy class — kept for backwards compatibility
# ---------------------------------------------------------------------------

class StockDataFetcher:
    """Fetches stock data from Yahoo Finance (single-ticker interface)."""

    def __init__(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        if start_date is None:
            start = datetime.now() - timedelta(days=365 * 30)
            self.start_date = start.strftime("%Y-%m-%d")
        else:
            self.start_date = start_date

    def fetch_stock_data(self, ticker: str) -> Optional[pd.DataFrame]:
        end_exclusive = (
            datetime.strptime(self.end_date, "%Y-%m-%d") + timedelta(days=1)
        ).strftime("%Y-%m-%d")
        df = _fetch_batch([ticker], self.start_date, end_exclusive)
        return df if not df.empty else None

    def fetch_multiple_stocks(self, tickers: List[str]) -> Dict[str, Optional[pd.DataFrame]]:
        end_exclusive = (
            datetime.strptime(self.end_date, "%Y-%m-%d") + timedelta(days=1)
        ).strftime("%Y-%m-%d")
        results: Dict[str, Optional[pd.DataFrame]] = {}
        for i in range(0, len(tickers), BATCH_SIZE):
            batch = tickers[i : i + BATCH_SIZE]
            df = _fetch_batch(batch, self.start_date, end_exclusive)
            for ticker in batch:
                subset = df[df["ticker"] == ticker.upper()] if not df.empty else pd.DataFrame()
                results[ticker] = subset if not subset.empty else None
        return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch stock data for a configured index.")
    parser.add_argument("--index", default="russell2000",
                        help="Index key from data/indices_config.json (default: russell2000)")
    parser.add_argument("--start", default=None,
                        help="Start date YYYY-MM-DD. Omit to fetch full history from 1996.")
    parser.add_argument("--end", default=None,
                        help="End date YYYY-MM-DD (default: today). Only used with --start.")
    args = parser.parse_args()

    cfg = load_index_config(args.index)
    csv_path = cfg["tickers_csv"]
    raw_dir  = cfg["raw_stock_dir"]

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(PROJECT_ROOT / "fetch_historical.log"),
        ],
    )

    if args.start:
        end = args.end or datetime.now().strftime("%Y-%m-%d")
        fetch_date_range(args.start, end, output_dir=raw_dir, csv_path=csv_path)
    else:
        fetch_historical(output_dir=raw_dir, csv_path=csv_path)