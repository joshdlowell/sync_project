import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from squishy_integrity import logger
from rest_client.rest_interface import RestProcessorInterface
from integrity_check.interfaces import MerkleTreeInterface


# class StandardFileSystem(FileSystemInterface):
#     """Standard file system implementation using pathlib"""
#
#     def exists(self, path: str) -> bool:
#         return Path(path).exists()
#
#     def is_file(self, path: str) -> bool:
#         return Path(path).is_file()
#
#     def is_dir(self, path: str) -> bool:
#         return Path(path).is_dir()
#
#     def walk(self, path: str) -> List[Tuple[str | None, list[str] | None, list[str] | None]]:
#         try:
#             path_obj = Path(path)
#             if not path_obj.exists():
#                 raise OSError(f"Path does not exist: {path}")
#
#             # Convert generator to list
#             return list(path_obj.walk())
#         except OSError as e:
#             logger.error(f"Failed to walk path {path}: {e}")
#             return [(None, None, None)]
#
#     def read_file_chunks(self, path: str, chunk_size: int = 65536):
#         with open(path, 'rb') as f:
#             while True:
#                 data = f.read(chunk_size)
#                 if not data:
#                     break
#                 yield data
#
#     def readlink(self, path: str) -> str:
#         return str(Path(path).readlink())

#
# class RestStorage(PersistentStorageInterface):
#     """Hash storage implementation using REST connector"""
#     def __init__(self, rest_processor):
#         self.rest_processor = rest_processor
#
#     def put_hashtable(self, hash_info: Dict[str, Any]) -> int:
#         return self.rest_processor.put_hashtable(hash_info)
#
#     def get_hashtable(self, path: str) -> Optional[Dict[str, Any]]:
#         return self.rest_processor.get_hashtable(path)
#
#     def get_single_hash(self, path: str) -> Optional[str]:
#         return self.rest_processor.get_single_hash(path)
#
#     def get_oldest_updates(self, root_path: str, percent: int = 10) -> list[str]:
#         return self.rest_processor.get_oldest_updates(root_path, percent)
#
#     def get_priority_updates(self) -> list[str] | None:
#         return self.rest_processor.get_priority_updates()
#
#     def get_health(self) -> dict | None:
#         return self.rest_processor.get_health()
#
#     def put_log(self,
#                 message: str,
#                 site_id: str=None,
#                 timestamp: int=None,
#                 detailed_message: str=None,
#                 log_level: str=None,
#                 session_id: str=None
#                 ) -> int:
#         return self.rest_processor.put_log(message, site_id, timestamp, detailed_message, log_level, session_id)
#
#     def find_orphaned_entries(self) -> list[str]:
#         return self.rest_processor.find_orphaned_entries()
#
#     def find_untracked_children(self) -> list[str]:
#         return self.rest_processor.find_untracked_children()
#
#     def get_pipeline_updates(self) -> list[str]:
#         return self.rest_processor.get_pipeline_updates()
#
#     def consolidate_logs(self) -> bool:
#         return self.rest_processor.consolidate_logs()
#
#     def collect_logs_to_ship(self) -> list[dict[str, Any]] | None:
#         return self.rest_processor.collect_logs_to_ship()
#
#     def delete_log_entries(self, log_ids: list[int]) -> Tuple[bool, list]:
#         return self.rest_processor.delete_log_entries(log_ids)
#
#     def collect_logs_older_than(self, days: int) -> list[dict[str, Any]] | None:
#         return self.rest_processor.collect_logs_older_than(days)

#
# class RestHashStorage(RestProcessorInterface):
#     """Hash storage implementation using REST connector"""
#     def __init__(self, rest_processor):
#         self.rest_processor = rest_processor
#
#     def put_hashtable(self, hash_info: Dict[str, Any]) -> int:
#         return self.rest_processor.put_hashtable(hash_info)
#
#     def get_hashtable(self, path: str) -> Optional[Dict[str, Any]]:
#         return self.rest_processor.get_hashtable(path)
#
#     def get_single_hash(self, path: str) -> Optional[str]:
#         return self.rest_processor.get_single_hash(path)
#
#     def get_single_timestamp(self, path: str) -> float | None:
#         return self.rest_processor.get_single_timestamp(path)
#
#     def get_oldest_updates(self, percent: int = 10) -> list[str]:
#         return self.rest_processor.get_oldest_updates(config.get('root_path'), percent)
#
#     def get_priority_updates(self) -> list[str] | None:
#         return self.rest_processor.get_priority_updates()
#
#     def get_health(self) -> dict | None:
#         return self.rest_processor.get_health()
#
#     def put_log(self, message: str, detailed_message: str=None, log_level: str=None, session_id: str=None) -> int:
#         return self.rest_processor.put_log(message=message, detailed_message=detailed_message, log_level=log_level, session_id=session_id)
#
#     def find_orphaned_entries(self) -> list[str]:
#         return self.rest_processor.find_orphaned_entries()
#
#     def find_untracked_children(self) -> list[str]:
#         return self.rest_processor.find_untracked_children()
#
#     def get_pipeline_updates(self) -> list[str]:
#         return self.rest_processor.get_pipeline_updates()
#
#     def consolidate_logs(self) -> bool:
#         return self.rest_processor.consolidate_logs()
#
#     def collect_logs_to_ship(self) -> list[dict[str, Any]] | None:
#         return self.rest_processor.collect_logs_to_ship()
#
#     def delete_log_entries(self, log_ids: list[int]) -> Tuple[bool, list]:
#         return self.rest_processor.delete_log_entries(log_ids)
#
#     def collect_logs_older_than(self, days: int) -> list[dict[str, Any]] | None:
#         return self.rest_processor.collect_logs_older_than(days)
#
#
#
#
#
#
#
#     @abstractmethod
#     def put_log(self,
#                 message: str,
#                 site_id: str=None,
#                 timestamp: int=None,
#                 detailed_message: str=None,
#                 log_level: str=None,
#                 session_id: str=None
#                 ) -> int:
#
#
#     @abstractmethod
#     def collect_logs_for_shipping(self) -> list[dict[str, Any]] | None:
#         """Retrieve all log entries ready to be sent to the core db via REST API.
#
#         Returns:
#             A list of the log entries to be put to the core database log table.
#         """
#         pass
#
#     @abstractmethod
#     def collect_logs_older_than(self, days: int) -> list[dict[str, Any]] | None:
#         """Retrieve all log entries older than the specified number of days.
#
#         Returns:
#             A list of the log entries that are older than the specified number of days.
#         """
#         pass
#
#     @abstractmethod
#     def delete_log_entries(self, log_ids: list[int]) -> Tuple[bool, list]:
#         """
#         Delete multiple log entries by their IDs.
#
#         Response data formatting:
#          if successful, a list with a single entry representing the number of entries deleted
#          if partial success, a list of the log IDs that failed to delete
#          and an empty list otherwise
#
#         Args:
#             log_ids: List of log entry IDs to delete
#
#         Returns:
#             A tuple containing (success, response_data)
#         """
#         pass
#
#     @abstractmethod
#     def get_site_liveness(self) -> list:
#         pass
#
#     @abstractmethod
#     def get_site_sync_status(self) -> list:
#         pass
#
#     @abstractmethod
#     def get_official_sites(self) -> list[str]:
#         pass
#
# class SHA1HashFunction(HashFunction):
#     """SHA-1 hash function implementation"""
#
#     def create_hasher(self):
#         return hashlib.sha1()
#
#     def hash_string(self, data: str) -> str:
#         return hashlib.sha1(data.encode()).hexdigest()


class RestClientStorage(RestProcessorInterface):
    """
    Interface for interacting with the REST API for hash storage operations.

    This class implements the HashStorageInterface required by the MerkleTreeService.
    """
    def __init__(self, rest_processor):
        self.rest_processor = rest_processor

    def put_hashtable(self, hash_info: dict) -> int:
        """
        Store hash information in the database.

        This method implements the HashStorageInterface.put_hashtable method
        required by the MerkleTreeService.

        Args:
            hash_info: Dictionary containing hash information for files and directories
            session_id: Optional session ID for grouping batches of updates

        Returns:
            int representing the number of updates sent to the REST API that were successful
        """
        return self.rest_processor.put_hashtable(hash_info)

    def get_hashtable(self, path: str) -> dict | None:
        """
        Get the complete hash table for a specific path.

        Args:
            path: The path to get the hash table for

        Returns:
            A dictionary containing the hash table, or None if not found or error
        """
        return self.rest_processor.get_hashtable(path)

    def get_single_hash(self, path: str) -> str | None:
        """
        Get the hash value for a specific path.

        Args:
            path: The path to get the hash for

        Returns:
            The hash value as a string, or None if not found or error
        """
        return self.rest_processor.get_single_hash(path)

    def get_oldest_updates(self, root_path: str, percent: int = 10) -> list[str]:
        """
        Get a list of directories that need to be updated based on their age.

        This method retrieves the oldest directories (based on timestamps) that
        should be updated. The number of directories is determined by the percent
        parameter.

        Args:
            root_path: The root directory to start from
            percent: The percentage of directories to return (default: 10%)

        Returns:
            A list of directory paths that need to be updated
        """
        return self.rest_processor.get_oldest_updates(root_path, percent)

    def get_single_timestamp(self, path: str) -> float | None:
        """
        Get the timestamp for a specific path.

        Args:
            path: The path to get the timestamp for

        Returns:
            The timestamp as a float, or None if not found or error
        """
        pass

    def get_priority_updates(self) -> list | None:
        """
        Get paths that need priority updates.

        Returns:
            A list containing paths as strings that need priority updates, or None if not found or error
        """
        return self.rest_processor.get_priority_updates()

    def get_health(self) -> dict | None:
        return self.rest_processor.get_health()

    def put_log(self,
                message: str,
                site_id: str=None,
                timestamp: int=None,
                detailed_message: str=None,
                log_level: str=None,
                session_id: str=None
                ) -> int:
        return self.rest_processor.put_log(message, site_id, timestamp, detailed_message, log_level, session_id)

    def find_orphaned_entries(self) -> list | None:
        """
        Get all entries that aren't listed by a parent

        Returns:
            A list containing paths in the database that aren't listed by a parent, or None if not found or error
        """
        return self.rest_processor.find_orphaned_entries()

    def find_untracked_children(self) -> list | None:
        """Get a list of children claimed by a parent but not tracked in the database

        Returns:
            A list containing paths in the database that aren't listed by a parent, or None if not found or error
        """
        return self.rest_processor.find_untracked_children()

    def get_pipeline_updates(self):
        """Get the list of updates from the pipeline that haven't been processed yet.

        Returns:
            A list containing paths in the database that have been updated by the CD pipeline, or None if not found or error
        """
        return self.rest_processor.get_pipeline_updates()

    def consolidate_logs(self) -> bool | None:
        """Trigger log consolidation via REST API.

        Returns:
            True if consolidation was completed, None otherwise.
        """
        return self.rest_processor.consolidate_logs()

    def collect_logs_for_shipping(self) -> list[dict[str, Any]] | None:
        """Retrieve all log entries ready to be sent to the core db via REST API.

        Returns:
            A list of the log entries to be put to the core database log table.
        """
        return self.rest_processor.collect_logs_to_ship()

    def collect_logs_older_than(self, days: int) -> list[dict[str, Any]] | None:
        """Retrieve all log entries older than the specified number of days.

        Returns:
            A list of the log entries that are older than the specified number of days.
        """
        return self.rest_processor.collect_logs_older_than(days)

    def delete_log_entries(self, log_ids: list[int]) -> Tuple[bool, list]:
        """
        Delete multiple log entries by their IDs.

        Response data formatting:
         if successful, a list with a single entry representing the number of entries deleted
         if partial success, a list of the log IDs that failed to delete
         and an empty list otherwise

        Args:
            log_ids: List of log entry IDs to delete

        Returns:
            A tuple containing (success, response_data)
        """
        return self.rest_processor.delete_log_entries(log_ids)

    def get_site_liveness(self) -> list:
        pass

    def get_site_sync_status(self) -> list:
        pass

    def get_official_sites(self) -> list[str]:
        pass


class MerkleTreeImplementation(MerkleTreeInterface):
    """Interface implementation for Merkle tree integrity checking"""
    def __init__(self, merkle_service: MerkleTreeInterface):
        self.merkle_service = merkle_service

    def compute_merkle_tree(self, dir_path: str) -> Optional[str]:
        """
        Create a Merkle tree hash for a directory and detect changes

        Args:
            dir_path: Directory to hash (must be within root_path)

        Returns:
            Directory hash string, or None if computation fails
        """
        return self.merkle_service.compute_merkle_tree(dir_path)

    def put_log_w_session(self, message: str, detailed_message: str=None) -> int:
        return self.merkle_service.put_log_w_session(message, detailed_message)

    def remove_redundant_paths_with_priority(self, priority: list, routine: list):
        """
        Remove redundant paths from the provided lists while preserving priority order.

        Args:
            priority: list of paths that should be processed first
            routine: list of paths for hash recomputing

        Returns:
            Combined, deduplicated list of paths with priority items first
        """
        return self.merkle_service.remove_redundant_paths_with_priority(priority, routine)
