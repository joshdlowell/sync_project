"""
Logging configuration for the database_client package.

This module provides a centralized logging configuration for this package.
"""
import logging
import sys
from typing import Optional

VALID_LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

def configure_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for the package.

    Args:
        log_level: Optional log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  If not provided, it will be read from the LOG_LEVEL environment variable
                  or default to INFO.

    Returns:
        Configured logger instance
    """
    # If not provided, set to default
    if log_level is None:
        log_level = 'INFO'

    # Create logger
    logger = logging.getLogger('database_client')

    # Set the log level
    numeric_level = getattr(logging, log_level, None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    logger.setLevel(numeric_level)

    # Only add handler if none exist (prevents duplicates)
    # if not logger.handlers:
    #     # Create a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Create formatter
    formatter = logging.Formatter(
        '[%(asctime)s] [%(process)d] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    return logger