"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Entry point to run the full stock data pipeline (fetch, validate, calculate KPIs) for any index and date range.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add data_pipeline to path
sys.path.insert(0, str(Path(__file__).parent / "data_pipeline"))

import data_pipeline.pipeline as _pipeline_mod
from data_pipeline.fetch import fetch_date_range, HISTORICAL_START
from data_pipeline.pipeline import DataPipeline


def load_indices_config() -> dict:
    cfg_path = Path(__file__).parent / "data/indices_config.json"
    if cfg_path.exists():
        with open(cfg_path) as f:
            return json.load(f)
    return {}


def main() -> None:
    args = sys.argv[1:]

    # --index
    index_key = "russell2000"
    if "--index" in args:
        pos = args.index("--index")
        if pos + 1 < len(args):
            index_key = args[pos + 1].lower().strip()

    # --start / --end / --today
    start_date = HISTORICAL_START
    end_date = datetime.today().strftime("%Y-%m-%d")
    if "--start" in args:
        pos = args.index("--start")
        if pos + 1 < len(args):
            start_date = args[pos + 1]
    if "--end" in args:
        pos = args.index("--end")
        if pos + 1 < len(args):
            end_date = args[pos + 1]
    if "--today" in args:
        start_date = end_date = datetime.today().strftime("%Y-%m-%d")

    # Resolve paths from indices_config.json
    cfg = load_indices_config()
    if cfg and index_key in cfg:
        idx_cfg = cfg[index_key]
        tickers_csv = idx_cfg.get("tickers_csv", "output.csv")
        index_name = idx_cfg.get("name", index_key)
        # data_root is parent of kpi_dir (e.g. data/sp500/stocks/kpis -> data/sp500)
        data_root = Path(idx_cfg.get("kpi_dir", "data/stocks/kpis")).parent.parent
        raw_dir = data_root / "stock" / "raw"
    else:
        tickers_csv = "output.csv"
        index_name = index_key
        data_root = Path("data")
        raw_dir = data_root / "stock" / "raw"

    print("=" * 60)
    print(f"Stock Pipeline — {index_name}")
    print(f"Tickers CSV  : {tickers_csv}")
    print(f"Raw stock dir: {raw_dir}")
    print(f"Date range   : {start_date} → {end_date}")
    print("=" * 60)

    # Step 1: Fetch raw stock data
    print("\nStep 1: Fetching stock data from yfinance...")
    fetch_date_range(
        start_date=start_date,
        end_date=end_date,
        output_dir=str(raw_dir),
        csv_path=tickers_csv,
    )

    # Step 2: Run validation + KPI pipeline
    # Patch the module-level RAW_STOCK_DIR so pipeline reads from the right place
    print("\nStep 2: Running validation + KPI pipeline...")
    _pipeline_mod.RAW_STOCK_DIR = raw_dir
    pipeline = DataPipeline(data_dir=data_root)
    pipeline.process_all_companies_all_transitions()

    print("\nDone.")


if __name__ == "__main__":
    main()
