import json
from time import sleep
from collections import deque

from .implementations import RestClientStorage, MerkleTreeImplementation
from squishy_coordinator import config, logger


class CoordinatorService:
    """Main service for Coordinator functionality"""
    def __init__(self,
                 rest_storage: RestClientStorage,
                 core_rest_storage: RestClientStorage,
                 integrity_service: MerkleTreeImplementation):
        self.rest_storage = rest_storage
        self.core_rest_storage = core_rest_storage
        self.integrity_service = integrity_service

    def is_healthy(self) -> bool:
        for i in range(5):
            health = self.rest_storage.get_health()
            if health.get('status', '').lower() == 'healthy':
                return True
            logger.warning("REST and/or database service are not healthy...")
            sleep(5)
        return False

    def consolidate_logs(self) -> bool:
        return self.rest_storage.consolidate_logs()

    def ship_logs_to_core(self) -> bool:
        # Verify site_id is configured before sending logs
        if not config.get('site_name', None).strip():
            logger.error("Cannot ship logs: no site name configured")
            return False

        # Pull consolidated logs and post them to the core logs
        log_entries = self.rest_storage.collect_logs_for_shipping()
        log_ids = []
        if config.is_core:
            log_func = self.rest_storage.put_log
        else:
            log_func = self.core_rest_storage.put_log
        for entry in log_entries if log_entries else []:
            result = log_func(
                site_id=config.get('site_name', None),
                log_level=entry.get('log_level'),
                timestamp=entry.get('timestamp'),
                message=entry.get('summary_message'),
                detailed_message=entry.get('detailed_message')
            )
            if result > 0:
                log_ids.append(entry.get('log_id'))

        logger.debug(f"Log entries: {log_ids}")
        if len(log_ids) < len(log_entries):
            logger.warning(f"Not all log entries were shipped to core. Failed to ship {len(log_entries) - len(log_ids)} entries.")

        # Delete log entries that shipped
        logger.info(f"Deleting {len(log_ids)} log entries that shipped from local storage.")
        ship_success, fail_list = self.rest_storage.delete_log_entries(log_ids)

        if not ship_success:
            logger.error(f"Failed to delete {len(fail_list)} shipped log entries from local storage.")

        # Delete log entries older than 90 days
        logger.info(f"Deleting log entries older than 90 days from local storage.")
        log_entries = self.rest_storage.collect_logs_older_than(90)
        log_ids = [entry.get('log_id') for entry in log_entries]
        if len(log_ids) > 0:
            old_success, fail_list = self.rest_storage.delete_log_entries(log_ids)
            if not old_success:
                logger.error(f"Failed to delete {len(fail_list)} old log entries from local storage.")

        return True

    def verify_database_integrity(self):
        """
        Comprehensive verification using SQL queries.
        Returns a tuple of orphaned entries, untracked children.
        """
        # DB entries that exist but parent doesn't list them
        orphans = self.rest_storage.find_orphaned_entries()
        if len(orphans) > 0:
            logger.warning(f"Found orphaned entries: {orphans}")
            self.put_log_entry("Found orphaned entries", json.dumps({'orphans':orphans}), "WARNING")
        else:
            logger.info("No orphaned entries found")

        # DB entries that don't exist but a parent claims them
        untracked = self.rest_storage.find_untracked_children()
        if len(untracked) > 0:
            logger.warning(f"Found untracked children: {untracked}")
            self.put_log_entry("Found untracked children", json.dumps({'untracked':untracked}), "WARNING")
        else:
            logger.info("No untracked children found")

    # def get_database_counts(self):
    #     """
    #     Returns counts of directories, files, links, and total records.
    #     Uses the already-fetched data if available, otherwise fetches it.
    #     """
    #     # You could cache the all_entries data if called frequently
    #     all_entries = self.rest_storage.get_ get_all_paths_and_children()
    #
    #     dir_count = 0
    #     file_count = 0
    #     link_count = 0
    #
    #     for parent_path, children in all_entries.items():
    #         dir_count += len(children['dirs'])
    #         file_count += len(children['files'])
    #         link_count += len(children['links'])
    #
    #     return {
    #         'directories': dir_count,
    #         'files': file_count,
    #         'links': link_count,
    #         'total_records': len(all_entries),
    #         'total_children': dir_count + file_count + link_count
    #     }

    def verify_hash_status(self) -> list[tuple[str, str, str]]:
        """
        Compare local and core file trees, returning differences as tuples of:
        (path, local_hash, core_hash)
        - Missing local files: (path, None, core_hash)
        - Additional local files: (path, local_hash, None)
        - Hash mismatches: (path, local_hash, core_hash)
        """
        differences = []
        # Use deque for efficient FIFO operations
        path_queue = deque([config.get('root_path')])
        processed_paths = set()  # Avoid infinite loops

        while path_queue:
            current_path = path_queue.popleft()

            # Skip if already processed (safety check)
            if current_path in processed_paths:
                continue
            processed_paths.add(current_path)

            # Get hashes from both sources
            local_hash = self.rest_storage.get_single_hash(current_path)
            core_hash = self.core_rest_storage.get_single_hash(current_path)

            # Handle different scenarios
            if local_hash is None and core_hash is None:
                # Both missing - shouldn't happen but skip if it does
                continue
            elif local_hash is None:
                # Missing from local
                self._log_difference("Missing local entry for core path", {'missing_file': current_path})
                differences.append((current_path, None, core_hash))
                # Add children from core to queue
                self._add_children_to_queue(current_path, path_queue, source='core')
            elif core_hash is None:
                # Additional in local (not in core)
                self._log_difference("Additional local entry not in core", {'extra_file': current_path})
                differences.append((current_path, local_hash, None))
                # Add children from local to queue
                self._add_children_to_queue(current_path, path_queue, source='local')
            elif local_hash != core_hash:
                # Hash mismatch
                self._log_difference("Local entry does not match core for path", {'hash_mismatch':current_path})
                differences.append((current_path, local_hash, core_hash))
                # Add children from both sources to queue
                self._add_children_to_queue(current_path, path_queue, source='both')
            else:
                # Hashes match - this search branch is complete
                continue

        return differences

    def log_and_create_updates(self, updates: list[tuple[str, str, str]]) -> list[dict[str, str]]:
        """
        Update local target hash values based on differences between local and core hashes.
        Create and return a list of dicts containing hash differences for passing to the core
        Args:
            updates: a list of tuples (path, local_hash, core_hash)
            - Missing local files: (path, None, core_hash)
            - Additional local files: (path, local_hash, None)
            - Hash mismatches: (path, local_hash, core_hash)
        returns:
            list of dicts containing paths as keys and local hash values as values
        """
        core_path_data = []
        for path, local_hash, core_hash in updates:
            if core_hash is None and local_hash is None:
                # Shouldn't happen
                continue

            elif local_hash and core_hash is None:  # Additional local files: (path, local_hash, None)
                # Core is not tracking this file
                self.update_target_hash(path, local_hash, '0')

            elif local_hash is None and core_hash:  # Missing local files: (path, None, core_hash)
                core_path_data.append({'path': path, 'current_hash': '0'})  # Placeholder hash for non-existent file
                # Parent hash has already been marked for priority update

            else:  # Hash mismatches: (path, local_hash, core_hash)
                core_path_data.append({'path': path, 'current_hash': local_hash})
                self.update_target_hash(path, local_hash, core_hash)

        return core_path_data

    def send_status_to_core(self, updates: list[dict[str, str]]) -> bool:
        """
        Send hash sync status updates to the core.
        Args:
            updates: a list of dicts with the keys: path and current_hash
        Returns:
            True if the update was sent, False otherwise
        """
        return self.core_rest_storage.put_remote_hash_status(updates, config.get('site_name'))

    def _add_children_to_queue(self, path: str, path_queue: deque, source: str = 'both') -> None:
        """
        Add children of the given path to the queue.

        Args:
            path: The parent path
            path_queue: The queue to add children to
            source: 'local', 'core', or 'both' - determines which storage to query
        """
        children = set()

        if source in ['local', 'both']:
            local_entry = self.rest_storage.get_hashtable(path)
            if local_entry:
                for category in ['dirs', 'files', 'links']:
                    children.update(local_entry.get(category, []))

        if source in ['core', 'both']:
            core_entry = self.core_rest_storage.get_hashtable(path)
            if core_entry:
                for category in ['dirs', 'files', 'links']:
                    children.update(core_entry.get(category, []))

        # Add all unique children to queue
        for child in children:
            child_path = f"{path}/{child}".replace('//', '/')  # Handle double slashes
            path_queue.append(child_path)

    def _log_difference(self, message: str, data: dict) -> None:
        """Helper method to log differences consistently"""
        logger.info(f"{message}: {data}")
        self.integrity_service.put_log_w_session(
                                                message=message,
                                                detailed_message=json.dumps(data)
                                                )

    def update_target_hash(self, path: str, current_hash: str, target_hash: str) -> int:
        """
        Put a new target hash into the database.

        Returns:
            int representing the number of updates sent to the REST API that were successful"""
        return self.rest_storage.put_hashtable({
            path: {
                'path': path,
                'current_hash': current_hash,
                'target_hash': target_hash
            }})

    def get_priority_updates(self) -> list[str]:
        """Get the list of database entries where the current hash does not match the target hash."""
        return self.rest_storage.get_priority_updates() or []

    def get_pipeline_updates(self) -> list[str]:
        """Get the list of updates that have been approved by the continuous delivery (CD) pipeline."""
        updates = self.rest_storage.get_pipeline_updates() or []
        update_paths = []
        for update in updates:
            update_paths.append(update['path'])
        return update_paths

    def recompute_hashes(self, path_list: list[str]) -> list[tuple[str, str]]:

        recomputed = []
        for path in path_list:
            recomputed.append((path, self.integrity_service.compute_merkle_tree(path)))

        return recomputed

    def put_log_entry(self, message: str, detailed_message: str=None, log_level: str=None) -> int:
        """Put a log entry into the database. Returns the ID of the new entry."""
        return self.integrity_service.put_log_w_session(message=message, detailed_message=detailed_message, log_level=log_level)
