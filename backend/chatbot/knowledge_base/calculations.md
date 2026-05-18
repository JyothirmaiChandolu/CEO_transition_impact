# How KPI Metrics Are Calculated

## Stock Performance Metrics

### Impact 90 Days (%)
**Measures: Stock price change 90 days after CEO transition**

Calculation:
```
impact_90days = ((price_at_day_90 - price_at_transition) / price_at_transition) × 100
```

Example (AAPL Tim Cook transition, 2011-08-24):
- Transition price: $52.16
- Price 90 days later (Nov 22): $61.76
- Impact: ((61.76 - 52.16) / 52.16) × 100 = +18.4%

Business meaning:
- Positive = market optimistic about new CEO
- Negative = market skeptical or concerned
- Larger swings can indicate macro events (recession, industry changes)

---

### Impact 1 Year (%)
**Measures: Stock price change 365 days after CEO transition**

Calculation:
```
impact_1year = ((price_at_day_365 - price_at_transition) / price_at_transition) × 100
```

Example (AAPL Tim Cook transition, 2011-08-24):
- Transition price: $52.16
- Price 1 year later (Aug 24, 2012): $75.80
- Impact: ((75.80 - 52.16) / 52.16) × 100 = +45.2%

Business meaning:
- Reflects investor confidence in CEO's strategy
- More time for new CEO to execute plans
- Better separation from short-term noise
- More correlated with actual business performance

---

### Pre-Transition Trend 90 Days (%)
**Measures: Stock momentum before new CEO arrival**

Calculation:
```
pre_trend_90d = ((price_at_transition - price_90d_before) / price_90d_before) × 100
```

Example (AAPL, 90 days before Aug 24):
- Price 90 days prior (May 27): $37.51
- Transition price (Aug 24): $52.16
- Trend: ((52.16 - 37.51) / 37.51) × 100 = +39.0%

Business meaning:
- Shows if company was already gaining momentum
- Helps separate CEO impact from pre-existing trends
- Positive trend = new CEO inheriting improving company
- Negative trend = new CEO stepping into challenges

---

## Volatility Metrics

### Volatility (%)
**Measures: How much the stock price fluctuates daily**

Calculation:
```
daily_returns = log(close_today / close_yesterday)
daily_volatility = StdDev(daily_returns over period)
annualized_volatility = daily_volatility × sqrt(252)
volatility_pct = annualized_volatility × 100
```

Interpretation:
- 252 trading days in a year (used for annualization)
- < 15% = Low volatility (stable, blue-chip stocks)
- 15-30% = Medium volatility (typical stocks)
- > 30% = High volatility (risky, tech stocks, small caps)

Example:
- Daily return standard deviation: 1.2%
- Annualized: 1.2% × sqrt(252) = 19.0%

---

## Risk-Adjusted Returns

### Sharpe Ratio
**Measures: Return per unit of risk taken**

Calculation:
```
sharpe_ratio = (mean_daily_return / std_dev_daily_return) × sqrt(252)
```

Or in percentage terms:
```
sharpe_ratio = (annual_return_pct - risk_free_rate) / volatility_pct
```

Interpretation:
- > 2.0 = Excellent (great returns with acceptable risk)
- 1.0 - 2.0 = Good (solid risk-adjusted returns)
- 0 - 1.0 = Acceptable (positive but not impressive)
- < 0 = Negative (losing money or underperforming risk-free rate)

Example:
- Annual return: 25%
- Volatility: 18%
- Risk-free rate: 4%
- Sharpe: (25 - 4) / 18 = 1.17 (good)

---

### Maximum Drawdown (%)
**Measures: Worst-case peak-to-trough loss**

Calculation:
```
For each day:
  running_max = highest price seen so far
  drawdown_today = (price_today - running_max) / running_max × 100

max_drawdown = minimum drawdown over period
```

Example:
- Stock peaks at $150
- Drops to $100
- Max drawdown: (100 - 150) / 150 × 100 = -33.3%

Business meaning:
- Shows worst loss if you bought at the peak
- Critical for risk management
- -20% to -50% typical for stocks
- > -50% considered severe

---

## Volume Metrics

### Average Volume
**Measures: Typical daily trading activity**

Calculation:
```
avg_volume_20d = sum(daily_volume for last 20 days) / 20
avg_volume_overall = sum(all daily volume) / number_of_days
```

Interpretation:
- High volume (>1M shares/day) = liquid, easy to trade
- Low volume (<100k/day) = illiquid, harder to buy/sell
- Used to assess market interest in stock

---

### Volume Trend (%)
**Measures: Change in trading activity**

Calculation:
```
volume_trend = ((current_avg_volume - previous_avg_volume) / previous_avg_volume) × 100
```

Example:
- Average volume last 20 days: 50M shares
- Average volume previous 20 days: 45M shares
- Trend: (50 - 45) / 45 × 100 = +11% (increasing interest)

---

## Recession and Macro Context

### Recession Periods
**Identifies: Trading during economic recessions**

Data source:
- NBER (National Bureau of Economic Research) official recession dates
- Format: { start_date, end_date, duration_months }

Impact on CEO transition analysis:
- CEO impact during recession = structural challenges + CEO quality
- CEO impact in growth period = easier to succeed
- Recession context critical for fair CEO assessment

Example:
- CEO transition: March 2008 (during 2007-2009 Great Recession)
- Stock impact heavily influenced by recession, not just CEO
- Must consider macro context when evaluating CEO performance

---

## Summary Table

| Metric | Formula | Interpretation | Risk Level |
|--------|---------|-----------------|-----------|
| Impact 90d | (price_90d - price_0) / price_0 | Immediate reaction | Medium |
| Impact 1yr | (price_365d - price_0) / price_0 | CEO strategy success | Low |
| Pre-trend | (price_0 - price_-90d) / price_-90d | Momentum before CEO | N/A |
| Volatility | AnnStdDev(returns) | Price fluctuation | Medium |
| Sharpe | Return / Risk | Risk-adjusted return | Low |
| Max Drawdown | (Trough - Peak) / Peak | Worst loss | High |
| Avg Volume | Mean(daily_volume) | Liquidity | Low |
| Volume Trend | (vol_now - vol_prev) / vol_prev | Trading activity change | Low |
