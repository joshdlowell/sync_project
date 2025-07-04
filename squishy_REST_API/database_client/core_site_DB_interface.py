from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple

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