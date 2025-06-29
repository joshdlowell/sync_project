from typing import Optional, Dict, Any, List
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
from .local_DB_interface import DBConnection
from squishy_REST_API import logger


class MYSQLConnection(DBConnection):
    """
    Database access class for hash table operations.

    This class provides methods to interact with the MySQL database
    for storing and retrieving hash information.
    """
    def __init__(self, host, database, user, password, port=3306,
                 connection_factory=None, autocommit=True, raise_on_warnings=True):
        """
        Initialize the database connection configuration.

        Args:
            host: Database host
            database: Database name
            user: Database user
            password: Database password
            port: Database port (default: 3306)
            connection_factory: Optional factory function for creating connections (for testing)
            autocommit: Whether to autocommit transactions (default: True)
            raise_on_warnings: Whether to raise on warnings (default: True)
        """
        self.config = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': port,
            'autocommit': autocommit,
            'raise_on_warnings': raise_on_warnings
        }
        self.database = database
        self.connection_factory = connection_factory or mysql.connector.connect

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.

        Yields:
            MySQL connection object

        Raises:
            Error: If a database error occurs
        """
        connection = None
        try:
            connection = self.connection_factory(**self.config)
            logger.debug(f"Database connection established to {self.config['host']}")
            yield connection
        except Error as e:
            logger.error(f"Database error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
                logger.debug("Database connection closed")

    def insert_or_update_hash(self, record: dict[str, Any]) -> bool:
        """
        Insert new record or update existing one. Logs changes discovered to database.

        Args:
            record: Dict of hashtable column:value keypairs to be added to the db

        Returns:
            True if successful, False if an error occurred.

        Raises:
            ValueError: If required parameters are not provided
        """
        # Validate required keys
        if missing_keys := {'path', 'current_hash'} - record.keys():
            logger.debug(f"Received update request missing keys: {missing_keys}")
            raise ValueError(f"{missing_keys} value(s) must be provided")

        path = record['path'].strip()
        current_hash = record['current_hash'].strip()
        logger.debug(f"Inserting or updating hash for path: {path}")

        # Get existing record
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT current_hash, dirs, links, files FROM hashtable WHERE path = %s", (path,))
                    result = cursor.fetchone()
        except Error as e:
            logger.error(f"Error checking database for existing record: {e}")
            return False

        # Format list fields for database
        format_list = lambda field_list: ','.join(x.strip() for x in field_list) if field_list else None
        dirs, links, files = (format_list(record.get(field)) for field in ['dirs', 'links', 'files'])

        # Initialize change tracking
        modified, created, deleted = set(), set(), set()

        # Calculate changes for existing records
        if result:
            existing_hash, existing_dirs, existing_links, existing_files = result
            parse_existing = lambda field: [x.strip() for x in field.split(",")] if field else []

            # Calculate additions and deletions for all field types
            for field_name, existing_str, request_list in [
                ('dirs', existing_dirs, record.get('dirs', [])),
                ('files', existing_files, record.get('files', [])),
                ('links', existing_links, record.get('links', []))
            ]:
                existing_list = parse_existing(existing_str)
                if not request_list:
                    request_list = []
                deleted.update(f"{path}/{x}" for x in set(existing_list) - set(request_list))

        logger.debug(f"Prepared data for path {path}: hash={current_hash}")
        logger.debug(f"dirs={len(record.get('dirs')) if record.get('dirs') else 'None'}")
        logger.debug(f"files={len(record.get('files'))if record.get('files') else 'None'}")
        logger.debug(f"links={len(record.get('links'))if record.get('links') else 'None'}")

        # Determine operation and build query
        query_params = {'path': path, 'current_hash': current_hash, 'dirs': dirs, 'files': files, 'links': links}

        if not result:  # New record
            logger.info(f"Inserting new record into database for path: {path}")
            created.add(path)
            query = """
                    INSERT INTO hashtable (path, current_hash, current_dtg_latest, current_dtg_first,
                                           dirs, files, links)
                    VALUES (%(path)s, %(current_hash)s, UNIX_TIMESTAMP(), `current_dtg_latest`,
                            %(dirs)s, %(files)s, %(links)s) AS entry
                    ON DUPLICATE KEY
                    UPDATE
                        current_hash = entry.current_hash,
                        current_dtg_latest = entry.current_dtg_latest,
                        current_dtg_first = entry.current_dtg_first,
                        dirs = entry.dirs,
                        files = entry.files,
                        links = entry.links
                    """
        elif result[0] == current_hash:  # Hash unchanged
            logger.info(f"Found existing record for path, hash unchanged: {path}")
            query = "UPDATE hashtable SET current_dtg_latest = UNIX_TIMESTAMP() WHERE path = %(path)s"
        else:  # Hash changed, move current hash and timestamp to previous and update record
            logger.info(f"Found existing record for path, hash has changed: {path}")
            modified.add(path)
            query = """
                    UPDATE hashtable
                    SET prev_hash          = `current_hash`,
                        prev_dtg_latest    = `current_dtg_latest`,
                        current_hash       = %(current_hash)s,
                        current_dtg_latest = UNIX_TIMESTAMP(),
                        current_dtg_first  = `current_dtg_latest`,
                        dirs               = %(dirs)s,
                        files              = %(files)s,
                        links              = %(links)s
                    WHERE path = %(path)s
                    """

        # Execute query and handle deletions
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, query_params)
                    if cursor.rowcount == 1:
                        logger.info(f"Successfully updated database for path: {path}")
                    if cursor.rowcount > 1:
                        logger.warning(f"Caution, multiple records were updated for a single record operation for path: {path}")
        except Error as e:
            logger.error(f"Error inserting/updating record: {e}")
            return False

        # Prune deleted paths from the database
        for del_path in deleted:
            self._delete_hash_entry(del_path)

        changes = {field: sorted(paths) for field, paths in
                   [('modified', modified), ('created', created), ('deleted', deleted)]}
        self._log_changes(changes)

        logger.debug(f"Changes: modified={len(modified)}, created={len(created)}, deleted={len(deleted)}")
        return True

    def _delete_hash_entry(self, path: str) -> bool:
        """
        Delete a hashtable record by path.

        Args:
            path: Path to delete from the database.

        Returns:
            True if the record was deleted, False if not found, or an error occurred.
        """
        query = "DELETE FROM hashtable WHERE path = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Delete the entry with the matching path
                    cursor.execute(query, (path,))

                    # Check if any rows were affected (deleted)
                    rows_affected = cursor.rowcount

            logger.info(f"Removed {rows_affected} record from the database: {path}")
            return rows_affected > 0

        except Exception as e:
            # Log the error
            logger.error(f"Error deleting hash entry for path {path}: {e}")
            return False

    def _log_changes(self, changes: dict[str, list[str]]) -> None:
        # Send change logs to db
        # TODO complete this method
        pass

    def get_hash_record(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get a single record by path.

        Args:
            path: Path to retrieve

        Returns:
            Dictionary with record data or None if not found or an error occurred
        """
        query = "SELECT * FROM hashtable WHERE path = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (path,))
                    result = cursor.fetchone()
                    if result:
                        logger.debug(f"Found record for path: {path}")
                    else:
                        logger.debug(f"No record found for path: {path}")
                    return result
        except Error as e:
            logger.error(f"Error fetching record: {e}")
            return None

    def get_single_hash_record(self, path: str) -> Optional[str]:
        """
        Get only the current hash value for a path.

        Args:
            path: Path to retrieve hash for

        Returns:
            Hash value as string or None if not found or an error occurred
        """
        query = "SELECT current_hash FROM hashtable WHERE path = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (path,))
                    result = cursor.fetchone()
                    if result:
                        logger.debug(f"Found hash for path: {path}")
                    else:
                        logger.debug(f"No hash found for path: {path}")
                    return result[0] if result else None
        except Error as e:
            logger.error(f"Error fetching hash: {e}")
            return None

    def get_single_timestamp(self, path: str) -> Optional[int]:
        """
        Get only the current hash timestamp value for a path.

        Args:
            path: Path to retrieve timestamp for

        Returns:
            timestamp value as int or None if not found or an error occurred
        """
        query = "SELECT current_dtg_latest FROM hashtable WHERE path = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (path,))
                    result = cursor.fetchone()
                    if result:
                        logger.debug(f"Found timestamp for path: {path}")
                    else:
                        logger.debug(f"No timestamp found for path: {path}")
                    return result[0] if result else None
        except Error as e:
            logger.error(f"Error fetching timestamp: {e}")
            return None

    def get_oldest_updates(self, path: str, percent: int = 10) -> List[str]:
        """
        Get a list of directories that need to be updated based on their age.

        This method retrieves the oldest 'last checked' items (based on timestamps)
        in the root of the given path. The number of items returned is determined
        by the percent parameter.

        Args:
            path: The directory to start from (absolute from /baseline root)
            percent: The percentage of items to return (default: 10%)

        Returns:
            A list of directory paths that need to be updated
        """
        # Get the hash record for the given path
        path_record = self.get_hash_record(path)

        # If the path doesn't exist in the database return the path
        if not path_record:
            logger.info(f"Path not found: {path}")
            return [path]

        # Parse database lists and combine all items
        parse_list = lambda field: [x.strip() for x in field.split(",")] if field else []

        all_items = []
        for item_type in ['dirs', 'files', 'links']:
            items = parse_list(path_record.get(item_type, ''))
            all_items.extend(items)

        # Create timestamp, path tuples and sort by timestamp (oldest first)
        timestamped_items = [
            (self.get_single_timestamp(f"{path}/{item}"), f"{path}/{item}")
            for item in all_items
        ]
        ordered_items = [item_path for _, item_path in sorted(timestamped_items)]

        # Calculate number of items to return
        update_num = max(1, min(int(len(ordered_items) * percent / 100), len(ordered_items)))

        logger.info(f"Returning the {update_num} oldest items")
        logger.debug(f"Oldest items: {ordered_items[:update_num]}")
        return ordered_items[:update_num]

    def get_priority_updates(self) -> List[str]:
        """
        Get directories where target_hash != current_hash, prioritizing shallowest paths
        to avoid redundant updates of nested directories.

        Returns:
            List of directory paths needing updates, deduplicated by hierarchy
        """
        query = """
                SELECT path \
                FROM hashtable
                WHERE target_hash IS NOT NULL \
                  AND current_hash != target_hash \
                """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    paths = [row[0] for row in cursor.fetchall()]
        except Error as e:
            logger.error(f"Error fetching priority updates: {e}")
            return []

        if not paths:
            logger.info("All hashes in the db are in sync")
            return []

        # Sort by depth and remove paths covered by shallower ones
        logger.debug(f"Pre-sorted priority updates: {paths}")
        paths = sorted(set(paths), key=lambda x: x.count('/'))

        priority = []
        for path in paths:
            # Skip if already covered by existing shallower path
            if not any(path.startswith(existing + '/') for existing in priority):
                priority.append(path)
        logger.debug(f"Sorted priority updates: {paths}")
        return priority

    def put_log(self, args_dict: dict) -> int | None:
        """
        Put log entry into database.

        This method inserts log entries into the local_database.

        Returns:
            log_id number (int) if the log entry was inserted, None if an error occurred
        """
        # Check for required parameters
        if not args_dict.get('summary_message'):
            logger.debug("No summary message provided, skipping log entry")
            return None

        # Extract parameters with defaults
        params = {
            'site_id': args_dict.get('site_id', 'local'),
            'log_level': args_dict.get('log_level', 'INFO'),
            'summary_message': args_dict.get('summary_message'),
            'detailed_message': args_dict.get('detailed_message', None)
        }

        query = """INSERT INTO logs (site_id, log_level, summary_message, detailed_message)
                   VALUES (%(site_id)s, %(log_level)s, %(summary_message)s, %(detailed_message)s)"""

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    if cursor.rowcount == 0:
                        logger.info("Log entry failed to insert")
                        return None
                    if cursor.rowcount > 1:
                        logger.warning("Multiple records were updated for a single log entry operation")

                    # Get the auto-generated log_id
                    log_id = cursor.lastrowid
                    logger.info(f"Successfully inserted log entry with ID: {log_id}")
                    return log_id
        except Error as e:
            logger.error(f"Error inserting log entry: {e}")
            return None

    def get_logs(self, limit: Optional[int] = None, offset: int = 0,
                 order_by: str = "timestamp", order_direction: str = "DESC") -> List[Dict[str, Any]]:
        """
        Get log entries from database.

        This method retrieves log entries from the local database with optional pagination
        and ordering capabilities.

        Args:
            limit: Maximum number of records to return (None for all records)
            offset: Number of records to skip for pagination
            order_by: Column name to order by (default: 'timestamp')
            order_direction: Sort direction - 'ASC' or 'DESC' (default: 'DESC')

        Returns:
            A list of dicts where each dict is a complete log entry from the database.
            Returns empty list if no records found or on error.

        Raises:
            ValueError: If invalid parameters are provided
        """
        # Input validation
        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            raise ValueError("Limit must be a positive integer")

        if not isinstance(offset, int) or offset < 0:
            raise ValueError("Offset must be a non-negative integer")

        if order_direction.upper() not in ('ASC', 'DESC'):
            raise ValueError("Order direction must be 'ASC' or 'DESC'")

        # Validate order_by column (whitelist approach for security)
        allowed_columns = {'log_id', 'site_id', 'log_level', 'timestamp'}  # Adjust based on schema changes
        if order_by not in allowed_columns:
            raise ValueError(f"Invalid order_by column. Allowed: {allowed_columns}")

        # Build query with proper parameterization
        base_query = "SELECT * FROM logs"
        query_parts = [base_query]
        query_params = []

        # Add ORDER BY clause (safe since we validated the column name)
        query_parts.append(f"ORDER BY {order_by} {order_direction.upper()}")

        # Add LIMIT and OFFSET
        if limit is not None:
            query_parts.append("LIMIT %s")
            query_params.append(limit)

        if offset > 0:
            query_parts.append("OFFSET %s")
            query_params.append(offset)

        final_query = " ".join(query_parts)

        try:
            with self._get_connection() as conn:
                with conn.cursor(dictionary=True, buffered=True) as cursor:
                    cursor.execute(final_query, query_params)
                    result = cursor.fetchall()

                    # More informative logging
                    record_count = len(result) if result else 0
                    logger.debug(f"Retrieved {record_count} log records from database")

                    return result or []  # Ensure we always return a list

        except mysql.connector.Error as e:
            # More specific error handling
            logger.error(f"MySQL error fetching log records: {e.errno} - {e.msg}")
            return []
        except Exception as e:
            # Catch any other unexpected errors
            logger.error(f"Unexpected error fetching log records: {e}")
            return []

    def delete_log_entry(self, log_id: int) -> bool:
        """
        Remove a log entry from the database.

        This method deletes a log_entry by log_id and is used to clean out local logs after they
         have been forwarded to the core DB.

        Args:
            An int representing the log entry's log_id to be removed from the local database.

        Returns:
            True if the log entry was deleted, False if not found, or an error occurred.
        """
        query = "DELETE FROM logs WHERE log_id = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Delete the entry with the matching path
                    cursor.execute(query, (log_id,))

                    # Check if any rows were affected (deleted)
                    rows_affected = cursor.rowcount

            logger.info(f"Removed {rows_affected} log entry from the database")
            return rows_affected > 0

        except Exception as e:
            # Log the error
            logger.error(f"Error deleting log entry #{log_id}: {e}")
            return False

    def life_check(self) -> bool:
        """
         Check if the database is active and responsive.

         This method verifies that the local database is alive and responding to requests.

         Returns:
             True if the database is active and responsive, False if not.
         """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1;")
                    _ = cursor.fetchall()  # Consume the result
                    # If the query executes without an exception, the database is responsive
                    logger.info("MySQL database is responsive.")
                    return True

        except Exception as e:
            logger.error(f"Error connecting to MySQL: {e}")
            return False
