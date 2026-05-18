# Outlier Analysis Methodology

## What Are Outliers?

Outliers are CEOs and companies whose performance significantly deviates from their sector peers. Instead of labeling all high/low performers the same way, we use statistical z-scores to identify:
- CEOs whose tenure length is unusual (very short or very long compared to sector average)
- Companies whose stock performance is extreme (best or worst in their sector)
- CEOs whose stock impact is exceptional (unusually strong or weak)

---

## Z-Score Standardization

### What is a Z-Score?

A z-score measures how many standard deviations away from the mean a value is.

Formula:
```
z_score = (value - sector_mean) / sector_std_dev
```

Interpretation:
- z = 0 → value equals sector average (normal)
- z = 1 → value is 1 std dev above average (above average)
- z = -1 → value is 1 std dev below average (below average)
- z = 2 → value is 2 std devs above average (very high)
- z = -2 → value is 2 std devs below average (very low)

Example (Sharpe Ratio in Technology sector):
```
Technology sector average Sharpe ratio: 0.85
Standard deviation: 0.30

Company A Sharpe ratio: 1.45
z = (1.45 - 0.85) / 0.30 = 2.0 (exceptional performer)

Company B Sharpe ratio: 0.55
z = (0.55 - 0.85) / 0.30 = -1.0 (below average)
```

---

## Three Types of Outliers

### 1. CEO Performance Outliers
**Question: Which CEOs had exceptional (or poor) impact on stock?**

Metrics measured:
- **90-day impact** (40% weight) = immediate market reaction
- **1-year impact** (35% weight) = sustained investor confidence
- **Volatility** (25% weight) = risk during CEO tenure

Composite z-score:
```
z_performance = 0.40 × z_90day + 0.35 × z_1year + 0.25 × z_volatility
```

Business meaning:
- High positive z = CEO brought stability AND returns (best outcome)
- High negative z = CEO brought losses or instability
- Important for assessing CEO talent and ability to lead

---

### 2. CEO Tenure Outliers
**Question: How does CEO tenure length correlate with stock performance?**

Metrics measured:
- **Tenure length** (years in CEO role)
- **Stock performance during tenure**
- **Company stability**

What we're looking for:
- Long-tenure CEOs (>15 years) → experienced, potentially set in ways
- Short-tenure CEOs (<2 years) → brief impact, often interim
- Optimal tenure → balance of experience and fresh perspective

Z-score calculation:
```
z_tenure = (ceo_years_in_role - sector_avg_years) / sector_std_dev_years
```

Business meaning:
- Very long tenures can indicate succession planning issues
- Very short tenures indicate instability or failed experiments
- Typical range varies by sector (tech: 5-7 years, finance: 8-10 years)

---

### 3. Company Stock Outliers
**Question: Which companies are sector leaders or laggards?**

Composite score combines:
- **Total return** (40%) = absolute price performance
- **Sharpe ratio** (35%) = risk-adjusted returns
- **Volatility** (15%) = price stability
- **Max drawdown** (10%) = downside protection

Composite z-score:
```
z_company = 0.40 × z_return + 0.35 × z_sharpe + 0.15 × z_volatility - 0.10 × z_max_drawdown
(negative on drawdown because lower is better)
```

Business meaning:
- High z_company = sector leader (strong return, stable, risk-adjusted)
- Low z_company = sector laggard (weak returns or high volatility)
- Identifies companies worth investigating

---

## Outlier Classification System

We use a tiered classification:

### STRONG Outliers
Threshold: |z_score| > 2.0

Meaning:
- Represents top or bottom ~2.3% of sector
- Statistically significant deviation
- Very unusual, noteworthy performance

Examples:
- STRONG POSITIVE CEO = "This CEO's impact was exceptional"
- STRONG NEGATIVE CEO = "This CEO struggled significantly"

### MODERATE Outliers
Threshold: |z_score| ≤ 2.0 but still in top/bottom 20%

Meaning:
- Represents roughly 5th-20th percentile or 80th-95th percentile
- Notable but not extreme
- Worthwhile but not exceptional

Examples:
- MODERATE POSITIVE = "This CEO performed well, above sector average"
- MODERATE NEGATIVE = "This CEO underperformed vs sector peers"

### NORMAL
Threshold: z_score between -0.84 and +0.84 (middle 60%)

Meaning:
- Typical sector performance
- Not particularly noteworthy
- Within expected range

---

## Step-by-Step Calculation Example

**Scenario: Analyzing AAPL (Technology Sector) Tim Cook appointment**

Step 1: Collect all Tech CEOs' 90-day impacts
```
Sector CEOs: [+18.4%, +5.2%, -3.1%, +12.3%, -8.5%, ...]
Sector mean: +8.0%
Sector std dev: 9.5%
```

Step 2: Calculate z-score for Tim Cook's 90-day impact
```
Tim Cook 90-day impact: +18.4%
z_90day = (18.4 - 8.0) / 9.5 = 1.09 (above average but not exceptional)
```

Step 3: Repeat for 1-year impact and volatility
```
z_1year = 1.25 (positive impact sustained)
z_volatility = -0.55 (lower volatility than average = good)
```

Step 4: Calculate composite z-score
```
z_performance = 0.40 × 1.09 + 0.35 × 1.25 + 0.25 × (-0.55)
              = 0.436 + 0.438 - 0.138
              = 0.74 (MODERATE POSITIVE)
```

Classification: **MODERATE POSITIVE CEO** (good performance, above sector average, but not exceptional)

---

## Sector-by-Sector Baselines

Z-scores are calculated per sector because different sectors have different norms:

| Sector | Avg Sharpe | Avg Volatility | Avg Tenure |
|--------|-----------|--------|------------|
| Technology | 0.85 | 28% | 6.2 years |
| Healthcare | 0.72 | 20% | 7.1 years |
| Financials | 0.65 | 22% | 7.8 years |
| Energy | 0.58 | 32% | 8.5 years |
| Consumer | 0.70 | 18% | 7.4 years |
| Industrials | 0.68 | 19% | 8.1 years |
| Utilities | 0.55 | 14% | 9.2 years |

---

## Why Sector Comparison?

Comparing within sector ensures fair assessment:
- Tech CEOs are inherently riskier (higher volatility expected)
- Utility CEOs are inherently safer (lower volatility expected)
- A +20% return is exceptional for Utilities but normal for Tech

Example:
```
Tech CEO with +25% return and 25% volatility → Good but not exceptional
Utility CEO with +12% return and 10% volatility → Exceptional

Raw returns look different, but risk-adjusted (Sharpe ratio) both are strong
```

---

## Using Outlier Analysis

### For Investors
- Identify companies with exceptional CEOs (STRONG POSITIVE)
- Avoid companies with struggling CEOs (STRONG NEGATIVE)
- Use sector context to understand if outperformance is sustainable

### For Companies
- Benchmark CEO performance vs peers
- Identify best practices from STRONG POSITIVE CEOs
- Plan succession for underperforming CEOs

### For Researchers
- Understand CEO impact on stock performance
- Control for sector and macro effects
- Identify outliers worth deeper investigation
