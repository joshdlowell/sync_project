from typing import Optional, Dict, Any, List
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager

from .db_interfaces import PipelineDBConnection
from database_client import logging_config


class PipelineMYSQLConnection(PipelineDBConnection):
    """
    Database access class for MySQL pipeline operations.

    This class provides methods to interact with the MySQL database
    for retrieving pipeline updates, sites, and updating hash values.
    """

    def __init__(self, host, database, user, password, port=3306,
                 connection_timeout=30, command_timeout=30, autocommit=True,
                 raise_on_warnings=True, **kwargs):
        """
        Initialize the MySQL database connection configuration.

        Args:
            host: Database server hostname or IP
            database: Database name
            user: Database username
            password: Database password
            port: Database port (default: 3306)
            connection_timeout: Connection timeout in seconds (default: 30)
            command_timeout: Command timeout in seconds (default: 30)
            autocommit: Whether to autocommit transactions (default: True)
            raise_on_warnings: Whether to raise on warnings (default: True)
        """
        self.config = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': port,
            'connection_timeout': connection_timeout,
            'autocommit': autocommit,
            'raise_on_warnings': raise_on_warnings,
            'sql_mode': 'TRADITIONAL'
        }

        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.connection_timeout = connection_timeout
        self.command_timeout = command_timeout

        self.other_args = kwargs

        self.logger = logging_config.configure_logging()

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.

        Yields:
            mysql.connector connection object

        Raises:
            Error: If a database error occurs
        """
        connection = None
        try:
            connection = mysql.connector.connect(**self.config)
            self.logger.debug(f"MySQL connection established to {self.host}")
            yield connection
        except Error as e:
            self.logger.error(f"MySQL database error: {e}")
            if connection:
                connection.rollback()
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error connecting to MySQL: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
                self.logger.debug("MySQL connection closed")

    def get_pipeline_updates(self) -> List[Dict[str, Any]]:
        """
        Get TeamCity updates that haven't been processed yet (hash_value is NULL).

        Returns:
            List of dictionaries containing update information with keys:
            - id: Database ID
            - TC_id: TeamCity job number
            - timestamp: Unix timestamp
            - update_path: Path to the update
            - update_size: Size in bytes
            - hash_value: Will be None for unprocessed updates
        """
        query = """
                SELECT id, TC_id, timestamp, update_path, update_size, hash_value
                FROM authorized_updates
                WHERE hash_value IS NULL
                ORDER BY timestamp ASC
                """

        try:
            with self._get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(query)
                    results = cursor.fetchall()

                    self.logger.debug(f"Retrieved {len(results)} unprocessed pipeline updates")
                    return results

        except Error as e:
            self.logger.error(f"Error fetching pipeline updates: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching pipeline updates: {e}")
            return []

    def put_pipeline_hash(self, update_path: str, hash_value: str) -> bool:
        """
        Update the hash value for a specific update path.

        Args:
            update_path: The path of the update to update
            hash_value: The calculated hash value to store

        Returns:
            True if successful, False if an error occurred

        Raises:
            ValueError: If required parameters are not provided
        """
        # Validate input parameters
        if not update_path or not hash_value:
            self.logger.debug("put_pipeline_hash missing update_path or hash_value")
            raise ValueError("update_path and hash_value must be provided")

        update_path = update_path.strip()
        hash_value = hash_value.strip()

        query = """
                UPDATE authorized_updates
                SET hash_value = %s
                WHERE update_path = %s
                  AND hash_value IS NULL
                """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (hash_value, update_path))

                    rows_affected = cursor.rowcount
                    conn.commit()

                    if rows_affected == 0:
                        self.logger.warning(f"No unprocessed update found for path: {update_path}")
                        return False
                    elif rows_affected == 1:
                        self.logger.info(f"Successfully updated hash for path: {update_path}")
                        return True
                    else:
                        self.logger.warning(
                            f"Multiple records updated for path: {update_path} (count: {rows_affected})")
                        return True

        except Error as e:
            self.logger.error(f"Error updating pipeline hash: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error updating pipeline hash: {e}")
            return False

    def get_official_sites(self) -> List[str]:
        """
        Get the current authoritative sites list from the MySQL table.

        Returns:
            List of site names (strings)
        """
        query = """
                SELECT name
                FROM pipe_site_list
                ORDER BY name
                """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    results = cursor.fetchall()

                    # Extract site names from the result tuples
                    sites = [row[0] for row in results]

                    self.logger.debug(f"Retrieved {len(sites)} official sites")
                    return sites

        except Error as e:
            self.logger.error(f"Error fetching official sites: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching official sites: {e}")
            return []

    def put_pipeline_site_completion(self, site: str) -> bool:
        """
        Mark a site as having completed pipeline processing.

        Args:
            site: The site name to mark as completed

        Returns:
            True if successful, False if an error occurred

        Raises:
            ValueError: If site parameter is not provided
        """
        # TODO: Implement this method based on your specific requirements
        # This is a placeholder implementation
        if not site:
            self.logger.debug("put_pipeline_site_completion missing site parameter")
            raise ValueError("site parameter must be provided")

        # Example implementation - adjust based on your table structure
        query = """
                UPDATE site_pipeline_status
                SET completed    = 1, \
                    completed_at = NOW()
                WHERE site_name = %s
                """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (site.strip(),))

                    rows_affected = cursor.rowcount
                    conn.commit()

                    if rows_affected > 0:
                        self.logger.info(f"Successfully marked site {site} as completed")
                        return True
                    else:
                        self.logger.warning(f"No site found to update: {site}")
                        return False

        except Error as e:
            self.logger.error(f"Error updating site completion status: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error updating site completion status: {e}")
            return False

    def pipeline_health_check(self) -> Dict[str, bool]:
        """
        Verify that the MySQL database is alive and responding to requests.

        Returns:
            Dictionary with 'pipeline_db' key indicating database health status
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()  # Consume the result

                    self.logger.info("MySQL pipeline database is responsive")
                    return {'pipeline_db': True}

        except Exception as e:
            self.logger.error(f"Error connecting to MySQL pipeline database: {e}")
            return {'pipeline_db': False}

    def get_update_by_path(self, update_path: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific update record by its path.

        Args:
            update_path: The path to search for

        Returns:
            Dictionary with update information or None if not found

        Raises:
            ValueError: If update_path is not provided
        """
        if not update_path:
            self.logger.debug("get_update_by_path missing update_path")
            raise ValueError("update_path must be provided")

        query = """
                SELECT id, TC_id, timestamp, update_path, update_size, hash_value
                FROM authorized_updates
                WHERE update_path = %s
                """

        try:
            with self._get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (update_path.strip(),))
                    result = cursor.fetchone()

                    if result:
                        self.logger.debug(f"Found update record for path: {update_path}")
                        return result
                    else:
                        self.logger.debug(f"No update record found for path: {update_path}")
                        return None

        except Error as e:
            self.logger.error(f"Error fetching update by path: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error fetching update by path: {e}")
            return None

    def get_processed_updates(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get processed updates (those with hash values).

        Args:
            limit: Maximum number of records to return (None for all)

        Returns:
            List of dictionaries containing processed update information
        """
        query = """
                SELECT id, TC_id, timestamp, update_path, update_size, hash_value
                FROM authorized_updates
                WHERE hash_value IS NOT NULL
                ORDER BY timestamp DESC
                """

        if limit is not None:
            if not isinstance(limit, int) or limit <= 0:
                raise ValueError("Limit must be a positive integer")
            query += f" LIMIT {limit}"

        try:
            with self._get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(query)
                    results = cursor.fetchall()

                    self.logger.debug(f"Retrieved {len(results)} processed pipeline updates")
                    return results

        except Error as e:
            self.logger.error(f"Error fetching processed updates: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching processed updates: {e}")
            return []