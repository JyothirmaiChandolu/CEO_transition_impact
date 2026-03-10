import logging
import os
from datetime import datetime
import uuid

class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[94m",   
        logging.INFO: "\033[92m",    
        logging.WARNING: "\033[93m", 
        logging.ERROR: "\033[91m",   
        logging.CRITICAL: "\033[95m" 
    }
    RESET = "\033[0m"
    def format(self, record):
        log_color = self.COLORS.get(record.levelno, self.RESET)
        log_fmt = f"{log_color}%(asctime)s - %(levelname)s - %(message)s{self.RESET}"
        formatter = logging.Formatter(log_fmt, "%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

def close_logger(logger):
    try:
        # Get the log file path from the first FileHandler (if exists)
        log_file = None
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                log_file = handler.baseFilename
                break

        if log_file and os.path.exists(log_file):
            footer_text = "\n\n===============================================\n"
            footer_text += "           PROJECT LOG END\n"
            footer_text += "===============================================\n"

            with open(log_file, "a") as f:
                f.write(footer_text)

        # Close all handlers
        for handler in logger.handlers:
            handler.close()
            logger.removeHandler(handler)

        print(f"Footer written and logger closed for: {log_file}")
    except Exception as e:
        print(f"ERROR: Failed to close logger properly: {e}")

def setup_logger(logging_folder,log_filename):
    run_datetime = datetime.now()

    # Folder structure: Year/Month/Day
    Year_stamp = run_datetime.strftime("%Y")
    Month_stamp = run_datetime.strftime("%m")
    Day_stamp = run_datetime.strftime("%d")
    Day_folder = os.path.join(logging_folder, Year_stamp, Month_stamp, Day_stamp)
    os.makedirs(Day_folder, exist_ok=True)

    unique_id = uuid.uuid4().hex[:8]  # Short 8-char UUID
    log_file = os.path.join(Day_folder, f"{log_filename.split('.')[0]}_{unique_id}.log")

    author = "Jyothirmai Chandolu"
    employee_id = "800342"
    project_name = "Impact of CEO transition on the company stock performance"
    project_description = "ETL pipeline fetching and processing Stock Exchange data."

    with open(log_file, "w") as f:
        f.write("===============================================\n")
        f.write("           PROJECT LOG\n")
        f.write("===============================================\n")
        f.write(f"Author Name        : {author}\n")
        f.write(f"Employee ID        : {employee_id}\n")
        f.write(f"Project Name       : {project_name}\n")
        f.write(f"Project Description: {project_description}\n")
        f.write(f"Log Session ID     : {unique_id}\n")
        f.write(f"Date Created       : {run_datetime.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("===============================================\n\n")

    logger = logging.getLogger(log_filename.split('.')[0])
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s",
                                       "%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorFormatter())
    logger.addHandler(console_handler)
    print(f"Log file ID  : {unique_id}")
    return logger