"""
Logging configuration module for the application.

This module provides a centralized logging setup with support for both console and file handlers.
It implements a singleton pattern for loggers and provides context manager support for
temporary log level changes.

Example:
    >>> from src.common.logging import get_logger
    >>> logger = get_logger('my_module')
    >>> logger.info('Hello, world!')
    
    >>> with temporary_log_level('DEBUG'):
    >>>     logger.debug('Temporary debug message')
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Generator
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from .config import config

# Singleton registry for loggers
_loggers: Dict[str, logging.Logger] = {}

def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger instance.
    
    This function implements a singleton pattern for loggers. If a logger with the given
    name already exists, it returns the existing instance. Otherwise, it creates a new
    logger with the default configuration.
    
    Args:
        name: The name of the logger.
        
    Returns:
        A configured logger instance.
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = setup_logger(name)
    _loggers[name] = logger
    return logger

def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up a logger with console and file handlers.
    
    Args:
        name: Logger name
        log_file: Optional log file path
        level: Logging level (default: INFO)
        max_bytes: Maximum size of log file before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
    
    Returns:
        Configured logger instance
        
    Raises:
        ValueError: If the log level is invalid
        OSError: If there are file system related errors
    """
    if not isinstance(level, int) or level not in {
        logging.DEBUG, logging.INFO, logging.WARNING,
        logging.ERROR, logging.CRITICAL
    }:
        raise ValueError(f"Invalid log level: {level}")
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if log_file is specified
    if log_file:
        try:
            log_path = Path(config.logging.log_dir) / log_file
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError as e:
            logger.error(f"Failed to setup file handler: {e}")
            # Continue with console handler only
    
    return logger

@contextmanager
def temporary_log_level(level: int) -> Generator[None, None, None]:
    """
    Context manager for temporarily changing the log level.
    
    Args:
        level: The temporary log level to use
        
    Example:
        >>> with temporary_log_level(logging.DEBUG):
        >>>     logger.debug('This will be logged')
    """
    root_logger = logging.getLogger()
    original_level = root_logger.level
    root_logger.setLevel(level)
    try:
        yield
    finally:
        root_logger.setLevel(original_level)

# Create default loggers
trading_logger = get_logger('trading')
api_logger = get_logger('api')
data_logger = get_logger('data') 