FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy data files the API reads at startup
COPY data/ ./data/
COPY sec_ceo_data/ ./sec_ceo_data/
COPY sec_ceo_data_sp500/ ./sec_ceo_data_sp500/
COPY output.csv ./output.csv
COPY sp500_output.csv ./sp500_output.csv

EXPOSE 8000

CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
