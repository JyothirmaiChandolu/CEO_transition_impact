import pandas as pd
import yfinance as yf
import os
import json
import uuid
import boto3
from datetime import datetime
from logging_setup import setup_logger, close_logger

# S3 Configuration (can be set via environment variables)
S3_BUCKET = os.environ.get('S3_BUCKET_RAW')

def upload_to_s3(local_file, s3_key):
    if not S3_BUCKET:
        return
    s3 = boto3.client('s3')
    try:
        s3.upload_file(local_file, S3_BUCKET, s3_key)
    except Exception as e:
        print(f"Error uploading to S3: {e}")

def fetch_stock_data_raw(logger, file_path, start_date, end_date, raw_dir):
    try:
        logger.info(f"RAW MODE → Fetching historical stock data ({start_date} to {end_date})")
        
        # Load tickers from data.csv
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return
            
        df = pd.read_csv(file_path)
        df = df.head(100) # Only first 100 as per original script
        df = df[df["Ticker"].notna() & (df["Ticker"] != "")]
        df["Ticker"] = df["Ticker"].str.replace(".", "-", regex=False)
        tickers = df["Ticker"].tolist()
        
        logger.info(f"Fetching data for {len(tickers)} tickers")

        # Download data
        data = yf.download(
            tickers=tickers,
            start=start_date,
            end=end_date + pd.Timedelta(days=1),
            group_by="ticker",
            threads=True,
            auto_adjust=False,
            progress=False
        )

        if data is None or data.empty:
            logger.warning("Download returned empty.")
            return

        data.index = pd.to_datetime(data.index)
        tickers_without_data = []
        
        # Determine tickers with no data
        for ticker in tickers:
            try:
                t_data = data if len(tickers) == 1 else data[ticker]
                if t_data.empty or t_data.isna().all().all():
                    tickers_without_data.append(ticker)
            except Exception:
                tickers_without_data.append(ticker)

        # Save files
        saved_days = 0
        for single_date in data.index:
            year = str(single_date.year)
            month = f"{single_date.month:02d}"
            day = f"{single_date.day:02d}"
            
            # Local dir structure
            month_dir = os.path.join(raw_dir, year, month)
            os.makedirs(month_dir, exist_ok=True)
            
            day_json = {}
            for ticker in tickers:
                try:
                    if ticker in tickers_without_data:
                        day_json[ticker] = {"Open": None, "High": None, "Low": None, "Close": None, "Adj Close": None, "Volume": None}
                    else:
                        row = data.loc[single_date] if len(tickers) == 1 else data[ticker].loc[single_date]
                        row_dict = row.to_dict()
                        day_json[ticker] = {k: (None if pd.isna(v) else float(v)) for k, v in row_dict.items()}
                except Exception:
                    day_json[ticker] = {"Open": None, "High": None, "Low": None, "Close": None, "Adj Close": None, "Volume": None}
            
            # Save local
            out_file = os.path.join(month_dir, f"{day}.json")
            with open(out_file, "w") as f:
                json.dump(day_json, f, indent=2)
            
            # Upload to S3 if configured
            if S3_BUCKET:
                s_key = f"stock_data_raw/{year}/{month}/{day}.json"
                upload_to_s3(out_file, s_key)
                
            saved_days += 1
            
        logger.info(f"Completed! Total days saved: {saved_days}")
        
    except Exception as e:
        logger.exception(f"Error in fetch_stock_data_raw: {e}")
        raise

def lambda_handler(event, context):
    """Entry point for AWS Lambda"""
    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Defaults for daily run
    file_path = "/tmp/data.csv"
    # In Lambda, we'd typically download data.csv from S3 first
    s3 = boto3.client('s3')
    try:
        s3.download_file(S3_BUCKET, 'data.csv', file_path)
    except Exception as e:
        logger.error(f"Could not download data.csv from S3: {e}")
        # Fallback to local if it exists in the bundle
        if os.path.exists('data.csv'):
            file_path = 'data.csv'
        else:
            return {"status": "error", "message": "data.csv missing"}

    # Run for the last 7 days to ensure no gaps (yfinance can be flaky)
    end_date = pd.Timestamp.now()
    start_date = end_date - pd.Timedelta(days=7)
    
    raw_dir = "/tmp/stock_data_raw"
    os.makedirs(raw_dir, exist_ok=True)
    
    fetch_stock_data_raw(logger, file_path, start_date, end_date, raw_dir)
    
    return {"status": "success", "days_processed": 7}

if __name__ == "__main__":
    # Local execution
    logging_folder = "log_files"
    unique_id = uuid.uuid4().hex[:8]
    log_filename = f"extract_{unique_id}.log"
    logger = setup_logger(logging_folder, log_filename)
    
    try:
        file_path = "data.csv" 
        # For full history, use these:
        start_date = pd.to_datetime("1996-01-01") 
        end_date = pd.to_datetime("2025-12-31")
        
        # For quick test, use last 30 days:
        # end_date = pd.Timestamp.now()
        # start_date = end_date - pd.Timedelta(days=30)
        
        raw_dir = "stock_data_raw" 
        fetch_stock_data_raw(logger, file_path, start_date, end_date, raw_dir)
    finally:
        close_logger(logger)