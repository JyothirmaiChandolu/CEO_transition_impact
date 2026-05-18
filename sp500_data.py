#!/usr/bin/env python3
"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Retrieves current S&P 500 Index constituents from iShares IVV ETF holdings and outputs tickers to a timestamped CSV file.
"""
import requests
import pandas as pd
from io import StringIO
from datetime import datetime
import re


def check_data_freshness():
    print("Checking holdings date...")
    page_url = "https://www.ishares.com/us/products/239726/ishares-core-sp-500-etf"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(page_url, headers=headers, timeout=10)
        if response.status_code == 200:
            pattern = r'as of\s+([A-Za-z]{3}\s+\d{1,2},\s+\d{4})'
            match = re.search(pattern, response.text, re.IGNORECASE)
            if match:
                holdings_date = match.group(1)
                print(f"Holdings as of: {holdings_date}")
                return holdings_date
            else:
                print("Couldn't find holdings date")
                return None
    except Exception as e:
        print(f"Failed to check holdings date: {e}")
        return None


def get_sp500_tickers():
    # S&P 500 tickers from iShares IVV ETF holdings
    url = "https://www.ishares.com/us/products/239726/ishares-core-sp-500-etf/1467271812596.ajax"

    params = {
        'fileType': 'csv',
        'fileName': 'IVV_holdings',
        'dataType': 'fund'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    print("Downloading...")
    response = requests.get(url, params=params, headers=headers)

    if response.status_code != 200:
        print(f"Failed: {response.status_code}")
        return None

    # top 9 rows ignored based on iShares CSV format
    df = pd.read_csv(StringIO(response.text), skiprows=9)

    if 'Asset Class' in df.columns:
        df = df[df['Asset Class'] == 'Equity']

    tickers = df['Ticker'].dropna().str.strip().str.upper()

    valid_tickers = []
    for ticker in tickers:
        if 1 <= len(ticker) <= 5 and ticker.replace('-', '').replace('.', '').isalnum():
            valid_tickers.append(ticker)

    final_tickers = sorted(list(set(valid_tickers)))
    print(f"Found {len(final_tickers)} tickers")

    if len(final_tickers) < 490:
        print(f"Warning: only {len(final_tickers)} tickers found (expected ~500)")

    return final_tickers


def save_tickers(tickers, update_time=None):
    if update_time:
        try:
            update_date = datetime.strptime(update_time, '%b %d, %Y')
            date_str = update_date.strftime('%Y%m%d')
        except Exception:
            date_str = datetime.now().strftime('%Y%m%d')
    else:
        date_str = datetime.now().strftime('%Y%m%d')

    filename = f"sp500_tickers_{date_str}.csv"

    df = pd.DataFrame({'ticker': tickers})
    df.to_csv(filename, index=False)

    print(f"Saved {len(tickers)} tickers to {filename}")
    return filename


if __name__ == "__main__":
    holdings_date = check_data_freshness()

    tickers = get_sp500_tickers()
    if tickers:
        filename = save_tickers(tickers, holdings_date)
    else:
        print("Failed to get tickers")
