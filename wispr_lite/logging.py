"""Logging configuration for Wispr-Lite.

Provides a centralized logger with file rotation and configurable verbosity.
Logs are stored under ~/.local/state/wispr-lite/logs.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


def get_log_dir() -> Path:
    """Get the log directory, creating it if necessary."""
    log_dir = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local' / 'state')) / 'wispr-lite' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_logger(name: str = 'wispr_lite', level: Optional[int] = None) -> logging.Logger:
    """Get or create a logger with file and console handlers.

    Args:
        name: Logger name, defaults to 'wispr_lite'
        level: Logging level; defaults to INFO

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if logger.handlers:
        if level is not None:
            logger.setLevel(level)
        return logger

    logger.setLevel(level or logging.INFO)

    # File handler with rotation
    log_file = get_log_dir() / 'wispr-lite.log'
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


def set_log_level(level: int) -> None:
    """Set the log level for all wispr_lite loggers.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
    """
    logger = logging.getLogger('wispr_lite')
    logger.setLevel(level)
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.handlers.RotatingFileHandler):
            handler.setLevel(level)
