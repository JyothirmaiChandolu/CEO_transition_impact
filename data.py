#!/usr/bin/env python3
"""
- Objective: Retrieve and print the current list of Russell 2000 Index's stock tickers (stock symboles, like 'AAPL' or 'TSLA', e.g.).
- Techniques: Use Python libraries like BeautifulSoup or Scrapy for web scraping, or explore available APIs.
- Deliverable: A well-commented Python script (.py file) that outputs the live-updated Russell 2000 Index's stock ticker list.

Retrieve current Russell 2000 Index constituents from iShares IWM ETF holdings.
Outputs list of stock tickers to timestamped files.

Environment:
Python 3.12
Requirements: requests, pandas

Usage: python russell2000_tickers.py

Output: ticker list in CSV file 
russell2000_tickers_YYYYMMDD.csv where YYYYMMDD is the date iShares updated the holdings.
"""
import requests
import pandas as pd
from io import StringIO
from datetime import datetime
import re

def check_data_freshness():
    print("Checking holdings date...")
    page_url = "https://www.ishares.com/us/products/239710/ishares-russell-2000-etf"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(page_url, headers=headers, timeout=10)
        if response.status_code == 200:
            # match "as of MMM DD, YYYY" under holding tab
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

def get_russell_2000_tickers():
    # Russell 2000 tickers from iShares IWM ETF holdings
    url = "https://www.ishares.com/us/products/239710/ishares-russell-2000-etf/1467271812596.ajax"
    
    params = {
        'fileType': 'csv',
        'fileName': 'IWM_holdings',
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
    
    # filter to valid tickers only
    valid_tickers = []
    for ticker in tickers:
        if 1 <= len(ticker) <= 5 and ticker.replace('-', '').replace('.', '').isalnum():
            valid_tickers.append(ticker)
    
    final_tickers = sorted(list(set(valid_tickers)))
    print(f"Find {len(final_tickers)} tickers")
    
    if len(final_tickers) < 1800:
        print(f"Warning: only {len(final_tickers)} tickers found")
    
    return final_tickers

def save_tickers(tickers, update_time=None):
    # convert update date to filename format
    if update_time:
        try:
            # parse "Sep 05, 2025" to "20250905"
            update_date = datetime.strptime(update_time, '%b %d, %Y')
            date_str = update_date.strftime('%Y%m%d')
        except:
            date_str = datetime.now().strftime('%Y%m%d')
    else:
        date_str = datetime.now().strftime('%Y%m%d')
    
    filename = f"russell2000_tickers_{date_str}.csv"
    
    # just tickers in CSV
    df = pd.DataFrame({'ticker': tickers})
    df.to_csv(filename, index=False)
    
    print(f"Saved {len(tickers)} tickers to {filename}")
    return filename

if __name__ == "__main__":
    holdings_date = check_data_freshness()
    
    tickers = get_russell_2000_tickers()
    if tickers:
        filename = save_tickers(tickers, holdings_date)
    else:
        print("Failed to get tickers")