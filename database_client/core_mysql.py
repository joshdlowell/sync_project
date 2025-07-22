from typing import Any, List, Dict
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager

from .db_interfaces import CoreDBConnection
from database_client import logging_config
from database_client.logging_config import VALID_LOG_LEVELS

class CoreMYSQLConnection(CoreDBConnection):
    """
    Database access class for hash table operations.

    This class provides methods to interact with the MySQL database
    for storing and retrieving hash information.
    """
    def __init__(self, host, database, user, password, port=3306,
                 connection_factory=None, autocommit=True, raise_on_warnings=True, **kwargs):
        """
        Initialize the database connection configuration.

        Args:
            host: Database host
            database: Database name
            user: Database user
            password: Database password
            port: Database port (default: 3306)
            connection_factory: Optional factory function for creating connections (for testing)
            autocommit: Whether to autocommit transactions (default: True)
            raise_on_warnings: Whether to raise on warnings (default: True)
        """
        self.config = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': port,
            'autocommit': autocommit,
            'raise_on_warnings': raise_on_warnings
        }

        self.other_args = kwargs

        self.database = database
        self.connection_factory = connection_factory or mysql.connector.connect
        self.logger = logging_config.configure_logging()

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.

        Yields:
            MySQL connection object

        Raises:
            Error: If a database error occurs
        """
        connection = None
        try:
            connection = self.connection_factory(**self.config)
            self.logger.debug(f"Database connection established to {self.config['host']}")
            yield connection
        except Error as e:
            self.logger.error(f"Database error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
                self.logger.debug("Database connection closed")

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
        query = """
                WITH
                    -- Get the most recent hash (current baseline)
                    current_baseline AS (SELECT hash_value, created_at, record_count
                                         FROM state_history
                                         ORDER BY created_at DESC
                                         LIMIT 1),
                    -- Get the second most recent hash (1 behind baseline)
                    previous_baseline AS (SELECT hash_value, created_at
                                          FROM state_history
                                          ORDER BY created_at DESC
                                          LIMIT 1 OFFSET 1),
                    -- Time boundaries
                    time_bounds AS (SELECT NOW() - INTERVAL 35 MINUTE as live_threshold,
                                           NOW() - INTERVAL 24 HOUR   as day_threshold),
                    -- Site categorization - INCLUDES ALL SITES FROM AUTHORITATIVE LIST
                    site_stats AS (SELECT sl.site_name,
                                          rhs.current_hash,
                                          rhs.last_updated,
                                          sh.created_at                 as hash_created_at,
                                          current_baseline.hash_value   as current_baseline_hash,
                                          previous_baseline.hash_value  as previous_baseline_hash,
                                          current_baseline.record_count as baseline_record_count,

                                          -- Sync status categorization
                                          CASE
                                              WHEN rhs.current_hash IS NULL
                                                  THEN 'sync_unknown' -- Site exists but no operational data
                                              WHEN rhs.current_hash = current_baseline.hash_value THEN 'sync_current'
                                              WHEN rhs.current_hash = previous_baseline.hash_value THEN 'sync_1_behind'
                                              WHEN sh.created_at >= time_bounds.day_threshold THEN 'sync_l24_behind'
                                              WHEN sh.created_at < time_bounds.day_threshold THEN 'sync_g24_behind'
                                              ELSE 'sync_unknown' \
                                              END                       as sync_status,

                                          -- Live status categorization
                                          CASE
                                              WHEN rhs.last_updated IS NULL
                                                  THEN 'live_inactive' -- Site exists but no operational data
                                              WHEN rhs.last_updated >= time_bounds.live_threshold THEN 'live_current'
                                              WHEN rhs.last_updated >= time_bounds.day_threshold AND
                                                   rhs.last_updated < time_bounds.live_threshold THEN 'live_1_behind'
                                              WHEN rhs.last_updated >= time_bounds.day_threshold THEN 'live_l24_behind'
                                              ELSE 'live_inactive'
                                              END                       as live_status

                                   FROM site_list sl -- Start with authoritative list
                                            LEFT JOIN remotes_hash_status rhs
                                                      ON sl.site_name = rhs.site_name -- Left join to include all sites
                                            CROSS JOIN current_baseline
                                            CROSS JOIN previous_baseline
                                            CROSS JOIN time_bounds
                                            LEFT JOIN state_history sh ON rhs.current_hash = sh.hash_value
                                   WHERE sl.online = 1 -- Only include online sites
                    )

                SELECT
                    -- Critical errors in last 24h (only for sites that exist in site_list)
                    COALESCE((SELECT COUNT(*)
                              FROM logs l
                                       INNER JOIN site_list sl ON l.site_id = sl.site_name
                              WHERE l.log_level = 'CRITICAL'
                                AND l.timestamp >= NOW() - INTERVAL 24 HOUR
                                AND sl.online = 1), 0)                               as crit_error_count,

                    -- Record count from current baseline
                    MAX(baseline_record_count)                                       as hash_record_count,

                    -- Sync status counts
                    SUM(CASE WHEN sync_status = 'sync_current' THEN 1 ELSE 0 END)    as sync_current,
                    SUM(CASE WHEN sync_status = 'sync_1_behind' THEN 1 ELSE 0 END)   as sync_1_behind,
                    SUM(CASE WHEN sync_status = 'sync_l24_behind' THEN 1 ELSE 0 END) as sync_l24_behind,
                    SUM(CASE WHEN sync_status = 'sync_g24_behind' THEN 1 ELSE 0 END) as sync_g24_behind,
                    SUM(CASE WHEN sync_status = 'sync_unknown' THEN 1 ELSE 0 END)    as sync_unknown,

                    -- Live status counts
                    SUM(CASE WHEN live_status = 'live_current' THEN 1 ELSE 0 END)    as live_current,
                    SUM(CASE WHEN live_status = 'live_1_behind' THEN 1 ELSE 0 END)   as live_1_behind,
                    SUM(CASE WHEN live_status = 'live_l24_behind' THEN 1 ELSE 0 END) as live_l24_behind,
                    SUM(CASE WHEN live_status = 'live_inactive' THEN 1 ELSE 0 END)   as live_inactive

                FROM site_stats;
                """

        # Initialize context with default values
        context = {
            'crit_error_count': 0,  # Number of Critical errors logged in the last 24h
            'hash_record_count': 0,  # Count of dirs/files/links currently on baseline
            'sync_current': 0,  # Baseline sync current
            'sync_1_behind': 0,  # Baseline on previous current
            'sync_l24_behind': 0,  # Baseline on some hash from last 24 hours
            'sync_g24_behind': 0,  # Baseline hash more than 24 hours ago
            'sync_unknown': 0,  # Baseline hash is not in the history table
            'live_current': 0,  # Heard from in last 35m
            'live_1_behind': 0,  # Heard from more than 35m ago
            'live_l24_behind': 0,  # Heard from in last 24h
            'live_inactive': 0,  # Have not heard from in over 24h
        }

        # Execute query and populate context
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    result = cursor.fetchone()  # Use fetchone() since query returns single row
                    if result:
                        # Update context with actual values from query result
                        context.update({
                            'crit_error_count': result[0] or 0,
                            'hash_record_count': result[1] or 0,
                            'sync_current': result[2] or 0,
                            'sync_1_behind': result[3] or 0,
                            'sync_l24_behind': result[4] or 0,
                            'sync_g24_behind': result[5] or 0,
                            'sync_unknown': result[6] or 0,
                            'live_current': result[7] or 0,
                            'live_1_behind': result[8] or 0,
                            'live_l24_behind': result[9] or 0,
                            'live_inactive': result[10] or 0,
                        })
                    self.logger.debug(f"Dashboard query result: {result}")
        except Exception as e:
            self.logger.error(f"Error collecting dashboard information: {e}")
            # Context remains with default values (0s) on error

        return context

    def get_site_liveness(self) -> list:
        """
        Get all sites from site_list with their last_updated timestamps and status categories.

        Returns:
            List of dictionaries containing site records with their status categories,
            or empty list if no records found or an error occurred.
            Each dictionary contains: site_name, last_updated, status_category
        """
        # Calculate timestamps for different time thresholds
        current_time = datetime.now()
        thirty_five_minutes_ago = datetime.now() - timedelta(minutes=35)
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

        params = [thirty_five_minutes_ago, twenty_four_hours_ago]

        query = """
                SELECT sl.site_name,
                       s.last_updated,
                       sl.online,
                       CASE
                           WHEN sl.online = 0 THEN 'marked_inactive'
                           WHEN s.last_updated IS NULL THEN 'live_inactive'
                           WHEN s.last_updated >= %s THEN 'live_current'
                           WHEN s.last_updated >= %s THEN 'live_behind'
                           ELSE 'live_inactive'
                           END as status_category
                FROM site_list sl
                         LEFT JOIN squishy_db.remotes_hash_status s ON sl.site_name = s.site_name
                ORDER BY sl.site_name
                """

        try:
            with self._get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(query, params)
                    results = cursor.fetchall()

                    cleaned_results = []
                    for row in results:
                        # Convert datetime to timestamp for JavaScript
                        timestamp = None
                        if row['last_updated']:
                            timestamp = int(row['last_updated'].timestamp())

                        cleaned_results.append({
                            'site_name': row['site_name'],
                            'last_updated': row['last_updated'],  # Keep original for moment.js
                            'last_updated_timestamp': timestamp,  # Add timestamp for sorting
                            'status_category': row['status_category']
                        })

                    if results:
                        self.logger.debug(f"Retrieved status for {len(results)} sites")
                        return cleaned_results
                    else:
                        self.logger.debug("No sites found in site_list")
                        return []

        except Error as e:
            self.logger.error(f"Error fetching site status summary: {e}")
            return []

    def get_site_sync_status(self) -> list:
        """
        Get synchronization status for all active sites based on their current hash
        compared to the hash history timeline.

        Returns:
            List of dictionaries containing site records with their sync status categories,
            or empty list if no records found or an error occurred.
            Each dictionary contains: site_name, current_hash, last_updated, sync_category
        """
        # Calculate timestamp for 24 hours ago
        # twenty_four_hours_ago = int(time()) - (24 * 60 * 60)
        # from datetime import datetime, timedelta

        # Calculate 24 hours ago as a datetime object
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

        query = """
                WITH ranked_hashes AS (SELECT hash_value, \
                                              created_at, \
                                              ROW_NUMBER() OVER (ORDER BY created_at DESC) as hash_rank \
                                       FROM state_history),
                     recent_hashes AS (SELECT hash_value \
                                       FROM ranked_hashes \
                                       WHERE hash_rank <= 2),
                     hash_24h AS (SELECT hash_value \
                                  FROM state_history \
                                  WHERE created_at >= %s)
                SELECT sl.site_name, \
                       s.current_hash, \
                       s.last_updated, \
                       CASE \
                           WHEN s.current_hash IS NULL THEN 'sync_unknown' \
                           WHEN s.current_hash = (SELECT hash_value FROM ranked_hashes WHERE hash_rank = 1) \
                               THEN 'sync_current' \
                           WHEN s.current_hash = (SELECT hash_value FROM ranked_hashes WHERE hash_rank = 2) \
                               THEN 'sync_1_behind' \
                           WHEN s.current_hash IN (SELECT hash_value FROM hash_24h) \
                               AND s.current_hash NOT IN (SELECT hash_value FROM recent_hashes) THEN 'sync_l24_behind' \
                           WHEN s.current_hash IN (SELECT hash_value FROM state_history) THEN 'sync_g24_behind' \
                           ELSE 'sync_unknown' \
                           END as sync_category
                FROM site_list sl
                         INNER JOIN squishy_db.remotes_hash_status s ON sl.site_name = s.site_name
                WHERE sl.online = 1
                ORDER BY sl.site_name
                """

        params = [twenty_four_hours_ago]

        try:
            with self._get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(query, params)
                    results = cursor.fetchall()

                    # Clean up the results to only include needed fields
                    cleaned_results = []
                    for row in results:
                        # Convert UNIX timestamps to datetime objects for template
                        # if row.get('last_updated'):
                        #     row['last_updated'] = datetime.fromtimestamp(int(row['last_updated'])).strftime(
                        #         '%m-%d-%Y %H:%M:%S')
                        # else:
                        #     row['last_updated'] = None
                        cleaned_results.append({
                            'site_name': row['site_name'],
                            'current_hash': row['current_hash'],
                            'last_updated': row['last_updated'],
                            'sync_category': row['sync_category']
                        })

                    if results:
                        self.logger.debug(f"Retrieved sync status for {len(results)} active sites")
                        return cleaned_results
                    else:
                        self.logger.debug("No active sites found for sync status check")
                        return []

        except Error as e:
            self.logger.error(f"Error fetching site sync status: {e}")
            return []

    def get_recent_logs(self, log_level: str = None, site_id: str = None) -> list:
        """
        Get all logs from the last 30 days, optionally filtered by log_level and/or site_id.

        Args:
            log_level: Optional log level to filter by (case-insensitive)
            site_id: Optional site ID to filter by (case-insensitive)

        Returns:
            List of dictionaries containing log records from the last 30 days,
            or empty list if no records found or an error occurred
        """
        # Calculate timestamp for 30 days ago
        # thirty_days_ago = int(time()) - (30 * 24 * 60 * 60)
        from datetime import datetime, timedelta

        # Calculate 24 hours ago as a datetime object
        thirty_days_ago = datetime.now() - timedelta(days=30)


        # Build query with optional filters
        query = """
                SELECT log_id, \
                       site_id, \
                       session_id, \
                       log_level, \
                       timestamp,
                       summary_message, \
                       detailed_message
                FROM logs
                WHERE timestamp >= %s \
                """
        params = [thirty_days_ago]

        if log_level:
            query += " AND UPPER(log_level) = UPPER(%s)"
            params.append(log_level)

        if site_id:
            query += " AND UPPER(site_id) = UPPER(%s)"
            params.append(site_id)

        query += " ORDER BY timestamp DESC"

        try:
            with self._get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(query, params)
                    results = cursor.fetchall()

                    filter_desc = []
                    if log_level:
                        filter_desc.append(f"log_level={log_level}")
                    if site_id:
                        filter_desc.append(f"site_id={site_id}")
                    filter_str = f" with filters: {', '.join(filter_desc)}" if filter_desc else ""
                    if results:
                        self.logger.debug(f"Retrieved {len(results)} log records from last 30 days{filter_str}")
                        return results
                    else:
                        self.logger.debug(f"No log records found in the last 30 days{filter_str}")
                        return []

        except Error as e:
            self.logger.error(f"Error fetching recent logs: {e}")
            return []

    def get_valid_site_ids(self) -> list:
        """
        Get all valid site IDs from the site_list table.

        Returns:
            List of site_name strings, or empty list if no sites found or error occurred
        """
        query = "SELECT site_name FROM site_list ORDER BY site_name"

        try:
            with self._get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(query)
                    results = cursor.fetchall()

                    if results:
                        site_ids = [row['site_name'] for row in results]
                        self.logger.debug(f"Retrieved {len(site_ids)} valid site IDs")
                        return site_ids
                    else:
                        self.logger.debug("No site IDs found")
                        return []

        except Error as e:
            self.logger.error(f"Error fetching valid site IDs: {e}")
            return []

    def sync_sites_from_mssql_upsert(self, mssql_sites: List[Dict[str, Any]]) -> bool:
        """
        Synchronize the MySQL site_list table with data from MSSQL using upsert approach.

        Args:
            mssql_sites: List of site dictionaries from MSSQL

        Returns:
            True if sync was successful, False otherwise
        """
        if not mssql_sites:
            self.logger.warning("No MSSQL sites data provided for sync")
            return False

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Start transaction
                    conn.start_transaction()

                    try:
                        # Get existing site_names from MySQL
                        cursor.execute("SELECT site_name FROM site_list")
                        existing_sites = {row[0] for row in cursor.fetchall()}

                        # Prepare sets for comparison
                        mssql_site_names = {site['site_name'] for site in mssql_sites if site.get('site_name')}

                        # Delete sites that no longer exist in MSSQL
                        sites_to_delete = existing_sites - mssql_site_names
                        if sites_to_delete:
                            delete_query = "DELETE FROM site_list WHERE site_name IN ({})".format(
                                ','.join(['%s'] * len(sites_to_delete))
                            )
                            cursor.execute(delete_query, list(sites_to_delete))
                            self.logger.debug(f"Deleted {len(sites_to_delete)} obsolete sites")

                        # Upsert sites from MSSQL
                        upsert_query = """
                                       INSERT INTO site_list (name, site_name, online, description)
                                       VALUES (%(name)s, %(site_name)s, %(online)s, %(description)s)
                                       ON DUPLICATE KEY UPDATE name        = VALUES(name),
                                                               online      = VALUES(online),
                                                               description = VALUES(description),
                                                               updated_at  = CURRENT_TIMESTAMP
                                       """

                        # Prepare data for upsert
                        upsert_data = []
                        for site in mssql_sites:
                            if site.get('site_name'):  # Only process sites with valid site_name
                                upsert_data.append({
                                    'name': site.get('name'),
                                    'site_name': site.get('site_name'),
                                    'online': bool(site.get('online', True)),
                                    'description': site.get('description')
                                })

                        # Execute batch upsert
                        if upsert_data:
                            cursor.executemany(upsert_query, upsert_data)

                        # Commit transaction
                        conn.commit()

                        self.logger.info(f"Successfully synced {len(upsert_data)} sites from MSSQL to MySQL")
                        return True

                    except Exception as e:
                        # Rollback on error
                        conn.rollback()
                        raise e

        except Error as e:
            self.logger.error(f"Error syncing sites from MSSQL: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error syncing sites from MSSQL: {e}")
            return False

    def get_hash_record_count(self) -> int:
        """
        Get the total count of records in the hashtable.

        Returns:
            Integer count of total records or None if an error occurred
        """
        query = "SELECT COUNT(*) as total_count FROM hashtable"

        try:
            with self._get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    if result:
                        count = result['total_count']
                        self.logger.debug(f"Total records in hashtable: {count}")
                        return count
                    else:
                        self.logger.debug("No count result returned")
                        return 0
        except Error as e:
            self.logger.error(f"Error fetching record count: {e}")
            return 0

    def get_log_count_last_24h(self, log_level: str) -> int:
        """
        Get count of log entries for a specific log level in the last 24 hours.

        This method counts log entries from the local database for a given log level
        that occurred within the last 24 hours based on timestamp object.

        Args:
            log_level: The log level to count. Must be one of:
                      'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'

        Returns:
            Integer count of matching log records in the last 24 hours.
            Returns 0 if no records found or on error.

        Raises:
            ValueError: If invalid log_level is provided
        """
        # Input validation
        allowed_log_levels = VALID_LOG_LEVELS
        if not isinstance(log_level, str):
            raise ValueError("log_level must be a string")

        if log_level.upper() not in allowed_log_levels:
            raise ValueError(f"Invalid log_level. Allowed: {allowed_log_levels}")

        from datetime import datetime, timedelta

        # Calculate 24 hours ago as a datetime object
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

        # Build query with proper parameterization
        query = """
                SELECT COUNT(*) as record_count
                FROM logs
                WHERE log_level = %s
                  AND timestamp >= %s
                """
        query_params = [log_level.upper(), twenty_four_hours_ago]

        try:
            with self._get_connection() as conn:
                with conn.cursor(dictionary=True, buffered=True) as cursor:
                    cursor.execute(query, query_params)
                    result = cursor.fetchone()

                    count = result['record_count'] if result else 0
                    self.logger.debug(f"Found {count} {log_level} log records in last 24 hours")

                    return count

        except mysql.connector.Error as e:
            # More specific error handling
            self.logger.error(f"MySQL error counting log records: {e.errno} - {e.msg}")
            return 0
        except Exception as e:
            # Catch any other unexpected errors
            self.logger.error(f"Unexpected error counting log records: {e}")
            return 0

    def put_remote_hash_status(self, update_list: list[dict[str, str]],
                               site_name: str,
                               drop_existing: bool = False,
                               root_path: str = None
                               ) -> list[str]:
        """
        Update the remote hash status for all out-of-sync hashes at a specific site.
        Args:
            update_list: List of dictionaries containing paths with their current hash at a given site
            site_name: The name of the site submitting the updates
            drop_existing: boolean indicating whether to drop existing records in the remote status
                table for the site before adding the updates
        Returns:
            List paths updated
        """
        # Validate required parameters
        if not update_list or not site_name:
            self.logger.debug(f"put_remote_hash_status missing update_list or site_name")
            raise ValueError("update_list and site_name must be provided")

        # If site is in sync, the only status update we get is baseline itself
        baseline_hash_only = False
        if len(update_list) == 1:
            if update_list[0]['path'] == root_path:
                baseline_hash_only = True

        # Validate each item in update_list has required keys
        for item in update_list:
            if not isinstance(item, dict) or 'path' not in item or 'current_hash' not in item:
                self.logger.debug(f"Invalid update_list item: {item}")
                raise ValueError("Each item in update_list must be a dict with 'path' and 'current_hash' keys")

        updated_paths = []

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Drop existing records for this site if requested
                    if drop_existing:
                        delete_query = "DELETE FROM remotes_hash_status WHERE site_name = %s"
                        cursor.execute(delete_query, (site_name,))
                        deleted_count = cursor.rowcount
                        self.logger.debug(f"Dropped {deleted_count} existing records for site: {site_name}")

                    # Process each update item
                    for item in update_list:
                        path = item['path']
                        current_hash = item['current_hash']

                        # Update sites table if the item is baseline.
                        if path == root_path:
                            # First try to update existing records for this site/path combination
                            update_query = """
                                           UPDATE remotes_hash_status
                                           SET current_hash = %s
                                           WHERE site_name = %s
                                           """
                            cursor.execute(update_query, (current_hash, site_name))

                            if cursor.rowcount > 0:
                                # Successfully updated existing record(s)
                                self.logger.debug(f"Updated {site_name} existing record in sites table")
                            else:
                                # No existing records found, insert new one
                                insert_query = """
                                               INSERT INTO squishy_db.remotes_hash_status (site_name, current_hash)
                                               VALUES (%s, %s) \
                                               """
                                cursor.execute(insert_query, (site_name, current_hash))

                                if cursor.rowcount > 0:
                                    updated_paths.append(path)
                                    self.logger.debug(f"Inserted new record for site: {site_name} into sites table")

                        # If the update contained only the baseline hash, then we are done.
                        if baseline_hash_only:
                            continue

                        if not drop_existing:
                            # First try to update existing records for this site/path combination
                            update_query = """
                                           UPDATE remotes_hash_status
                                           SET current_hash = %s
                                           WHERE site_name = %s
                                             AND path = %s
                                           """
                            cursor.execute(update_query, (current_hash, site_name, path))

                            if cursor.rowcount > 0:
                                # Successfully updated existing record(s)
                                updated_paths.append(path)
                                self.logger.debug(
                                    f"Updated {cursor.rowcount} existing record(s) for site: {site_name}, path: {path}")
                            else:
                                # No existing records found, insert new one
                                insert_query = """
                                               INSERT INTO remotes_hash_status (site_name, path, current_hash)
                                               VALUES (%s, %s, %s)
                                               """
                                cursor.execute(insert_query, (site_name, path, current_hash))

                                if cursor.rowcount > 0:
                                    updated_paths.append(path)
                                    self.logger.debug(f"Inserted new record for site: {site_name}, path: {path}")
                        else:
                            # When drop_existing=True, just insert all records
                            insert_query = """
                                           INSERT INTO remotes_hash_status (site_name, path, current_hash)
                                           VALUES (%s, %s, %s)
                                           """
                            cursor.execute(insert_query, (site_name, path, current_hash))

                            if cursor.rowcount > 0:
                                updated_paths.append(path)
                                self.logger.debug(f"Inserted record for site: {site_name}, path: {path}")

                    self.logger.debug(f"Successfully processed {len(updated_paths)} paths for site: {site_name}")
                    return updated_paths

        except Error as e:
            self.logger.error(f"Error updating remote hash status: {e}")
            return []