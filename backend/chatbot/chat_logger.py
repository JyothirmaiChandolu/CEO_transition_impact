"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Logs all chat interactions with token counts and metadata to a persistent file.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import Optional


class ChatLogger:
    """Logs chat interactions with detailed metadata."""

    def __init__(self, log_dir: str = "logs/chat"):
        """
        Initialize chat logger.

        Args:
            log_dir: Directory for storing log files
        """
        self.log_dir = Path(log_dir)
        self.session_id = str(uuid4())[:8]
        self.setup_log_file()

    def setup_log_file(self):
        """Create log directory and file with date-based structure."""
        now = datetime.now()
        # Create directory: logs/chat/YYYY/MM/DD
        log_path = self.log_dir / str(now.year) / f"{now.month:02d}" / f"{now.day:02d}"
        log_path.mkdir(parents=True, exist_ok=True)

        # Create log file: YYYY-MM-DD_UUID.log
        self.log_file = log_path / f"{now.strftime('%Y-%m-%d')}_{self.session_id}.log"

        # Initialize logger
        self.logger = logging.getLogger(f"chat_{self.session_id}")
        self.logger.setLevel(logging.INFO)

        # File handler
        handler = logging.FileHandler(self.log_file)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # Log session start
        self.logger.info(f"Session started - ID: {self.session_id}")

    def log_chat_interaction(
        self,
        question: str,
        answer: str,
        input_tokens: int,
        output_tokens: int,
        model: str = "gpt-4o-mini",
        company_context: Optional[str] = None,
        sector_context: Optional[str] = None
    ):
        """
        Log a single chat interaction.

        Args:
            question: User's question
            answer: Bot's answer
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            model: Model used
            company_context: Optional company ticker
            sector_context: Optional sector
        """
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer[:200] + "..." if len(answer) > 200 else answer,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "model": model,
            "company": company_context,
            "sector": sector_context
        }

        # Log as JSON for easy parsing
        self.logger.info(json.dumps(interaction))

    def log_error(self, error_message: str, exception: Optional[Exception] = None):
        """
        Log an error.

        Args:
            error_message: Error description
            exception: Optional exception object
        """
        if exception:
            self.logger.error(f"{error_message} | Exception: {str(exception)}")
        else:
            self.logger.error(error_message)

    def log_session_end(self, total_interactions: int, total_tokens: int):
        """
        Log session end with summary.

        Args:
            total_interactions: Number of interactions in session
            total_tokens: Total tokens used
        """
        summary = {
            "session_end": True,
            "total_interactions": total_interactions,
            "total_tokens": total_tokens,
            "timestamp": datetime.now().isoformat()
        }
        self.logger.info(json.dumps(summary))

    def get_log_file_path(self) -> str:
        """Get the full path to the log file."""
        return str(self.log_file)


if __name__ == "__main__":
    # Test chat logger
    logger = ChatLogger()

    print(f"Log file: {logger.get_log_file_path()}")

    logger.log_chat_interaction(
        question="What is a recession?",
        answer="A recession is a period of economic decline characterized by negative GDP growth...",
        input_tokens=15,
        output_tokens=85,
        model="gpt-4o-mini",
        company_context=None,
        sector_context=None
    )

    logger.log_chat_interaction(
        question="How did AAPL stock perform after Tim Cook became CEO?",
        answer="After Tim Cook became CEO on August 24, 2011, AAPL stock showed strong performance...",
        input_tokens=25,
        output_tokens=95,
        model="gpt-4o-mini",
        company_context="AAPL",
        sector_context="Technology"
    )

    logger.log_session_end(total_interactions=2, total_tokens=315)

    print("✓ Chat logs created successfully")
    print(f"  Session ID: {logger.session_id}")
    print(f"  Log file: {logger.get_log_file_path()}")
