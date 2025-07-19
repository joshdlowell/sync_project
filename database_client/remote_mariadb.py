from typing import Optional, Dict, Any, List
import json
import mariadb
from contextlib import contextmanager

from .db_interfaces import RemoteDBConnection
from database_client import logging_config


class RemoteMariaDBConnection(RemoteDBConnection):
    """
    Database access class for hash table operations.

    This class provides methods to interact with the MariaDB database
    for storing and retrieving hash information.
    """

    def __init__(self, host=None, database=None, user=None, password=None, port=3306,
                 connection_factory=None, autocommit=True, **kwargs):
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
        """
        self.config = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': port,
            'autocommit': autocommit
        }
        self.database = database
        self.connection_factory = connection_factory or mariadb.connect

        self.other_args = kwargs

        self.logger = logging_config.configure_logging()

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.
        Yields:
            MariaDB connection object
        Raises:
            mariadb.Error: If a database error occurs
        """
        connection = None
        try:
            connection = self.connection_factory(**self.config)
            self.logger.debug(f"Database connection established to {self.config['host']}")
            yield connection
        except mariadb.Error as e:
            self.logger.error(f"Database error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                connection.close()
                self.logger.debug("Database connection closed")

    def get_hash_record(self, path: str) -> Dict[str, Any] | None:
        """
        Get a single record by path.
        Args:
            path: Path to retrieve
        Returns:
            Dictionary with record data or None if not found or an error occurred
        Raises:
            ValueError: If required parameters are not provided
        """
        # Validate required keys
        if not path:
            self.logger.debug(f"get_hash_record missing path")
            raise ValueError(f"path value must be provided")

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM hashtable WHERE path = ?", (path,))
                columns = [desc[0] for desc in cursor.description]
                row = cursor.fetchone()

                if row:
                    result = dict(zip(columns, row))
                    # convert lists for sql storage
                    self._convert_to_from_json(result)
                    self.logger.debug(f"Found record for path: {path}")
                    return result
                else:
                    self.logger.debug(f"No record found for path: {path}")
                    return None
        except mariadb.Error as e:
            self.logger.error(f"Error fetching record: {e}")
            return None

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
        # Validate required keys and data formatting
        if missing_keys := {'path', 'current_hash'} - record.keys():
            self.logger.debug(f"Update request missing keys: {missing_keys}")
            raise ValueError(f"{missing_keys} value(s) must be provided")
        for field in {'dirs', 'files', 'links'}:
            if record.get(field, None) and not isinstance(record[field], list):
                raise ValueError(f"Update request fields dirs, files and, links must be lists")

        # Collect data
        path = record['path'].strip()
        current_hash = record['current_hash'].strip()
        dirs = record.get('dirs', [])
        files = record.get('files', [])
        links = record.get('links', [])
        target_hash = record.get('target_hash', None)

        # Get existing record
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT current_hash, dirs, links, files, target_hash FROM hashtable WHERE path = ?", (path,))
                result = cursor.fetchone()
        except mariadb.Error as e:
            self.logger.error(f"Error checking database for existing record: {e}")
            return False

        # Handle the case where result is None (path not in database)
        if result is None:
            # Set default values for new record
            existing_hash = None
            existing_dirs = []
            existing_links = []
            existing_files = []
            existing_target_hash = None
        else:
            # Unpack existing record
            existing_hash, existing_dirs_json, existing_links_json, existing_files_json, existing_target_hash = result
            existing_dirs = json.loads(existing_dirs_json) if existing_dirs_json else []
            existing_links = json.loads(existing_links_json) if existing_links_json else []
            existing_files = json.loads(existing_files_json) if existing_files_json else []

        # Determine the final target_hash value (update if passed, otherwise keep as is)
        final_target_hash = target_hash.strip() if target_hash is not None else existing_target_hash

        # Build params list for sql query (MariaDB uses ? placeholders)
        query_params = [path, current_hash, json.dumps(dirs), json.dumps(files), json.dumps(links), final_target_hash]

        # Initialize change tracking
        modified, created, deleted = set(), set(), set()

        # EXISTING RECORD build query and calculate changes for existing records
        if result:
            self.logger.debug(f"Updating hash for path: {path}")

            if existing_hash == current_hash:  # Hash unchanged
                self.logger.debug(f"Hash unchanged: {path}")
                query = """
                        UPDATE hashtable
                        SET current_dtg_latest = CURRENT_TIMESTAMP,
                            target_hash        = ?
                        WHERE path = ?
                        """
                query_params = [final_target_hash, path]
            else:  # Hash changed, move current_hash and timestamp to previous columns and update the record
                self.logger.info(f"Hash changed: {path}")
                modified.add(path)
                query = """
                        UPDATE hashtable
                        SET prev_hash          = current_hash,
                            prev_dtg_latest    = current_dtg_latest,
                            current_hash       = ?,
                            current_dtg_latest = CURRENT_TIMESTAMP,
                            current_dtg_first  = current_dtg_latest,
                            dirs               = ?,
                            files              = ?,
                            links              = ?,
                            target_hash        = ?
                        WHERE path = ?
                        """
                query_params = [current_hash, json.dumps(dirs), json.dumps(files), json.dumps(links), final_target_hash,
                                path]

            # Calculate deletions for all field types (additions added automatically)
            for field_name, existing_list, request_list in [
                ('dirs', existing_dirs or [], dirs),
                ('files', existing_files or [], files),
                ('links', existing_links or [], links)
            ]:
                deleted.update(f"{path}/{x}" for x in set(existing_list) - set(request_list))
        # NEW RECORD build query and add to created list
        else:
            self.logger.info(f"Inserting new record for path: {path}")
            created.add(path)
            query = """
                    INSERT INTO hashtable (path, current_hash, current_dtg_latest, current_dtg_first,
                                           dirs, files, links, target_hash)
                    VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?, ?, ?)
                    ON DUPLICATE KEY UPDATE current_hash       = VALUES(current_hash), \
                                            current_dtg_latest = VALUES(current_dtg_latest), \
                                            current_dtg_first  = VALUES(current_dtg_first), \
                                            dirs               = VALUES(dirs), \
                                            files              = VALUES(files), \
                                            links              = VALUES(links), \
                                            target_hash        = VALUES(target_hash)
                    """

        self.logger.debug(f"Prepared data for path {path}: hash={current_hash}")

        # Execute query and handle deletions
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, query_params)
                if cursor.rowcount == 1:
                    self.logger.info(f"Successfully updated database for path: {path}")
                if cursor.rowcount > 1:
                    self.logger.warning(
                        f"Caution, multiple records were updated for a single record operation for path: {path}")
        except mariadb.Error as e:
            self.logger.error(f"Error inserting/updating record: {e}")
            return False

        # Prune deleted paths from the database
        for deleted_path in deleted:
            deleted.update(self._recursive_delete_hash(deleted_path))
            self.logger.info(f"Removed {len(deleted)} records from the database")
        # Log changes to the database under the session_id passed in.
        changes = json.dumps({field: sorted(paths) for field, paths in
                              [('modified', modified), ('created', created), ('deleted', deleted)]})
        log_entry = {
            'session_id': record.get('session_id', None),
            'summary_message': f"Database hash changes",
            'detailed_message': changes
        }
        self.put_log(log_entry)
        self.logger.debug(f"Changes logged to database under session_id {record.get('session_id', None)}")
        return True

    def _convert_to_from_json(self, params):
        """Takes a list of lists and convert to list of json string or other way around, in place"""
        for key in ['dirs', 'files', 'links']:
            if key in params:
                if isinstance(params[key], list):
                    params[key] = json.dumps(params[key])
                elif isinstance(params[key], str):
                    params[key] = json.loads(params[key])

    def _recursive_delete_hash(self, path: str) -> set[str]:
        """delete a hash record and all its children recursively."""
        deleted_list = []
        # Get existing record
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT dirs, links, files FROM hashtable WHERE path = ?", (path,))
                result = cursor.fetchone()
                if not result:
                    self.logger.debug(f"No record found for path: {path}")
                    return set()

                # Convert to dict for _convert_to_from_json
                result_dict = {'dirs': result[0], 'links': result[1], 'files': result[2]}
        except mariadb.Error as e:
            self.logger.error(f"Error checking database for existing record: {e}")
            return set()

        # convert lists for sql storage
        self._convert_to_from_json(result_dict)
        # Combine list fields from the database and call recursive delete on each one
        dirs, links, files = (result_dict.get(field, []) for field in ['dirs', 'links', 'files'])
        for item in [f"{path}/{item}" for item in dirs + files + links]:
            deleted_list.extend(self._recursive_delete_hash(item))

        if self._delete_hash_entry(path):
            deleted_list.append(path)

        return set(deleted_list)

    def _delete_hash_entry(self, path: str) -> bool:
        """
        Delete a hashtable record by path.
        Args:
            path: Path to delete from the database.
        Returns:
            True if the record was deleted, False if not found, or an error occurred.
        """
        query = "DELETE FROM hashtable WHERE path = ?"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (path,))
                rows_affected = cursor.rowcount
            return rows_affected > 0
        except Exception as e:
            self.logger.error(f"Error deleting hash entry for path {path}: {e}")
            return False

    def get_single_field(self, path: str, field: str) -> str | int | None:
        """
        Get a single field value for a path from the hashtable.
        Args:
            path: Path to retrieve field for
            field: Database column name to retrieve (e.g., 'current_hash', 'current_dtg_latest')
        Returns:
            Field value (string for hash, int for timestamp) or None if not found or an error occurred
        Raises:
            ValueError: If required parameters are not provided
        """
        # Validate required parameters
        if not path or not field:
            self.logger.debug(f"get_single_field missing path or field")
            raise ValueError(f"path and field value must be provided")
        if field not in {'current_hash', 'current_dtg_latest'}:
            raise ValueError(f"Invalid field name: {field}")

        query = f"SELECT {field} FROM hashtable WHERE path = ?"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (path,))
                result = cursor.fetchone()
                if result:
                    self.logger.debug(f"Found {field} for path: {path}")
                    return result[0]
                else:
                    self.logger.debug(f"No {field} found for path: {path}")
                    return None
        except mariadb.Error as e:
            self.logger.error(f"Error fetching {field}: {e}")
            return None

    def get_priority_updates(self) -> List[str]:
        """
        Get directories where target_hash != current_hash, prioritizing the shallowest paths
        to avoid redundant updates of nested directories.
        Returns:
            List of directory paths needing updates, deduplicated by hierarchy
        """
        query = """
                SELECT path
                FROM hashtable
                WHERE target_hash IS NOT NULL
                  AND current_hash != target_hash
                """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                paths = [row[0] for row in cursor.fetchall()]
        except mariadb.Error as e:
            self.logger.error(f"Error fetching priority updates: {e}")
            return []

        if not paths:
            self.logger.info("All hashes in the db are in sync")
            return []

        # Sort by depth and eliminate parents that will be updated by deeper children
        self.logger.debug(f"Pre-sorted priority updates: {paths}")
        paths_set = set(paths)
        deepest_only = []
        for path in paths_set:
            # Check if this path has any descendants in the changed set
            has_descendants = any(
                other_path.startswith(path + '/')
                for other_path in paths_set
                if other_path != path
            )
            # Only include paths that have no descendants in the changed set
            if not has_descendants:
                deepest_only.append(path)
        # Sort deepest first for consistent processing order
        deepest_only.sort(key=lambda x: (-x.count('/'), x))
        self.logger.debug(f"Deepest changed nodes only: {deepest_only}")
        return deepest_only

    def put_log(self, args_dict: dict) -> int | None:
        """
        Insert a log entry into the local_database.
        Returns:
            log_id number (int) if the log entry was inserted, None if an error occurred
        Raises:
            ValueError: If required parameters are not provided
        """
        # Validate required keys and data formatting
        if 'message' in args_dict.keys() and 'summary_message' not in args_dict.keys():
            args_dict['summary_message'] = args_dict['message']
        if missing_keys := {'summary_message'} - args_dict.keys():
            self.logger.debug(f"Update request missing keys: {missing_keys}")
            raise ValueError(f"{missing_keys} value(s) must be provided")

        # Extract parameters with defaults
        params = [
            args_dict.get('site_id', 'local'),
            args_dict.get('log_level', 'INFO'),
            args_dict.get('session_id', None),
            args_dict.get('summary_message'),
            args_dict.get('detailed_message', None)
        ]

        query = """INSERT INTO logs (site_id, log_level, session_id, summary_message, detailed_message)
                   VALUES (?, ?, ?, ?, ?)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                if cursor.rowcount == 0:
                    self.logger.debug("Log entry failed to insert")
                    return None
                if cursor.rowcount > 1:
                    self.logger.warning("Multiple records were updated for a single log entry operation")

                # Get the auto-generated log_id
                log_id = cursor.lastrowid
                self.logger.debug(f"Successfully inserted log entry with ID: {log_id}")

                return log_id
        except mariadb.Error as e:
            self.logger.error(f"Error inserting log entry: {e}")
            return None

    def get_logs(self, limit: Optional[int] = None, offset: int = 0,
                 order_by: str = "timestamp", order_direction: str = "DESC",
                 session_id_filter: Optional[str] = None,
                 older_than_days: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get log entries from database.

        This method retrieves log entries from the local database with optional pagination,
        ordering, and filtering capabilities.

        Args:
            limit: Maximum number of records to return (None for all records)
            offset: Number of records to skip for pagination
            order_by: Column name to order by (default: 'timestamp')
            order_direction: Sort direction - 'ASC' or 'DESC' (default: 'DESC')
            session_id_filter: Filter by session_id - None for all records,
                              'null' for records with NULL session_id (logs to ship),
                              or specific session_id value
            older_than_days: Filter records older than specified number of days

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

        if older_than_days is not None and (not isinstance(older_than_days, int) or older_than_days <= 0):
            raise ValueError("older_than_days must be a positive integer")

        # Validate order_by column (whitelist approach for security)
        allowed_columns = {'log_id', 'site_id', 'log_level', 'timestamp', 'session_id'}
        if order_by not in allowed_columns:
            raise ValueError(f"Invalid order_by column. Allowed: {allowed_columns}")

        # Build query with proper parameterization
        base_query = "SELECT * FROM logs"
        query_parts = [base_query]
        query_params = []
        where_conditions = []

        # Add WHERE clause for session_id filtering
        if session_id_filter is not None:
            if session_id_filter == 'null':
                where_conditions.append("session_id IS NULL")
            else:
                where_conditions.append("session_id = ?")
                query_params.append(session_id_filter)

        # Add WHERE clause for date filtering
        if older_than_days is not None:
            where_conditions.append("timestamp < DATE_SUB(CURRENT_TIMESTAMP, INTERVAL %s DAY)")
            query_params.append(older_than_days)

        # Combine WHERE conditions
        if where_conditions:
            query_parts.append("WHERE " + " AND ".join(where_conditions))

        # Add ORDER BY clause (safe since we validated the column name)
        query_parts.append(f"ORDER BY {order_by} {order_direction.upper()}")

        # Add LIMIT and OFFSET
        if limit is not None:
            query_parts.append("LIMIT ?")
            query_params.append(limit)

        if offset > 0:
            query_parts.append("OFFSET ?")
            query_params.append(offset)

        final_query = " ".join(query_parts)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(final_query, query_params)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                # Convert to list of dictionaries
                result = [dict(zip(columns, row)) for row in rows]

                # More informative logging
                record_count = len(result) if result else 0
                filter_info = []
                if session_id_filter is not None:
                    filter_info.append(f"session_id: {session_id_filter}")
                if older_than_days is not None:
                    filter_info.append(f"older than {older_than_days} days")

                filter_str = f" (filters: {', '.join(filter_info)})" if filter_info else ""
                self.logger.debug(f"Retrieved {record_count} log records from database{filter_str}")

                return result or []  # Ensure we always return a list

        except mariadb.Error as e:
            # More specific error handling
            self.logger.error(f"MariaDB error fetching log records: {e}")
            raise Exception("Error fetching log records from database")
        except Exception as e:
            # Catch any other unexpected errors
            self.logger.error(f"Unexpected error fetching log records: {e}")
            raise Exception(e)

    def consolidate_logs(self) -> bool:
        """
        Consolidate log entries by session ID, grouping and deduplicating JSON-encoded detailed messages.

        Returns:
            bool: True if consolidation was successful, False otherwise
        """
        try:
            # Find all unique session IDs that have log entries
            query = "SELECT DISTINCT session_id FROM logs WHERE session_id IS NOT NULL"
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                session_ids = [row[0] for row in cursor.fetchall()]

            if not session_ids:
                self.logger.info("No sessions found to consolidate")
                return True

            self.logger.debug(f"Found {len(session_ids)} sessions to consolidate")

            # Consolidate each session
            for session_id in session_ids:
                self._consolidate_logs(session_id)

            self.logger.info("Log consolidation completed successfully")
            return True

        except mariadb.Error as e:
            self.logger.error(f"Error during log consolidation: {e}")
            return False

    def _consolidate_logs(self, session_id: str) -> None:
        """
        Consolidate log entries for a specific session ID.

        Args:
            session_id: The session ID to consolidate logs for
        """
        # Get all entries for this session_id
        query = "SELECT * FROM logs WHERE session_id = ? ORDER BY log_id"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (session_id,))
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                result = [dict(zip(columns, row)) for row in rows]

                if result:
                    self.logger.debug(f"Found {len(result)} entries with session id {session_id}")
                else:
                    self.logger.debug(f"No log entry found with session id {session_id}")
                    return
        except mariadb.Error as e:
            self.logger.error(f"Error fetching log entry: {e}")
            return

        # Group entries by log level
        log_level_groups = {}
        session_type = None
        has_finish_session = False

        for log_entry in result:
            log_level = log_entry.get('log_level', 'INFO')
            summary_message = log_entry.get('summary_message', '')

            # Check for session start/finish messages
            if 'START SESSION' in summary_message:
                session_type = log_entry.get('detailed_message', 'Unknown Session')
                continue
            elif 'FINISH SESSION' in summary_message:
                has_finish_session = True
                continue

            # Initialize log level group if not exists
            if log_level not in log_level_groups:
                log_level_groups[log_level] = {
                    'entries': [],
                    'consolidated_data': {},
                    'site_id': log_entry.get('site_id', 'local')
                }

            log_level_groups[log_level]['entries'].append(log_entry)

        # Process each log level group
        for log_level, group_data in log_level_groups.items():
            self.logger.debug(f"Consolidating {len(group_data['entries'])} entries for log level {log_level}")

            # Consolidate JSON data for this log level
            consolidated_changes = {}

            for log_entry in group_data['entries']:
                try:
                    data = json.loads(log_entry.get('detailed_message', '{}'))
                    self.logger.debug(f"Processing JSON encoded log entry")

                    # Merge data by keys, deduplicating lists
                    for key, value in data.items():
                        if key not in consolidated_changes:
                            consolidated_changes[key] = set()

                        if isinstance(value, list):
                            consolidated_changes[key].update(value)
                        else:
                            consolidated_changes[key].add(str(value))

                except json.JSONDecodeError as e:
                    self.logger.debug(f"Not a JSON encoded log entry: {e}")
                    # Handle non-JSON entries by treating them as text
                    text_key = 'messages'
                    if text_key not in consolidated_changes:
                        consolidated_changes[text_key] = set()
                    consolidated_changes[text_key].add(log_entry.get('detailed_message', ''))

            # Sort and convert sets back to lists
            sorted_changes = {}
            for key, value_set in consolidated_changes.items():
                sorted_changes[key] = sorted(list(value_set))

            # Create consolidated entry
            detailed_message = json.dumps(sorted_changes, indent=2)

            summary_entry = {
                'site_id': group_data['site_id'],
                'session_id': None if has_finish_session else session_id,
                'log_level': log_level,
                'summary_message': f"Consolidated {log_level} entries for session {session_id}" +
                                   (f" ({session_type})" if session_type else ""),
                'detailed_message': detailed_message,
            }

            # Insert consolidated entry
            self.put_log(summary_entry)

            # Delete original entries for this log level
            log_ids_to_delete = [log_entry['log_id'] for log_entry in group_data['entries']]
            deleted_count, failed_deletes = self.delete_log_entries(log_ids_to_delete)

            if failed_deletes:
                self.logger.warning(f"Failed to delete {len(failed_deletes)} entries: {failed_deletes}")

            self.logger.debug(f"Consolidated {deleted_count} {log_level} entries for session {session_id}")

        self.logger.info(f"Finished consolidating session {session_id}")

    def delete_log_entries(self, log_ids: list[int]) -> tuple[list, list]:
        """
        Delete log_entries by log_id.

        Args:
            An int representing the log entry's log_id to be removed from the local database.

        Returns:
            True if the log entry was deleted, False if not found, or an error occurred.
        """
        # Validate input
        if not log_ids:
            self.logger.warning("Missing 'log_ids' field")
            raise ValueError("Missing 'log_ids' field")
        if isinstance(log_ids, int):
            log_ids = [log_ids]
        if not isinstance(log_ids, list):
            self.logger.warning("'log_ids' must be an number or list of numbers")
            raise ValueError("The 'log_ids' parameter must be a number or list of numbers.")
        try:  # Validate all IDs are integers
            log_ids = [int(log_id) for log_id in log_ids]
        except (ValueError, TypeError):
            self.logger.warning("Invalid log_ids format")
            raise ValueError("The 'log_ids' parameter must be a list of numbers.")

        self.logger.info(f"Deleting {len(log_ids)} log entries")

        query = "DELETE FROM logs WHERE log_id = ?"

        deleted_count = 0
        failed_deletes = []
        for log_id in log_ids:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (log_id,))
                    affected = cursor.rowcount
                    if affected == 0:
                        failed_deletes.append(log_id)
                    else:
                        deleted_count += affected
            except Exception as e:
                self.logger.warning(f"Error deleting log entry {log_id}: {e}")
                failed_deletes.append(log_id)

        self.logger.debug(f"Removed {deleted_count} log entry from the database")
        return deleted_count, failed_deletes

    def find_orphaned_entries(self) -> list[str]:
        """
        Returns a list of entries that exist but aren't listed in their parent's children arrays.
        """
        # Get the root path - you'll need to pass this or access it here
        root_path = self.config.get('root_path')

        # Find entries that exist but aren't listed in their parent's children arrays
        query = """
                SELECT e.path as orphaned_path
                FROM hashtable e
                WHERE e.path != ? -- Exclude root path
                  AND NOT EXISTS (SELECT 1
                                  FROM hashtable parent
                                  WHERE parent.path = SUBSTRING(
                                          e.path, 1,
                                          CHAR_LENGTH(e.path) -
                                          CHAR_LENGTH(SUBSTRING_INDEX(e.path, '/', -1)) - 1)
                                    AND (
                                      JSON_CONTAINS(parent.dirs, JSON_QUOTE(SUBSTRING_INDEX(e.path, '/', -1))) OR
                                      JSON_CONTAINS(parent.files, JSON_QUOTE(SUBSTRING_INDEX(e.path, '/', -1))) OR
                                      JSON_CONTAINS(parent.links, JSON_QUOTE(SUBSTRING_INDEX(e.path, '/', -1)))
                                      ))
                ORDER BY e.path;
                """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (root_path,))
                result = cursor.fetchall()
        except mariadb.Error as e:
            self.logger.error(f"Error fetching orphaned entries: {e}")
            raise Exception(e)

        # Extract just the path strings from the tuples
        return [row[0] for row in result]

    def find_untracked_children(self) -> list[Any]:
        """
        Find children listed by parents but don't exist as entries.

        Returns:
            List of dictionaries with keys: untracked_path, parent_path, child_name, child_type
        """
        query = """
                SELECT DISTINCT CONCAT(
                                        parent.path, '/', child_name.name) as untracked_path,
                                parent.path                                as parent_path,
                                child_name.name                            as child_name,
                                child_types.child_type                     as child_type
                FROM hashtable parent
                         CROSS JOIN JSON_TABLE(
                        JSON_ARRAY(
                                JSON_OBJECT('names', parent.dirs, 'type', 'dirs'),
                                JSON_OBJECT('names', parent.files, 'type', 'files'),
                                JSON_OBJECT('names', parent.links, 'type', 'links')
                        ),
                        '$[*]' COLUMNS (
                            child_list JSON PATH '$.names',
                            child_type VARCHAR(10) PATH '$.type'
                            )
                                    ) as child_types
                         CROSS JOIN JSON_TABLE(
                        child_types.child_list,
                        '$[*]' COLUMNS (
                            name VARCHAR(255) PATH '$'
                            )
                                    ) as child_name
                         LEFT JOIN hashtable existing
                                   ON CONCAT(parent.path, '/', child_name.name) = existing.path
                WHERE existing.path IS NULL
                  AND child_types.child_list IS NOT NULL
                ORDER BY parent.path, child_name.name
                """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                result = cursor.fetchall()
        except mariadb.Error as e:
            self.logger.error(f"Error fetching untracked children: {e}")
            raise Exception(e)

        return [row[0] for row in result]  # Just the untracked paths

    def health_check(self) -> dict[str, bool]:
        """
        Verify that the local database is alive and responding to requests.
        Returns:
            {local_db: True or False} depending on if the database is active and responsive.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1;")
                _ = cursor.fetchall()  # Consume the result
                # If the query executes without an exception, the database is responsive
                self.logger.info("MariaDB database is responsive.")
                return {'local_db': True}

        except Exception as e:
            self.logger.error(f"Error connecting to MariaDB: {e}")

        return {'local_db': False}