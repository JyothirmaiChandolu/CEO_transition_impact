import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime
from pathlib import Path

# --- Configuration ---
ROOT = Path(os.getcwd())
STOCK_DIR = ROOT / 'stock_data_raw'
DATA_CSV = ROOT / 'data.csv'
SEC_CSV = ROOT / 'sec_10k_filings_results_with_ceo_new.csv'
OUTPUT_DIR = ROOT / 'public' / 'data'
STOCKS_OUTPUT_DIR = OUTPUT_DIR / 'stocks'

# --- CEO Name Normalization ---
def normalize_ceo_name(name):
    if not name or name == 'NOT FOUND' or str(name).strip() == '':
        return None
    
    # Remove common suffixes and clean punctuation
    cleaned = str(name)
    cleaned = re.sub(r',?\s*(Jr\.?|Sr\.?|III|IV|II|Ph\.?D\.?)\s*$', '', cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace('.', '')
    cleaned = re.sub(r'\s+', ' ', cleaned).strip().lower()
    
    parts = cleaned.split(' ')
    if len(parts) < 2:
        return cleaned
    
    # Use first initial + last name for comparison (handles Steve/Steven, etc.)
    first_initial = parts[0][0]
    last_name = parts[-1]
    return f"{first_initial}_{last_name}"

def main():
    print("Starting preprocessing (Python)...")
    
    # 1. Load company list
    if not DATA_CSV.exists():
        print(f"Error: {DATA_CSV} not found")
        return
    
    company_df = pd.read_csv(DATA_CSV)
    company_map = {}
    for _, row in company_df.iterrows():
        company_map[row['Ticker']] = {
            'name': row['Company'],
            'sector': row['Sector']
        }
    print(f"Loaded {len(company_map)} companies from data.csv")

    # 2. Load SEC filings
    if not SEC_CSV.exists():
        print(f"Error: {SEC_CSV} not found")
        return
        
    sec_df = pd.read_csv(SEC_CSV)
    print(f"Loaded {len(sec_df)} SEC filings")

    # Normalize names and sort by date
    sec_df['normalized_name'] = sec_df['ceo_name'].apply(normalize_ceo_name)
    sec_df = sec_df.sort_values(['ticker', 'filing_date'])

    # 3. Detect CEO Transitions
    transitions_by_ticker = {}
    
    for ticker, group in sec_df.groupby('ticker'):
        transitions = []
        last_valid_name = None
        last_valid_filing = None
        
        for _, filing in group.iterrows():
            curr_name = filing['normalized_name']
            if not curr_name:
                continue
                
            if last_valid_name and last_valid_name != curr_name:
                # Transition detected!
                prev_date = datetime.strptime(last_valid_filing['filing_date'], '%Y-%m-%d')
                curr_date = datetime.strptime(filing['filing_date'], '%Y-%m-%d')
                
                # Calculate midpoint date
                midpoint = prev_date + (curr_date - prev_date) / 2
                trans_date = midpoint.strftime('%Y-%m-%d')
                
                transitions.append({
                    'previousCEO': last_valid_filing['ceo_name'],
                    'newCEO': filing['ceo_name'],
                    'transitionDate': trans_date,
                    'filingBefore': last_valid_filing['filing_date'],
                    'filingAfter': filing['filing_date']
                })
            
            last_valid_name = curr_name
            last_valid_filing = filing
            
        if transitions:
            transitions_by_ticker[ticker] = transitions
            company_info = company_map.get(ticker, {})
            name = company_info.get('name', ticker)
            print(f"  {ticker} ({name}): {len(transitions)} transition(s)")

    total_transitions = sum(len(t) for t in transitions_by_ticker.values())
    print(f"\nTotal: {len(transitions_by_ticker)} companies with {total_transitions} transitions")

    # 4. Read stock data (Walking the directory structure)
    print("\nReading stock data...")
    stock_data_by_ticker = {ticker: [] for ticker in company_map.keys()}
    file_count = 0
    
    if STOCK_DIR.exists():
        # Get sorted years
        years = sorted([d for d in os.listdir(STOCK_DIR) if re.match(r'^\d{4}$', d)])
        
        for year in years:
            year_path = STOCK_DIR / year
            months = sorted([d for d in os.listdir(year_path) if re.match(r'^\d{2}$', d)])
            
            for month in months:
                month_path = year_path / month
                day_files = sorted([f for f in os.listdir(month_path) if f.endswith('.json')])
                
                for day_file in day_files:
                    day = day_file.replace('.json', '')
                    date_str = f"{year}-{month}-{day}"
                    file_path = month_path / day_file
                    
                    try:
                        with open(file_path, 'r') as f:
                            day_data = json.load(f)
                            
                        for ticker in company_map.keys():
                            if ticker in day_data:
                                entry = day_data[ticker]
                                adj_close = entry.get('Adj Close')
                                if adj_close is not None:
                                    stock_data_by_ticker[ticker].append({
                                        'd': date_str,
                                        'c': round(float(adj_close), 2),
                                        'o': round(float(entry.get('Open')), 2) if entry.get('Open') is not None else None,
                                        'h': round(float(entry.get('High')), 2) if entry.get('High') is not None else None,
                                        'l': round(float(entry.get('Low')), 2) if entry.get('Low') is not None else None,
                                        'v': int(entry.get('Volume')) if entry.get('Volume') is not None else None
                                    })
                        file_count += 1
                    except Exception:
                        continue # Skip corrupt files
            print(f"  Processed {year} ({file_count} files so far)", end='\r')
    
    print(f"\nRead {file_count} stock data files")

    # 5. Generate output files
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    STOCKS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Build companies.json
    companies_list = []
    companies_with_transitions = 0
    
    # Process companies from data.csv
    for ticker, info in company_map.items():
        trans = transitions_by_ticker.get(ticker, [])
        stock_count = len(stock_data_by_ticker.get(ticker, []))
        
        if trans:
            companies_with_transitions += 1
            
        companies_list.append({
            'ticker': ticker,
            'name': info['name'],
            'sector': info['sector'],
            'hasTransitions': len(trans) > 0,
            'transitionCount': len(trans),
            'transitions': trans,
            'dataPoints': stock_count
        })

    # Add companies from SEC data not in data.csv (parity with JS)
    for ticker, trans in transitions_by_ticker.items():
        if ticker not in company_map:
            companies_with_transitions += 1
            # Get company name from first filing
            company_name = sec_df[sec_df['ticker'] == ticker].iloc[0]['company_name']
            
            companies_list.append({
                'ticker': ticker,
                'name': company_name,
                'sector': 'Unknown',
                'hasTransitions': True,
                'transitionCount': len(trans),
                'transitions': trans,
                'dataPoints': 0
            })

    companies_list.sort(key=lambda x: str(x['name']))

    output_json = {
        'companies': companies_list,
        'stats': {
            'totalCompanies': len(companies_list),
            'companiesWithTransitions': companies_with_transitions,
            'totalTransitions': total_transitions,
            'dateRange': '1996-2025',
            'stockDataFiles': file_count
        }
    }

    with open(OUTPUT_DIR / 'companies.json', 'w') as f:
        json.dump(output_json, f, indent=2)
    
    print(f"\nGenerated companies.json ({len(companies_list)} companies, {total_transitions} transitions)")

    # Generate individual stock files
    stock_files_written = 0
    for ticker, data in stock_data_by_ticker.items():
        if data:
            # Sort by date just in case
            data.sort(key=lambda x: x['d'])
            with open(STOCKS_OUTPUT_DIR / f"{ticker}.json", 'w') as f:
                json.dump({'ticker': ticker, 'data': data}, f)
            stock_files_written += 1
            
    print(f"Generated {stock_files_written} stock data files in public/data/stocks/")
    print("\nPreprocessing complete!")

if __name__ == "__main__":
    main()
