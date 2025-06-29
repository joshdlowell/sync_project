from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple

class DBConnection(ABC):
    """
    Database access class for hash table operations.

    This class provides methods to interact with the MySQL database
    for storing and retrieving hash information.
    """

    @abstractmethod
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
        pass

    @abstractmethod
    def get_hash_record(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get a single record by path.

        Args:
            path: Path to retrieve

        Returns:
            Dictionary with record data or None if not found or an error occurred
        """
        pass

    @abstractmethod
    def get_single_hash_record(self, path: str) -> Optional[str]:
        """
        Get only the current hash value for a path.

        Args:
            path: Path to retrieve hash for

        Returns:
            Hash value as string or None if not found or an error occurred
        """
        pass

    @abstractmethod
    def get_single_timestamp(self, path: str) -> Optional[int]:
        """
        Get only the current hash timestamp value for a path.

        Args:
            path: Path to retrieve timestamp for

        Returns:
            timestamp value as int or None if not found or an error occurred
        """
        pass

    @abstractmethod
    def get_oldest_updates(self, root_path: str, percent: int = 10) -> List[str]:
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
    def get_priority_updates(self) -> List[str]:
        """
        Get a list of directories where the target hash (if it exists) does not match
        the current hash.

        This method retrieves the directories that should be scheduled for updates from
        the gold copy or have been changed due to corruption or tampering.

        Returns:
            A list of directory paths that need to be rechecked
        """
        pass

    @abstractmethod
    def put_log(self, args_dict: dict) -> int | None:
        """
        Put log entry into database.

        This method inserts log entries into the local_database.

        Returns:
            log_id number (int) if the log entry was inserted, None if an error occurred
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def life_check(self) -> bool:
        """
         Check if the database is active and responsive.

         This method verifies that the local database is alive and responding to requests.

         Returns:
             True if the database is active and responsive, False if not.
         """
        pass
