from typing import Optional, Dict, Any, List
import time
import json

from .db_interfaces import RemoteDBConnection
from database_client import logging_config


class RemoteInMemoryConnection(RemoteDBConnection):
    """
    In-memory database implementation for hash table operations.

    This class provides methods to interact with local data structures
    for storing and retrieving hash information, mimicking the MySQL implementation
    for testing and contingency scenarios.
    """

    def __init__(self, host=None, database=None, user=None, password=None, port=3306,
                 connection_factory=None, autocommit=True, raise_on_warnings=True, **kwargs):
        """
        Initialize the in-memory database with empty data structures.
        """
        # Store config for compatibility (even though not used)
        self.config = {
            'host': host or 'localhost',
            'database': database or 'memory',
            'user': user or 'memory_user',
            'password': password or '',
            'port': port,
            'autocommit': autocommit,
            'raise_on_warnings': raise_on_warnings
        }
        self.database = database or 'memory'
        self.connection_factory = connection_factory
        self.other_args = kwargs

        # Main hashtable storage - keyed by path
        self.hashtable = {}

        # Logs storage - list of log entries with auto-incrementing IDs
        self.logs = []
        self._next_log_id = 1

        self.logger = logging_config.configure_logging()

        self.logger.debug(f"In-memory database connection established to {self.config['host']}")

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
            record = self.hashtable.get(path)
            if record:
                self.logger.debug(f"Found record for path: {path}")
                # Return a copy to prevent external modification
                return record.copy()
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
        existing_record = self.hashtable.get(path)
        current_time = int(time.time())

        # Initialize change tracking
        modified, created, deleted = set(), set(), set()

        if existing_record:
            # Determine the final target_hash value
            existing_target_hash = existing_record.get('target_hash')
            final_target_hash = target_hash.strip() if target_hash is not None else existing_target_hash

            # Calculate deletions for all field types
            for field_name, existing_list, request_list in [
                ('dirs', existing_record.get('dirs', []), dirs),
                ('files', existing_record.get('files', []), files),
                ('links', existing_record.get('links', []), links)
            ]:
                deleted.update(f"{path}/{x}" for x in set(existing_list) - set(request_list))

            if existing_record['current_hash'] == current_hash:  # Hash unchanged
                self.logger.debug(f"Hash unchanged: {path}")
                existing_record['current_dtg_latest'] = current_time
                existing_record['target_hash'] = final_target_hash
            else:  # Hash changed
                self.logger.info(f"Hash changed: {path}")
                modified.add(path)

                # Move current to previous
                existing_record['prev_hash'] = existing_record['current_hash']
                existing_record['prev_dtg_latest'] = existing_record['current_dtg_latest']

                # Update current
                existing_record['current_hash'] = current_hash
                existing_record['current_dtg_latest'] = current_time
                existing_record['current_dtg_first'] = current_time
                existing_record['dirs'] = dirs
                existing_record['files'] = files
                existing_record['links'] = links
                existing_record['target_hash'] = final_target_hash

        else:  # New record
            self.logger.info(f"Inserting new record for path: {path}")
            created.add(path)

            self.hashtable[path] = {
                'path': path,
                'current_hash': current_hash,
                'current_dtg_latest': current_time,
                'current_dtg_first': current_time,
                'dirs': dirs,
                'files': files,
                'links': links,
                'target_hash': target_hash.strip() if target_hash is not None else None,
                'prev_hash': None,
                'prev_dtg_latest': None
            }

        self.logger.debug(f"Prepared data for path {path}: hash={current_hash}")
        self.logger.debug(f"dirs={len(record.get('dirs', []))}")
        self.logger.debug(f"files={len(record.get('files', []))}")
        self.logger.debug(f"links={len(record.get('links', []))}")

        self.logger.info(f"Successfully updated database for path: {path}")

        # Prune deleted paths from the database
        for deleted_path in deleted:
            deleted.update(self._recursive_delete_hash(deleted_path))
            if deleted:
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
        self.logger.debug(f"Changes: modified={len(modified)}, created={len(created)}, deleted={len(deleted)}")

        return True

    def _recursive_delete_hash(self, path: str) -> set[str]:
        """Delete a hash record and all its children recursively."""
        deleted_list = []

        # Get existing record
        existing_record = self.hashtable.get(path)
        if not existing_record:
            self.logger.debug(f"No record found for path: {path}")
            return set()

        # Combine list fields and call recursive delete on each one
        dirs = existing_record.get('dirs', [])
        files = existing_record.get('files', [])
        links = existing_record.get('links', [])

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
        try:
            if path in self.hashtable:
                del self.hashtable[path]
                return True
            return False
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

        try:
            record = self.hashtable.get(path)
            if record:
                self.logger.debug(f"Found {field} for path: {path}")
                return record.get(field)
            else:
                self.logger.debug(f"No {field} found for path: {path}")
                return None
        except Exception as e:
            self.logger.error(f"Error fetching {field}: {e}")
            return None

    def get_priority_updates(self) -> List[str]:
        """
        Get directories where target_hash != current_hash, prioritizing the shallowest paths
        to avoid redundant updates of nested directories.
        Returns:
            List of directory paths needing updates, deduplicated by hierarchy
        """
        try:
            # Find all paths where target_hash exists and differs from current_hash
            paths = []
            for path, record in self.hashtable.items():
                target_hash = record.get('target_hash')
                if target_hash and target_hash != record['current_hash']:
                    paths.append(path)

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

        except Exception as e:
            self.logger.error(f"Error fetching priority updates: {e}")
            return []

    def put_log(self, args_dict: dict) -> int | None:
        """
        Insert a log entry into the local_database.
        Returns:
            log_id number (int) if the log entry was inserted, None if an error occurred
        Raises:
            ValueError: If required parameters are not provided
        """
        try:
            # Validate required keys and data formatting
            if 'message' in args_dict.keys() and 'summary_message' not in args_dict.keys():
                args_dict['summary_message'] = args_dict['message']
            if missing_keys := {'summary_message'} - args_dict.keys():
                self.logger.debug(f"Update request missing keys: {missing_keys}")
                raise ValueError(f"{missing_keys} value(s) must be provided")

            # Extract parameters with defaults
            log_entry = {
                'log_id': self._next_log_id,
                'site_id': args_dict.get('site_id', 'local'),
                'log_level': args_dict.get('log_level', 'INFO'),
                'session_id': args_dict.get('session_id', None),
                'summary_message': args_dict.get('summary_message'),
                'detailed_message': args_dict.get('detailed_message', None),
                'timestamp': int(time.time())
            }

            # Add to logs and increment ID counter
            self.logs.append(log_entry)
            log_id = self._next_log_id
            self._next_log_id += 1

            self.logger.debug(f"Successfully inserted log entry with ID: {log_id}")
            return log_id

        except Exception as e:
            self.logger.error(f"Error inserting log entry: {e}")
            return None

    def get_logs(self, limit: Optional[int] = None, offset: int = 0,
                 order_by: str = "timestamp", order_direction: str = "DESC",
                 session_id_filter: Optional[str] = None,
                 older_than_days: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get log entries from database.
        """
        try:
            # Input validation
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer")

            if not isinstance(offset, int) or offset < 0:
                raise ValueError("Offset must be a non-negative integer")

            if order_direction.upper() not in ('ASC', 'DESC'):
                raise ValueError("Order direction must be 'ASC' or 'DESC'")

            if older_than_days is not None and (not isinstance(older_than_days, int) or older_than_days <= 0):
                raise ValueError("older_than_days must be a positive integer")

            # Validate order_by column
            allowed_columns = {'log_id', 'site_id', 'log_level', 'timestamp', 'session_id'}
            if order_by not in allowed_columns:
                raise ValueError(f"Invalid order_by column. Allowed: {allowed_columns}")

            # Start with all logs
            result = [log.copy() for log in self.logs]

            # Apply session_id filter
            if session_id_filter is not None:
                if session_id_filter == 'null':
                    result = [log for log in result if log.get('session_id') is None]
                else:
                    result = [log for log in result if log.get('session_id') == session_id_filter]

            # Apply date filter
            if older_than_days is not None:
                cutoff_time = int(time.time()) - (older_than_days * 24 * 60 * 60)
                result = [log for log in result if log.get('timestamp', 0) < cutoff_time]

            # Sort by specified column and direction
            reverse_order = order_direction.upper() == 'DESC'
            result.sort(key=lambda x: x.get(order_by, 0), reverse=reverse_order)

            # Apply offset and limit
            if offset > 0:
                result = result[offset:]

            if limit is not None:
                result = result[:limit]

            # More informative logging
            record_count = len(result)
            filter_info = []
            if session_id_filter is not None:
                filter_info.append(f"session_id: {session_id_filter}")
            if older_than_days is not None:
                filter_info.append(f"older than {older_than_days} days")

            filter_str = f" (filters: {', '.join(filter_info)})" if filter_info else ""
            self.logger.debug(f"Retrieved {record_count} log records from database{filter_str}")

            return result

        except ValueError:
            raise
        except Exception as e:
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
            session_ids = list(set(log.get('session_id') for log in self.logs
                                   if log.get('session_id') is not None))

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
        """
        Consolidate log entries for a specific session ID.
        Args:
            session_id: The session ID to consolidate logs for
        """
        # Get all entries for this session_id
        session_logs = [log for log in self.logs if log.get('session_id') == session_id]

        if not session_logs:
            self.logger.debug(f"No log entry found with session id {session_id}")
            return

        self.logger.debug(f"Found {len(session_logs)} entries with session id {session_id}")

        # Group entries by log level
        log_level_groups = {}
        session_type = None
        has_finish_session = False

        for log_entry in session_logs:
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

                except json.JSONDecodeError:
                    self.logger.debug(f"Not a JSON encoded log entry")
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

    def delete_log_entries(self, log_ids: list[int]) -> tuple[int, list]:
        """
        Delete log_entries by log_id.
        Args:
            log_ids: List of log_ids to delete
        Returns:
            Tuple of (deleted_count, failed_deletes)
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

        deleted_count = 0
        failed_deletes = []

        for log_id in log_ids:
            try:
                # Find and remove the log entry
                for i, log_entry in enumerate(self.logs):
                    if log_entry['log_id'] == log_id:
                        del self.logs[i]
                        deleted_count += 1
                        break
                else:
                    failed_deletes.append(log_id)
            except Exception as e:
                self.logger.warning(f"Error deleting log entry {log_id}: {e}")
                failed_deletes.append(log_id)

        self.logger.debug(f"Removed {deleted_count} log entries from the database")
        return deleted_count, failed_deletes

    def find_orphaned_entries(self) -> list[str]:
        """
        Returns a list of entries that exist but aren't listed in their parent's children arrays.
        """
        root_path = self.config.get('root_path', '/')
        orphaned = []

        for path in self.hashtable.keys():
            if path == root_path:
                continue

            # Find parent path
            parent_path = path.rsplit('/', 1)[0] if '/' in path else root_path
            child_name = path.rsplit('/', 1)[1] if '/' in path else path

            # Check if parent exists
            parent_record = self.hashtable.get(parent_path)
            if not parent_record:
                orphaned.append(path)
                continue

            # Check if child is listed in parent's arrays
            all_children = (parent_record.get('dirs', []) +
                            parent_record.get('files', []) +
                            parent_record.get('links', []))

            if child_name not in all_children:
                orphaned.append(path)

        return sorted(orphaned)

    def find_untracked_children(self) -> list[str]:
        """
        Find children listed by parents but don't exist as entries.
        Returns:
            List of untracked child paths
        """
        untracked = []

        for path, record in self.hashtable.items():
            # Check all child types
            for child_type in ['dirs', 'files', 'links']:
                children = record.get(child_type, [])
                for child_name in children:
                    child_path = f"{path}/{child_name}"
                    if child_path not in self.hashtable:
                        untracked.append(child_path)

        return sorted(untracked)

    def health_check(self) -> dict[str, bool]:
        """
        Verify that the local database is alive and responding to requests.
        Returns:
            {local_db: True or False} depending on if the database is active and responsive.
        """
        try:
            # For in-memory implementation, just verify the data structures exist
            if hasattr(self, 'hashtable') and hasattr(self, 'logs'):
                self.logger.info("In-memory database is responsive.")
                return {'local_db': True}
            else:
                self.logger.error("In-memory database structures not found.")
                return {'local_db': False}
        except Exception as e:
            self.logger.error(f"Error checking in-memory database: {e}")
            return {'local_db': False}

    # Additional utility methods for testing
    def clear_all_data(self):
        """Clear all data from the in-memory database. Useful for testing."""
        self.hashtable.clear()
        self.logs.clear()
        self._next_log_id = 1
        self.logger.info("All data cleared from in-memory database")

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the in-memory database."""
        return {
            'hashtable_records': len(self.hashtable),
            'log_entries': len(self.logs),
            'next_log_id': self._next_log_id
        }