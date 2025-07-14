from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class RemoteDBConnection(ABC):
    """
    Database access class for hash table operations.

    This class provides methods to interact with the MySQL database
    for storing and retrieving hash information.
    """

    @abstractmethod
    def get_hash_record(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get a single record by path.
        Args:
            path: Path to retrieve
        Returns:
            Dictionary with record data or None if not found or an error occurred
        Raises:
            ValueError: If required parameters are not provided
        """
        pass

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
        pass

    @abstractmethod
    def delete_log_entries(self, log_ids: list[int]) -> tuple[list, list]:
        """
        Remove log entry from the database.

        This method deletes a log_entry by log_id and is used to clean out local logs after they
         have been forwarded to the core DB.

        Args:
            An int representing the log entry's log_id to be removed from the local database.

        Returns:
            True if the log entry was deleted, False if not found, or an error occurred.
        """
        pass

    @abstractmethod
    def consolidate_logs(self) -> bool:
        """
        Consolidate log entries by session ID, grouping and deduplicating JSON-encoded detailed messages.

        Returns:
            bool: True if consolidation was successful, False otherwise
        """
        pass

    @abstractmethod
    def find_orphaned_entries(self) -> list[str]:
        """
        Find children that exist as entries but aren't listed by their parent.

        Returns:
             List of entries that exist but aren't listed in their parent's children arrays.
        """
        pass

    @abstractmethod
    def find_untracked_children(self) -> list[Any]:
        """
        Find children listed by parents but don't exist as entries.

        Alternate return (not used):
            List of dictionaries with keys: untracked_path, parent_path, child_name, child_type
        Returns:
            List of paths that are listed in their parent's children arrays but don't exist as entries in the database.
        """
        pass

    @abstractmethod
    def health_check(self) -> dict[str, bool]:
        """
         Verify that the local database is alive and responding to requests.
         Returns:
             {local_db: True or False} depending on if the database is active and responsive.
         """
        pass


class CoreDBConnection(ABC):
    """
    Database access class for core site operations.

    This class provides methods to interact with the MySQL database
    for storing and retrieving hash information.
    """

    def get_dashboard_content(self) -> dict[str, Any]:
        """
        Retrieve dashboard metrics for site monitoring system.

        Executes a complex query to gather site synchronization status, live status,
        and critical error counts across all sites in the site_list. Uses current
        and previous baselines from state_history to categorize sync status.

        Returns:
            dict[str, Any]: Dashboard metrics containing:
                - crit_error_count (int): Critical errors in last 24 hours
                - hash_record_count (int): Record count from current baseline
                - sync_current (int): Sites with current baseline sync
                - sync_1_behind (int): Sites one baseline behind
                - sync_l24_behind (int): Sites with hash from last 24 hours
                - sync_g24_behind (int): Sites with hash older than 24 hours
                - sync_unknown (int): Sites with unknown baseline hash
                - live_current (int): Sites active in last 35 minutes
                - live_1_behind (int): Sites active between 35m-24h ago
                - live_l24_behind (int): Sites active in last 24 hours
                - live_inactive (int): Sites inactive for over 24 hours

        Note:
            Returns dictionary with zero values for all metrics if query fails.
            Only includes sites that exist in the authoritative site_list table.
        """
        pass

    def get_recent_logs(self) -> list:
        """
        Get all logs from the last 30 days.

        Returns:
            List of dictionaries containing log records from the last 30 days,
            or empty list if no records found or an error occurred
        """
        pass

    def get_hash_record_count(self) -> int:
        """
        Get the total count of records in the hashtable.

        Returns:
            Integer count of total records or None if an error occurred
        """
        pass


    def get_log_count_last_24h(self, log_level: str) -> int:
        """
        Get count of log entries for a specific log level in the last 24 hours.

        This method counts log entries from the local database for a given log level
        that occurred within the last 24 hours based on unix timestamp.

        Args:
            log_level: The log level to count. Must be one of:
                      'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'

        Returns:
            Integer count of matching log records in the last 24 hours.
            Returns 0 if no records found or on error.

        Raises:
            ValueError: If invalid log_level is provided
        """
        pass

    @abstractmethod
    def get_site_liveness(self) -> list:
        """
        Get all sites from site_list with their last_updated timestamps and status categories.

        Returns:
            List of dictionaries containing site records with their status categories,
            or empty list if no records found or an error occurred.
            Each dictionary contains: site_name, last_updated, status_category
        """
        pass

    @abstractmethod
    def get_site_sync_status(self) -> list:
        """
        Get synchronization status for all active sites based on their current hash
        compared to the hash history timeline.

        Returns:
            List of dictionaries containing site records with their sync status categories,
            or empty list if no records found or an error occurred.
            Each dictionary contains: site_name, current_hash, last_updated, sync_category
        """
        pass

    @abstractmethod
    def put_remote_hash_status(self, update_list: list[dict[str, str]], site_name: str, drop_existing: bool = False) -> list[str]:
        """
        Update the remote hash status for all out-of-sync hashes at a specific site.
        Args:
            update_list: List of dictionaries containing paths with their current hash at a given site
            site_name: The name of the site submitting the updates
            drop_existing: boolean indicating whether to drop existing records for the site before adding the updates

        Returns:
            List paths updated
        """
        pass


class PipelineDBConnection(ABC):
    """
    Database access class for core site pipeline database operations.

    This class provides methods to interact with the pipeline database
    for storing and retrieving information.
    """

    @abstractmethod
    def get_pipeline_updates(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def put_pipeline_hash(self, update_path: str, hash_value: str) -> bool:
        pass

    @abstractmethod
    def get_official_sites(self) -> List[str]:
        pass

    @abstractmethod
    def put_pipeline_site_completion(self, site: str) -> bool:
        pass

    @abstractmethod
    def pipeline_health_check(self) -> Dict[str, bool]:
        pass
