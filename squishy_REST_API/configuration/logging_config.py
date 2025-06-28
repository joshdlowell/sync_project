"""
Logging configuration for REST API package.

This module provides a centralized logging configuration for the application.
"""
import logging
import sys
from typing import Optional

# from squishy_REST_API import config


def configure_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        log_level: Optional log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  If not provided, it will be read from the LOG_LEVEL environment variable
                  or default to INFO.

    Returns:
        Configured logger instance
    """
    # Get log level from environment variable if not provided
    if log_level is None:
        log_level = 'INFO'

    # Create logger
    logger = logging.getLogger('rest_api')

    # Set log level
    numeric_level = getattr(logging, log_level, None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    logger.setLevel(numeric_level)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    return logger
