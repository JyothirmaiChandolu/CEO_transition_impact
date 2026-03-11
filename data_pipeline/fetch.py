"""
Data Fetching Module
Fetches stock data from yfinance
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class StockDataFetcher:
    """Fetches stock data from Yahoo Finance"""

    def __init__(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Initialize fetcher

        Args:
            start_date: Start date in YYYY-MM-DD format (default: 30 years ago)
            end_date: End date in YYYY-MM-DD format (default: today)
        """
        if end_date is None:
            self.end_date = datetime.now().strftime('%Y-%m-%d')
        else:
            self.end_date = end_date

        if start_date is None:
            # Default: 30 years of data
            start = datetime.now() - timedelta(days=365*30)
            self.start_date = start.strftime('%Y-%m-%d')
        else:
            self.start_date = start_date

    def fetch_stock_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        Fetch stock data for a ticker

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')

        Returns:
            DataFrame with columns: date, ticker, open, high, low, close, volume
        """
        try:
            logger.info(f"Fetching {ticker} data from {self.start_date} to {self.end_date}")

            data = yf.download(
                ticker,
                start=self.start_date,
                end=self.end_date,
                progress=False
            )

            if data.empty:
                logger.warning(f"No data found for {ticker}")
                return None

            # Reset index and rename columns
            data = data.reset_index()
            data.columns = ['date', 'open', 'high', 'low', 'close', 'volume']

            # Add ticker column
            data['ticker'] = ticker.upper()

            # Format date
            data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')

            # Select and reorder columns
            data = data[['date', 'ticker', 'open', 'high', 'low', 'close', 'volume']]

            # Convert types
            data['open'] = data['open'].round(2)
            data['high'] = data['high'].round(2)
            data['low'] = data['low'].round(2)
            data['close'] = data['close'].round(2)
            data['volume'] = data['volume'].astype(int)

            logger.info(f"Successfully fetched {len(data)} records for {ticker}")
            return data

        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            return None

    def fetch_multiple_stocks(self, tickers: list) -> Dict[str, Optional[pd.DataFrame]]:
        """
        Fetch data for multiple stocks

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary mapping ticker to DataFrame
        """
        results = {}
        for ticker in tickers:
            results[ticker] = self.fetch_stock_data(ticker)
        return results
