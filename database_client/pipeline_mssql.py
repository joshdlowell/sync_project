from typing import Optional, Dict, Any, List
import pyodbc
from contextlib import contextmanager

from .db_interfaces import PipelineDBConnection
import logging_config


class PipelineMSSQLConnection(PipelineDBConnection):
    """
    Database access class for MSSQL pipeline operations.

    This class provides methods to interact with the MSSQL database
    for retrieving pipeline updates, sites, and updating hash values.
    """

    def __init__(self, server=None, database=None, username=None, password=None, driver=None,
                 port=1433, connection_timeout=30, command_timeout=30, **kwargs):
        """
        Initialize the MSSQL database connection configuration.

        Args:
            server: Database server hostname or IP
            database: Database name
            username: Database username
            password: Database password
            driver: ODBC driver (default: ODBC Driver 17 for SQL Server)
            port: Database port (default: 1433)
            connection_timeout: Connection timeout in seconds (default: 30)
            command_timeout: Command timeout in seconds (default: 30)
        """
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.driver = driver or "ODBC Driver 17 for SQL Server"
        self.port = port
        self.connection_timeout = connection_timeout
        self.command_timeout = command_timeout

        self.other_args = kwargs

        # Build connection string
        self.connection_string = (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.server},{self.port};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"Connection Timeout={self.connection_timeout};"
        )

        self.logger = logging_config.configure_logging()

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.

        Yields:
            pyodbc connection object

        Raises:
            Exception: If a database error occurs
        """
        connection = None
        try:
            connection = pyodbc.connect(self.connection_string)
            connection.timeout = self.command_timeout
            self.logger.debug(f"MSSQL connection established to {self.server}")
            yield connection
        except pyodbc.Error as e:
            self.logger.error(f"MSSQL database error: {e}")
            if connection:
                connection.rollback()
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error connecting to MSSQL: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                connection.close()
                self.logger.debug("MSSQL connection closed")

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
                ORDER BY timestamp ASC \
                """

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)

                # Get column names
                columns = [column[0] for column in cursor.description]

                # Fetch all rows and convert to list of dictionaries
                results = []
                for row in cursor.fetchall():
                    row_dict = dict(zip(columns, row))
                    results.append(row_dict)

                self.logger.debug(f"Retrieved {len(results)} unprocessed pipeline updates")
                return results

        except pyodbc.Error as e:
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
                SET hash_value = ?
                WHERE update_path = ? \
                  AND hash_value IS NULL \
                """

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
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
                    self.logger.warning(f"Multiple records updated for path: {update_path} (count: {rows_affected})")
                    return True

        except pyodbc.Error as e:
            self.logger.error(f"Error updating pipeline hash: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error updating pipeline hash: {e}")
            return False

    def get_official_sites(self) -> List[str]:
        """
        Get the current authoritative sites list from the MSSQL table.

        Returns:
            List of site names (strings)
        """
        query = """
                SELECT name
                FROM site_list
                ORDER BY name \
                """

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)

                # Extract site names from the result tuples
                sites = [row[0] for row in cursor.fetchall()]

                self.logger.debug(f"Retrieved {len(sites)} official sites")
                return sites

        except pyodbc.Error as e:
            self.logger.error(f"Error fetching official sites: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching official sites: {e}")
            return []

    def put_pipeline_site_completion(self, site: str) -> bool:
        # TODO implement this method
        pass

    def pipeline_health_check(self) -> Dict[str, bool]:
        """
        Verify that the MSSQL database is alive and responding to requests.

        Returns:
            Dictionary with 'pipeline_db' key indicating database health status
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()  # Consume the result

                self.logger.info("MSSQL pipeline database is responsive")
                return {'pipeline_db': True}

        except Exception as e:
            self.logger.error(f"Error connecting to MSSQL pipeline database: {e}")
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
                WHERE update_path = ? \
                """

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (update_path.strip(),))

                row = cursor.fetchone()
                if row:
                    columns = [column[0] for column in cursor.description]
                    result = dict(zip(columns, row))
                    self.logger.debug(f"Found update record for path: {update_path}")
                    return result
                else:
                    self.logger.debug(f"No update record found for path: {update_path}")
                    return None

        except pyodbc.Error as e:
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
                ORDER BY timestamp DESC \
                """

        if limit is not None:
            if not isinstance(limit, int) or limit <= 0:
                raise ValueError("Limit must be a positive integer")
            # Note: MSSQL uses TOP instead of LIMIT
            query = query.replace("SELECT", f"SELECT TOP {limit}")

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)

                columns = [column[0] for column in cursor.description]
                results = []
                for row in cursor.fetchall():
                    row_dict = dict(zip(columns, row))
                    results.append(row_dict)

                self.logger.debug(f"Retrieved {len(results)} processed pipeline updates")
                return results

        except pyodbc.Error as e:
            self.logger.error(f"Error fetching processed updates: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching processed updates: {e}")
            return []