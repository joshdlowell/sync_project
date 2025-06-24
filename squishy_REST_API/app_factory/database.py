"""
Database module for REST API package.

This module provides a factory function to create database instances
using configuration from the config module.
"""
from typing import Optional

from squishy_REST_API.configs.config import config, logger
from squishy_REST_API.DB_connections.local_mysql import MYSQLConnection


def get_db_instance() -> Optional[MYSQLConnection]:
    """
    Create a database instance using configuration.
    
    Returns:
        HashTableDB instance or None if configuration is invalid
    """
    # Check required configuration
    required_keys = ['db_host', 'db_name', 'db_user', 'db_password']
    
    if not all(config.get(key) for key in required_keys):
        missing_keys = [key for key in required_keys if not config.get(key)]
        logger.error(f"Missing required database configuration: {', '.join(missing_keys)}")
        return None
    
    # Create database instance
    try:
        db = MYSQLConnection(
            host=config.get('db_host'),
            database=config.get('db_name'),
            user=config.get('db_user'),
            password=config.get('db_password'),
            port=config.get('db_port', 3306)
        )
        logger.info(f"Database instance created for {config.get('db_host')}/{config.get('db_name')}")
        return db
    except Exception as e:
        logger.error(f"Error creating database instance: {e}")
        return None


# Default database instance
db_instance = get_db_instance()