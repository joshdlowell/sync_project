"""
Configuration module for REST API package.

This module centralizes configuration management and provides a way to
load configuration from environment variables or configuration files.
"""
import os
import sys
import logging
from typing import Dict, Any, Optional, Union


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


class Config:
    """Configuration class for REST API package."""

    # Define required keys as class constants
    REQUIRED_KEYS = ['db_user', 'db_password', 'secret_key']
    SENSITIVE_KEYS = ['db_password', 'secret_key']

    # Default values for configuration
    DEFAULTS = {
        'db_host': 'mysql-squishy-db',
        'db_name': 'squishy_db',
        'db_user': None,
        'db_password': None,
        'db_port': 3306,
        'api_host': '0.0.0.0',
        'api_port': 5000,
        'debug': False,
        'secret_key': None,
        'log_level': 'INFO'
    }

    # Environment variable mapping
    ENV_MAPPING = {
        'db_host': 'LOCAL_MYSQL_NAME',
        'db_name': 'LOCAL_DATABASE',
        'db_user': 'LOCAL_USER',
        'db_password': 'LOCAL_PASSWORD',
        'db_port': 'LOCAL_MYSQL_PORT',
        'api_host': 'API_HOST',
        'api_port': 'API_PORT',
        'debug': 'DEBUG',
        'secret_key': 'SECRET_KEY',
        'log_level': 'LOG_LEVEL'
    }

    # Valid log levels
    VALID_LOG_LEVELS = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration with optional dictionary.

        Args:
            config_dict: Optional dictionary with configuration values

        Raises:
            ConfigError: If required configuration is missing
        """
        self._config: Dict[str, Any] = self.DEFAULTS.copy()

        if config_dict:
            self._config.update(config_dict)
        else:
            self._load_from_environment()

        self._validate_configuration()

    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        for config_key, env_key in self.ENV_MAPPING.items():
            env_value = os.environ.get(env_key)
            if env_value is not None:
                self._config[config_key] = self._convert_value(config_key, env_value)

    def _convert_value(self, key: str, value: str) -> Union[int, bool, str]:
        """
        Convert string values to appropriate types.

        Args:
            key: Configuration key
            value: String value to convert

        Returns:
            Converted value

        Raises:
            ConfigError: If conversion fails
        """
        if key in ('db_port', 'api_port'):
            try:
                return int(value)
            except ValueError:
                raise ConfigError(f"Invalid integer value for {key}: {value}")
        elif key == 'debug':
            return value.lower() in ('true', '1', 'yes', 'on')
        return value

    def _validate_configuration(self) -> None:
        """
        Validate that all required configuration is present.

        Raises:
            ConfigError: If required configuration is missing
        """
        missing_keys = [
            key for key in self.REQUIRED_KEYS
            if key not in self._config or self._config[key] is None
        ]

        if missing_keys:
            raise ConfigError(f"Missing required configuration keys: {', '.join(missing_keys)}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key: Configuration key
            default: Default value if key is not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def get_database_url(self) -> str:
        """
        Get database connection URL.

        Returns:
            Database connection URL
        """
        return (
            f"mysql://{self._config['db_user']}:{self._config['db_password']}"
            f"@{self._config['db_host']}:{self._config['db_port']}/{self._config['db_name']}"
        )

    def is_debug_mode(self) -> bool:
        """
        Check if debug mode is enabled.

        Returns:
            True if debug mode is enabled, False otherwise
        """
        return bool(self._config.get('debug', False))

    def configure_logging(self, logger_name: str = None) -> logging.Logger:
        """
        Configure logging for the application.

        Returns:
            Configured logger instance
        """
        if not logger_name:
            logger_name = 'rest_api'

        log_level = str(self._config.get('log_level', 'INFO')).upper()

        # Validate log level
        if log_level not in self.VALID_LOG_LEVELS:
            log_level = 'INFO'

        # Create logger
        logger = logging.getLogger(logger_name)

        # Avoid adding multiple handlers if logger is already configured
        if logger.handlers:
            return logger

        # Set log level
        numeric_level = getattr(logging, log_level)
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

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access to configuration."""
        return self._config[key]

    def __contains__(self, key: str) -> bool:
        """Allow 'in' operator for checking key existence."""
        return key in self._config

    def __repr__(self) -> str:
        """String representation of config (without sensitive data)."""
        safe_config = {k: v for k, v in self._config.items()
                      if k not in ('db_password', 'secret_key')}
        return f"Config({safe_config})"


def create_config(config_dict: Optional[Dict[str, Any]] = None) -> Config:
    """
    Create a configuration instance.

    Args:
        config_dict: Optional dictionary with configuration values

    Returns:
        Configuration instance
    """
    return Config(config_dict)


# Default configuration instance
config = Config()
logger = config.configure_logging()