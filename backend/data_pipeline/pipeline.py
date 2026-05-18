"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Orchestrates data validation, transformation, and KPI calculation for pre-fetched Russell 2000 stock data.
"""
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from fetch import load_tickers, TICKERS_CSV, DATA_DIR, load_index_config
from validate import DataValidator
from calculate_kpis import KPICalculator

logger = logging.getLogger(__name__)


class DataPipeline:
    """Orchestrates the complete data pipeline over pre-fetched raw stock CSVs."""

    def __init__(self, data_dir: Path = None, raw_stock_dir: Path = None):
        """
        Args:
            data_dir:      Root directory for processed output (e.g. data/rus2000).
            raw_stock_dir: Directory containing pre-fetched raw stock CSVs.
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / 'data'
        self.data_dir = Path(data_dir)
        self.raw_stock_dir = Path(raw_stock_dir) if raw_stock_dir else self.data_dir / 'stock' / 'raw'
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.validator = DataValidator()
        self.kpi_calculator = KPICalculator()

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # ------------------------------------------------------------------
    # Raw data loader
    # ------------------------------------------------------------------

    def _build_ticker_cache(self) -> Dict[str, Any]:
        """
        Read every raw CSV once, concat into one DataFrame, and partition by ticker.
        Result is cached on self so subsequent calls are free.
        """
        import pandas as pd

        if hasattr(self, '_ticker_cache'):
            return self._ticker_cache

        all_files = sorted(self.raw_stock_dir.glob("**/*.csv"))
        logger.info(f"Building ticker cache: reading {len(all_files)} CSV files...")

        dfs = []
        for f in all_files:
            try:
                dfs.append(pd.read_csv(f, dtype={"ticker": str}))
            except Exception as e:
                logger.warning(f"Skipping {f.name}: {e}")

        if not dfs:
            self._ticker_cache = {}
            return {}

        combined = pd.concat(dfs, ignore_index=True).sort_values("date")
        self._ticker_cache = {
            ticker: grp.reset_index(drop=True)
            for ticker, grp in combined.groupby("ticker")
        }
        logger.info(f"Cache ready: {len(self._ticker_cache)} tickers in memory")
        return self._ticker_cache

    def _load_ticker_from_raw(self, ticker: str) -> Optional[object]:
        """Return cached DataFrame for one ticker (triggers cache build on first call)."""
        cache = self._build_ticker_cache()
        result = cache.get(ticker.upper())
        return result if result is not None else None

    # ------------------------------------------------------------------
    # Single-stock processing
    # ------------------------------------------------------------------

    def process_stock(self, ticker: str, transition_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a single stock: load from raw CSVs → validate → KPIs → save.

        Args:
            ticker: Stock ticker symbol
            transition_date: Optional CEO transition date (YYYY-MM-DD)
        """
        result = {'ticker': ticker, 'timestamp': datetime.now().isoformat(), 'stages': {}}

        # Stage 1: Load from raw CSVs
        logger.info(f"[{ticker}] Stage 1: Loading from raw CSVs...")
        raw_data = self._load_ticker_from_raw(ticker)
        if raw_data is None or len(raw_data) == 0:
            result['stages']['fetch'] = {'status': 'failed', 'message': 'No data in raw CSVs'}
            return result

        result['stages']['fetch'] = {
            'status': 'success',
            'records': len(raw_data),
            'date_range': f"{raw_data['date'].iloc[0]} to {raw_data['date'].iloc[-1]}"
        }

        # Stage 2: Validate
        logger.info(f"[{ticker}] Stage 2: Validating...")
        valid_df, invalid_df, stats = self.validator.validate_dataframe(raw_data)
        result['stages']['validate'] = {
            'status': 'success',
            'total_rows': stats['total_rows'],
            'valid_rows': stats['valid_rows'],
            'invalid_rows': stats['invalid_rows'],
            'errors': len(stats['errors'])
        }

        if len(valid_df) == 0:
            result['stages']['validate']['status'] = 'failed'
            result['stages']['validate']['message'] = 'No valid records after validation'
            return result

        # Stage 3: Save validated data
        logger.info(f"[{ticker}] Stage 3: Saving validated data...")
        valid_path, invalid_path = self.validator.save_validation_results(
            valid_df, invalid_df, ticker, self.data_dir
        )
        result['stages']['save'] = {'status': 'success', 'valid_path': str(valid_path)}

        # Stage 4: Calculate KPIs
        logger.info(f"[{ticker}] Stage 4: Calculating KPIs...")
        kpis = self.kpi_calculator.calculate_all_kpis(valid_df, ticker, transition_date)

        # Stage 5: Save KPIs
        logger.info(f"[{ticker}] Stage 5: Saving KPIs...")
        kpi_dir = self.data_dir / 'stocks' / 'kpis'
        kpi_dir.mkdir(parents=True, exist_ok=True)
        kpi_path = kpi_dir / f'{ticker}_kpis.json'
        with open(kpi_path, 'w') as f:
            json.dump(kpis, f, indent=2)

        result['stages']['kpi'] = {
            'status': 'success',
            'kpi_path': str(kpi_path),
            'metrics': {
                'price_metrics': len(kpis.get('price_metrics', {})),
                'volume_metrics': len(kpis.get('volume_metrics', {})),
                'risk_metrics': len(kpis.get('risk_metrics', {}))
            }
        }

        result['status'] = 'success'
        return result

    def process_stock_with_all_transitions(self, ticker: str, transitions_list: List[str]) -> Dict[str, Any]:
        """
        Process a single stock with multiple CEO transition dates.

        Args:
            ticker: Stock ticker symbol
            transitions_list: List of transition dates (YYYY-MM-DD)
        """
        result = {'ticker': ticker, 'timestamp': datetime.now().isoformat(), 'stages': {}}

        # Stage 1: Load from raw CSVs
        logger.info(f"[{ticker}] Stage 1: Loading from raw CSVs...")
        raw_data = self._load_ticker_from_raw(ticker)
        if raw_data is None or len(raw_data) == 0:
            result['stages']['fetch'] = {'status': 'failed', 'message': 'No data in raw CSVs'}
            return result

        result['stages']['fetch'] = {
            'status': 'success',
            'records': len(raw_data),
            'date_range': f"{raw_data['date'].iloc[0]} to {raw_data['date'].iloc[-1]}"
        }

        # Stage 2: Validate
        logger.info(f"[{ticker}] Stage 2: Validating...")
        valid_df, invalid_df, stats = self.validator.validate_dataframe(raw_data)
        result['stages']['validate'] = {
            'status': 'success',
            'total_rows': stats['total_rows'],
            'valid_rows': stats['valid_rows'],
            'invalid_rows': stats['invalid_rows']
        }

        if len(valid_df) == 0:
            result['stages']['validate']['status'] = 'failed'
            return result

        # Stage 3: Save validated data
        logger.info(f"[{ticker}] Stage 3: Saving validated data...")
        valid_path, invalid_path = self.validator.save_validation_results(
            valid_df, invalid_df, ticker, self.data_dir
        )
        result['stages']['save'] = {'status': 'success', 'valid_path': str(valid_path)}

        # Stage 4: Calculate KPIs with all transitions
        logger.info(f"[{ticker}] Stage 4: Calculating KPIs for {len(transitions_list)} transitions...")
        kpis = self.kpi_calculator.calculate_all_kpis(valid_df, ticker, transition_dates=transitions_list)

        # Stage 5: Save KPIs
        logger.info(f"[{ticker}] Stage 5: Saving KPIs...")
        kpi_dir = self.data_dir / 'stocks' / 'kpis'
        kpi_dir.mkdir(parents=True, exist_ok=True)
        kpi_path = kpi_dir / f'{ticker}_kpis.json'
        with open(kpi_path, 'w') as f:
            json.dump(kpis, f, indent=2)

        result['stages']['kpi'] = {
            'status': 'success',
            'kpi_path': str(kpi_path),
            'transitions_analyzed': len(transitions_list)
        }

        result['status'] = 'success'
        return result

    # ------------------------------------------------------------------
    # Bulk processing
    # ------------------------------------------------------------------

    def process_multiple_stocks(self, tickers: List[str], transitions: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Process a list of tickers.

        Args:
            tickers: List of ticker symbols
            transitions: Optional dict mapping ticker → single transition date
        """
        transitions = transitions or {}
        results = []

        for ticker in tickers:
            result = self.process_stock(ticker, transitions.get(ticker))
            results.append(result)

        return self._save_summary(results, len(tickers))

    def process_all_russell2000(self, transitions: Dict[str, List[str]] = None) -> List[Dict[str, Any]]:
        """
        Process all 1917 Russell 2000 companies from pre-fetched raw CSVs.

        Args:
            transitions: Optional dict mapping ticker → list of transition dates.
                         If provided, uses process_stock_with_all_transitions for that ticker.
        """
        tickers = load_tickers(TICKERS_CSV)
        transitions = transitions or {}
        results = []
        total = len(tickers)

        # Load all raw CSVs once — avoids re-scanning files for every ticker
        self._build_ticker_cache()

        for idx, ticker in enumerate(tickers, 1):
            logger.info(f"[{idx}/{total}] Processing {ticker}...")
            transition_dates = transitions.get(ticker, [])
            if transition_dates:
                result = self.process_stock_with_all_transitions(ticker, transition_dates)
            else:
                result = self.process_stock(ticker)
            results.append(result)

        return self._save_summary(results, total)

    def process_all_companies_all_transitions(self) -> List[Dict[str, Any]]:
        """
        Process all companies using transition dates from companies.json.
        Reads stock data from pre-fetched raw CSVs.
        """
        companies_file = self.data_dir / 'companies.json'
        if not companies_file.exists():
            logger.error(f"Companies file not found: {companies_file}")
            return []

        with open(companies_file, 'r') as f:
            companies_data = json.load(f)

        results = []
        total = len(companies_data.get('companies', []))

        for idx, company in enumerate(companies_data.get('companies', []), 1):
            ticker = company['ticker']
            transitions_list = [
                t['transitionDate']
                for t in company.get('transitions', [])
                if t.get('transitionDate')
            ]

            if not transitions_list:
                logger.info(f"[{idx}/{total}] {ticker}: No transitions, skipping")
                continue

            logger.info(f"[{idx}/{total}] Processing {ticker} with {len(transitions_list)} transitions...")
            result = self.process_stock_with_all_transitions(ticker, transitions_list)
            results.append(result)

        return self._save_summary(results, total)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _save_summary(self, results: List[Dict[str, Any]], total: int) -> List[Dict[str, Any]]:
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_stocks': total,
            'processed': len(results),
            'successful': sum(1 for r in results if r.get('status') == 'success'),
            'failed': sum(1 for r in results if r.get('status') != 'success'),
        }
        summary_path = self.data_dir / 'pipeline_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(
            f"Pipeline complete: {summary['successful']}/{summary['processed']} succeeded. "
            f"Summary → {summary_path}"
        )
        return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the data pipeline for a configured index.")
    parser.add_argument("--index", default="russell2000",
                        help="Index key from data/indices_config.json (default: russell2000)")
    args = parser.parse_args()

    cfg = load_index_config(args.index)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(Path(__file__).parent.parent / "pipeline.log"),
        ],
    )

    pipeline = DataPipeline(
        data_dir=Path(cfg["data_dir"]),
        raw_stock_dir=Path(cfg["raw_stock_dir"]),
    )
    pipeline.process_all_companies_all_transitions()
