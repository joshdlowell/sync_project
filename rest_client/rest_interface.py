from abc import ABC, abstractmethod
from typing import Any, Tuple


class RestProcessorInterface(ABC):
    """
    Interface for interacting with the REST API for hash storage operations.

    This class implements the HashStorageInterface required by the MerkleTreeService.
    """
    @abstractmethod
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
        pass

    @abstractmethod
    def get_hashtable(self, path: str) -> dict | None:
        """
        Get the complete hash table for a specific path.

        Args:
            path: The path to get the hash table for

        Returns:
            A dictionary containing the hash table, or None if not found or error
        """
        pass

    @abstractmethod
    def get_single_hash(self, path: str) -> str | None:
        """
        Get the hash value for a specific path.

        Args:
            path: The path to get the hash for

        Returns:
            The hash value as a string, or None if not found or error
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_single_timestamp(self, path: str) -> float | None:
        """
        Get the timestamp for a specific path.

        Args:
            path: The path to get the timestamp for

        Returns:
            The timestamp as a float, or None if not found or error
        """
        pass

    @abstractmethod
    def get_priority_updates(self) -> list | None:
        """
        Get paths that need priority updates.

        Returns:
            A list containing paths as strings that need priority updates, or None if not found or error
        """
        pass

    @abstractmethod
    def get_health(self) -> dict | None:
        """Get the liveness of the rest api and database."""
        pass

    @abstractmethod
    def put_log(self,
                message: str,
                site_id: str=None,
                timestamp: int=None,
                detailed_message: str=None,
                log_level: str=None,
                session_id: str=None
                ) -> int:
        """
        Store log information in the database.

        This method implements the HashStorageInterface.put_log method
        required by the MerkleTreeService.
        Permitted log levels: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'

        Args:
            message: string containing the log message
            detailed_message: string containing the detailed log message
            log_level: string containing the log level
            session_id: string containing the session id for grouping batches of updates

        Returns:
            int representing the number of updates sent to the REST API that were successfully
        """
        pass

    @abstractmethod
    def find_orphaned_entries(self) -> list | None:
        """
        Get all entries that aren't listed by a parent

        Returns:
            A list containing paths in the database that aren't listed by a parent, or None if not found or error
        """
        pass

    @abstractmethod
    def find_untracked_children(self) -> list | None:
        """Get a list of children claimed by a parent but not tracked in the database

        Returns:
            A list containing paths in the database that aren't listed by a parent, or None if not found or error
        """
        pass

    @abstractmethod
    def get_pipeline_updates(self):
        """Get the list of updates from the pipeline that haven't been processed yet.

        Returns:
            A list containing paths in the database that have been updated by the CD pipeline, or None if not found or error
        """
        pass

    @abstractmethod
    def consolidate_logs(self) -> bool | None:
        """Trigger log consolidation via REST API.

        Returns:
            True if consolidation was completed, None otherwise.
        """
        pass

    @abstractmethod
    def collect_logs_for_shipping(self) -> list[dict[str, Any]] | None:
        """Retrieve all log entries ready to be sent to the core db via REST API.

        Returns:
            A list of the log entries to be put to the core database log table.
        """
        pass

    @abstractmethod
    def collect_logs_older_than(self, days: int) -> list[dict[str, Any]] | None:
        """Retrieve all log entries older than the specified number of days.

        Returns:
            A list of the log entries that are older than the specified number of days.
        """
        pass

    @abstractmethod
    def delete_log_entries(self, log_ids: list[int]) -> Tuple[int, list]:
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
        pass

    @abstractmethod
    def get_site_liveness(self) -> list:
        pass

    @abstractmethod
    def get_site_sync_status(self) -> list:
        pass

    @abstractmethod
    def sync_official_sites(self) -> bool:
        pass

    @abstractmethod
    def put_pipeline_update(self, update_path: str, hash_value: str) -> bool:
        pass

    @abstractmethod
    def put_remote_hash_status(self, status_updates: list[dict[str, str]], site_name: str, root_path: str=None) -> bool:
        pass
