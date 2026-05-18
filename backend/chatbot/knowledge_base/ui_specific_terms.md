# UI-Specific Terms and Concepts

## CEO Impact & Performance Metrics

**Price at Transition**
- The stock price on the exact CEO transition date
- Used as the baseline for calculating all return percentages
- Different from pre-transition trend baseline
- Important reference point for investors

**Cumulative Return**
- Running total of gains/losses since CEO transition date
- Tracked daily to show performance progression
- Shows how CEO performance compounds over time
- Example: Day 30 return +5%, Day 60 return +8% (cumulative, not +3%)

**Abnormal Returns**
- Stock returns above/below what would normally be expected
- Isolates CEO impact from general market movements
- Calculated against company baseline expectations
- Helps determine if CEO created or destroyed value relative to expectations

## Statistical Outlier Analysis

**Z-Score (Multiple Types)**
- Z-Score 90-Day: how 90-day returns compare to sector average
- Z-Score 1-Year: how 1-year returns compare to sector average
- Z-Score Volatility: how risk compares to sector average
- Z-Score Tenure: how CEO tenure compares to sector average
- All measured in standard deviations from mean

**Composite Z-Score**
- Single combined score from multiple weighted metrics
- For CEOs: 40% (90-day) + 35% (1-year) + 25% (volatility)
- For Companies: 40% (return) + 30% (Sharpe) + 15% (volatility) + 15% (drawdown)
- Used for overall ranking of CEOs/companies

**Percentile Ranking**
- Position from 0-100% among sector peers
- Example: 75th percentile = better than 75% of peers
- Shows relative ranking, not absolute performance
- Directly answers "how does this CEO rank among peers?"

**Outlier Status & Strength**
- Status: OUTLIER_HIGH (top 20%, Z > 2.0), OUTLIER_LOW (bottom 20%, Z < -2.0), NORMAL (middle 60%)
- Strength: STRONG (statistically significant |Z| > 2.0), MODERATE (notable but not extreme), NORMAL
- Combination identifies: how exceptional is this CEO/company compared to sector

**Standard Deviation (Std Dev) in Context**
- Shows variability within a sector
- Sector Mean ± 1 Std Dev = typical range
- Values beyond ± 2 Std Dev = unusual (outliers)
- Used to define what's "normal" vs "exceptional"

## Index & Market Comparison

**S&P 100 (OEX) Index**
- Benchmark index for comparing company performance
- Contains 100 largest U.S. companies
- Used in "Index Comparison" tab
- Shows how company stock performed vs. broad market

**S&P 100 Comparison**
- Tab showing company performance vs. index performance
- Answers: did CEO beat or underperform the market?
- Relative performance: company gain % vs index gain %
- Example: company +15%, index +10% = CEO outperformed by 5%

## Recession & Economic Context

**Recession Benchmark**
- Specific analysis for CEO transitions during recessions
- Compares company vs. S&P 100 performance during recession
- Shows how CEO navigated economic crisis
- Outperformance during recession is more impressive than in expansion

**Macro-Economic Context**
- Economic conditions when transition occurred
- States whether in expansion or recession
- Affects expectations: easier to succeed in expansion, harder in recession
- Influences interpretation of CEO performance

**Outperformance (During Recession)**
- How much better/worse company did vs. S&P 100 during recession
- Example: company down 10%, index down 20% = +10% outperformance
- Shows CEO crisis management skill

## Investor Sentiment Analysis

**Investor Sentiment / Investor Reaction**
- Positive: stock gained >2% after transition (optimistic market view)
- Negative: stock fell <-2% after transition (pessimistic market view)
- Neutral: stock moved -2% to +2% (ordinary transition)
- Based on actual market price movement, not opinion

**Investor Confidence (as metric)**
- Platform-wide metric showing % of investors with positive sentiment
- Example: "Investor Confidence: 76%" = most investors positive about transitions
- Shows collective market optimism/pessimism

## Risk Classification

**Volatility Level (Risk Profile)**
- Categorical risk assessment: Low, Medium, High
- Low: <15% annualized volatility = stable stock
- Medium: 15-30% annualized volatility = typical risk
- High: >30% annualized volatility = risky stock
- Shows risk profile at a glance

**Market Volatility (as shown metric)**
- Measure of price fluctuation around CEO transition
- Often spikes during uncertainty of leadership change
- Example: "Market Volatility: ±8.2%" = typical daily moves ±8.2%

## Tenure Analysis

**Tenure Duration**
- How long CEO served: e.g., "5y 3m" = 5 years 3 months
- Long-tenure CEOs (>10y): rare, indicates success or founder-led
- Short-tenure CEOs (<2y): rapid replacement or instability
- Measured from transition date to end of CEO tenure

**Long-Tenure (Outlier)**
- CEO tenure in top 20% of sector (Z > 2.0)
- Exceptional longevity in role
- Shows board confidence and CEO-company fit
- Perceptile indicator shows exact ranking

**Short-Tenure (Outlier)**
- CEO tenure in bottom 20% of sector (Z < -2.0)
- Very brief time in role
- May indicate poor fit, forced departure, or interim role
- Percentile shows how much shorter than typical

## Sector Analysis

**Sector Mean**
- Average metric value across entire sector
- Used as reference for comparison
- Example: "Sector mean 1-year return: +8.5%"
- Shows what "typical" looks like for sector

**Sector Statistics**
- Collection of stats for a sector: mean, std dev, outlier counts
- Shows distribution of CEO performance in sector
- Helps contextualize individual CEO metrics
- Base data for calculating z-scores and percentiles

## Data Quality Metrics

**Data Validation (97.8% verified)**
- Percentage of transitions verified against SEC filings
- Shows reliability of analysis
- All transitions cross-checked with multiple sources
- 97.8% = very high data quality

**Leadership Transition Profile**
- Summary section showing both outgoing and incoming CEO
- Includes tenure ended/tenure began dates
- Visual presentation of who replaced whom and when
- Context for the transition being analyzed

## Market Impact Metrics

**Market Cap Change**
- Dollar amount change in company's total market value
- Example: "$2.8B increase" = shareholders gained $2.8B in wealth
- Shows monetary impact of CEO on shareholder value
- Combines stock price change + market's view of share count

**Average Stock Impact**
- Platform-wide metric: typical 90-day return across all transitions
- Example: "+12.4%" = average CEO gets this return in first 90 days
- Benchmark for comparing individual CEO performance
- Shows what's "normal" across entire S&P 100

## Visualization & Analysis Specific

**Trading Volume Analysis**
- Chart showing trading activity around transition date
- Volume spike indicates market attention to news
- High volume with price move = strong sentiment confirmation
- Low volume = market indifference to announcement

**Relative Performance**
- How company performed vs. benchmark during recession
- Outperformance = CEO did better than average
- Underperformance = CEO did worse than average
- Key metric for assessing crisis management
