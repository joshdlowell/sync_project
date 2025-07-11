from typing import Optional, Dict, Any, List
import json
import pyodbc
from contextlib import contextmanager

from .db_interfaces import RemoteDBConnection
from database_client import logging_config


class RemoteMSSQLConnection(RemoteDBConnection):
    """
    Database access class for hash table operations using Microsoft SQL Server.

    This class provides methods to interact with the MSSQL database
    for storing and retrieving hash information.
    """

    def __init__(self, server=None, database=None, user=None, password=None, port=1433,
                 connection_factory=None, autocommit=True, **kwargs):
        """
        Initialize the database connection configuration.

        Args:
            server: Database server
            database: Database name
            user: Database user
            password: Database password
            port: Database port (default: 1433)
            connection_factory: Optional factory function for creating connections (for testing)
            autocommit: Whether to autocommit transactions (default: True)
        """
        # Build connection string for MSSQL
        conn_str_parts = [
            f"DRIVER={{ODBC Driver 17 for SQL Server}}",
            f"SERVER={server},{port}",
            f"DATABASE={database}",
            f"UID={user}",
            f"PWD={password}",
            "TrustServerCertificate=yes"
        ]

        self.connection_string = ";".join(conn_str_parts)
        self.database = database
        self.autocommit = autocommit
        self.connection_factory = connection_factory or pyodbc.connect
        self.other_args = kwargs

        self.logger = logging_config.configure_logging()

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.
        Yields:
            MSSQL connection object
        Raises:
            Exception: If a database error occurs
        """
        connection = None
        try:
            connection = self.connection_factory(self.connection_string, autocommit=self.autocommit)
            self.logger.debug(f"Database connection established to MSSQL server")
            yield connection
        except Exception as e:
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

                # Convert to dictionary
                columns = [column[0] for column in cursor.description]
                row = cursor.fetchone()

                if row:
                    result = dict(zip(columns, row))
                    self.logger.debug(f"Found record for path: {path}")
                    return result
                else:
                    self.logger.debug(f"No record found for path: {path}")
                    return None
        except Exception as e:
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
                    "SELECT current_hash, dirs, files, links, target_hash FROM hashtable WHERE path = ?",
                    (path,))
                result = cursor.fetchone()
        except Exception as e:
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

        # Determine the final target_hash value
        final_target_hash = target_hash.strip() if target_hash is not None else existing_target_hash

        # Initialize change tracking
        modified, created, deleted = set(), set(), set()

        # EXISTING RECORD build query and calculate changes for existing records
        if result:
            self.logger.debug(f"Updating hash for path: {path}")

            if existing_hash == current_hash:  # Hash unchanged
                self.logger.debug(f"Hash unchanged: {path}")
                query = """
                        UPDATE hashtable
                        SET current_dtg_latest = DATEDIFF(SECOND, '1970-01-01', GETUTCDATE()),
                            target_hash        = ?
                        WHERE path = ?
                        """
                query_params = (final_target_hash, path)
            else:  # Hash changed
                self.logger.info(f"Hash changed: {path}")
                modified.add(path)
                query = """
                        UPDATE hashtable
                        SET prev_hash          = current_hash,
                            prev_dtg_latest    = current_dtg_latest,
                            current_hash       = ?,
                            current_dtg_latest = DATEDIFF(SECOND, '1970-01-01', GETUTCDATE()),
                            current_dtg_first  = current_dtg_latest,
                            dirs               = ?,
                            files              = ?,
                            links              = ?,
                            target_hash        = ?
                        WHERE path = ?
                        """
                query_params = (current_hash, dirs, files, links, final_target_hash, path)

            # Calculate deletions for all field types
            if existing_dirs:
                existing_dirs_list = existing_dirs if existing_dirs else []
                dirs_list = record.get('dirs', [])
                deleted.update(f"{path}/{x}" for x in set(existing_dirs_list) - set(dirs_list))

            if existing_files:
                existing_files_list = existing_files if existing_files else []
                files_list = record.get('files', [])
                deleted.update(f"{path}/{x}" for x in set(existing_files_list) - set(files_list))

            if existing_links:
                existing_links_list = existing_links if existing_links else []
                links_list = record.get('links', [])
                deleted.update(f"{path}/{x}" for x in set(existing_links_list) - set(links_list))

        # NEW RECORD build query and add to created list
        else:
            self.logger.info(f"Inserting new record for path: {path}")
            created.add(path)
            query = """
                    MERGE hashtable AS target
                    USING (SELECT ? AS path, ? AS current_hash, ? AS dirs, ? AS files, ? AS links, ? AS target_hash) AS source
                    ON target.path = source.path
                    WHEN MATCHED THEN
                        UPDATE SET current_hash = source.current_hash,
                                   current_dtg_latest = DATEDIFF(SECOND, '1970-01-01', GETUTCDATE()),
                                   current_dtg_first = current_dtg_latest,
                                   dirs = source.dirs,
                                   files = source.files,
                                   links = source.links,
                                   target_hash = source.target_hash
                    WHEN NOT MATCHED THEN
                        INSERT (path, current_hash, current_dtg_latest, current_dtg_first, dirs, files, links, target_hash)
                        VALUES (source.path, source.current_hash, 
                                DATEDIFF(SECOND, '1970-01-01', GETUTCDATE()),
                                DATEDIFF(SECOND, '1970-01-01', GETUTCDATE()),
                                source.dirs, source.files, source.links, source.target_hash);
                    """
            query_params = (path, current_hash, dirs, files, links, final_target_hash)

        self.logger.debug(f"Prepared data for path {path}: hash={current_hash}")

        # convert lists for sql storage
        self._convert_to_from_json(query_params)
        # Execute query and handle deletions
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, query_params)
                if cursor.rowcount >= 1:
                    self.logger.info(f"Successfully updated database for path: {path}")
        except Exception as e:
            self.logger.error(f"Error inserting/updating record: {e}")
            return False

        # Prune deleted paths from the database
        for deleted_path in deleted:
            deleted.update(self._recursive_delete_hash(deleted_path))
            self.logger.info(f"Removed {len(deleted)} records from the database")

        # Log changes to the database
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
                cursor.execute("SELECT dirs, files, links FROM hashtable WHERE path = ?", (path,))
                result = cursor.fetchone()

                if not result:
                    self.logger.debug(f"No record found for path: {path}")
                    return set()
        except Exception as e:
            self.logger.error(f"Error checking database for existing record: {e}")
            return set()

        # Parse JSON strings back to lists
        dirs = json.loads(result[0]) if result[0] else []
        files = json.loads(result[1]) if result[1] else []
        links = json.loads(result[2]) if result[2] else []

        # Recursively delete children
        for item in [f"{path}/{item}" for item in dirs + files + links]:
            deleted_list.extend(self._recursive_delete_hash(item))

        if self._delete_hash_entry(path):
            deleted_list.append(path)

        return set(deleted_list)

    def _delete_hash_entry(self, path: str) -> bool:
        """Delete a hashtable record by path."""
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
        """Get a single field value for a path from the hashtable."""
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
        except Exception as e:
            self.logger.error(f"Error fetching {field}: {e}")
            return None

    def get_priority_updates(self) -> List[str]:
        """Get directories where target_hash != current_hash."""
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
        except Exception as e:
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
        """Insert a log entry into the database."""
        if 'message' in args_dict.keys() and 'summary_message' not in args_dict.keys():
            args_dict['summary_message'] = args_dict['message']
        if missing_keys := {'summary_message'} - args_dict.keys():
            self.logger.debug(f"Update request missing keys: {missing_keys}")
            raise ValueError(f"{missing_keys} value(s) must be provided")

        params = (
            args_dict.get('site_id', 'local'),
            args_dict.get('log_level', 'INFO'),
            args_dict.get('session_id', None),
            args_dict.get('summary_message'),
            args_dict.get('detailed_message', None)
        )

        query = """INSERT INTO logs (site_id, log_level, session_id, summary_message, detailed_message)
                   OUTPUT INSERTED.log_id
                   VALUES (?, ?, ?, ?, ?)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                result = cursor.fetchone()

                if result:
                    log_id = result[0]
                    self.logger.debug(f"Successfully inserted log entry with ID: {log_id}")
                    return log_id
                else:
                    self.logger.debug("Log entry failed to insert")
                    return None
        except Exception as e:
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

        allowed_columns = {'log_id', 'site_id', 'log_level', 'timestamp', 'session_id'}
        if order_by not in allowed_columns:
            raise ValueError(f"Invalid order_by column. Allowed: {allowed_columns}")

        # Build query
        base_query = "SELECT * FROM logs"
        query_parts = [base_query]
        query_params = []
        where_conditions = []

        # Add WHERE conditions
        if session_id_filter is not None:
            if session_id_filter == 'null':
                where_conditions.append("session_id IS NULL")
            else:
                where_conditions.append("session_id = ?")
                query_params.append(session_id_filter)

        if older_than_days is not None:
            where_conditions.append("timestamp < DATEADD(day, -?, GETDATE())")
            query_params.append(older_than_days)

        if where_conditions:
            query_parts.append("WHERE " + " AND ".join(where_conditions))

        # Add ORDER BY
        query_parts.append(f"ORDER BY {order_by} {order_direction.upper()}")

        # Add OFFSET and FETCH for pagination (MSSQL syntax)
        if offset > 0:
            query_parts.append(f"OFFSET {offset} ROWS")
        else:
            query_parts.append("OFFSET 0 ROWS")

        if limit is not None:
            query_parts.append(f"FETCH NEXT {limit} ROWS ONLY")

        final_query = " ".join(query_parts)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(final_query, query_params)

                # Convert to list of dictionaries
                columns = [column[0] for column in cursor.description]
                result = []
                for row in cursor.fetchall():
                    result.append(dict(zip(columns, row)))

                record_count = len(result)
                filter_info = []
                if session_id_filter is not None:
                    filter_info.append(f"session_id: {session_id_filter}")
                if older_than_days is not None:
                    filter_info.append(f"older than {older_than_days} days")

                filter_str = f" (filters: {', '.join(filter_info)})" if filter_info else ""
                self.logger.debug(f"Retrieved {record_count} log records from database{filter_str}")

                return result

        except Exception as e:
            self.logger.error(f"MSSQL error fetching log records: {e}")
            raise Exception("Error fetching log records from database")

    def consolidate_logs(self) -> bool:
        """Consolidate log entries by session ID."""
        try:
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

        except Exception as e:
            self.logger.error(f"Error during log consolidation: {e}")
            return False

    def _consolidate_logs(self, session_id: str) -> None:
        """Consolidate log entries for a specific session ID."""
        query = "SELECT * FROM logs WHERE session_id = ? ORDER BY log_id"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (session_id,))

                # Convert to list of dictionaries
                columns = [column[0] for column in cursor.description]
                result = []
                for row in cursor.fetchall():
                    result.append(dict(zip(columns, row)))

                if result:
                    self.logger.debug(f"Found {len(result)} entries with session id {session_id}")
                else:
                    self.logger.debug(f"No log entry found with session id {session_id}")
                    return
        except Exception as e:
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
        """Delete log entries by log_id."""
        if not log_ids:
            self.logger.warning("Missing 'log_ids' field")
            raise ValueError("Missing 'log_ids' field")
        if isinstance(log_ids, int):
            log_ids = [log_ids]
        if not isinstance(log_ids, list):
            self.logger.warning("'log_ids' must be an number or list of numbers")
            raise ValueError("The 'log_ids' parameter must be a number or list of numbers.")
        try:
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
                    if cursor.rowcount == 0:
                        failed_deletes.append(log_id)
                    else:
                        deleted_count += cursor.rowcount
            except Exception as e:
                self.logger.warning(f"Error deleting log entry {log_id}: {e}")
                failed_deletes.append(log_id)

        self.logger.debug(f"Removed {deleted_count} log entry from the database")
        return deleted_count, failed_deletes

    def find_orphaned_entries(self) -> list[str]:
        """Find entries that exist but aren't listed in their parent's children arrays."""
        root_path = self.config.get('root_path')  # You'll need to add this to config

        # MSSQL version using JSON functions
        query = """
                SELECT e.path as orphaned_path
                FROM hashtable e
                WHERE e.path != ?
                  AND NOT EXISTS (SELECT 1 
                                  FROM hashtable parent 
                                  WHERE parent.path = LEFT(e.path, LEN(e.path) - 
                                                                   LEN(RIGHT(e.path, CHARINDEX('/', REVERSE(e.path)) - 1)) - 
                                                                   1) 
                                    AND ( 
                                      JSON_VALUE(parent.dirs, '$') LIKE 
                                      '%' + RIGHT(e.path, CHARINDEX('/', REVERSE(e.path)) - 1) + '%' OR 
                                      JSON_VALUE(parent.files, '$') LIKE 
                                      '%' + RIGHT(e.path, CHARINDEX('/', REVERSE(e.path)) - 1) + '%' OR 
                                      JSON_VALUE(parent.links, '$') LIKE 
                                      '%' + RIGHT(e.path, CHARINDEX('/', REVERSE(e.path)) - 1) + '%' 
                                      ))
                ORDER BY e.path
                """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (root_path,))
                result = cursor.fetchall()
        except Exception as e:
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
                SELECT DISTINCT CONCAT(parent.path, '/', child_name.value) as untracked_path,
                                parent.path                                as parent_path,
                                child_name.value                           as child_name,
                                child_types.child_type                     as child_type
                FROM hashtable parent
                         CROSS JOIN (SELECT 'dirs' as child_type, parent.dirs as child_list
                                     FROM hashtable parent
                                     WHERE parent.dirs IS NOT NULL
                                     UNION ALL
                                     SELECT 'files' as child_type, parent.files as child_list
                                     FROM hashtable parent
                                     WHERE parent.files IS NOT NULL
                                     UNION ALL
                                     SELECT 'links' as child_type, parent.links as child_list
                                     FROM hashtable parent
                                     WHERE parent.links IS NOT NULL) as child_types
                    CROSS APPLY OPENJSON(child_types.child_list) as child_name
                         LEFT JOIN hashtable existing
                ON CONCAT(parent.path, '/', child_name.value) = existing.path
                WHERE existing.path IS NULL
                  AND child_types.child_list IS NOT NULL
                ORDER BY parent.path, child_name.value
                """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    result = cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error fetching untracked children: {e}")
            raise Exception(e)

        return [row[0] for row in result]  # Just the untracked paths

    def health_check(self) -> dict[str, bool]:
        """Verify that the database is alive and responding."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                self.logger.info("MSSQL database is responsive.")
                return {'local_db': True}
        except Exception as e:
            self.logger.error(f"Error connecting to MSSQL: {e}")
        return {'local_db': False}
