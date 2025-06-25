import mysql.connector
from mysql.connector import Error
from time import time
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Tuple

from squishy_REST_API.configuration.logging_config import logger


class HashTableDB:
    """
    Database access class for hash table operations.

    This class provides methods to interact with the MySQL database
    for storing and retrieving hash information.
    """

    def __init__(self, host, database, user, password, port=3306, 
                 connection_factory=None, autocommit=True, raise_on_warnings=True):
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
        self.database = database
        self.connection_factory = connection_factory or mysql.connector.connect

    @contextmanager
    def get_connection(self):
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
            logger.debug(f"Database connection established to {self.config['host']}")
            yield connection
        except Error as e:
            logger.error(f"Database error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
                logger.debug("Database connection closed")

    def insert_or_update_hash(self, path: str, **kwargs) -> Optional[Dict[str, list]]:
        """
        Insert new record or update existing one.

        Args:
            path: Path to insert or update
            **kwargs: Additional fields to insert or update

        Returns:
            Dictionary with modified, created, and deleted paths, or None if an error occurred
        """
        # First, check if record exists and get current columns for possible modification
        existing_hash, existing_dtg_latest = None, None
        existing_dirs, existing_links, existing_files = [], [], []

        logger.debug(f"Inserting or updating hash for path: {path}")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT current_hash, current_dtg_latest, dirs, links, files FROM hashtable WHERE path = %s", (path,))
                result = cursor.fetchone()
                if result:
                    existing_hash, existing_dtg_latest, existing_dirs, existing_links, existing_files = result
                    logger.debug(f"Found existing record for path: {path}")
        except Error as e:
            logger.error(f"Error checking existing record: {e}")
            return None
        # Initialize changes dictionary
        modified, created, deleted = set(), set(), set()

        # Convert lists formatted values to strings for db storage
        request_dirs_string, request_dirs_list = self.string_cleaner(kwargs.get('dirs'))
        request_files_string, request_files_list = self.string_cleaner(kwargs.get('files'))
        request_links_string, request_links_list = self.string_cleaner(kwargs.get('links'))

        # prep and Set update values
        if len(existing_dirs) > 0: existing_dirs = [x.strip() for x in existing_dirs.split(",")]
        if len(existing_links) > 0: existing_links = [x.strip() for x in existing_links.split(",")]
        if len(existing_files) > 0: existing_files = [x.strip() for x in existing_files.split(",")]

        data = {
            'path': path,
            'current_hash': kwargs.get('current_hash'),
            'current_dtg_latest': kwargs.get('current_dtg_latest', time()),
            'current_dtg_first': kwargs.get('current_dtg_latest', time()),
            'dirs': request_dirs_string,
            'files': request_files_string,
            'links': request_links_string
        }

        logger.debug(f"Prepared data for path {path}: hash={data['current_hash']}, dirs={len(request_dirs_list)}, files={len(request_files_list)}, links={len(request_links_list)}")

        # Prep DB query
        # Case 1: Hash unchanged - only update the current hash latest dtg
        if existing_hash and existing_hash == data['current_hash']:
            logger.debug(f"Hash unchanged for {path}, updating timestamp only")
            query = """
            UPDATE hashtable 
            SET current_dtg_latest = %(current_dtg_latest)s
            WHERE path = %(path)s
            """
        # Case 2: Hash changed, update existing entry
        elif existing_hash:
            logger.debug(f"Hash changed for {path}, updating record")
            # Modify previous hash data to reflect the update
            data['prev_hash'] = existing_hash
            data['prev_dtg_latest'] = existing_dtg_latest
            # Add current path since we are modifying its hash
            modified.update([path])
            # Get added dirs, files, links
            logger.debug(f"Existing dirs: {existing_dirs}")
            logger.debug(f"New dirs: {request_dirs_list}")
            created.update([f"{path}/{x}" for x in set(request_dirs_list) - set(existing_dirs)])
            created.update([f"{path}/{x}" for x in set(request_files_list) - set(existing_files)])
            created.update([f"{path}/{x}" for x in set(request_links_list) - set(existing_links)])
            # Get deleted dirs, files, links
            deleted.update([f"{path}/{x}" for x in set(existing_dirs) - set(request_dirs_list)])
            deleted.update([f"{path}/{x}" for x in set(existing_files) - set(request_files_list)])
            deleted.update([f"{path}/{x}" for x in set(existing_links) - set(request_links_list)])
            # Prune deleted paths from the database
            for del_path in deleted:
                self.delete_record(del_path)

            query = """
            UPDATE hashtable 
            SET current_hash = %(current_hash)s,
                current_dtg_latest = %(current_dtg_latest)s,
                current_dtg_first = %(current_dtg_first)s,
                prev_hash = %(prev_hash)s,
                prev_dtg_latest = %(prev_dtg_latest)s,
                dirs = %(dirs)s, 
                files = %(files)s, 
                links = %(links)s
            WHERE path = %(path)s
            """

        # Case 3: New db entry (sql DB enforces "current_hash" not null)
        else:
            # Add current path since we are modifying its hash
            modified.update([path])
            # Get added dirs, files, links
            created.update([f"{path}/{x}" for x in set(existing_dirs)])
            created.update([f"{path}/{x}" for x in set(existing_files)])
            created.update([f"{path}/{x}" for x in set(existing_links)])

            query = """
            INSERT INTO hashtable (
                path, current_hash, current_dtg_latest, current_dtg_first,
                dirs, files, links
            ) VALUES (
                %(path)s, %(current_hash)s, %(current_dtg_latest)s, %(current_dtg_first)s,
                %(dirs)s, %(files)s, %(links)s
            ) AS entry
            ON DUPLICATE KEY UPDATE
                current_hash = entry.current_hash,
                current_dtg_latest = entry.current_dtg_latest,
                current_dtg_first = entry.current_dtg_first,
                dirs = entry.dirs,
                files = entry.files,
                links = entry.links
            """

        changes = {'modified': list(modified), 'created': list(created), 'deleted': list(deleted)}
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, data)
                logger.info(f"Successfully updated database for path: {path}")
                logger.debug(f"Changes: modified={len(modified)}, created={len(created)}, deleted={len(deleted)}")
                return changes
        except Error as e:
            logger.error(f"Error inserting/updating record: {e}")
            return None

    def get_hash_record(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get a single record by path.

        Args:
            path: Path to retrieve

        Returns:
            Dictionary with record data or None if not found or an error occurred
        """
        query = "SELECT * FROM hashtable WHERE path = %s"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, (path,))
                result = cursor.fetchone()
                if result:
                    logger.debug(f"Found record for path: {path}")
                else:
                    logger.debug(f"No record found for path: {path}")
                return result
        except Error as e:
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
        query = "SELECT current_hash FROM hashtable WHERE path = %s"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (path,))
                result = cursor.fetchone()
                if result:
                    logger.debug(f"Found hash for path: {path}")
                else:
                    logger.debug(f"No hash found for path: {path}")
                return result[0] if result else None
        except Error as e:
            logger.error(f"Error fetching hash: {e}")
            return None

    def delete_record(self, path: str) -> bool:
        """
        Delete a record by path.

        Args:
            path: Path to delete

        Returns:
            True if record was deleted, False if not found or an error occurred
        """
        query = "DELETE FROM hashtable WHERE path = %s"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (path,))
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Deleted record for path: {path}")
                else:
                    logger.debug(f"No record found to delete for path: {path}")
                return deleted
        except Error as e:
            logger.error(f"Error deleting record: {e}")
            return False





    def get_all_records(self) -> List[Dict[str, Any]]:
        """
        Get all records from the hashtable.

        Returns:
            List of dictionaries containing record data, ordered by most recent update first.
            Empty list if an error occurred.
        """
        query = "SELECT * FROM hashtable ORDER BY current_dtg_latest DESC"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query)
                results = cursor.fetchall()
                logger.debug(f"Retrieved {len(results)} records from hashtable")
                return results
        except Error as e:
            logger.error(f"Error fetching all records: {e}")
            return []

    # def update_hash(self, path: str, **kwargs) -> bool:
    #     """Update specific fields for a record"""
    #     if not kwargs:
    #         return False
    #
    #     # Build dynamic update query
    #     set_clauses = []
    #     values = []
    #
    #     for key, value in kwargs.items():
    #         if key in ['current_hash', 'target_hash', 'prev_hash', 'dirs', 'files', 'links']:
    #             set_clauses.append(f"{key} = %s")
    #             values.append(value)
    #         elif key in ['current_dtg_latest', 'current_dtg_first', 'prev_dtg_latest']:
    #             set_clauses.append(f"{key} = %s")
    #             values.append(value)
    #
    #     if not set_clauses:
    #         return False
    #
    #     query = f"UPDATE hashtable SET {', '.join(set_clauses)} WHERE path = %s"
    #     values.append(path)
    #
    #     try:
    #         with self.get_connection() as conn:
    #             cursor = conn.cursor()
    #             cursor.execute(query, values)
    #             return cursor.rowcount > 0
    #     except Error as e:
    #         print(f"Error updating record: {e}")
    #         return False


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
        # Get the hash record for the root path
        base_record = self.get_hash_record(root_path)

        # If the root path doesn't exist or has no timestamp, return just the root path
        if not base_record or 'current_dtg_latest' not in base_record:
            logger.info(f"Root path not found or has no timestamp: {root_path}")
            return [root_path]

        # Get the directories from the root path
        dirs_string = base_record.get('dirs', '')
        if not dirs_string:
            logger.info(f"No child directories found for root path: {root_path}")
            return [root_path]

        # Convert the comma-separated string to a list
        dirs = [d.strip() for d in dirs_string.split(',') if d.strip()]
        if not dirs:
            logger.info(f"No valid child directories found for root path: {root_path}")
            return [root_path]

        # Build a list of (timestamp, directory) tuples
        dir_timestamps = []
        for directory in dirs:
            full_path = f"{root_path}/{directory}"
            dir_record = self.get_hash_record(full_path)

            if dir_record and 'current_dtg_latest' in dir_record:
                timestamp = dir_record['current_dtg_latest']
                dir_timestamps.append((timestamp, full_path))
            else:
                # If a directory has no timestamp, consider it very old
                dir_timestamps.append((0, full_path))

        # Sort by timestamp (oldest first)
        ordered_dirs = [directory for _, directory in sorted(dir_timestamps)]

        # Calculate number of directories to return
        update_num = max(1, int(len(dirs) * percent / 100))
        update_num = min(update_num, len(dirs))

        logger.info(f"Returning {update_num} oldest directories for update")
        return ordered_dirs[:update_num]

    def search_by_hash(self, hash_value: str, hash_type: str = 'current') -> List[Dict[str, Any]]:
        """
        Search records by hash value.

        Args:
            hash_value: Hash value to search for
            hash_type: Type of hash to search ('current', 'target', or 'prev')

        Returns:
            List of dictionaries containing matching records

        Raises:
            ValueError: If hash_type is not one of the valid types
        """
        valid_types = ['current', 'target', 'prev']
        if hash_type not in valid_types:
            logger.error(f"Invalid hash_type: {hash_type}")
            raise ValueError(f"hash_type must be one of: {valid_types}")

        column = f"{hash_type}_hash"
        query = f"SELECT * FROM hashtable WHERE {column} = %s"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, (hash_value,))
                results = cursor.fetchall()
                logger.debug(f"Found {len(results)} records with {hash_type} hash: {hash_value}")
                return results
        except Error as e:
            logger.error(f"Error searching by hash: {e}")
            return []

    def get_tables(self, detailed: bool = False) -> List[Dict[str, Any]]:
        """
        Get information about tables in the database.

        Args:
            detailed: If True, returns additional table information

        Returns:
            List of dictionaries with table information
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if detailed:
                    # Get detailed table information
                    cursor.execute("""
                        SELECT 
                            TABLE_NAME,
                            TABLE_TYPE,
                            ENGINE,
                            TABLE_ROWS,
                            DATA_LENGTH,
                            CREATE_TIME
                        FROM information_schema.TABLES 
                        WHERE TABLE_SCHEMA = %s
                    """, (self.database,))

                    results = cursor.fetchall()
                    tables_info = []

                    for row in results:
                        name, table_type, engine, rows, size, created = row
                        size_kb = size // 1024 if size else 0
                        created_str = created.strftime('%Y-%m-%d') if created else None

                        tables_info.append({
                            'name': name,
                            'type': table_type,
                            'engine': engine,
                            'rows': rows or 0,
                            'size_kb': size_kb,
                            'created': created_str
                        })

                    logger.debug(f"Retrieved detailed information for {len(tables_info)} tables")
                    return tables_info
                else:
                    # Simple table list
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()

                    table_names = []
                    if tables:
                        for table in tables:
                            table_names.append({'name': table[0]})

                    logger.debug(f"Retrieved {len(table_names)} table names")
                    return table_names

        except Error as e:
            logger.error(f"Error retrieving table information: {e}")
            return []

    def show_all_tables(self, detailed: bool = False) -> List[str]:
        """
        Show all tables in the database (prints to console).

        Args:
            detailed: If True, shows additional table information

        Returns:
            List of table names
        """
        tables_info = self.get_tables(detailed)

        if not tables_info:
            logger.warning("No tables found or error occurred")
            return []

        if detailed:
            print(f"Detailed table information for database '{self.database}':")
            print("-" * 80)
            print(f"{'Table Name':<20} {'Type':<10} {'Engine':<10} {'Rows':<10} {'Size (KB)':<12} {'Created'}")
            print("-" * 80)

            table_names = []
            for table in tables_info:
                print(
                    f"{table['name']:<20} {table['type']:<10} {table['engine'] or 'N/A':<10} "
                    f"{table['rows']:<10} {table['size_kb']:<12} {table['created'] or 'N/A'}"
                )
                table_names.append(table['name'])

            return table_names
        else:
            print(f"Tables in database '{self.database}':")
            print("-" * 40)

            table_names = []
            if tables_info:
                for table in tables_info:
                    print(f"  • {table['name']}")
                    table_names.append(table['name'])
            else:
                print("  No tables found.")

            return table_names


    @staticmethod
    def string_cleaner(value: Any) -> Tuple[str, List[str]]:
        """
        Clean and normalize string or list values for database storage.

        Args:
            value: String or list to clean

        Returns:
            Tuple containing (comma-separated string, list of values)
        """
        if value is None:
            return "", []

        if isinstance(value, list):
            clean_list = [x.strip() for x in value]
            clean_string = ",".join(clean_list)
        else:
            # Handle string that might be formatted as a list
            string = str(value)
            if len(string) > 0 and string[0] == "[": 
                string = string[1:]
            if len(string) > 0 and string[-1] == "]": 
                string = string[:-1]

            clean_list = [x.strip() for x in string.split(",") if x.strip()]
            clean_string = ",".join(clean_list)

        return clean_string, clean_list
