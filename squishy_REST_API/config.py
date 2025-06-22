"""
Configuration module for REST API package.

This module centralizes configuration management and provides a way to
load configuration from environment variables or configuration files.
"""
import os
from typing import Dict, Any, Optional


class Config:
    """Configuration class for REST API package."""

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration with optional dictionary.
        
        Args:
            config_dict: Optional dictionary with configuration values
        """
        self._config = config_dict or {}
        
        # Load environment variables if not provided in config_dict
        if not config_dict:
            self._load_from_environment()

    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        # Database configuration
        self._config['db_host'] = os.environ.get('LOCAL_MYSQL_NAME', 'mysql-squishy-db')
        self._config['db_name'] = os.environ.get('LOCAL_DATABASE', 'squishy_db')
        self._config['db_user'] = os.environ.get('LOCAL_USER', 'app_user')
        self._config['db_password'] = os.environ.get('LOCAL_PASSWORD', '')
        self._config['db_port'] = int(os.environ.get('LOCAL_MYSQL_PORT', '3306'))
        
        # API configuration
        self._config['api_host'] = os.environ.get('API_HOST', '0.0.0.0')
        self._config['api_port'] = int(os.environ.get('API_PORT', '5000'))
        self._config['debug'] = os.environ.get('DEBUG', 'False').lower() == 'true'
        self._config['secret_key'] = os.environ.get('secret_key', None)

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
    
    def validate_required_keys(self, required_keys: list) -> bool:
        """
        Validate that all required keys are present in configuration.
        
        Args:
            required_keys: List of required configuration keys
            
        Returns:
            True if all required keys are present, False otherwise
        """
        for key in required_keys:
            if key not in self._config or not self._config[key]:
                return False
        return True


# Default configuration instance
config = Config()