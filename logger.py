import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import WRITE_LOGS


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "scraper.log"


class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[35m",
    }

    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        message = super().format(record)
        return f"{color}{message}{self.RESET}"


def setup_logger(write_logs: bool = False) -> logging.Logger:
    logger = logging.getLogger("scraper")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # Prevent duplicate handlers if setup_logger() is called multiple times
    logger.handlers.clear()

    # Console handler — always enabled
    console_handler = logging.StreamHandler(sys.stdout)

    console_handler.setFormatter(
        ColoredFormatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
    )

    logger.addHandler(console_handler)

    # File handler — only when requested
    if write_logs:
        LOG_DIR.mkdir(exist_ok=True)

        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )

        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

        logger.addHandler(file_handler)

    return logger


logger = setup_logger(write_logs=WRITE_LOGS)