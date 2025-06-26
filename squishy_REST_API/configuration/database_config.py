"""
Database module for REST API package.

This module provides a factory function to create database instances
using configuration from the config module.
"""
from typing import Optional
from squishy_REST_API import config
from squishy_REST_API.configuration.logging_config import logger
from squishy_REST_API.storage_service import MYSQLConnection, LocalMemoryConnection, DBConnection


def get_db_instance(db_type: str=None) -> Optional[DBConnection]:
    """
    Create a database instance using configuration.
    
    Returns:
        HashTableDB instance or None if configuration is invalid
    """
    if not db_type:
        db_type = config.get('db_type', 'mysql')
    if 'mysql' == db_type.lower():
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
        except Exception as e:
            logger.error(f"Error creating database instance: {e}")
            return None
    elif 'internal' == db_type.lower():
        db = LocalMemoryConnection()
        logger.info(f"Non-persistent database instance created internally")
    else:
        logger.error(f"Error creating database of unknown type: {db_type}")
        return None

    return db
