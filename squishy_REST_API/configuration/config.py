"""
Configuration module for REST API package.

This module centralizes configuration management and provides a way to
load configuration from environment variables or configuration files.
"""
import os
from typing import Dict, Any, Optional, Union

from .logging_config import configure_logging

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass



class Config:
    """Configuration class for REST API package."""
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    # Define required keys as class constants
    REQUIRED_KEYS = ['db_user', 'db_password', 'secret_key']
    SENSITIVE_KEYS = ['db_password', 'secret_key']

    # Default values for configuration
    DEFAULTS = {
        'db_type': 'mysql',
        'db_host': 'mysql-squishy-db',
        'db_name': 'squishy_db',
        'db_user': None,
        'db_password': None,
        'db_port': 3306,
        'api_host': '0.0.0.0',
        'api_port': 5000,
        'debug': False,
        'secret_key': None,
        'log_level': 'INFO',
        'workers': 4,  # Gunicorn specific configs start here
        'worker_class': 'sync',
        'timeout': 30,
        'keepalive': 2,
        'max_requests': 1000,
        'max_requests_jitter': 100,
        'accesslog': '-',
        'errorlog': '-',
        'proc_name': 'squishy_rest_api',
        'use_gunicorn': True
    }

    # Environment variable mapping (add more gunicorn adjustments?)
    ENV_MAPPING = {
        'db_type': 'LOCAL_DB_TYPE',
        'db_host': 'LOCAL_MYSQL_HOST',
        'db_name': 'LOCAL_MYSQL_DATABASE',
        'db_user': 'LOCAL_MYSQL_USER',
        'db_password': 'LOCAL_MYSQL_PASSWORD',
        'db_port': 'LOCAL_MYSQL_PORT',
        'api_host': 'API_HOST',
        'api_port': 'API_PORT',
        'debug': 'DEBUG',
        'secret_key': 'API_SECRET_KEY',
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

        self.gunicorn_config = {
            'bind': f'{self._config["api_host"]}:{self._config["api_port"]}',
            'workers': self._config["workers"],
            'worker_class': self._config["worker_class"],
            'timeout': self._config["timeout"],
            'keepalive': self._config["keepalive"],
            'max_requests': self._config["max_requests"],
            'max_requests_jitter': self._config["max_requests_jitter"],
            'loglevel': self._config["log_level"],  # Accepts same levels as our logger debug,info,warning,error,critical
            'accesslog': self._config["accesslog"],
            'errorlog': self._config["errorlog"],
            'proc_name': self._config["proc_name"],
        }

        # Create logger
        self.logger = configure_logging(self._config.get('log_level'))

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
        elif key in ('debug', 'use_gunicorn'):
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

        self._config['log_level'] = self._config['log_level'].upper()
        if self._config['log_level'].upper() not in self.VALID_LOG_LEVELS:
            self._config['log_level'] = 'INFO'

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


# Default configuration instances
config = Config()
# Default logger instance
logger = config.logger
# class RESTConfig:
#     _instance = None
#     _config = None
#
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(RESTConfig, cls).__new__(cls)
#         return cls._instance
#
#     @property
#     def config(self) -> Config:
#         if self._config is None:
#             self._config = Config()
#         return self._config