"""Logging configuration for the application."""

import logging
import sys
from datetime import datetime
from typing import Optional
import json
from logging.handlers import RotatingFileHandler

from app.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


def setup_logging() -> None:
    """
    Configure logging for the application.
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if settings.LOG_FORMAT == "json":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
    
    root_logger.addHandler(console_handler)
    
    # File handler (if configured)
    if settings.LOG_FILE:
        try:
            file_handler = RotatingFileHandler(
                settings.LOG_FILE,
                maxBytes=10_485_760,  # 10MB
                backupCount=5,
            )
            if settings.LOG_FORMAT == "json":
                file_handler.setFormatter(JSONFormatter())
            else:
                file_handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S"
                    )
                )
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Failed to create log file handler: {e}")
    
    # Set logging levels for third-party libraries
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerContext:
    """
    Context manager for adding extra fields to logs.
    """
    
    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.extra = kwargs
        self._old_factory = None
    
    def __enter__(self):
        """Add extra fields to log records."""
        self._old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self._old_factory(*args, **kwargs)
            for key, value in self.extra.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, *args):
        """Restore original log record factory."""
        logging.setLogRecordFactory(self._old_factory)