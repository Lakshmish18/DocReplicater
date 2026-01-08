"""
Structured Logging Module
Provides consistent logging across the application.
"""

import logging
import sys
from typing import Optional
from app.config import settings


def setup_logging(level: Optional[str] = None) -> None:
    """Configure application-wide logging."""
    log_level = getattr(logging, level or settings.LOG_LEVEL)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=settings.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


# Initialize logging on module import
setup_logging()

