import pytest
import os
import mysql.connector
from mysql.connector import Error


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "mysql: mark test as requiring MySQL database"
    )
    config.addinivalue_line(
        "markers", "mssql: mark test as requiring MS SQL Server database"
    )


@pytest.fixture(scope="session")
def mysql_config():
    """Provide MySQL configuration for tests."""
    return {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'database': os.getenv('MYSQL_DATABASE', 'test_db'),
        'user': os.getenv('MYSQL_USER', 'test_user'),
        'password': os.getenv('MYSQL_PASSWORD', 'test_pass'),
        'port': int(os.getenv('MYSQL_PORT', 3306))
    }


@pytest.fixture(scope="session")
def mysql_available(mysql_config):
    """Check if MySQL is available for testing."""
    try:
        with mysql.connector.connect(**mysql_config) as conn:
            return True
    except Error:
        return False


def pytest_runtest_setup(item):
    """Skip tests based on markers and availability."""
    mysql_marker = item.get_closest_marker("mysql")
    if mysql_marker is not None:
        mysql_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'database': os.getenv('MYSQL_DATABASE', 'test_db'),
            'user': os.getenv('MYSQL_USER', 'test_user'),
            'password': os.getenv('MYSQL_PASSWORD', 'test_pass'),
            'port': int(os.getenv('MYSQL_PORT', 3306))
        }

        if not all([mysql_config['host'], mysql_config['database'],
                    mysql_config['user'], mysql_config['password']]):
            pytest.skip("MySQL configuration not provided")

        try:
            with mysql.connector.connect(**mysql_config) as conn:
                pass
        except Error as e:
            pytest.skip(f"MySQL not available: {e}")
