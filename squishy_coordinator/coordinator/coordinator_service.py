import json
from typing import Dict, Optional, Any, List
from time import sleep
from collections import deque

from .interfaces import PersistentStorageInterface

from integrity_check.merkle_tree_service import MerkleTreeService
# from .validators import PathValidator
# from .tree_walker import DirectoryTreeWalker
# from .file_hasher import FileHasher
from squishy_coordinator import config, logger


class CoordinatorService:
    """Main service for Coordinator functionality"""

    def __init__(self,
                 local_storage: PersistentStorageInterface,
                 core_storage: PersistentStorageInterface,
                 integrity_service: MerkleTreeService,
                 # tree_walker: DirectoryTreeWalker,
                 # file_hasher: FileHasher,
                 # path_validator: PathValidator):
                 ):
        # self.hash_storage = hash_storage
        # self.tree_walker = tree_walker
        # self.file_hasher = file_hasher
        # self.path_validator = path_validator
        self.local_storage = local_storage
        self.core_storage = core_storage
        self.integrity_service = integrity_service

    def consolidate_logs(self) -> bool:
        return self.local_storage.consolidate_logs()

    def ship_logs_to_core(self) -> bool:
        log_entries = self.local_storage.collect_logs_to_ship()
        # ship them
        log_ids = []
        for entry in log_entries if log_entries else []:
            result = self.core_storage.put_log(
                site_id=entry.get('site_id'),
                log_level=entry.get('log_level'),
                timestamp=entry.get('timestamp'),
                message=entry.get('message'),
                detailed_message=entry.get('detailed_message')
            )
            if result:
                log_ids.append(result)

        if len(log_ids) < len(log_entries):
            logger.warning(f"Not all log entries were shipped to core. Failed to ship {len(log_entries) - len(log_ids)} entries.")

        # Delete log entries that shipped
        logger.info(f"Deleting {len(log_ids)} log entries that shipped from local storage.")
        success, fail_list = self.local_storage.delete_log_entries(log_ids)

        if not success:
            logger.error(f"Failed to delete {len(fail_list)} shipped log entries from local storage.")

        # Delete log entries older than 90 days
        logger.info(f"Deleting log entries older than 90 days from local storage.")
        log_entries = self.local_storage.collect_logs_older_than(90)
        success, fail_list = self.local_storage.delete_log_entries(fail_list + [entry.get('id') for entry in log_entries])
        if not success:
            logger.error(f"Failed to delete {len(fail_list)} old log entries from local storage.")

    def verify_database_integrity(self):
        """
        Comprehensive verification using SQL queries.
        Returns a tuple of orphaned entries, untracked children.
        """

        orphans = self.local_storage.find_orphaned_entries()
        if len(orphans) > 0:
            logger.warning(f"Found orphaned entries: {orphans}")
            self.put_log_entry("Found orphaned entries", json.dumps({'orphans':orphans}), "WARNING")
        else:
            logger.info("No orphaned entries found")

        untracked = self.local_storage.find_untracked_children()
        if len(untracked) > 0:
            logger.warning(f"Found untracked children: {untracked}")
            self.put_log_entry("Found untracked children", json.dumps({'untracked':untracked}), "WARNING")
        else:
            logger.info("No untracked children found")

    def get_database_counts(self):
        """
        Returns counts of directories, files, links, and total records.
        Uses the already-fetched data if available, otherwise fetches it.
        """
        # You could cache the all_entries data if called frequently
        all_entries = self.local_storage.get_all_paths_and_children()

        dir_count = 0
        file_count = 0
        link_count = 0

        for parent_path, children in all_entries.items():
            dir_count += len(children['dirs'])
            file_count += len(children['files'])
            link_count += len(children['links'])

        return {
            'directories': dir_count,
            'files': file_count,
            'links': link_count,
            'total_records': len(all_entries),
            'total_children': dir_count + file_count + link_count
        }

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
            local_hash = self.local_storage.get_single_hash(current_path)
            core_hash = self.core_storage.get_single_hash(current_path)

            # Handle different scenarios
            if local_hash is None and core_hash is None:
                # Both missing - shouldn't happen but skip if it does
                continue
            elif local_hash is None:
                # Missing from local
                self._log_difference("Missing local entry for core path", current_path)
                differences.append((current_path, None, core_hash))
                # Add children from core to queue
                self._add_children_to_queue(current_path, path_queue, source='core')
            elif core_hash is None:
                # Additional in local (not in core)
                self._log_difference("Additional local entry not in core", current_path)
                differences.append((current_path, local_hash, None))
                # Add children from local to queue
                self._add_children_to_queue(current_path, path_queue, source='local')
            elif local_hash != core_hash:
                # Hash mismatch
                self._log_difference("Local entry does not match core for path", current_path)
                differences.append((current_path, local_hash, core_hash))
                # Add children from both sources to queue
                self._add_children_to_queue(current_path, path_queue, source='both')
            else:
                # Hashes match - still need to check children
                self._add_children_to_queue(current_path, path_queue, source='both')

        return differences

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
            local_entry = self.local_storage.get_hashtable(path)
            if local_entry:
                for category in ['dirs', 'files', 'links']:
                    children.update(local_entry.get(category, []))

        if source in ['core', 'both']:
            core_entry = self.core_storage.get_hashtable(path)
            if core_entry:
                for category in ['dirs', 'files', 'links']:
                    children.update(core_entry.get(category, []))

        # Add all unique children to queue
        for child in children:
            child_path = f"{path}/{child}".replace('//', '/')  # Handle double slashes
            path_queue.append(child_path)

    def _log_difference(self, message: str, path: str) -> None:
        """Helper method to log differences consistently"""
        # TODO needs update to align with detailed dumps
        logger.info(f"{message}: {path}")
        self.put_log_entry(message,
                            detailed_message=json.dumps([path]),
                            session_id=config.session_id)

    def update_target_hash(self, path: str, current_hash: str, target_hash: str) -> int:
        """
        Put a new target hash into the database.

        Returns:
            int representing the number of updates sent to the REST API that were successful"""
        return self.local_storage.put_hashtable({
            'path': path,
            'current_hash': current_hash,
            'target_hash': target_hash
        })

    def get_priority_updates(self) -> list[str]:
        """Get the list of database entries where the current hash does not match the target hash."""
        return self.local_storage.get_priority_updates() or []

    def get_pipeline_updates(self) -> list[str]:
        """Get the list of updates that have been approved by the continuous delivery (CD) pipeline."""
        return self.local_storage.get_pipeline_updates() or []

    def recompute_hashes(self, path_list: list[str]) -> list[tuple[str, str]]:

        recomputed = []
        for path in path_list:
            recomputed.append((path, self.integrity_service.compute_merkle_tree(config.root_path, path)))

        return recomputed

    def put_log_entry(self, message: str, detailed_message: str=None, log_level: str=None, session_id: bool=True) -> int:
        """Put a log entry into the database. Returns the ID of the new entry."""
        if session_id:
            session_id = config.session_id
        else:
            session_id = None
        return self.local_storage.put_log(message, detailed_message, log_level, session_id)