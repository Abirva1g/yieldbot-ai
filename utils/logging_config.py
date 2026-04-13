"""Logging configuration for YieldBot AI."""
import logging
import sys
from typing import Dict, Any
from contextlib import contextmanager


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(self, include_extras: bool = True):
        super().__init__()
        self.include_extras = include_extras
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if record.exc_info and self.include_extras:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add custom fields
        for key, value in record.__dict__.items():
            if key not in ["msg", "args", "levelname", "levelno", "pathname", 
                          "filename", "module", "lineno", "funcName", "created",
                          "msecs", "relativeCreated", "thread", "threadName",
                          "processName", "process", "message", "exc_info",
                          "exc_text", "stack_info"]:
                log_data[key] = value
        
        import json
        return json.dumps(log_data)


def setup_logger(name: str = "YieldBot") -> logging.Logger:
    """Set up logger with JSON formatting."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Console handler with simple format for development
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Use simple format for console, JSON for file handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


# Global logger instance
logger = setup_logger()


@contextmanager
def temporary_log_fields(logger_instance: logging.Logger, **fields):
    """Context manager to temporarily add fields to log records."""
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        for key, value in fields.items():
            setattr(record, key, value)
        return record
    
    logging.setLogRecordFactory(record_factory)
    try:
        yield
    finally:
        logging.setLogRecordFactory(old_factory)
