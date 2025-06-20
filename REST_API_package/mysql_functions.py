import mysql.connector
from mysql.connector import Error
from time import time
from contextlib import contextmanager
from typing import Optional, Dict, Any


class HashTableDB:
    def __init__(self, host, database, user, password, port=3306):

        self.config = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': port,
            'autocommit': True,
            'raise_on_warnings': True
        }
        self.database = database

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        connection = None
        try:
            connection = mysql.connector.connect(**self.config)
            yield connection
        except Error as e:
            print(f"Database error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()

    def insert_or_update_hash(self, path: str, **kwargs) -> Optional[Dict[str, set]]:
        """Insert new record or update existing one"""
        # First, check if record exists and get current columns for possible modification
        existing_hash, existing_dtg_latest = None, None
        existing_dirs, existing_links, existing_files = [], [], []
        print(path)
        print(type(path))
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT current_hash, current_dtg_latest, dirs, links, files FROM hashtable WHERE path = %s", (path,))
                result = cursor.fetchone()
                if result:
                    existing_hash, existing_dtg_latest, existing_dirs, existing_links, existing_files = result
        except Error as e:
            print(f"Error checking existing record: {e}")
            return None
        # Initialize changes dictionary
        modified, created, deleted = set(), set(), set()

        # print(kwargs.get('dirs'))
        # print(type(kwargs.get('dirs')))
        # Convert lists formatted values to strings for db storage
        request_dirs_string, request_dirs_list = string_cleaner(kwargs.get('dirs'))
        request_files_string, request_files_list = string_cleaner(kwargs.get('files'))
        request_links_string, request_links_list = string_cleaner(kwargs.get('links'))

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

        # Prep DB query
        # Case 1: Hash unchanged - only update the current hash latest dtg
        if existing_hash and existing_hash == data['current_hash']:
            query = """
            UPDATE hashtable 
            SET current_dtg_latest = %(current_dtg_latest)s
            WHERE path = %(path)s
            """
        # Case 2: Hash changed, update existing entry
        elif existing_hash:
            # Modify previous hash data to reflect the update
            data['prev_hash'] = existing_hash
            data['prev_dtg_latest'] = existing_dtg_latest
            # Add current path since we are modifying its hash
            modified.update([path])
            # Get added dirs, files, links
            print(existing_dirs)
            print(type(existing_dirs))
            print(kwargs['dirs'])
            print(type(kwargs['dirs']))
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
                return changes
        except Error as e:
            print(f"Error inserting/updating record: {e}")
            return None

    def get_hash_record(self, path: str) -> Optional[Dict[str, Any]]:
        """Get a single record by path"""
        query = "SELECT * FROM hashtable WHERE path = %s"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, (path,))
                result = cursor.fetchone()
                return result
        except Error as e:
            print(f"Error fetching record: {e}")
            return None

    def get_single_hash_record(self, path: str) -> Optional[str]:
        """Get a single record by path"""
        query = "SELECT current_hash FROM hashtable WHERE path = %s"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (path,))
                result = cursor.fetchone()
                return result
        except Error as e:
            print(f"Error fetching record: {e}")
            return None

    def delete_record(self, path: str) -> bool:
        """Delete a record by path"""
        query = "DELETE FROM hashtable WHERE path = %s"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (path,))
                return cursor.rowcount > 0
        except Error as e:
            print(f"Error deleting record: {e}")
            return False





    def get_all_records(self) -> list:
        """Get all records"""
        query = "SELECT * FROM hashtable ORDER BY current_dtg_latest DESC"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query)
                results = cursor.fetchall()
                return results
        except Error as e:
            print(f"Error fetching records: {e}")
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


    def search_by_hash(self, hash_value: str, hash_type: str = 'current') -> list:
        """Search records by hash value"""
        valid_types = ['current', 'target', 'prev']
        if hash_type not in valid_types:
            raise ValueError(f"hash_type must be one of: {valid_types}")

        column = f"{hash_type}_hash"
        query = f"SELECT * FROM hashtable WHERE {column} = %s"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, (hash_value,))
                results = cursor.fetchall()
                return results
        except Error as e:
            print(f"Error searching by hash: {e}")
            return []

    def show_all_tables(self, detailed: bool = False) -> list[str]:
        """
        Show all tables in the database
        Args:
            detailed: If True, shows additional table information
        Returns:
            List of table names
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

                    print(f"Detailed table information for database '{self.database}':")
                    print("-" * 80)
                    print(f"{'Table Name':<20} {'Type':<10} {'Engine':<10} {'Rows':<10} {'Size (KB)':<12} {'Created'}")
                    print("-" * 80)

                    table_names = []
                    for row in results:
                        name, table_type, engine, rows, size, created = row
                        size_kb = size // 1024 if size else 0
                        created_str = created.strftime('%Y-%m-%d') if created else 'N/A'

                        print(
                            f"{name:<20} {table_type:<10} {engine or 'N/A':<10} {rows or 0:<10} {size_kb:<12} {created_str}")
                        table_names.append(name)

                    return table_names

                else:
                    # Simple table list
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()

                    print(f"Tables in database '{self.database}':")
                    print("-" * 40)

                    table_names = []
                    if tables:
                        for table in tables:
                            table_name = table[0]
                            print(f"  • {table_name}")
                            table_names.append(table_name)
                    else:
                        print("  No tables found.")

                    return table_names


        except Error as e:
            print(f"Error executing query: {e}")
            return []

        finally:
            cursor.close()


# HELPERS
def string_cleaner(string: str) -> tuple[str, list]:
    if string is None:
        return "", []
    if isinstance(string, list):
        clean_list = [x.strip() for x in string]
        clean_string = ",".join(clean_list)
    else:
        if "[" == string[0]: string = string[1:-1]
        if "]" == string[-1]: string = string[:-1]
        clean_list = [x.strip() for x in string.split(",")]
        clean_string = ",".join(clean_list)
    return clean_string, clean_list