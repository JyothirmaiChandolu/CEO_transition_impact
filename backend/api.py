"""
Title: CEO performance analysis
Author: Jyothirmai Chandolu
Employee_id: 800342

FastAPI Backend
Serves all /api/* endpoints for the frontend and integrates the RAG chatbot.
"""
import sys
import json
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

BASE_DIR   = Path(__file__).parent.parent
DATA_DIR   = BASE_DIR / "data"

sys.path.insert(0, str(Path(__file__).parent))          # backend/ — for chatbot, data_pipeline
sys.path.insert(0, str(Path(__file__).parent / "data_pipeline"))  # direct module imports

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="CEO Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Index config
# ---------------------------------------------------------------------------

def _load_indices_config() -> dict:
    p = DATA_DIR / "indices_config.json"
    if not p.exists():
        raise RuntimeError("data/indices_config.json not found")
    with open(p) as f:
        return json.load(f)

_INDICES_CONFIG: dict = _load_indices_config()


def _get_index_config(index_key: str) -> dict:
    if index_key not in _INDICES_CONFIG:
        raise HTTPException(404, f"Unknown index: {index_key}")
    return _INDICES_CONFIG[index_key]


# ---------------------------------------------------------------------------
# Per-index in-memory caches
# ---------------------------------------------------------------------------

_companies_cache: dict[str, dict] = {}
_kpi_cache: dict[str, dict] = {}       # key: "{index_key}_{ticker}"
_stock_cache: dict[str, list] = {}     # key: "{index_key}_{ticker}"
_impact_cache: dict[str, dict] = {}    # key: "{index_key}_{ticker}_{date}"


def _companies(index_key: str) -> dict:
    if index_key not in _companies_cache:
        cfg = _get_index_config(index_key)
        p = BASE_DIR / cfg["companies_file"]
        if not p.exists():
            raise HTTPException(404, f"companies.json not found for index {index_key}")
        with open(p) as f:
            _companies_cache[index_key] = json.load(f)
    return _companies_cache[index_key]


def _kpi(index_key: str, ticker: str) -> dict | None:
    t = ticker.upper()
    cache_key = f"{index_key}_{t}"
    if cache_key not in _kpi_cache:
        cfg = _get_index_config(index_key)
        kpi_dir = BASE_DIR / cfg["kpi_dir"]
        p = kpi_dir / f"{t}_kpis.json"
        _kpi_cache[cache_key] = json.load(open(p)) if p.exists() else None
    return _kpi_cache[cache_key]


def _stock(index_key: str, ticker: str) -> list | None:
    t = ticker.upper()
    cache_key = f"{index_key}_{t}"
    if cache_key not in _stock_cache:
        cfg = _get_index_config(index_key)
        val_dir = BASE_DIR / cfg["validated_dir"]
        p = val_dir / f"{t}_validated.json"
        _stock_cache[cache_key] = json.load(open(p)) if p.exists() else None
    return _stock_cache[cache_key]


# ---------------------------------------------------------------------------
# Outlier helpers
# ---------------------------------------------------------------------------

def _z(values: np.ndarray) -> np.ndarray:
    std = values.std()
    return (values - values.mean()) / std if std > 0 else np.zeros_like(values, dtype=float)


def _strength(z: float) -> str:
    return "STRONG" if abs(z) >= 2.0 else "MODERATE" if abs(z) >= 1.5 else "NORMAL"


def _status(z: float) -> str:
    return "OUTLIER_HIGH" if z >= 1.5 else "OUTLIER_LOW" if z <= -1.5 else "NORMAL"


def _tenure(row: dict) -> int | None:
    try:
        s, e = row.get("start_date", ""), row.get("end_date", "")
        if s and e:
            return (pd.to_datetime(e) - pd.to_datetime(s)).days
    except Exception:
        pass
    return None


def _tenure_label(days: int | None) -> str:
    if not days or days < 0:
        return "Unknown"
    y, m = days // 365, (days % 365) // 30
    if y == 0 and m == 0:
        return "<1m"
    if y == 0:
        return f"{m}m"
    if m == 0:
        return f"{y}y"
    return f"{y}y {m}m"


def _transition_impact_cached(index_key: str, ticker: str, transition_date: str) -> dict:
    key = f"{index_key}_{ticker.upper()}_{transition_date}"
    if key not in _impact_cache:
        _impact_cache[key] = _compute_transition_impact(index_key, ticker, transition_date)
    return _impact_cache[key]


# ---------------------------------------------------------------------------
# /api/indices
# ---------------------------------------------------------------------------

@app.get("/api/indices")
async def get_indices():
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "benchmark_ticker": v["benchmark_ticker"],
        }
        for k, v in _INDICES_CONFIG.items()
    ]


# ---------------------------------------------------------------------------
# /api/{index}/companies
# ---------------------------------------------------------------------------

@app.get("/api/{index}/companies")
async def get_companies(index: str):
    return _companies(index)


# ---------------------------------------------------------------------------
# /api/{index}/stocks
# ---------------------------------------------------------------------------

@app.get("/api/{index}/stocks/{ticker}")
async def get_stock(index: str, ticker: str):
    data = _stock(index, ticker)
    if data is None:
        raise HTTPException(404, f"No stock data for {ticker}")
    return {"ticker": ticker.upper(), "total_records": len(data), "data": data}


@app.get("/api/{index}/stocks/{ticker}/range")
async def get_stock_range(index: str, ticker: str, start_date: str, end_date: str):
    data = _stock(index, ticker)
    if data is None:
        raise HTTPException(404, f"No stock data for {ticker}")
    filtered = [r for r in data if start_date <= r["date"] <= end_date]
    return {"ticker": ticker.upper(), "records": len(filtered), "data": filtered}


# ---------------------------------------------------------------------------
# /api/{index}/kpis
# ---------------------------------------------------------------------------

def _compute_transition_impact(index_key: str, ticker: str, transition_date: str) -> dict:
    """Compute CEO transition impact from validated stock data."""
    from data_pipeline.fetch_macro import MacroDataFetcher
    records = _stock(index_key, ticker)
    if not records:
        return {}

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    td = pd.to_datetime(transition_date)

    # Find closest trading day on or after transition date
    after = df[df["date"] >= td]
    if after.empty:
        return {}
    idx0 = after.index[0]
    transition_price = float(df.loc[idx0, "close"])

    # Price 90 days after
    t90 = td + pd.Timedelta(days=90)
    after90 = df[df["date"] >= t90]
    price_90d = float(after90.iloc[0]["close"]) if not after90.empty else None

    # Price 1 year after
    t1y = td + pd.Timedelta(days=365)
    after1y = df[df["date"] >= t1y]
    price_1y = float(after1y.iloc[0]["close"]) if not after1y.empty else None

    # Pre-transition 90-day trend
    t_before90 = td - pd.Timedelta(days=90)
    before90 = df[(df["date"] >= t_before90) & (df["date"] < td)]
    if not before90.empty:
        pre_price = float(before90.iloc[0]["close"])
        pre_trend = round((transition_price - pre_price) / pre_price * 100, 2) if pre_price else 0
    else:
        pre_trend = 0

    impact_90d = round((price_90d - transition_price) / transition_price * 100, 2) if price_90d else None
    impact_1y = round((price_1y - transition_price) / transition_price * 100, 2) if price_1y else None

    try:
        macro = MacroDataFetcher().get_macro_context(transition_date)
    except Exception:
        macro = {"in_recession": False, "recession_period": None, "context": "Unknown"}

    note = (
        f"CEO transition on {transition_date}. "
        f"Stock at ${transition_price:.2f}. "
        + (f"90-day impact: {impact_90d:+.1f}%. " if impact_90d is not None else "")
        + (f"1-year impact: {impact_1y:+.1f}%." if impact_1y is not None else "No 1-year data yet.")
    )

    return {
        "transition_date": transition_date,
        "transition_price": round(transition_price, 2),
        "impact_90days_pct": impact_90d,
        "impact_1year_pct": impact_1y,
        "pre_transition_trend_90d_pct": pre_trend,
        "macro_economic_context": {
            "in_recession": macro.get("in_recession", False),
            "recession_period": macro.get("recession_period"),
            "context": macro.get("context", "Unknown"),
        },
        "analysis_note": note,
    }


@app.get("/api/{index}/kpis/{ticker}")
async def get_kpis(index: str, ticker: str, transition_date: Optional[str] = None):
    kpi = _kpi(index, ticker)
    if kpi is None:
        raise HTTPException(404, f"No KPIs for {ticker}")

    if transition_date:
        kpi = dict(kpi)
        kpi["transition_impact"] = _compute_transition_impact(index, ticker, transition_date)

    return kpi


@app.get("/api/{index}/kpis/{ticker}/price")
async def get_price(index: str, ticker: str):
    kpi = _kpi(index, ticker)
    if kpi is None:
        raise HTTPException(404, f"No KPIs for {ticker}")
    return kpi.get("price_metrics", {})


@app.get("/api/{index}/kpis/{ticker}/volume")
async def get_volume(index: str, ticker: str):
    kpi = _kpi(index, ticker)
    if kpi is None:
        raise HTTPException(404, f"No KPIs for {ticker}")
    return kpi.get("volume_metrics", {})


@app.get("/api/{index}/kpis/{ticker}/risk")
async def get_risk(index: str, ticker: str):
    kpi = _kpi(index, ticker)
    if kpi is None:
        raise HTTPException(404, f"No KPIs for {ticker}")
    return kpi.get("risk_metrics", {})


@app.get("/api/{index}/kpis/{ticker}/transition")
async def get_transition(index: str, ticker: str, transition_date: Optional[str] = None):
    kpi = _kpi(index, ticker)
    if kpi is None:
        raise HTTPException(404, f"No KPIs for {ticker}")
    if transition_date:
        impact = _compute_transition_impact(index, ticker, transition_date)
    else:
        impacts = kpi.get("transition_impacts") or []
        impact = kpi.get("transition_impact") or (impacts[0] if impacts else None)
    if not impact:
        raise HTTPException(404, f"No transition impact for {ticker}")
    return impact


# ---------------------------------------------------------------------------
# /api/{index}/archive
# ---------------------------------------------------------------------------

@app.get("/api/{index}/archive")
async def get_archive(index: str):
    cfg = _get_index_config(index)
    p = BASE_DIR / cfg["metadata_file"]
    if not p.exists():
        return {"index": index, "companies": []}
    with open(p) as f:
        raw = json.load(f)

    companies = []
    # Support dict keyed by ticker or list
    items = raw.items() if isinstance(raw, dict) else ((c.get("ticker", ""), c) for c in raw)
    for ticker, meta in items:
        companies.append({
            "ticker": ticker,
            "name": meta.get("name") or meta.get("longName") or meta.get("shortName") or ticker,
            "sector": meta.get("sector", ""),
            "industry": meta.get("industry", ""),
            "country": meta.get("country", ""),
            "employees": meta.get("employees") or meta.get("fullTimeEmployees"),
            "marketCap": meta.get("marketCap"),
            "website": meta.get("website", ""),
        })
    return {"index": index, "companies": companies}


# ---------------------------------------------------------------------------
# /api/index/{index_ticker} — global market index data (unchanged)
# ---------------------------------------------------------------------------

_INDEX_ALIASES = {
    "OEX": "^OEX",
    "SPX": "^GSPC",
    "NDX": "^NDX",
    "DJI": "^DJI",
    "RUT": "^RUT",
}
_index_cache: dict = {}

def _index_dirs() -> list[Path]:
    """Return all index_dir paths defined across all index configs."""
    dirs = []
    for cfg in _INDICES_CONFIG.values():
        d = cfg.get("index_dir")
        if d:
            dirs.append(BASE_DIR / d)
    return dirs


@app.get("/api/index/{index_ticker}")
async def get_index(index_ticker: str):
    key = index_ticker.upper()
    if key in _index_cache:
        return _index_cache[key]

    # Serve from pre-fetched local file — search all per-index dirs
    local: Path | None = None
    for d in _index_dirs():
        candidate = d / f"{key}.json"
        if candidate.exists():
            local = candidate
            break
    if local is not None:
        with open(local) as f:
            result = json.load(f)
        _index_cache[key] = result
        return result

    # Fallback: fetch live from yfinance
    yf_ticker = _INDEX_ALIASES.get(key, index_ticker)
    raw = yf.download(yf_ticker, start="1996-01-01", progress=False)
    if raw.empty:
        raise HTTPException(404, f"No data for index {index_ticker}")
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = [col[0] for col in raw.columns]
    raw = raw.reset_index()
    data = []
    for _, row in raw.iterrows():
        def _v(col, default=0.0):
            try:
                return float(row.get(col, default))
            except (TypeError, ValueError):
                return float(default)
        data.append({
            "date": str(row["Date"])[:10],
            "ticker": key,
            "open": round(_v("Open"), 2),
            "high": round(_v("High"), 2),
            "low": round(_v("Low"), 2),
            "close": round(_v("Close"), 2),
            "volume": int(_v("Volume")),
        })
    result = {"ticker": key, "total_records": len(data), "data": data}
    _index_cache[key] = result
    return result


# ---------------------------------------------------------------------------
# /api/analysis/recession-impact — unchanged
# ---------------------------------------------------------------------------

@app.get("/api/analysis/recession-impact")
async def get_recession_impact():
    from data_pipeline.fetch_macro import MacroDataFetcher

    rut_file = BASE_DIR / _INDICES_CONFIG.get("russell2000", {}).get("index_dir", "data/rus2000/index") / "RUT.json"
    if not rut_file.exists():
        raise HTTPException(503, "Russell 2000 index data not found. Fetch it first.")
    with open(rut_file) as f:
        rut = json.load(f)

    index_df = pd.DataFrame(rut["data"])
    macro = MacroDataFetcher()
    result = macro.get_recession_impact(index_df)

    return {
        "timestamp": datetime.now().isoformat(),
        "index": "Russell 2000",
        "benchmark_decline": f"{result['summary']['average_decline']}% average",
        "recessions": result["recessions"],
        "summary": result["summary"],
    }


# ---------------------------------------------------------------------------
# /api/{index}/outliers/sector/{sector}
# ---------------------------------------------------------------------------

@app.get("/api/{index}/outliers/sector/{sector}")
async def get_sector_outliers(index: str, sector: str, period_years: Optional[int] = None):
    companies_data = _companies(index)
    sector_cos = [c for c in companies_data["companies"] if c.get("sector") == sector]
    if not sector_cos:
        raise HTTPException(404, f"Sector '{sector}' not found or has no companies")

    today = datetime.now()
    ceo_perf_rows, ceo_tenure_rows, co_rows = [], [], []

    for c in sector_cos:
        ticker = c["ticker"]
        kpi = _kpi(index, ticker)
        if kpi is None:
            continue

        pm = kpi.get("price_metrics", {})
        rm = kpi.get("risk_metrics", {})
        co_rows.append({
            "ticker": ticker,
            "company_name": c.get("name", ticker),
            "total_return_pct": pm.get("total_return_pct") or 0,
            "volatility_pct": pm.get("volatility_pct") or 0,
            "sharpe_ratio": rm.get("sharpe_ratio") or 0,
            "max_drawdown_pct": rm.get("max_drawdown_pct") or 0,
        })

        transitions = c.get("transitions", [])
        for i, t in enumerate(transitions):
            ceo_name = t.get("newCEO", "Unknown")
            if ceo_name in ("Unknown", "ERROR", "NOT FOUND"):
                continue
            trans_date = t.get("transitionDate", "")
            if not trans_date:
                continue

            impact = _transition_impact_cached(index, ticker, trans_date)
            i90 = impact.get("impact_90days_pct")
            i1y = impact.get("impact_1year_pct")
            macro_ctx = impact.get("macro_economic_context", {}).get("context", "Unknown")

            ceo_perf_rows.append({
                "ticker": ticker, "company_name": c.get("name", ticker),
                "ceo_name": ceo_name, "transition_date": trans_date,
                "impact_90days_pct": i90 or 0,
                "impact_1year_pct": i1y or 0,
                "daily_volatility_pct": rm.get("daily_volatility_pct") or 0,
                "macro_context": macro_ctx,
            })

            # Tenure: this transition to next, or today
            end_str = transitions[i + 1].get("transitionDate") if i + 1 < len(transitions) else today.strftime("%Y-%m-%d")
            try:
                td = (pd.to_datetime(end_str) - pd.to_datetime(trans_date)).days
                if td > 0:
                    ceo_tenure_rows.append({
                        "ticker": ticker, "company_name": c.get("name", ticker),
                        "ceo_name": ceo_name, "transition_date": trans_date,
                        "tenure_days": td, "tenure_label": _tenure_label(td),
                        "impact_1year_pct": i1y or 0,
                    })
            except Exception:
                pass

    def _build_outlier_list(rows, sort_key, score_key, threshold=1.5):
        if not rows:
            return [], [], []
        df = pd.DataFrame(rows)
        vals = df[score_key].values.astype(float)
        df["z"] = _z(vals)
        df["pct"] = df[score_key].rank(pct=True) * 100
        df = df.sort_values("z", ascending=False).reset_index(drop=True)
        cut = max(1, len(df) // 5)
        high, low, all_ = [], [], []
        for idx, row in df.iterrows():
            z = float(row["z"])
            rec = {**{k: row[k] for k in row.index if k not in ("z", "pct")},
                   "composite_z_score": round(z, 2),
                   "is_outlier": bool(abs(z) >= threshold),
                   "outlier_strength": _strength(z),
                   "outlier_status": _status(z)}
            all_.append(rec)
            if idx < cut:
                high.append(rec)
            elif idx >= len(df) - cut:
                low.append(rec)
        return high, low, all_

    # CEO performance outliers
    if ceo_perf_rows:
        pdf = pd.DataFrame(ceo_perf_rows)
        pdf["z90"] = _z(pdf["impact_90days_pct"].values.astype(float))
        pdf["z1y"] = _z(pdf["impact_1year_pct"].values.astype(float))
        pdf["cz"]  = 0.40 * pdf["z90"] + 0.35 * pdf["z1y"] + 0.25 * _z(-pdf["daily_volatility_pct"].values.astype(float))
        pdf["p90"] = pdf["impact_90days_pct"].rank(pct=True) * 100
        pdf["p1y"] = pdf["impact_1year_pct"].rank(pct=True) * 100
        cut = max(1, len(pdf) // 5)
        pdf = pdf.sort_values("cz", ascending=False).reset_index(drop=True)

        high_perf, low_perf, all_ceos = [], [], []
        for idx, row in pdf.iterrows():
            z = float(row["cz"])
            rec = {
                "ticker": row["ticker"], "company_name": row["company_name"],
                "ceo_name": row["ceo_name"], "transition_date": row["transition_date"],
                "impact_90days_pct": round(float(row["impact_90days_pct"]), 2),
                "impact_1year_pct": round(float(row["impact_1year_pct"]), 2),
                "daily_volatility_pct": round(float(row["daily_volatility_pct"]), 2),
                "z_score_90days": round(float(row["z90"]), 2),
                "z_score_1year": round(float(row["z1y"]), 2),
                "composite_z_score": round(z, 2),
                "percentile_90days": round(float(row["p90"]), 1),
                "percentile_1year": round(float(row["p1y"]), 1),
                "macro_context": row["macro_context"],
                "is_outlier": bool(abs(z) >= 1.5),
                "outlier_strength": _strength(z),
                "outlier_status": _status(z),
            }
            all_ceos.append(rec)
            if idx < cut:
                high_perf.append({**rec, "outlier_status": "OUTLIER_HIGH",
                                   "outlier_strength": rec["outlier_strength"] if rec["outlier_strength"] != "NORMAL" else "MODERATE"})
            elif idx >= len(pdf) - cut:
                low_perf.append({**rec, "outlier_status": "OUTLIER_LOW",
                                  "outlier_strength": rec["outlier_strength"] if rec["outlier_strength"] != "NORMAL" else "MODERATE"})
    else:
        high_perf = low_perf = all_ceos = []

    # CEO tenure outliers
    if ceo_tenure_rows:
        tdf = pd.DataFrame(ceo_tenure_rows)
        tdf["zt"] = _z(tdf["tenure_days"].values.astype(float))
        tdf["pt"] = tdf["tenure_days"].rank(pct=True) * 100
        tdf = tdf.sort_values("zt", ascending=False).reset_index(drop=True)
        cut_t = max(1, len(tdf) // 5)
        long_t, short_t, all_t = [], [], []
        for idx, row in tdf.iterrows():
            z = float(row["zt"])
            rec = {
                "ticker": row["ticker"], "company_name": row["company_name"],
                "ceo_name": row["ceo_name"], "transition_date": row["transition_date"],
                "tenure_days": int(row["tenure_days"]),
                "tenure_label": row["tenure_label"],
                "impact_1year_pct": round(float(row["impact_1year_pct"]), 2),
                "z_score_tenure": round(z, 2),
                "percentile_tenure": round(float(row["pt"]), 1),
                "is_outlier": bool(abs(z) >= 1.5),
                "outlier_strength": _strength(z),
                "outlier_status": _status(z),
            }
            all_t.append(rec)
            if idx < cut_t:
                long_t.append({**rec, "outlier_status": "OUTLIER_HIGH",
                                "outlier_strength": rec["outlier_strength"] if rec["outlier_strength"] != "NORMAL" else "MODERATE"})
            elif idx >= len(tdf) - cut_t:
                short_t.append({**rec, "outlier_status": "OUTLIER_LOW",
                                 "outlier_strength": rec["outlier_strength"] if rec["outlier_strength"] != "NORMAL" else "MODERATE"})
    else:
        long_t = short_t = all_t = []

    # Company outliers
    if co_rows:
        cdf = pd.DataFrame(co_rows)
        cdf["zr"] = _z(cdf["total_return_pct"].values.astype(float))
        cdf["zs"] = _z(cdf["sharpe_ratio"].values.astype(float))
        cdf["zv"] = -_z(cdf["volatility_pct"].values.astype(float))
        cdf["zd"] = -_z(cdf["max_drawdown_pct"].values.astype(float))
        cdf["cz"] = 0.40 * cdf["zr"] + 0.30 * cdf["zs"] + 0.15 * cdf["zv"] + 0.15 * cdf["zd"]
        cdf["pr"] = cdf["total_return_pct"].rank(pct=True) * 100
        cdf["ps"] = cdf["sharpe_ratio"].rank(pct=True) * 100
        cdf = cdf.sort_values("cz", ascending=False).reset_index(drop=True)
        cut_c = max(1, len(cdf) // 5)
        high_cos, low_cos, all_cos = [], [], []
        for idx, row in cdf.iterrows():
            z = float(row["cz"])
            rec = {
                "ticker": row["ticker"], "company_name": row["company_name"],
                "total_return_pct": round(float(row["total_return_pct"]), 2),
                "volatility_pct": round(float(row["volatility_pct"]), 2),
                "sharpe_ratio": round(float(row["sharpe_ratio"]), 2),
                "max_drawdown_pct": round(float(row["max_drawdown_pct"]), 2),
                "z_total_return": round(float(row["zr"]), 2),
                "z_volatility_ann": round(float(row["zv"]), 2),
                "z_sharpe": round(float(row["zs"]), 2),
                "z_drawdown": round(float(row["zd"]), 2),
                "composite_company_z": round(z, 2),
                "percentile_total_return": round(float(row["pr"]), 1),
                "percentile_sharpe": round(float(row["ps"]), 1),
                "is_outlier": bool(abs(z) >= 1.5),
                "outlier_strength": _strength(z),
                "outlier_status": _status(z),
            }
            all_cos.append(rec)
            if idx < cut_c:
                high_cos.append({**rec, "outlier_status": "OUTLIER_HIGH",
                                  "outlier_strength": rec["outlier_strength"] if rec["outlier_strength"] != "NORMAL" else "MODERATE"})
            elif idx >= len(cdf) - cut_c:
                low_cos.append({**rec, "outlier_status": "OUTLIER_LOW",
                                 "outlier_strength": rec["outlier_strength"] if rec["outlier_strength"] != "NORMAL" else "MODERATE"})
    else:
        high_cos = low_cos = all_cos = []

    def _safe_stat(lst, key):
        vals = [r[key] for r in lst if r.get(key) is not None]
        return (float(np.mean(vals)), float(np.std(vals))) if len(vals) >= 2 else (0.0, 0.0)

    m90, s90 = _safe_stat(ceo_perf_rows, "impact_90days_pct")
    m1y, s1y = _safe_stat(ceo_perf_rows, "impact_1year_pct")
    mt, st = _safe_stat(ceo_tenure_rows, "tenure_days")
    mr, sr = _safe_stat(co_rows, "total_return_pct")
    ms, ss = _safe_stat(co_rows, "sharpe_ratio")

    return {
        "sector": sector,
        "total_ceos_analyzed": len(ceo_perf_rows),
        "total_companies_analyzed": len(co_rows),
        "outlier_count": sum(1 for r in all_ceos if r["is_outlier"]),
        "sector_statistics": {
            "ceo_performance": {"mean_90day": round(m90, 2), "std_90day": round(s90, 2),
                                "mean_1year": round(m1y, 2), "std_1year": round(s1y, 2)},
            "tenure": {"mean_tenure_days": round(mt, 0), "std_tenure_days": round(st, 0)},
            "company": {"mean_total_return": round(mr, 2), "std_total_return": round(sr, 2),
                        "mean_sharpe": round(ms, 2), "std_sharpe": round(ss, 2)},
        },
        "performance_outliers": {"high_performers": high_perf, "low_performers": low_perf, "all_ceos": all_ceos},
        "tenure_outliers": {"long_tenure": long_t, "short_tenure": short_t, "all_ceos": all_t},
        "company_outliers": {"high_performers": high_cos, "low_performers": low_cos, "all_companies": all_cos},
    }


# ---------------------------------------------------------------------------
# /api/{index}/rankings
# ---------------------------------------------------------------------------

@app.get("/api/{index}/rankings/ceos")
async def get_ceo_rankings(index: str, top_n: int = 20, macro_adjusted: bool = True):
    rows = []
    today = datetime.now()
    for c in _companies(index)["companies"]:
        ticker = c["ticker"]
        kpi = _kpi(index, ticker)
        if kpi is None:
            continue
        rm = kpi.get("risk_metrics", {})
        transitions = c.get("transitions", [])
        for i, t in enumerate(transitions):
            ceo_name = t.get("newCEO", "Unknown")
            if ceo_name in ("Unknown", "ERROR", "NOT FOUND"):
                continue
            trans_date = t.get("transitionDate", "")
            if not trans_date:
                continue
            impact = _transition_impact_cached(index, ticker, trans_date)
            if not impact or impact.get("impact_1year_pct") is None:
                continue
            in_rec = impact.get("macro_economic_context", {}).get("in_recession", False)
            end_str = transitions[i + 1].get("transitionDate") if i + 1 < len(transitions) else today.strftime("%Y-%m-%d")
            rows.append({
                "ticker": ticker,
                "company_name": c.get("name", ticker),
                "sector": c.get("sector", ""),
                "ceo_name": ceo_name,
                "transition_date": trans_date,
                "impact_1year_pct": impact.get("impact_1year_pct") or 0,
                "impact_90days_pct": impact.get("impact_90days_pct") or 0,
                "daily_volatility_pct": rm.get("daily_volatility_pct") or 10,
                "macro_multiplier": 1.2 if in_rec and macro_adjusted else 1.0,
                "macro_context": impact.get("macro_economic_context", {}).get("context", ""),
                "start_date": t.get("startDate", ""),
                "end_date": end_str,
            })

    if not rows:
        return {"total_analyzed": 0, "macro_adjusted": macro_adjusted, "top_ceos": [], "global_stats": {}}

    df = pd.DataFrame(rows)
    df["z1y"] = _z(df["impact_1year_pct"].values)
    df["z90"] = _z(df["impact_90days_pct"].values)
    df["zv"]  = -_z(df["daily_volatility_pct"].values)
    df["tenure_days"] = df.apply(_tenure, axis=1).fillna(365)
    df["tenure_eff"] = df["impact_1year_pct"] / (df["tenure_days"] / 365 + 0.1)
    df["zte"] = _z(df["tenure_eff"].values)
    df["score"] = (df["z1y"] * 0.4 + df["z90"] * 0.3 + df["zv"] * 0.2 + df["zte"] * 0.1) * df["macro_multiplier"]
    df["pct"] = df["score"].rank(pct=True) * 100
    df = df.sort_values("score", ascending=False).head(top_n).reset_index(drop=True)

    top = []
    for rank, (_, row) in enumerate(df.iterrows(), 1):
        td = int(row["tenure_days"])
        top.append({
            "rank": rank,
            "ticker": row["ticker"],
            "company_name": row["company_name"],
            "sector": row["sector"],
            "ceo_name": row["ceo_name"],
            "transition_date": row["transition_date"],
            "impact_1year_pct": round(float(row["impact_1year_pct"]), 2),
            "impact_90days_pct": round(float(row["impact_90days_pct"]), 2),
            "daily_volatility_pct": round(float(row["daily_volatility_pct"]), 2),
            "tenure_days": td,
            "tenure_label": f"{td // 365}y {(td % 365) // 30}m",
            "tenure_efficiency": round(float(row["tenure_eff"]), 2),
            "macro_context": row["macro_context"],
            "composite_score": round(float(row["score"]), 2),
            "macro_multiplier": row["macro_multiplier"],
            "percentile_global": round(float(row["pct"]), 1),
            "score_breakdown": {
                "z_1year": round(float(row["z1y"]), 2),
                "z_90day": round(float(row["z90"]), 2),
                "z_vol": round(float(row["zv"]), 2),
                "z_tenure_eff": round(float(row["zte"]), 2),
            },
        })

    all_df = pd.DataFrame(rows)
    return {
        "total_analyzed": len(rows),
        "macro_adjusted": macro_adjusted,
        "top_ceos": top,
        "global_stats": {
            "mean_1year": round(float(all_df["impact_1year_pct"].mean()), 2),
            "std_1year": round(float(all_df["impact_1year_pct"].std()), 2),
            "mean_90day": round(float(all_df["impact_90days_pct"].mean()), 2),
            "std_90day": round(float(all_df["impact_90days_pct"].std()), 2),
        },
    }


@app.get("/api/{index}/rankings/companies")
async def get_company_rankings(index: str, top_n: int = 20):
    rows = []
    for c in _companies(index)["companies"]:
        ticker = c["ticker"]
        kpi = _kpi(index, ticker)
        if kpi is None:
            continue
        pm = kpi.get("price_metrics", {})
        rm = kpi.get("risk_metrics", {})
        if any(v is None for v in [pm.get("total_return_pct"), pm.get("volatility_pct"),
                                    rm.get("sharpe_ratio"), rm.get("max_drawdown_pct")]):
            continue
        rows.append({
            "ticker": ticker,
            "company_name": c.get("name", ticker),
            "sector": c.get("sector", ""),
            "total_return_pct": pm["total_return_pct"],
            "volatility_pct": pm["volatility_pct"],
            "sharpe_ratio": rm["sharpe_ratio"],
            "max_drawdown_pct": rm["max_drawdown_pct"],
        })

    if not rows:
        return {"total_analyzed": 0, "top_companies": [], "global_stats": {}}

    df = pd.DataFrame(rows)
    df["zr"] = _z(df["total_return_pct"].values)
    df["zs"] = _z(df["sharpe_ratio"].values)
    df["zv"] = -_z(df["volatility_pct"].values)
    df["zd"] = -_z(df["max_drawdown_pct"].values)
    df["score"] = df["zr"] * 0.35 + df["zs"] * 0.35 + df["zv"] * 0.15 + df["zd"] * 0.15
    df["pct"] = df["score"].rank(pct=True) * 100
    df = df.sort_values("score", ascending=False).head(top_n).reset_index(drop=True)

    top = []
    for rank, (_, row) in enumerate(df.iterrows(), 1):
        top.append({
            "rank": rank,
            "ticker": row["ticker"],
            "company_name": row["company_name"],
            "sector": row["sector"],
            "total_return_pct": round(float(row["total_return_pct"]), 2),
            "volatility_pct": round(float(row["volatility_pct"]), 2),
            "sharpe_ratio": round(float(row["sharpe_ratio"]), 2),
            "max_drawdown_pct": round(float(row["max_drawdown_pct"]), 2),
            "composite_score": round(float(row["score"]), 2),
            "percentile_global": round(float(row["pct"]), 1),
            "score_breakdown": {
                "z_return": round(float(row["zr"]), 2),
                "z_sharpe": round(float(row["zs"]), 2),
                "z_vol": round(float(row["zv"]), 2),
                "z_drawdown": round(float(row["zd"]), 2),
            },
        })

    all_df = pd.DataFrame(rows)
    return {
        "total_analyzed": len(rows),
        "top_companies": top,
        "global_stats": {
            "mean_return": round(float(all_df["total_return_pct"].mean()), 2),
            "std_return": round(float(all_df["total_return_pct"].std()), 2),
            "mean_sharpe": round(float(all_df["sharpe_ratio"].mean()), 2),
            "std_sharpe": round(float(all_df["sharpe_ratio"].std()), 2),
        },
    }


# ---------------------------------------------------------------------------
# /api/ceo/profile  — Wikipedia-based CEO profile lookup
# ---------------------------------------------------------------------------

@app.get("/api/ceo/profile")
async def get_ceo_profile(name: str, company: str = "", impact_90d: Optional[float] = None):
    import httpx

    bio: str | None = None
    image_url: str | None = None
    url: str | None = None
    page_title: str = name

    # Step 1: Wikipedia fetch
    try:
        headers = {"User-Agent": "CEOAnalysisTool/1.0 (research project)"}
        async with httpx.AsyncClient(timeout=10, headers=headers) as client:
            search = await client.get(
                "https://en.wikipedia.org/w/api.php",
                params={"action": "query", "list": "search",
                        "srsearch": f"{name} CEO {company}".strip(),
                        "format": "json", "srlimit": 3},
            )
            results = search.json().get("query", {}).get("search", [])
            if results:
                # Prefer a result whose title contains the CEO's last name
                last_name = name.split()[-1].lower()
                best = next((r for r in results if last_name in r["title"].lower()), results[0])
                page_title = best["title"]
                page_resp = await client.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={"action": "query", "titles": page_title,
                            "prop": "extracts|pageimages|info",
                            "exintro": True, "explaintext": True,
                            "pithumbsize": 600, "inprop": "url",
                            "format": "json"},
                )
                pages = page_resp.json().get("query", {}).get("pages", {})
                page = next(iter(pages.values()))
                raw = page.get("extract", "") or ""
                if len(raw) > 900:
                    cut = raw.rfind(". ", 0, 900)
                    bio = raw[: cut + 1] if cut != -1 else raw[:900]
                else:
                    bio = raw or None
                image_url = page.get("thumbnail", {}).get("source") if page.get("thumbnail") else None
                url = page.get("fullurl")
    except Exception as e:
        logger.error(f"Wikipedia fetch error for '{name}': {e}")

    # Step 2: OpenAI structured extraction
    background = "Executive Leader"
    focus = "Strategic Growth"
    narrative: str | None = None
    mandates: list[str] = []

    try:
        from openai import AsyncOpenAI
        oai = AsyncOpenAI()
        impact_note = (
            f"The stock moved {impact_90d:+.1f}% in the 90 days after the transition."
            if impact_90d is not None else ""
        )
        prompt = f"""You are analyzing {name}, the incoming CEO at {company}.

Wikipedia bio:
{bio or "No Wikipedia data available."}

{impact_note}

Return a JSON object with exactly these fields:
{{
  "background": "Previous role in 2-4 words (e.g. 'Former CFO', 'Former COO', 'Industry Veteran')",
  "focus": "Strategic focus area in 2-4 words (e.g. 'Digital Transformation', 'Operational Excellence')",
  "narrative": "Two paragraphs separated by a newline. First paragraph: what this CEO transition signals strategically for {company}. Second paragraph: their appointment context, their background, and the market's reaction{(' (' + f'{impact_90d:+.1f}%' + ' stock move)') if impact_90d is not None else ''}.",
  "mandates": ["Specific objective or achievement 1", "Specific objective or achievement 2", "Specific objective or achievement 3"]
}}

Base everything on the Wikipedia bio where available; use general knowledge about {name} and {company} otherwise. Return only valid JSON."""

        resp = await oai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=600,
        )
        extracted = json.loads(resp.choices[0].message.content)
        background = extracted.get("background", background)
        focus = extracted.get("focus", focus)
        narrative = extracted.get("narrative")
        mandates = extracted.get("mandates", [])[:3]
    except Exception as e:
        logger.error(f"OpenAI profile extraction error for '{name}': {e}")
        # Smart fallback: derive fields from bio text heuristically
        if bio:
            bio_lower = bio.lower()
            # Guess background from role keywords
            for role in ["chief operating officer", "coo", "chief financial officer", "cfo",
                         "president", "chief technology officer", "cto", "vice president",
                         "general counsel", "chief marketing officer"]:
                if role in bio_lower:
                    abbr = {"chief operating officer": "Former COO", "coo": "Former COO",
                            "chief financial officer": "Former CFO", "cfo": "Former CFO",
                            "chief technology officer": "Former CTO", "cto": "Former CTO",
                            "president": "Former President", "vice president": "Former VP",
                            "general counsel": "Former General Counsel",
                            "chief marketing officer": "Former CMO"}.get(role, "Executive Leader")
                    background = abbr
                    break
            # Guess focus from keywords
            for kw, label in [("technology", "Technology & Innovation"),
                               ("digital", "Digital Transformation"),
                               ("finance", "Financial Excellence"),
                               ("operations", "Operational Excellence"),
                               ("growth", "Revenue Growth"),
                               ("sustain", "Sustainability"),
                               ("health", "Healthcare Innovation")]:
                if kw in bio_lower:
                    focus = label
                    break
            # Build a two-paragraph narrative from the bio
            sentences = [s.strip() for s in bio.replace("\n", " ").split(".") if len(s.strip()) > 30]
            p1 = ". ".join(sentences[:2]) + "." if sentences else ""
            p2 = ". ".join(sentences[2:4]) + "." if len(sentences) > 2 else ""
            impact_txt = f" The stock moved {impact_90d:+.1f}% in the 90 days following the transition." if impact_90d is not None else ""
            narrative = f"{p1}\n{p2}{impact_txt}".strip()
            mandates = [
                f"Lead {company}'s next phase of strategic growth",
                "Drive operational efficiency and shareholder value",
                "Execute the company's long-term vision and transformation agenda",
            ]
        else:
            impact_txt = f" The stock moved {impact_90d:+.1f}% in the 90 days following the transition." if impact_90d is not None else ""
            narrative = (
                f"The appointment of {name} as CEO of {company} marks a new chapter in the company's leadership journey."
                f"\nAppointed to drive the company's strategic agenda, {name} brings executive experience to the role.{impact_txt}"
            )
            mandates = [
                f"Lead {company}'s strategic growth and market expansion",
                "Strengthen operational performance and shareholder value",
                "Build and inspire a high-performing leadership team",
            ]

    return {
        "name": name,
        "bio": bio,
        "image_url": image_url,
        "url": url,
        "wikipedia_title": page_title,
        "background": background,
        "focus": focus,
        "narrative": narrative,
        "mandates": mandates,
    }


# ---------------------------------------------------------------------------
# /api/chat
# ---------------------------------------------------------------------------

@app.post("/api/chat")
async def chat(body: dict):
    query = body.get("query", "")
    if not query:
        raise HTTPException(400, "query is required")
    try:
        from chatbot.rag_pipeline import RAGPipeline
        rag = RAGPipeline(data_dir=str(DATA_DIR))
        response = rag.answer(
            query,
            ticker=body.get("ticker"),
            sector=body.get("sector"),
            transition_date=body.get("transition_date"),
        )
        return {"response": response}
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return {"response": f"Chat service unavailable: {e}"}


# ---------------------------------------------------------------------------
# Serve built frontend (production)
# ---------------------------------------------------------------------------

DIST_DIR = BASE_DIR / "dist"
if DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="frontend")
