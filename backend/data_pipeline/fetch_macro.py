"""
Title: CEO performance analysis
Author: Jyothirmai Chandolu
Employee_id: 800342

Macro-Economic Data Fetcher
Fetches FRED and NBER recession data for macro-economic analysis
"""
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MacroDataFetcher:
    """Fetches macro-economic indicators and recession data"""

    # NBER Recession dates (Peak to Trough) - sourced from NBER
    NBER_RECESSIONS = [
        {'start': '2001-03-01', 'end': '2001-11-01', 'name': '2001 Recession'},
        {'start': '2007-12-01', 'end': '2009-06-01', 'name': '2007-2009 Financial Crisis'},
        {'start': '2020-02-01', 'end': '2020-04-01', 'name': '2020 COVID-19 Recession'},
    ]

    def __init__(self):
        """Initialize macro data fetcher"""
        self.recessions = self._prepare_recession_data()

    def _prepare_recession_data(self) -> pd.DataFrame:
        """Prepare recession periods as DataFrame"""
        data = []
        for recession in self.NBER_RECESSIONS:
            data.append({
                'start_date': recession['start'],
                'end_date': recession['end'],
                'name': recession['name']
            })
        return pd.DataFrame(data)

    def get_recession_data(self) -> pd.DataFrame:
        """
        Get NBER recession periods

        Returns:
            DataFrame with recession start/end dates
        """
        logger.info("Loaded NBER recession data")
        return self.recessions

    def is_in_recession(self, date_str: str) -> bool:
        """
        Check if a date falls within a recession period

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            True if date is in recession, False otherwise
        """
        check_date = pd.to_datetime(date_str)

        for _, recession in self.recessions.iterrows():
            start = pd.to_datetime(recession['start_date'])
            end = pd.to_datetime(recession['end_date'])

            if start <= check_date <= end:
                return True

        return False

    def get_recession_name(self, date_str: str) -> Optional[str]:
        """
        Get recession name for a given date

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Recession name or None if not in recession
        """
        check_date = pd.to_datetime(date_str)

        for _, recession in self.recessions.iterrows():
            start = pd.to_datetime(recession['start_date'])
            end = pd.to_datetime(recession['end_date'])

            if start <= check_date <= end:
                return recession['name']

        return None

    def get_macro_context(self, date_str: str) -> Dict[str, Any]:
        """
        Get macro-economic context for a date

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Dictionary with recession status and context
        """
        in_recession = self.is_in_recession(date_str)
        recession_name = self.get_recession_name(date_str)

        return {
            'date': date_str,
            'in_recession': in_recession,
            'recession_period': recession_name,
            'context': 'Recession Period' if in_recession else 'Economic Expansion'
        }

    def create_date_range_macro_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Create a date-indexed DataFrame marking recession periods

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with daily recession flags
        """
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        data = []

        for date in date_range:
            date_str = date.strftime('%Y-%m-%d')
            macro_context = self.get_macro_context(date_str)
            data.append({
                'date': date_str,
                'in_recession': macro_context['in_recession'],
                'recession_period': macro_context['recession_period']
            })

        return pd.DataFrame(data)

    def get_recession_impact(self, index_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compute peak/trough/decline/recovery for each NBER recession using index price data.

        Args:
            index_df: DataFrame with 'date' (datetime) and 'close' columns, sorted by date.

        Returns:
            Dict with recession impact details and summary statistics.
        """
        df = index_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()

        recessions_out = []
        declines = []

        for r in self.NBER_RECESSIONS:
            start = pd.to_datetime(r['start'])
            end = pd.to_datetime(r['end'])
            duration_months = round((end - start).days / 30.44, 1)

            period = df.loc[start:end, 'close'] if 'close' in df.columns else pd.Series(dtype=float)

            if period.empty:
                recessions_out.append({
                    'name': r['name'],
                    'period': {'start': r['start'], 'end': r['end'], 'duration_months': duration_months},
                    'peak': {'date': r['start'], 'price': 0},
                    'trough': {'date': r['end'], 'price': 0},
                    'decline': {'amount': 0, 'percentage': 0, 'vs_benchmark': 'No data for this period'},
                    'recovery': {'date': r['end'], 'price': 0, 'gain_percentage': 0},
                })
                continue

            peak_price = float(period.iloc[0])
            peak_date = str(period.index[0].date())
            trough_price = float(period.min())
            trough_date = str(period.idxmin().date())
            decline_pct = round((trough_price - peak_price) / peak_price * 100, 2) if peak_price else 0
            declines.append(decline_pct)

            # First date after trough where price returns to or exceeds pre-recession peak
            post_trough = df.loc[period.idxmin():, 'close']
            recovered = post_trough[post_trough >= peak_price]
            if not recovered.empty:
                rec_date = str(recovered.index[0].date())
                rec_price = float(recovered.iloc[0])
            else:
                rec_date = 'Not yet recovered'
                rec_price = float(df['close'].iloc[-1])
            rec_gain = round((rec_price - trough_price) / trough_price * 100, 2) if trough_price else 0

            recessions_out.append({
                'name': r['name'],
                'period': {'start': r['start'], 'end': r['end'], 'duration_months': duration_months},
                'peak': {'date': peak_date, 'price': round(peak_price, 2)},
                'trough': {'date': trough_date, 'price': round(trough_price, 2)},
                'decline': {
                    'amount': round(trough_price - peak_price, 2),
                    'percentage': decline_pct,
                    'vs_benchmark': 'Russell 2000',
                },
                'recovery': {'date': rec_date, 'price': round(rec_price, 2), 'gain_percentage': rec_gain},
            })

        valid = [d for d in declines if d != 0]
        summary = {
            'total_recessions_analyzed': len(valid),
            'average_decline': round(sum(valid) / len(valid), 2) if valid else 0,
            'max_decline': round(min(valid), 2) if valid else 0,
            'min_decline': round(max(valid), 2) if valid else 0,
        }

        return {'recessions': recessions_out, 'summary': summary}

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics about recession periods"""
        total_days = 0
        recession_days = 0

        for _, recession in self.recessions.iterrows():
            start = pd.to_datetime(recession['start_date'])
            end = pd.to_datetime(recession['end_date'])
            duration = (end - start).days
            total_days += duration

        recession_days = total_days
        total_period_days = (pd.Timestamp.now().normalize() - pd.to_datetime('1996-01-02')).days

        return {
            'total_recession_periods': len(self.recessions),
            'total_recession_days': recession_days,
            'total_analysis_period_days': total_period_days,
            'recession_percentage': round((recession_days / total_period_days) * 100, 2),
            'recessions': [
                {
                    'name': r['name'],
                    'start': r['start'],
                    'end': r['end'],
                    'duration_months': round((pd.to_datetime(r['end']) - pd.to_datetime(r['start'])).days / 30.44, 1)
                }
                for r in self.NBER_RECESSIONS
            ]
        }
