"""
Data Pipeline Orchestrator
Orchestrates fetching, validation, transformation, and KPI calculation
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from fetch import StockDataFetcher
from validate import DataValidator
from calculate_kpis import KPICalculator

logger = logging.getLogger(__name__)


class DataPipeline:
    """Orchestrates the complete data pipeline"""

    def __init__(self, data_dir: Path = None):
        """
        Initialize pipeline

        Args:
            data_dir: Directory to store processed data (default: ../data)
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / 'data'

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.fetcher = StockDataFetcher()
        self.validator = DataValidator()
        self.kpi_calculator = KPICalculator()

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def process_stock(self, ticker: str, transition_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a single stock through the entire pipeline

        Args:
            ticker: Stock ticker symbol
            transition_date: CEO transition date (YYYY-MM-DD) for impact metrics

        Returns:
            Dictionary with processing results
        """
        result = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'stages': {}
        }

        # Stage 1: Fetch
        logger.info(f"[{ticker}] Stage 1: Fetching data...")
        raw_data = self.fetcher.fetch_stock_data(ticker)
        if raw_data is None or len(raw_data) == 0:
            result['stages']['fetch'] = {'status': 'failed', 'message': 'No data found'}
            return result

        result['stages']['fetch'] = {
            'status': 'success',
            'records': len(raw_data),
            'date_range': f"{raw_data['date'].iloc[0]} to {raw_data['date'].iloc[-1]}"
        }

        # Stage 2: Validate
        logger.info(f"[{ticker}] Stage 2: Validating data...")
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
        result['stages']['save'] = {
            'status': 'success',
            'valid_path': str(valid_path),
            'invalid_path': str(invalid_path)
        }

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

    def process_multiple_stocks(self, tickers: List[str], transitions: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Process multiple stocks through the pipeline

        Args:
            tickers: List of ticker symbols
            transitions: Dictionary mapping ticker to transition date

        Returns:
            List of processing results
        """
        if transitions is None:
            transitions = {}

        results = []
        for ticker in tickers:
            transition_date = transitions.get(ticker)
            result = self.process_stock(ticker, transition_date)
            results.append(result)

        # Save summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_stocks': len(tickers),
            'successful': sum(1 for r in results if r.get('status') == 'success'),
            'failed': sum(1 for r in results if r.get('status') != 'success'),
            'results': results
        }

        summary_path = self.data_dir / 'pipeline_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Pipeline complete. Summary saved to {summary_path}")
        return results
