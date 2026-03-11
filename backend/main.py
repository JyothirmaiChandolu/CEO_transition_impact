"""
FastAPI Backend
Serves stock data and KPIs from the data pipeline
"""
import json
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="CEO Impact Analysis API", version="1.0.0")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data directory
DATA_DIR = Path(__file__).parent.parent / 'data'


# ==================== HELPER FUNCTIONS ====================

def load_json(filepath: Path):
    """Load JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {filepath}")
        return None


def get_validated_stocks() -> dict:
    """Get list of all validated stocks"""
    validated_dir = DATA_DIR / 'stocks' / 'validated'
    if not validated_dir.exists():
        return {}

    stocks = {}
    for json_file in validated_dir.glob('*_validated.json'):
        ticker = json_file.stem.replace('_validated', '')
        try:
            data = load_json(json_file)
            stocks[ticker] = data
        except Exception as e:
            logger.error(f"Error loading {json_file}: {e}")

    return stocks


def get_kpi(ticker: str) -> dict:
    """Get KPI data for a stock"""
    kpi_file = DATA_DIR / 'stocks' / 'kpis' / f'{ticker.upper()}_kpis.json'
    return load_json(kpi_file)


# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "CEO Impact Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "companies": "/api/companies",
            "stocks": "/api/stocks/{ticker}",
            "kpis": "/api/kpis/{ticker}",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "data_dir": str(DATA_DIR)}


# ==================== STOCKS ENDPOINTS ====================

@app.get("/api/stocks")
async def get_all_stocks():
    """Get list of all available stocks"""
    stocks = get_validated_stocks()
    return {
        "total_stocks": len(stocks),
        "tickers": list(stocks.keys())
    }


@app.get("/api/stocks/{ticker}")
async def get_stock_data(ticker: str, limit: int = None):
    """
    Get validated stock data for a ticker

    Args:
        ticker: Stock ticker (e.g., 'AAPL')
        limit: Limit number of records (optional)
    """
    stock_file = DATA_DIR / 'stocks' / 'validated' / f'{ticker.upper()}_validated.json'

    if not stock_file.exists():
        raise HTTPException(status_code=404, detail=f"Stock data not found for {ticker}")

    data = load_json(stock_file)
    if data is None:
        raise HTTPException(status_code=500, detail="Error loading stock data")

    if limit and limit > 0:
        data = data[-limit:]

    return {
        "ticker": ticker.upper(),
        "total_records": len(data),
        "data": data
    }


@app.get("/api/stocks/{ticker}/range")
async def get_stock_range(ticker: str, start_date: str = None, end_date: str = None):
    """
    Get stock data within a date range

    Args:
        ticker: Stock ticker
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    """
    stock_file = DATA_DIR / 'stocks' / 'validated' / f'{ticker.upper()}_validated.json'

    if not stock_file.exists():
        raise HTTPException(status_code=404, detail=f"Stock data not found for {ticker}")

    data = load_json(stock_file)
    if data is None:
        raise HTTPException(status_code=500, detail="Error loading stock data")

    df = pd.DataFrame(data)

    if start_date:
        df = df[df['date'] >= start_date]
    if end_date:
        df = df[df['date'] <= end_date]

    return {
        "ticker": ticker.upper(),
        "date_range": {"start": start_date, "end": end_date},
        "records": len(df),
        "data": df.to_dict('records')
    }


# ==================== KPI ENDPOINTS ====================

@app.get("/api/kpis/{ticker}")
async def get_kpis(ticker: str):
    """
    Get all KPI metrics for a stock

    Args:
        ticker: Stock ticker
    """
    kpis = get_kpi(ticker)

    if kpis is None:
        raise HTTPException(status_code=404, detail=f"KPI data not found for {ticker}")

    return kpis


@app.get("/api/kpis/{ticker}/price")
async def get_price_metrics(ticker: str):
    """Get price-based KPI metrics"""
    kpis = get_kpi(ticker)

    if kpis is None:
        raise HTTPException(status_code=404, detail=f"KPI data not found for {ticker}")

    return {
        "ticker": ticker.upper(),
        "last_updated": kpis.get('last_updated'),
        "price_metrics": kpis.get('price_metrics', {})
    }


@app.get("/api/kpis/{ticker}/volume")
async def get_volume_metrics(ticker: str):
    """Get volume-based KPI metrics"""
    kpis = get_kpi(ticker)

    if kpis is None:
        raise HTTPException(status_code=404, detail=f"KPI data not found for {ticker}")

    return {
        "ticker": ticker.upper(),
        "last_updated": kpis.get('last_updated'),
        "volume_metrics": kpis.get('volume_metrics', {})
    }


@app.get("/api/kpis/{ticker}/risk")
async def get_risk_metrics(ticker: str):
    """Get risk-based KPI metrics"""
    kpis = get_kpi(ticker)

    if kpis is None:
        raise HTTPException(status_code=404, detail=f"KPI data not found for {ticker}")

    return {
        "ticker": ticker.upper(),
        "last_updated": kpis.get('last_updated'),
        "risk_metrics": kpis.get('risk_metrics', {})
    }


@app.get("/api/kpis/{ticker}/transition")
async def get_transition_impact(ticker: str):
    """Get CEO transition impact metrics"""
    kpis = get_kpi(ticker)

    if kpis is None:
        raise HTTPException(status_code=404, detail=f"KPI data not found for {ticker}")

    transition = kpis.get('transition_impact')
    if not transition:
        raise HTTPException(status_code=404, detail=f"No transition data for {ticker}")

    return {
        "ticker": ticker.upper(),
        "transition_impact": transition
    }


# ==================== COMPANIES ENDPOINT ====================

@app.get("/api/companies")
async def get_companies():
    """Get list of all companies with stock data"""
    companies_file = DATA_DIR / 'companies.json'

    if not companies_file.exists():
        raise HTTPException(status_code=404, detail="Companies data not found")

    companies = load_json(companies_file)
    return companies if companies else {"companies": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
