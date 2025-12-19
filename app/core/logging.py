"""
Centralized logging configuration for the Language Learning API.

Provides:
- Console logging with colors (development)
- File logging with rotation (all environments)
- Separate error log file
- Environment-aware log levels
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Environment configuration
ENV = os.getenv('ENVIRONMENT', 'development').lower()

# Log levels based on environment
LOG_LEVELS = {
    'development': logging.DEBUG,
    'test': logging.WARNING,
    'production': logging.INFO
}

# Log directory setup
LOG_DIR = Path(__file__).parent.parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# Log format
LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(name: str = 'app') -> logging.Logger:
    """
    Set up and return a configured logger.
    
    Args:
        name: Logger name (usually __name__ of the module)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    log_level = LOG_LEVELS.get(ENV, logging.DEBUG)
    logger.setLevel(log_level)
    
    # Console handler (always enabled in development)
    if ENV == 'development':
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(ColoredFormatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = RotatingFileHandler(
        LOG_DIR / 'app.log',
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(file_handler)
    
    # Separate file handler for errors only
    error_handler = RotatingFileHandler(
        LOG_DIR / 'error.log',
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(error_handler)
    
    # Prevent logs from propagating to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Usage:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.info("This is an info message")
    
    Args:
        name: Module name (use __name__)
    
    Returns:
        Configured logger instance
    """
    return setup_logging(name or 'app')
