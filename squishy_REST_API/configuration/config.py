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
    REQUIRED_KEYS = ['db_user', 'db_password', 'secret_key', 'site_name', 'core_name']
    SENSITIVE_KEYS = ['db_password', 'secret_key']
    NUMERIC_KEYS = ['db_port', 'api_port', 'workers', 'timeout', 'keepalive', 'max_requests', 'max_requests_jitter']
    BOOLEAN_KEYS = ['debug', 'use_gunicorn']
    MAX_LENGTHS = {'site_name': 5}


    # Default generic configuration values
    DEFAULTS = {
        'valid_log_levels': {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'},
        'log_level': 'INFO',
        'site_name': None,
        'core_name': 'HQS0',
        # 'core_top_level_domain': 'home'
    }
    # REST API (flask) default configs
    DEFAULTS.update({
        'api_host': '0.0.0.0',
        'api_port': 5000,
        'debug': False,
        'secret_key': None
    })
    # Gunicorn (WSGI) default configs
    DEFAULTS.update({
        'workers': 4,
        'worker_class': 'sync',
        'timeout': 30,
        'keepalive': 2,
        'max_requests': 1000,
        'max_requests_jitter': 100,
        'accesslog': '-',
        'errorlog': '-',
        'proc_name': 'squishy_rest_api',
        'use_gunicorn': True
    })
    # Database default configs
    DEFAULTS.update({
        'db_type': 'mysql',
        'db_host': 'mysql_squishy_db',
        'db_name': 'squishy_db',
        'db_user': None,
        'db_password': None,
        'db_port': 3306,

        'pipeline_db_type': 'mysql',
        'pipeline_db_server': 'mysql_squishy_db',
        'pipeline_db_name': 'squishy_db',
        'pipeline_db_user': None,
        'pipeline_db_password': None,
        'pipeline_db_port': 1433,
    })

    # Environment variable mapping
    ENV_MAPPING = {
        'db_type': 'LOCAL_DB_TYPE',
        'db_host': 'LOCAL_DB_HOST',
        'db_name': 'LOCAL_DB_DATABASE',
        'db_user': 'LOCAL_DB_USER',
        'db_password': 'LOCAL_DB_PASSWORD',
        'db_port': 'LOCAL_DB_PORT',
        'pipeline_db_type': 'PIPELINE_DB_TYPE',
        'pipeline_db_server': 'PIPELINE_DB_SERVER',
        'pipeline_db_name': 'PIPELINE_DB_NAME',
        'pipeline_db_user': 'PIPELINE_DB_USER',
        'pipeline_db_password': 'PIPELINE_DB_PASSWORD',
        'pipeline_db_port': 'PIPELINE_DB_PORT',
        'site_name': 'SITE_NAME',
        'core_name': 'CORE_NAME',
        'api_host': 'API_HOST',
        'api_port': 'API_PORT',
        'debug': 'DEBUG',
        'secret_key': 'API_SECRET_KEY',
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

        self.database_config = {
            'remote_type': self._config['db_type'],
            'remote_config': {
                'server': self._config['db_host'],
                'host': self._config['db_host'],
                'database': self._config['db_name'],
                'user': self._config['db_user'],
                'password': self._config['db_password'],
                'port': self._config['db_port'],
            },
            'core_type': self._config['db_type'],
            'core_config': {
                'server': self._config['db_host'],
                'host': self._config['db_host'],
                'database': self._config['db_name'],
                'user': self._config['db_user'],
                'password': self._config['db_password'],
                'port': self._config['db_port'],
            },
            'pipeline_type': self._config['pipeline_db_type'],
            'pipeline_config': {
                'server': self._config['pipeline_db_server'],
                'host': self._config['pipeline_db_server'],
                'database': self._config['pipeline_db_name'] ,
                'user': self._config['pipeline_db_user'],
                'password': self._config['pipeline_db_password'],
                'port': self._config['pipeline_db_port']
            }
        }

        # Get sites' data
        self.site_name = self._config.get('site_name')
        self.site_name = self.site_name.upper() if self.site_name else None

        core_name = self._config.get('core_name')
        self.is_core = (
                core_name is not None and
                self.site_name is not None and
                self.site_name in core_name.upper()
        )


        # Update database dict based on is_core status
        if not self.is_core:
            for key in {'core_type', 'core_config', 'pipeline_type', 'pipeline_config'}:
                self.database_config[key] = None

        # Create logger
        self.logger = configure_logging(self._config.get('log_level'))

    # @property
    # def core_api_url(self) -> str:
    #     return f"https://{self._config.get('core_host')}.{self._config.get('core_top_level_domain')}"

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

        for key, max_length in self.MAX_LENGTHS.items():
            if self._config[key] and len(self._config[key]) > max_length:
                raise ConfigError(f"Configuration value for {key} must be {max_length} or fewer characters")

        self._config['site_name'] = self._config['site_name'].upper()

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
        except ConfigError as e:
            # Revert the change if validation fails
            if had_key:
                self._config[key] = original_value
            else:
                del self._config[key]
            # Re-raise the error
            raise ConfigError(e)

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
logger = config.logger
