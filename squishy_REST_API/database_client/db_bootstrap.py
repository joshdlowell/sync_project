"""
Database module for REST API package.

This module provides a factory function to create database instances
using configuration from the config module.
"""
from typing import Optional
from squishy_REST_API import config, logger
from .local_DB_interface import DBConnection
from .local_mysql import MYSQLConnection
from .local_memory import LocalMemoryConnection
from .core_site_DB_interface import CoreDBConnection
from .core_site_mysql import CoreMYSQLConnection


class DBClient:

    @property
    def database_client(self, db_type: str = None) -> DBConnection:
        return self.create_db_service(db_type=db_type)

    def create_db_service(self, db_type) -> DBConnection:
        """
        Create a database instance using configuration.

        Returns:
            DBConnection instance

        Raises:
            ValueError: When database configuration values are invalid or missing.
            ConnectionError: When unable to establish database connection.
            Exception: For any other unexpected errors during database creation.
        """
        try:
            if not db_type:
                db_type = config.get('db_type', 'mysql')

            if 'mysql' == db_type.lower():
                # Check required configuration
                required_keys = ['db_host', 'db_name', 'db_user', 'db_password']

                if not all(config.get(key) for key in required_keys):
                    missing_keys = [key for key in required_keys if not config.get(key)]
                    logger.error(f"Missing required database configuration: {', '.join(missing_keys)}")
                    raise ValueError

                # Create database instance
                db = MYSQLConnection(
                    host=config.get('db_host'),
                    database=config.get('db_name'),
                    user=config.get('db_user'),
                    password=config.get('db_password'),
                    port=config.get('db_port', 3306)
                )
                logger.info(f"Database instance created for {config.get('db_host')}/{config.get('db_name')}")

            elif 'internal' == db_type.lower():
                db = LocalMemoryConnection()
                logger.info(f"Non-persistent database instance created internally")

            else:
                logger.error(f"Error creating database of unknown type: {db_type}")
                raise ValueError

            return db

        except ValueError as e:
            logger.error(f"Unable to bootstrap database_client: {e}")
            exit(78)  # Configuration error
        except ConnectionError as e:
            logger.error(f"Unable to establish database connection: {e}")
            exit(78)  # Configuration error
        except Exception as e:
            logger.error(f"Error creating database instance: {e}")
            exit(78)  # Configuration error

class CoreDBClient:

    @property
    def database_client(self, db_type: str = None) -> CoreDBConnection:
        return self.create_db_service(db_type=db_type)

    def create_db_service(self, db_type) -> CoreDBConnection:
        """
        Create a core database instance using configuration.

        Returns:
            DBConnection instance

        Raises:
            ValueError: When database configuration values are invalid or missing.
            ConnectionError: When unable to establish database connection.
            Exception: For any other unexpected errors during database creation.
        """
        try:
            if not db_type:
                db_type = config.get('db_type', 'mysql')

            if 'mysql' == db_type.lower():
                # Check required configuration
                required_keys = ['db_host', 'db_name', 'db_user', 'db_password']

                if not all(config.get(key) for key in required_keys):
                    missing_keys = [key for key in required_keys if not config.get(key)]
                    logger.error(f"Missing required database configuration: {', '.join(missing_keys)}")
                    raise ValueError

                # Create database instance
                db = CoreMYSQLConnection(
                    host=config.get('db_host'),
                    database=config.get('db_name'),
                    user=config.get('db_user'),
                    password=config.get('db_password'),
                    port=config.get('db_port', 3306)
                )
                logger.info(f"Database instance created for {config.get('db_host')}/{config.get('db_name')}")

            elif 'internal' == db_type.lower():
                db = LocalMemoryConnection()
                logger.info(f"Non-persistent database instance created internally")

            else:
                logger.error(f"Error creating database of unknown type: {db_type}")
                raise ValueError

            return db

        except ValueError as e:
            logger.error(f"Unable to bootstrap database_client: {e}")
            exit(78)  # Configuration error
        except ConnectionError as e:
            logger.error(f"Unable to establish database connection: {e}")
            exit(78)  # Configuration error
        except Exception as e:
            logger.error(f"Error creating database instance: {e}")
            exit(78)  # Configuration error
