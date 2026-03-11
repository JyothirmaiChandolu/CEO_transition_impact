"""
Daily Data Update Scheduler
Runs the data pipeline on a daily schedule
"""
import schedule
import time
import logging
import json
from pathlib import Path
from datetime import datetime
from pipeline import DataPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataScheduler:
    """Schedules and runs data pipeline updates"""

    def __init__(self, data_dir: Path = None):
        """Initialize scheduler"""
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / 'data'

        self.data_dir = Path(data_dir)
        self.pipeline = DataPipeline(data_dir)
        self.last_run = None
        self.last_status = None

    def load_tickers(self) -> dict:
        """Load tickers and transition dates from config"""
        config_file = Path(__file__).parent.parent / 'data' / 'companies.json'

        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    # Extract tickers and transitions
                    tickers = {}
                    for company in data.get('companies', []):
                        ticker = company.get('ticker')
                        transitions = company.get('transitions', [])
                        if ticker and transitions:
                            # Get the most recent transition
                            latest_transition = max(
                                transitions,
                                key=lambda t: t.get('transitionDate', ''),
                                default=None
                            )
                            if latest_transition:
                                tickers[ticker] = latest_transition.get('transitionDate')
                        elif ticker:
                            tickers[ticker] = None

                    return tickers
            except Exception as e:
                logger.error(f"Error loading config: {e}")

        # Fallback: use hardcoded list (update with your S&P 100 companies)
        return {
            'AAPL': None, 'MSFT': None, 'GOOGL': None, 'AMZN': None,
            'NVDA': None, 'TSLA': None, 'META': None, 'BRK.B': None,
            'JNJ': None, 'V': None, 'WMT': None, 'JPM': None,
            # Add more as needed
        }

    def run_daily_update(self):
        """Run the daily data update"""
        logger.info("=" * 60)
        logger.info("Starting daily data update...")
        logger.info("=" * 60)

        start_time = datetime.now()

        try:
            tickers = self.load_tickers()
            logger.info(f"Processing {len(tickers)} stocks...")

            # Run pipeline
            results = self.pipeline.process_multiple_stocks(
                list(tickers.keys()),
                transitions=tickers
            )

            # Count results
            successful = sum(1 for r in results if r.get('status') == 'success')
            failed = len(results) - successful

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.last_run = start_time
            self.last_status = {
                'status': 'completed',
                'successful': successful,
                'failed': failed,
                'total': len(results),
                'duration_seconds': duration,
                'timestamp': end_time.isoformat()
            }

            logger.info("=" * 60)
            logger.info(f"Daily update complete!")
            logger.info(f"Successful: {successful}/{len(results)}")
            logger.info(f"Failed: {failed}/{len(results)}")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Error during daily update: {e}", exc_info=True)
            self.last_status = {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def schedule_jobs(self, time_of_day: str = "09:00"):
        """
        Schedule daily jobs

        Args:
            time_of_day: Time to run (HH:MM format, default: 09:00)
        """
        schedule.every().day.at(time_of_day).do(self.run_daily_update)
        logger.info(f"Scheduled daily update at {time_of_day}")

    def start(self, time_of_day: str = "09:00"):
        """Start the scheduler"""
        logger.info("Starting data scheduler...")
        self.schedule_jobs(time_of_day)

        # Run once immediately on startup (optional)
        # self.run_daily_update()

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")

    def get_status(self):
        """Get scheduler status"""
        return {
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'last_status': self.last_status,
            'next_run': schedule.next_run().isoformat() if schedule.next_run() else None
        }


if __name__ == "__main__":
    scheduler = DataScheduler()

    # Option 1: Run once
    scheduler.run_daily_update()

    # Option 2: Run on schedule (uncomment to use)
    # scheduler.start(time_of_day="09:00")
