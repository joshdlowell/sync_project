"""
Configuration module for integrity package.

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
    """Configuration class for integrity package."""
    _instance = None
    _config = None
    _session_id = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            # Session id for grouping log updates
            cls._session_id = os.urandom(16).hex()
        return cls._instance

    # Define key requirements as class constants
    REQUIRED_KEYS = []
    SENSITIVE_KEYS = []
    NUMERIC_KEYS = ['rest_api_port']
    BOOLEAN_KEYS = ['debug']

    # Default values for configuration
    DEFAULTS = {
        'rest_api_host': 'squishy_rest_api',
        'rest_api_port': 5000,
        'root_path': '/baseline',  # REQUIRED
        'debug': False,
        'log_level': 'INFO',
        # 'max_retries': 3,
        # 'retry_delay': 5,
        # 'long_delay': 30,
        # 'max_runtime_min': 10
    }

    # Environment variable mapping
    ENV_MAPPING = {
        'rest_api_host': 'REST_API_HOST',
        'rest_api_port': 'REST_API_PORT',
        'root_path': 'BASELINE',
        'debug': 'DEBUG',
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
        self.logger = None  # Create variable to allow for initial or update config creation
        self._config: Dict[str, Any] = self.DEFAULTS.copy()

        if config_dict:
            self._config.update(config_dict)
        else:
            self._load_from_environment()

        self._validate_configuration()

        # If update didn't configure logging, then we do it here
        if not self.logger:
            log_level = self._config['log_level'] if not self._config['debug'] else 'DEBUG'
            self.logger = configure_logging(log_level)

    @property
    def rest_api_url(self) -> str:
        return f"http://{self._config.get('rest_api_host')}:{self._config.get('rest_api_port')}"

    @property
    def session_id(self) -> str:
        return self._session_id

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
        if key in ['rest_api_port', 'max_retries', 'retry_delay', 'long_delay', 'max_runtime_minutes']:
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

        self._config['log_level'] = self._config['log_level'].upper()
        if self._config['log_level'].upper() not in self.VALID_LOG_LEVELS:
            self._config['log_level'] = 'INFO'

    def update_config(self, config_dict: Dict[str, Any]) -> None:
        for key, value in config_dict.items():
            self._set(key, value)
            if key == 'debug' and value == True:
                self.logger = configure_logging('DEBUG')


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

    def _set(self, key: str, value: Any = None) -> None:
        """
        Set configuration value by key (used for running tests).

        Args:
            key: Configuration key
            value: The value to set

        Raises:
            ConfigError: If the new configuration is invalid
        """
        # Store the original value for potential rollback
        original_value = self._config.get(key)
        had_key = key in self._config

        # Set the new value
        self._config[key] = value

        try:
            # Validate the configuration with the new value
            self._validate_configuration()
        except ConfigError:
            # Revert the change if validation fails
            if had_key:
                self._config[key] = original_value
            else:
                del self._config[key]
            # Re-raise the error
            raise ConfigError(f"Invalid configuration key: {key}")

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


# Default configuration instance
config = Config()
