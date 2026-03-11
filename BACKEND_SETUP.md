# Backend Setup Guide

## Overview

The backend consists of:
1. **Data Pipeline** - Fetches, validates, transforms, and calculates KPIs for stock data
2. **FastAPI Server** - REST API to serve pre-calculated data to the frontend
3. **Scheduler** - Daily automated updates

## Architecture

```
Data Pipeline:
├── fetch.py           - Fetch stock data from yfinance
├── validate.py        - Validate data (duplicates, nulls, types)
├── calculate_kpis.py  - Calculate financial metrics
└── pipeline.py        - Orchestrate the entire process

FastAPI Backend:
└── main.py            - REST API endpoints

Scheduler:
└── scheduler.py       - Daily automated pipeline runs
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Tickers

Edit `data/companies.json` to include your companies. Example:

```json
{
  "companies": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "sector": "Technology",
      "transitions": [
        {
          "transitionDate": "2014-09-17",
          "previousCEO": "Steve Jobs",
          "newCEO": "Tim Cook",
          "filingBefore": "2014-05-22",
          "filingAfter": "2014-10-23"
        }
      ]
    }
  ]
}
```

### 3. Run Data Pipeline

#### One-time run:
```bash
python data_pipeline/scheduler.py
```

#### For specific tickers:
```python
from pathlib import Path
from data_pipeline import DataPipeline

pipeline = DataPipeline(data_dir=Path('../data'))

# Single stock
result = pipeline.process_stock('AAPL', transition_date='2014-09-17')

# Multiple stocks
results = pipeline.process_multiple_stocks(
    ['AAPL', 'MSFT', 'GOOGL'],
    transitions={'AAPL': '2014-09-17', 'MSFT': '2014-02-04'}
)
```

### 4. Start FastAPI Server

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: http://localhost:8000

API documentation: http://localhost:8000/docs

### 5. Setup Daily Scheduler (Optional)

For automatic daily updates:

```bash
python data_pipeline/scheduler.py
```

Or use system cron/scheduler:

```bash
# Run every day at 9 AM
0 9 * * * cd /path/to/CEO_impact_website_UI && python data_pipeline/scheduler.py
```

## Data Pipeline Flow

```
1. FETCH
   └─> yfinance → Raw stock data (OHLCV)

2. VALIDATE
   └─> Check: duplicates, primary keys, nulls, data types
       └─> Valid: /data/stocks/validated/{ticker}.json
       └─> Invalid: /data/stocks/invalid/{ticker}.csv

3. TRANSFORM
   └─> Calculate daily returns, clean data

4. CALCULATE KPIs
   ├─> Price Metrics: returns, volatility, moving averages
   ├─> Volume Metrics: avg volume, trends
   ├─> Risk Metrics: Sharpe ratio, max drawdown, beta
   └─> Transition Impact: pre/post CEO performance
       └─> Saved: /data/stocks/kpis/{ticker}.json

5. SERVE
   └─> FastAPI endpoints return pre-calculated data
```

## Data Storage

```
data/
├── stocks/
│   ├── validated/
│   │   ├── AAPL_validated.json    (Raw OHLCV data)
│   │   ├── MSFT_validated.json
│   │   └── ...
│   ├── kpis/
│   │   ├── AAPL_kpis.json        (Calculated metrics)
│   │   ├── MSFT_kpis.json
│   │   └── ...
│   └── invalid/
│       ├── AAPL_invalid.csv       (Failed validation rows)
│       └── ...
└── companies.json
```

## API Endpoints

### Health Check
```
GET /health
```

### Companies
```
GET /api/companies
```

### Stock Data
```
GET /api/stocks
GET /api/stocks/{ticker}
GET /api/stocks/{ticker}/range?start_date=2020-01-01&end_date=2021-01-01
```

### KPIs
```
GET /api/kpis/{ticker}
GET /api/kpis/{ticker}/price
GET /api/kpis/{ticker}/volume
GET /api/kpis/{ticker}/risk
GET /api/kpis/{ticker}/transition
```

## Data Validation Rules

### Stock Data Validation

| Field  | Type  | Required | Rules |
|--------|-------|----------|-------|
| date   | str   | Yes      | Format: YYYY-MM-DD |
| ticker | str   | Yes      | 1-5 uppercase letters, Primary Key |
| open   | float | Yes      | Must be > 0 |
| high   | float | Yes      | Must be > 0 |
| low    | float | Yes      | Must be > 0 |
| close  | float | Yes      | Must be > 0 |
| volume | int   | Yes      | Must be >= 0 |

Primary Key: `(date, ticker)` - No duplicates allowed

## KPI Metrics Explained

### Price Metrics
- **Total Return %**: Overall price change percentage
- **Volatility %**: Annualized standard deviation (252 trading days)
- **Moving Averages**: 20, 50, 200-day averages
- **Price Range**: High and low prices in period

### Volume Metrics
- **Avg Volume**: Average daily trading volume
- **Avg Volume 20D**: Last 20 days average
- **Volume Trend %**: Change from historical average

### Risk Metrics
- **Sharpe Ratio**: Return per unit of risk
- **Max Drawdown %**: Largest peak-to-trough decline
- **Daily Volatility %**: Daily price fluctuation

### Transition Impact
- **90-Day Impact %**: Stock change 90 days after transition
- **1-Year Impact %**: Stock change 1 year after transition
- **Pre-Transition Trend %**: Performance 90 days before transition

## Troubleshooting

### No data found for ticker
- Verify ticker symbol (use uppercase)
- Check yfinance data availability
- Some tickers may not have sufficient historical data

### Validation errors
- Check CSV format in companies.json
- Ensure dates are in YYYY-MM-DD format
- Verify ticker symbols are 1-5 uppercase letters

### API returns 404
- Run pipeline first to generate data files
- Check /data/stocks/validated/ folder exists
- Verify ticker data was successfully processed

## Frontend Integration

Frontend expects API at `VITE_API_URL` (default: http://localhost:8000/api)

Set in `.env`:
```
VITE_API_URL=http://localhost:8000/api
```

## Deployment

### Docker
```dockerfile
FROM python:3.11
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### AWS
- Lambda for data pipeline (scheduled with EventBridge)
- API Gateway for FastAPI
- S3 for data storage
- RDS/DynamoDB for future database needs

### Heroku
```bash
heroku create ceo-impact-api
git push heroku main
```

## Development

### Run tests
```bash
pytest data_pipeline/tests/
```

### Check logs
```bash
tail -f data_pipeline.log
```

### Debug scheduler
```python
from data_pipeline.scheduler import DataScheduler
scheduler = DataScheduler()
print(scheduler.get_status())
```
