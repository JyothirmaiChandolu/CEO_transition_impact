"""
Title: CEO performance analysis
Author: Jyothirmai Chandolu
Employee_id: 800342

KPI Calculation Module
Calculates price, volume, risk, and CEO transition impact metrics with macro-economic context
"""
import sys
from pathlib import Path

# Add current directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from fetch_macro import MacroDataFetcher


class KPICalculator:
    """Calculates financial KPIs from stock data"""

    @staticmethod
    def calculate_price_metrics(df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate price-based metrics: returns, volatility, moving averages"""
        if len(df) < 2:
            return {}

        # Daily returns
        df['daily_return'] = df['close'].pct_change()

        # Total return
        total_return = ((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]) * 100

        # Volatility (annualized)
        daily_volatility = df['daily_return'].std()
        annualized_volatility = daily_volatility * np.sqrt(252)

        # Moving averages
        ma_20 = df['close'].tail(20).mean() if len(df) >= 20 else None
        ma_50 = df['close'].tail(50).mean() if len(df) >= 50 else None
        ma_200 = df['close'].tail(200).mean() if len(df) >= 200 else None

        # Price trend
        price_high = df['close'].max()
        price_low = df['close'].min()
        current_price = df['close'].iloc[-1]

        return {
            'total_return_pct': round(total_return, 2),
            'volatility_pct': round(annualized_volatility * 100, 2),
            'volatility_level': 'High' if annualized_volatility > 0.40 else 'Medium' if annualized_volatility > 0.25 else 'Low',
            'ma_20': round(ma_20, 2) if ma_20 else None,
            'ma_50': round(ma_50, 2) if ma_50 else None,
            'ma_200': round(ma_200, 2) if ma_200 else None,
            'price_high': round(price_high, 2),
            'price_low': round(price_low, 2),
            'current_price': round(current_price, 2)
        }

    @staticmethod
    def calculate_volume_metrics(df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate volume-based metrics: average volume, volume trends"""
        if len(df) == 0:
            return {}

        avg_volume = df['volume'].mean()
        avg_volume_20 = df['volume'].tail(20).mean() if len(df) >= 20 else avg_volume
        current_volume = df['volume'].iloc[-1]

        # Volume trend (last 20 days vs historical)
        volume_trend = ((avg_volume_20 - avg_volume) / avg_volume * 100) if avg_volume > 0 else 0

        return {
            'avg_volume': int(avg_volume),
            'avg_volume_20d': int(avg_volume_20),
            'current_volume': int(current_volume),
            'volume_trend_pct': round(volume_trend, 2)
        }

    @staticmethod
    def calculate_risk_metrics(df: pd.DataFrame, risk_free_rate: float = 0.02) -> Dict[str, Any]:
        """Calculate risk metrics: beta, Sharpe ratio, max drawdown"""
        if len(df) < 2:
            return {}

        # Daily returns
        returns = df['close'].pct_change().dropna()

        # Sharpe Ratio (annualized)
        mean_return = returns.mean() * 252
        std_return = returns.std() * np.sqrt(252)
        sharpe_ratio = (mean_return - risk_free_rate) / std_return if std_return > 0 else 0

        # Maximum Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        return {
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown_pct': round(max_drawdown * 100, 2),
            'daily_volatility_pct': round(returns.std() * 100, 2)
        }

    @staticmethod
    def calculate_ceo_transition_impact(df: pd.DataFrame, transition_date: str) -> Dict[str, Any]:
        """
        Calculate impact metrics around CEO transition with macro-economic context.
        Uses nearest valid trading date if exact date unavailable (weekends, holidays).
        """
        try:
            transition = datetime.strptime(transition_date, '%Y-%m-%d')
        except:
            return {}

        # Initialize macro fetcher for recession context
        macro_fetcher = MacroDataFetcher()

        # Find closest date in data (handles weekends/holidays automatically)
        df['date'] = pd.to_datetime(df['date'])
        closest_idx = (df['date'] - transition).abs().argmin()
        transition_row = df.iloc[closest_idx]

        # Get the adjusted date (nearest trading day)
        transition_actual_date_obj = transition_row['date']
        days_diff = abs((transition_actual_date_obj - transition).days)

        # Only use if within 5 days (handles weekends/holidays)
        if days_diff > 5:
            return {}  # Skip transitions too far from data

        transition_price = transition_row['close']
        transition_actual_date = transition_actual_date_obj.strftime('%Y-%m-%d')

        # Get macro context at transition
        transition_macro = macro_fetcher.get_macro_context(transition_actual_date)

        # 90 days after
        end_90 = transition + timedelta(days=90)
        df_after_90 = df[df['date'] <= end_90]
        if len(df_after_90) > closest_idx:
            price_after_90 = df_after_90.iloc[-1]['close']
            impact_90d = ((price_after_90 - transition_price) / transition_price) * 100
        else:
            impact_90d = None

        # 1 year after
        end_1y = transition + timedelta(days=365)
        df_after_1y = df[df['date'] <= end_1y]
        if len(df_after_1y) > closest_idx:
            price_after_1y = df_after_1y.iloc[-1]['close']
            impact_1y = ((price_after_1y - transition_price) / transition_price) * 100
        else:
            impact_1y = None

        # 90 days before
        start_90 = transition - timedelta(days=90)
        df_before_90 = df[df['date'] >= start_90]
        if len(df_before_90) > 0:
            price_before_90 = df_before_90.iloc[0]['close']
            trend_90d_before = ((transition_price - price_before_90) / price_before_90) * 100
        else:
            trend_90d_before = None

        result = {
            'transition_date': transition_actual_date,
            'transition_price': round(transition_price, 2),
            'impact_90days_pct': round(impact_90d, 2) if impact_90d else None,
            'impact_1year_pct': round(impact_1y, 2) if impact_1y else None,
            'pre_transition_trend_90d_pct': round(trend_90d_before, 2) if trend_90d_before else None,
            'macro_economic_context': {
                'in_recession': transition_macro['in_recession'],
                'recession_period': transition_macro['recession_period'],
                'context': transition_macro['context']
            }
        }

        # Add recession/expansion analysis
        if transition_macro['in_recession']:
            result['analysis_note'] = f"⚠️ CEO transition occurred during {transition_macro['recession_period']}. Stock movement may be confounded by macro-economic factors."
        else:
            result['analysis_note'] = "✓ CEO transition occurred during economic expansion. Stock movement more likely reflects CEO impact."

        return result

    @staticmethod
    def calculate_all_kpis(df: pd.DataFrame, ticker: str, transition_date: Optional[str] = None, transition_dates: Optional[List[str]] = None) -> Dict[str, Any]:
        """Calculate all KPIs for a stock with macro-economic context

        Args:
            df: Stock data DataFrame
            ticker: Stock ticker symbol
            transition_date: Single transition date (legacy, for backward compatibility)
            transition_dates: List of transition dates (new, preferred for multiple transitions)
        """
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)

        # Initialize macro fetcher
        macro_fetcher = MacroDataFetcher()

        kpis = {
            'ticker': ticker,
            'last_updated': datetime.now().isoformat(),
            'data_points': len(df),
            'date_range': {
                'start': df['date'].iloc[0].strftime('%Y-%m-%d'),
                'end': df['date'].iloc[-1].strftime('%Y-%m-%d')
            },
            'price_metrics': KPICalculator.calculate_price_metrics(df),
            'volume_metrics': KPICalculator.calculate_volume_metrics(df),
            'risk_metrics': KPICalculator.calculate_risk_metrics(df),
            'macro_summary': macro_fetcher.get_summary_stats()
        }

        # Handle multiple transitions (new approach)
        if transition_dates and len(transition_dates) > 0:
            kpis['transition_impacts'] = []
            for td in transition_dates:
                impact = KPICalculator.calculate_ceo_transition_impact(df, td)
                if impact:
                    kpis['transition_impacts'].append(impact)

        # Handle single transition (legacy approach, for backward compatibility)
        elif transition_date:
            kpis['transition_impact'] = KPICalculator.calculate_ceo_transition_impact(df, transition_date)

        return kpis
