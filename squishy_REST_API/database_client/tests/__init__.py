"""
Test package for squishy_REST_API database module.

This package contains both unit tests and integration tests for the database
client factory and implementations.

Unit tests use mocks and can run without external dependencies.
Integration tests require actual database connections.
"""

# Test configuration
import os

# Default test database configurations
DEFAULT_MYSQL_CONFIG = {
    'host': os.getenv('TEST_MYSQL_HOST', 'localhost'),
    'database': os.getenv('TEST_MYSQL_DATABASE', 'test_db'),
    'user': os.getenv('TEST_MYSQL_USER', 'test_user'),
    'password': os.getenv('TEST_MYSQL_PASSWORD', 'test_pass'),
    'port': int(os.getenv('TEST_MYSQL_PORT', 3306))
}

DEFAULT_MSSQL_CONFIG = {
    'server': os.getenv('TEST_MSSQL_SERVER', 'localhost'),
    'database': os.getenv('TEST_MSSQL_DATABASE', 'test_db'),
    'username': os.getenv('TEST_MSSQL_USERNAME', 'test_user'),
    'password': os.getenv('TEST_MSSQL_PASSWORD', 'test_pass'),
    'port': int(os.getenv('TEST_MSSQL_PORT', 1433))
}