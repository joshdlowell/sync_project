from typing import Optional, Dict, Any, List
import time
import hashlib
from squishy_REST_API.DB_connections.local_DB_interface import DBConnection
from squishy_REST_API.configs.config import logger


class LocalMemoryConnection(DBConnection):
    """
    In-memory database implementation for hash table operations.

    This class provides methods to interact with local data structures
    for storing and retrieving hash information, mimicking the MySQL implementation
    for testing and contingency scenarios.
    """

    def __init__(self):
        """
        Initialize the in-memory database with empty data structures.
        """
        # Main hashtable storage - keyed by path
        self.hashtable = {}

        # Logs storage - list of log entries with auto-incrementing IDs
        self.logs = []
        self._next_log_id = 1

        logger.debug("Local memory database initialized")

    def _generate_hashed_path(self, path: str) -> str:
        """
        Generate SHA256 hash of path to mimic MySQL's computed column.

        Args:
            path: The path to hash

        Returns:
            SHA256 hash of the path
        """
        return hashlib.sha256(path.encode()).hexdigest()

    def insert_or_update_hash(self, record: dict[str, Any]) -> Optional[Dict[str, list]]:
        """
        Insert new record or update existing one.

        Args:
            record: Dict of hashtable column:value keypairs to be added to the db

        Returns:
            Dictionary with modified, created, and deleted paths, or None if an error occurred

        Raises:
            ValueError: If required parameters are not provided
        """
        # Validate required keys
        if missing_keys := {'path', 'current_hash'} - set(record.keys()):
            logger.debug(f"Received update request missing keys: {missing_keys}")
            raise ValueError(f"{missing_keys} value(s) must be provided")

        path = record['path'].strip()
        current_hash = record['current_hash'].strip()
        logger.debug(f"Inserting or updating hash for path: {path}")

        # Get existing record
        existing_record = self.hashtable.get(path)
        current_time = int(time.time())

        # Format list fields
        format_list = lambda field_list: ','.join(x.strip() for x in field_list) if field_list else None
        dirs = format_list(record.get('dirs'))
        links = format_list(record.get('links'))
        files = format_list(record.get('files'))

        # Initialize change tracking
        modified, created, deleted = set(), set(), set()

        # Calculate changes for existing records
        if existing_record:
            parse_existing = lambda field: [x.strip() for x in field.split(",")] if field else []

            # Calculate additions and deletions for all field types
            for field_name, existing_str, request_list in [
                ('dirs', existing_record.get('dirs'), record.get('dirs', [])),
                ('files', existing_record.get('files'), record.get('files', [])),
                ('links', existing_record.get('links'), record.get('links', []))
            ]:
                existing_list = parse_existing(existing_str)
                # created.update(f"{path}/{x}" for x in set(request_list) - set(existing_list))
                deleted.update(f"{path}/{x}" for x in set(existing_list) - set(existing_list))

        logger.debug(f"Prepared data for path {path}: hash={current_hash}, "
                     f"dirs={len(record.get('dirs', []))}, files={len(record.get('files', []))}, "
                     f"links={len(record.get('links', []))}")

        if not existing_record:  # New record
            logger.info(f"Inserting new record into database for path: {path}")
            created.add(path)

            self.hashtable[path] = {
                'path': path,
                'hashed_path': self._generate_hashed_path(path),
                'current_hash': current_hash,
                'current_dtg_latest': current_time,
                'current_dtg_first': current_time,
                'target_hash': record.get('target_hash'),
                'prev_hash': None,
                'prev_dtg_latest': None,
                'dirs': dirs,
                'files': files,
                'links': links
            }

        elif existing_record['current_hash'] == current_hash:  # Hash unchanged
            logger.info(f"Found existing record for path, hash unchanged: {path}")
            existing_record['current_dtg_latest'] = current_time

        else:  # Hash changed
            logger.info(f"Found existing record for path, hash has changed: {path}")
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

        logger.info(f"Successfully updated database for path: {path}")

        # Prune deleted paths from the database
        for del_path in deleted:
            self._delete_hash_entry(del_path)

        changes = {field: sorted(paths) for field, paths in
                   [('modified', modified), ('created', created), ('deleted', deleted)]}

        logger.debug(f"Changes: modified={len(modified)}, created={len(created)}, deleted={len(deleted)}")
        return changes

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
                logger.info(f"Removed 1 record from the database: {path}")
                return True
            else:
                logger.info(f"Removed 0 records from the database: {path}")
                return False

        except Exception as e:
            logger.error(f"Error deleting hash entry for path {path}: {e}")
            return False

    def get_hash_record(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get a single record by path.

        Args:
            path: Path to retrieve

        Returns:
            Dictionary with record data or None if not found or an error occurred
        """
        try:
            record = self.hashtable.get(path)
            if record:
                logger.debug(f"Found record for path: {path}")
                # Return a copy to prevent external modification
                return record.copy()
            else:
                logger.debug(f"No record found for path: {path}")
                return None

        except Exception as e:
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
        try:
            record = self.hashtable.get(path)
            if record:
                logger.debug(f"Found hash for path: {path}")
                return record['current_hash']
            else:
                logger.debug(f"No hash found for path: {path}")
                return None

        except Exception as e:
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
        try:
            record = self.hashtable.get(path)
            if record:
                logger.debug(f"Found timestamp for path: {path}")
                return record['current_dtg_latest']
            else:
                logger.debug(f"No timestamp found for path: {path}")
                return None

        except Exception as e:
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
        # Filter out None timestamps and sort
        valid_items = [(ts, path) for ts, path in timestamped_items if ts is not None]
        ordered_items = [item_path for _, item_path in sorted(valid_items)]

        # Calculate number of items to return
        update_num = max(1, min(int(len(ordered_items) * percent / 100), len(ordered_items)))

        logger.info(f"Returning the {update_num} oldest items")
        return ordered_items[:update_num]

    def get_priority_updates(self) -> List[str]:
        """
        Get directories where target_hash != current_hash, prioritizing shallowest paths
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
                logger.debug("All hashes in the db are in sync")
                return []

            # Sort by depth and remove paths covered by shallower ones
            paths = sorted(set(paths), key=lambda x: x.count('/'))

            priority = []
            for path in paths:
                # Skip if already covered by existing shallower path
                if not any(path.startswith(existing + '/') for existing in priority):
                    priority.append(path)

            return priority

        except Exception as e:
            logger.error(f"Error fetching priority updates: {e}")
            return []

    def put_log(self, args_dict: dict) -> int | None:
        """
        Put log entry into database.

        This method inserts log entries into the local_database.

        Returns:
            log_id number (int) if the log entry was inserted, None if an error occurred
        """
        try:
            # Check for required parameters
            if not args_dict.get('summary_message'):
                logger.debug("No summary message provided, skipping log entry")
                return None
            # Check site_id length requirement (if included)
            if args_dict.get('site_id') and len(args_dict.get('site_id')) > 5 :
                logger.debug("site_id must be less than 5 characters, skipping log entry")
                return None

            # Create log entry
            log_entry = {
                'log_id': self._next_log_id,
                'site_id': args_dict.get('site_id', 'local'),
                'log_level': args_dict.get('log_level', 'INFO'),
                'timestamp': int(time.time()),
                'summary_message': args_dict.get('summary_message'),
                'detailed_message': args_dict.get('detailed_message')
            }

            # Add to logs and increment ID counter
            self.logs.append(log_entry)
            log_id = self._next_log_id
            self._next_log_id += 1

            logger.debug(f"Entry inserted into logs table: {log_id}")
            return log_id

        except Exception as e:
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
        try:
            # Input validation
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer")

            if not isinstance(offset, int) or offset < 0:
                raise ValueError("Offset must be a non-negative integer")

            if order_direction.upper() not in ('ASC', 'DESC'):
                raise ValueError("Order direction must be 'ASC' or 'DESC'")

            # Validate order_by column
            allowed_columns = {'log_id', 'site_id', 'log_level', 'timestamp'}
            if order_by not in allowed_columns:
                raise ValueError(f"Invalid order_by column. Allowed: {allowed_columns}")

            # Make a copy of logs to avoid modifying original
            result = [log.copy() for log in self.logs]

            # Sort by specified column and direction
            reverse_order = order_direction.upper() == 'DESC'
            result.sort(key=lambda x: x.get(order_by, 0), reverse=reverse_order)

            # Apply offset and limit
            if offset > 0:
                result = result[offset:]

            if limit is not None:
                result = result[:limit]

            record_count = len(result)
            logger.debug(f"Retrieved {record_count} log records from database")

            return result

        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
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
        try:
            # Find and remove the log entry with matching log_id
            for i, log_entry in enumerate(self.logs):
                if log_entry['log_id'] == log_id:
                    del self.logs[i]
                    logger.info(f"Removed 1 log entry from the database")
                    return True

            logger.info(f"Removed 0 log entries from the database")
            return False

        except Exception as e:
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
            # For in-memory implementation, just verify the data structures exist
            if hasattr(self, 'hashtable') and hasattr(self, 'logs'):
                logger.info("Local memory database is responsive.")
                return True
            else:
                logger.error("Local memory database structures not found.")
                return False

        except Exception as e:
            logger.error(f"Error checking local memory database: {e}")
            return False

    # Additional utility methods for testing and debugging
    def clear_all_data(self):
        """Clear all data from the in-memory database. Useful for testing."""
        self.hashtable.clear()
        self.logs.clear()
        self._next_log_id = 1
        logger.info("All data cleared from local memory database")

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the in-memory database."""
        return {
            'hashtable_records': len(self.hashtable),
            'log_entries': len(self.logs),
            'next_log_id': self._next_log_id
        }