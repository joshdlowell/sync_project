"""
Configuration module for rest_client package.

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
    """Configuration class for rest_client package."""
    # Define required keys as class constants
    REQUIRED_KEYS = []
    SENSITIVE_KEYS = []
    NUMERIC_KEYS = ['max_retries', 'retry_delay', 'long_delay']
    BOOLEAN_KEYS = []

    # Default values for configuration
    DEFAULTS = {
        'valid_log_levels': {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'},
        'log_level': 'INFO',
        'max_retries': 3,
        'retry_delay': 5,
        'long_delay': 30,
        'hash_validator_required_keys': {'path', 'current_hash'},
        'hash_validator_keys': {'path',
                                'target_hash',
                                'current_hash',
                                'current_dtg_latest',
                                'dirs',
                                'files',
                                'links',
                                'session_id'
                                }
    }

    ENV_MAPPING = {
        'log_level': 'LOG_LEVEL'
    }

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
        if key in self.NUMERIC_KEYS:
            try:
                return int(value)
            except ValueError:
                raise ConfigError(f"Invalid integer value for {key}: {value}")
        elif key == self.BOOLEAN_KEYS:
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
        if self._config['log_level'] not in self._config.get('valid_log_levels'):
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


# Default configuration instances
config = Config()
logger = config.logger
