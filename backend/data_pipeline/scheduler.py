"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Schedules daily stock data fetches and runs the full pipeline for all Russell 2000 companies.
"""
import sys
import time
import logging
import schedule
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from fetch import fetch_current, fetch_single_date, fetch_date_range, DATA_DIR, TICKERS_CSV
from pipeline import DataPipeline

LOG_FILE = Path(__file__).parent.parent / "scheduler.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class DataScheduler:
    """Schedules daily fetch + pipeline runs for all 1917 Russell 2000 companies."""

    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = Path(data_dir)
        self.last_run = None
        self.last_status = None

    # ------------------------------------------------------------------
    # Core run methods
    # ------------------------------------------------------------------

    def run_daily_update(self):
        """Fetch today's data for all 1917 tickers and run the full pipeline."""
        today = datetime.now().strftime("%Y-%m-%d")
        logger.info("=" * 60)
        logger.info(f"Daily update started — date: {today}")
        logger.info("=" * 60)
        start = datetime.now()

        try:
            # Step 1: Fetch today's stock data for all 1917 companies
            logger.info("Step 1: Fetching today's stock data...")
            fetch_current(output_dir=DATA_DIR, csv_path=TICKERS_CSV)

            # Step 2: Run full pipeline (validate + KPIs) over all raw data
            logger.info("Step 2: Running pipeline for all Russell 2000 companies...")
            pipeline = DataPipeline(self.data_dir)
            pipeline.process_all_russell2000()

            duration = (datetime.now() - start).total_seconds()
            self.last_run = start
            self.last_status = {
                "status": "completed",
                "date": today,
                "duration_seconds": round(duration, 2),
                "timestamp": datetime.now().isoformat(),
            }
            logger.info(f"Daily update complete in {duration:.0f}s")

        except Exception as e:
            logger.error(f"Daily update failed: {e}", exc_info=True)
            self.last_status = {
                "status": "failed",
                "date": today,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def run_for_date(self, target_date: str):
        """
        Fetch data for a specific date and run the full pipeline.

        Args:
            target_date: YYYY-MM-DD
        """
        try:
            datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid date format: {target_date}. Use YYYY-MM-DD")
            return

        logger.info("=" * 60)
        logger.info(f"Single-date run — date: {target_date}")
        logger.info("=" * 60)
        start = datetime.now()

        try:
            logger.info("Step 1: Fetching stock data...")
            fetch_single_date(target_date, output_dir=DATA_DIR, csv_path=TICKERS_CSV)

            logger.info("Step 2: Running pipeline...")
            pipeline = DataPipeline(self.data_dir)
            pipeline.process_all_russell2000()

            duration = (datetime.now() - start).total_seconds()
            self.last_run = start
            self.last_status = {
                "status": "completed",
                "date": target_date,
                "duration_seconds": round(duration, 2),
                "timestamp": datetime.now().isoformat(),
            }
            logger.info(f"Single-date run complete in {duration:.0f}s")

        except Exception as e:
            logger.error(f"Single-date run failed: {e}", exc_info=True)
            self.last_status = {
                "status": "failed",
                "date": target_date,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def run_for_date_range(self, start_date: str, end_date: str):
        """
        Fetch data for a date range and run the full pipeline.

        Args:
            start_date: YYYY-MM-DD (inclusive)
            end_date:   YYYY-MM-DD (inclusive)
        """
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError as e:
            logger.error(f"Invalid date format: {e}. Use YYYY-MM-DD")
            return

        logger.info("=" * 60)
        logger.info(f"Date-range run — {start_date} to {end_date}")
        logger.info("=" * 60)
        start = datetime.now()

        try:
            logger.info("Step 1: Fetching stock data...")
            fetch_date_range(start_date, end_date, output_dir=DATA_DIR, csv_path=TICKERS_CSV)

            logger.info("Step 2: Running pipeline...")
            pipeline = DataPipeline(self.data_dir)
            pipeline.process_all_russell2000()

            duration = (datetime.now() - start).total_seconds()
            self.last_run = start
            self.last_status = {
                "status": "completed",
                "start_date": start_date,
                "end_date": end_date,
                "duration_seconds": round(duration, 2),
                "timestamp": datetime.now().isoformat(),
            }
            logger.info(f"Date-range run complete in {duration:.0f}s")

        except Exception as e:
            logger.error(f"Date-range run failed: {e}", exc_info=True)
            self.last_status = {
                "status": "failed",
                "start_date": start_date,
                "end_date": end_date,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    # ------------------------------------------------------------------
    # Scheduler control
    # ------------------------------------------------------------------

    def schedule_jobs(self, time_of_day: str = "18:00"):
        """
        Schedule the daily update job.

        Args:
            time_of_day: HH:MM (24h) — default 18:00, after market close
        """
        schedule.every().day.at(time_of_day).do(self.run_daily_update)
        logger.info(f"Scheduled daily update at {time_of_day}")

    def start(self, time_of_day: str = "18:00"):
        """Start the scheduler loop. Runs indefinitely until Ctrl+C."""
        logger.info("Scheduler starting...")
        self.schedule_jobs(time_of_day)
        logger.info(f"Next run: {schedule.next_run()}")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped.")

    def get_status(self):
        """Return last run status and next scheduled run."""
        return {
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_status": self.last_status,
            "next_run": schedule.next_run().isoformat() if schedule.next_run() else None,
        }


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    scheduler = DataScheduler()

    if len(sys.argv) > 2:
        # Date range:   python scheduler.py 2024-01-01 2024-12-31
        scheduler.run_for_date_range(sys.argv[1], sys.argv[2])

    elif len(sys.argv) > 1:
        if sys.argv[1] == "--schedule":
            # Run on daily schedule:  python scheduler.py --schedule
            # Optional time arg:      python scheduler.py --schedule 16:30
            time_arg = sys.argv[2] if len(sys.argv) > 2 else "18:00"
            scheduler.start(time_of_day=time_arg)
        else:
            # Single date:  python scheduler.py 2024-06-15
            scheduler.run_for_date(sys.argv[1])

    else:
        # No args: fetch today and run pipeline
        scheduler.run_daily_update()
