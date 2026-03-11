"""
KPI Calculation Module
Calculates price, volume, risk, and CEO transition impact metrics
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Any
from datetime import datetime, timedelta


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
        """Calculate impact metrics around CEO transition"""
        try:
            transition = datetime.strptime(transition_date, '%Y-%m-%d')
        except:
            return {}

        # Find closest date in data
        df['date'] = pd.to_datetime(df['date'])
        closest_idx = (df['date'] - transition).abs().argmin()
        transition_row = df.iloc[closest_idx]
        transition_price = transition_row['close']
        transition_actual_date = transition_row['date'].strftime('%Y-%m-%d')

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

        return {
            'transition_date': transition_actual_date,
            'transition_price': round(transition_price, 2),
            'impact_90days_pct': round(impact_90d, 2) if impact_90d else None,
            'impact_1year_pct': round(impact_1y, 2) if impact_1y else None,
            'pre_transition_trend_90d_pct': round(trend_90d_before, 2) if trend_90d_before else None
        }

    @staticmethod
    def calculate_all_kpis(df: pd.DataFrame, ticker: str, transition_date: Optional[str] = None) -> Dict[str, Any]:
        """Calculate all KPIs for a stock"""
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)

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
            'risk_metrics': KPICalculator.calculate_risk_metrics(df)
        }

        if transition_date:
            kpis['transition_impact'] = KPICalculator.calculate_ceo_transition_impact(df, transition_date)

        return kpis
