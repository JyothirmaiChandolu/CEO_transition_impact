# CEO Transition Analysis Framework

## Data Sources

### CEO Transition Dates
**Primary Source: SEC 8-K Filings**

**What is the SEC?**
- Securities and Exchange Commission - U.S. federal regulatory agency
- Oversees stock market and protects investors
- Requires public companies to disclose material information
- Website: sec.gov
- Database: EDGAR (Electronic Data Gathering, Organization, and Retrieval)

**What is 8-K Filing?**
- Form 8-K: "Current Report of Material Events"
- Mandatory filing for major company events (mergers, resignations, CEO changes, etc.)
- Must be filed within 4 business days of the triggering event
- Publicly available on SEC EDGAR database
- Official, audited source of CEO transition dates
- Contains: New CEO name, previous CEO name, transition date, reason for transition

**Why It's Reliable:**
- Legal requirement - companies must file accurately
- SEC enforces strict penalties for false filings
- Audited by company's accounting firm
- Official regulatory record
- Used by all institutional investors for decision-making

**Secondary Source: Company Announcements**
- Press releases from company website
- Official investor relations statements
- Confirms/validates 8-K filing information

**Tertiary Source: News Verification**
- Web research to confirm transition date accuracy
- Cross-reference with multiple sources
- Ensure date reflects official takeover, not announcement

### Dataset Scope
- **Companies:** 100 S&P 100 companies (largest US companies)
- **Time Period:** 1996 - 2025 (30 years)
- **Total Transitions:** 251 CEO changes
- **Companies with transitions:** 91 out of 100
- **Data Quality:** Verified via SEC filings and web research

---

## Stock Price Data

### Data Source: yfinance (Yahoo Finance)

**What is Yahoo Finance (yfinance)?**
- Free financial data API provided by Yahoo
- Aggregates historical stock price data from multiple exchanges
- Covers NYSE, NASDAQ, and other global exchanges
- Python library: yfinance - easy access to historical data
- Website: finance.yahoo.com

**OHLCV Data Explained:**
- **O (Open)**: Stock price at market open for that day
- **H (High)**: Highest price during that trading day
- **L (Low)**: Lowest price during that trading day
- **C (Close)**: Final closing price at end of trading day
- **V (Volume)**: Total shares traded that day (in units)

**Adjusted Close Price:**
- Close price adjusted for stock splits and dividends
- Example: If stock splits 2-for-1, historical prices are halved
- Example: If $2 dividend paid, adjusted close is reduced by $2
- Used for accurate long-term return calculations
- Prevents artificial gaps from corporate actions

**Data Reliability:**
- Yahoo Finance aggregates data from official exchanges
- Matches SEC CRSP database for accuracy
- Used by professional traders and investors
- Free and publicly accessible
- Updates daily with market data

**Coverage in This Dataset:**
- Reliable historical data back to 1996 for S&P 100 stocks
- Total records: ~7,600 per company (30 years × 252 trading days)
- Covers all CEO transitions with before/after data

### Data Collection
- Daily prices collected for each company
- Total records: ~7,600 per company (30 years × 252 trading days)
- Covers all CEO transitions in the dataset
- Includes dates before/after each transition

### Data Quality Checks
- Validate no missing dates (gaps indicate data issues)
- Check for duplicate records
- Verify price continuity (no sudden impossible jumps)
- Flag anomalies for manual review

---

## SEC vs yfinance: How They Work Together

| Aspect | SEC (CEO Dates) | yfinance (Stock Prices) |
|--------|-----------------|----------------------|
| **Purpose** | Disclose CEO transitions | Provide historical price data |
| **Authority** | U.S. federal regulation | Yahoo Finance aggregation |
| **Accuracy** | 100% (legally required) | 99%+ (matches exchanges) |
| **What You Get** | CEO names, transition dates | OHLCV prices, volume |
| **For Analysis** | Exact point in time to measure | Price movement before/after |
| **Example** | "CEO change: 2020-03-15" | "Price on 2020-03-15: $45.32" |

**How They're Used Together in CEO Analysis:**

1. **Get transition date from SEC 8-K filing:**
   - Find official CEO change date
   - Confirm via EDGAR database
   - Example: "New CEO appointed: March 15, 2020"

2. **Get stock prices from yfinance:**
   - Get price on transition date from yfinance
   - Get price 90 days after from yfinance
   - Get price 1 year after from yfinance
   - Example: $45.32 (March 15), $52.10 (June 13), $58.75 (March 15, 2021)

3. **Calculate CEO impact:**
   - 90-day impact = ($52.10 - $45.32) / $45.32 = +14.9%
   - 1-year impact = ($58.75 - $45.32) / $45.32 = +29.5%
   - Conclusion: CEO appointment correlated with stock gains

**Data Quality Verification:**
- SEC date + yfinance price = complete picture
- If SEC shows date but yfinance has no data = data gap
- If prices jump 50% overnight on SEC filing = likely CEO-related move
- Cross-checking validates both data sources

---

## Macro-Economic Context

### Recession Periods
**Source: NBER (National Bureau of Economic Research)**
- Official US recession dates
- Determined by NBER Business Cycle Dating Committee
- Covers: 1996-2025

Official recession periods in our dataset:
```
2001-03-01 to 2001-11-30  (9 months - Dot-com crash)
2007-12-01 to 2009-06-30  (18 months - Great Recession)
2020-02-01 to 2020-04-30  (3 months - COVID-19 pandemic)
```

### Impact on CEO Analysis
- CEO transitions during recessions are different (defensive CEO appointments)
- Stock performance during recession influenced by macro factors, not just CEO
- Stock performance during growth periods more CEO-dependent

Example:
```
CEO A: appointed March 2008 (Great Recession)
- Stock down 40% in first year
- Likely due to recession, not poor CEO skills

CEO B: appointed March 2010 (post-recession recovery)
- Stock up 60% in first year
- Mix of economic recovery and CEO strategy
```

---

## KPI Calculation Framework

### Data Input Pipeline
```
1. Load stock price data (daily OHLCV)
2. Load CEO transition date for company
3. Filter stock data around transition date
4. Calculate metrics before and after transition
5. Normalize by sector
6. Generate final KPI report
```

### Calculation Steps

**Step 1: Extract Price Points**
```
transition_date = CEO change date from data/companies.json
price_at_transition = closing price on transition_date
price_90d_after = closing price 90 days after transition_date
price_1yr_after = closing price 365 days after transition_date
price_90d_before = closing price 90 days before transition_date
```

**Step 2: Calculate Performance Impacts**
```
impact_90days = ((price_90d - price_transition) / price_transition) × 100
impact_1year = ((price_1yr - price_transition) / price_transition) × 100
pre_transition_trend = ((price_transition - price_90d_before) / price_90d_before) × 100
```

**Step 3: Calculate Volatility and Risk Metrics**
```
daily_returns = [log(close[i] / close[i-1]) for each day]
volatility = std(daily_returns) × sqrt(252) × 100
sharpe_ratio = (mean(daily_returns) × 252) / (std(daily_returns) × sqrt(252))
max_drawdown = minimum((price - running_max) / running_max) × 100
```

**Step 4: Aggregate Volume Metrics**
```
avg_volume_20d = average(volume last 20 days)
avg_volume_overall = average(all volumes)
volume_trend = ((avg_volume_20d - avg_volume_prev) / avg_volume_prev) × 100
```

**Step 5: Add Macro Context**
```
recession_periods = [all active recessions during CEO tenure]
in_recession = transition_date in any recession period
context_description = "CEO transition occurred during [recession/growth period]"
```

---

## Sector Classification

### 11 GICS Sectors
All companies classified into one of these sectors:

1. **Technology** - Software, semiconductors, IT services
2. **Healthcare** - Pharmaceuticals, medical devices, biotech, healthcare services
3. **Financials** - Banks, insurance, investment firms
4. **Consumer Discretionary** - Retail, automotive, hospitality, entertainment
5. **Industrials** - Manufacturing, machinery, aerospace, construction
6. **Energy** - Oil, gas, mining, utilities (power generation)
7. **Utilities** - Electric power, gas distribution, water utilities
8. **Real Estate** - REITs, real estate development
9. **Materials** - Chemicals, metals, mining, construction materials
10. **Consumer Staples** - Food, beverages, household products
11. **Communication Services** - Telecommunications, media, entertainment

### Why Sector Classification Matters
- Different sectors have different risk/return profiles
- Tech more volatile than utilities
- Financial metrics not directly comparable across sectors
- Z-score outlier analysis is per-sector for fair comparison

---

## CEO Transition Types

### 1. Planned Succession
**Characteristics:**
- CEO announced retirement date in advance
- Often appointed insider or known external candidate
- Smooth transition with continuity

**Market Impact:**
- Usually positive (reduces uncertainty)
- Stock may increase on succession announcement
- 90-day and 1-year impacts more positive

Example: Tim Cook became AAPL CEO (announced transition)

### 2. Unexpected Departure
**Characteristics:**
- CEO resigns or is forced out without warning
- May cause market uncertainty
- Could indicate internal issues

**Market Impact:**
- Often negative in short term (uncertainty premium)
- May recover if new CEO is well-received

### 3. Interim Leadership
**Characteristics:**
- No official new permanent CEO yet
- Temporary leadership during search
- Higher uncertainty

**Market Impact:**
- Neutral to negative (shows no clear successor)
- May be worse if search is extended

### 4. Internal vs External Promotion
**Internal (Insider):**
- From within company
- Usually positive (continuity)
- Prepared transition

**External (Outsider):**
- From outside company
- Can be risky (unknown fit)
- May bring fresh perspective

---

## Analysis Quality Indicators

### Data Completeness
- Stock data available for full transition period
- CEO transition date clearly documented
- No suspicious gaps in price data

### Macro Context
- Recession period clearly identified
- Allows for contextual analysis
- Important for fair CEO assessment

### Outlier Flagging
- QC flags mark potentially problematic transitions
- May indicate data quality issues
- Flagged records reviewed manually

### Confidence Levels
- High confidence: Multiple sources confirm date, complete data
- Medium confidence: SEC 8-K confirmed, data intact
- Low confidence: Limited sources, some data gaps

---

## Common Analysis Scenarios

### "How did this CEO impact stock?"
1. Find transition date
2. Get stock price at transition
3. Calculate 90-day and 1-year impacts
4. Check macro context (recession?)
5. Compare to sector average (z-score)
6. Answer: "Yes, positive impact of +X%, above sector average"

### "Compare two CEOs"
1. Get both transition dates
2. Calculate both 1-year impacts
3. Normalize by sector (z-scores)
4. Account for recession periods (if different)
5. Compare: "CEO A better risk-adjusted, CEO B had better absolute return"

### "What drives CEO success?"
1. Analyze all CEO transitions in sector
2. Calculate z-scores for each
3. Identify STRONG POSITIVE CEOs
4. Extract common traits (tenure style, background, timing)
5. Identify factors correlated with success

---

## Limitations and Caveats

### Stock Price Limits
- Stock price reflects market sentiment, not all company performance
- CEO impact mixed with macro events
- Can't attribute 100% of price change to CEO

### Transition Date Challenges
- Official date might differ from actual change date
- Interim period can blur transitions
- Some CEOs announced but not taken over yet

### Sector Effects
- Industry dynamics major factor in stock performance
- Technology boom vs energy decline affects returns
- CEO can't overcome strong sector headwinds

### Survivorship Bias
- Only analyzing companies that survived to 2025
- Companies that went bankrupt excluded
- Some CEOs may have been fired but records lost

### Time Period Effects
- 1996-2000: dot-com boom (easy to succeed)
- 2000-2003: tech crash (hard to succeed)
- 2007-2009: Great Recession (all suffered)
- 2020+: tech boom (easy to succeed)
