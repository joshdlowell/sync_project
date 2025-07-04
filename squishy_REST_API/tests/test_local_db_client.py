import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from squishy_REST_API.configuration import config
# Import both implementations
from squishy_REST_API.database_client.local_mysql import MYSQLConnection
from squishy_REST_API.database_client.local_memory import LocalMemoryConnection


class DBConnectionTestMixin():
    """
    Mixin class containing all the test methods for the DBConnection interface.
    This ensures both implementations are tested with the same test cases.
    """

    def setUp(self):
        """This should be overridden in each test class to set up self.db
        """
        self.db = None  # Add this line
        raise NotImplementedError("Subclasses must implement setUp")

    def test_insert_hash_record_missing_required_fields(self):
        """Test that ValueError is raised when required fields are missing"""
        # Missing 'current_hash'
        record = {'path': '/test/path'}

        with self.assertRaises(ValueError) as context:
            self.db.insert_or_update_hash(record)

        self.assertIn("current_hash", str(context.exception))

        # Missing 'path'
        record = {'current_hash': 'abc123'}

        with self.assertRaises(ValueError) as context:
            self.db.insert_or_update_hash(record)

        self.assertIn("path", str(context.exception))

    def test_update_existing_hash_record_same_hash(self):
        """Test updating an existing record with the same hash"""
        record = {
            'path': '/test/path',
            'current_hash': 'abc123',
            'dirs': ['dir1'],
            'files': ['file1.txt']
        }

        # Insert initial record
        self.db.insert_or_update_hash(record)

        # Update with same hash
        result = self.db.insert_or_update_hash(record)

        self.assertIsNotNone(result)
        self.assertTrue(result)

    def test_update_existing_hash_record_different_hash(self):
        """Test updating an existing record with a different hash"""
        initial_record = {
            'path': '/test/path',
            'current_hash': 'abc123',
            'dirs': ['dir1'],
            'files': ['file1.txt']
        }

        # Insert initial record
        self.db.insert_or_update_hash(initial_record)

        # Update with different hash
        updated_record = {
            'path': '/test/path',
            'current_hash': 'def456',
            'dirs': ['dir1', 'dir2'],
            'files': ['file1.txt', 'file2.txt']
        }

        result = self.db.insert_or_update_hash(updated_record)

        self.assertIsNotNone(result)
        self.assertTrue(result)

    def test_get_hash_record_existing(self):
        """Test retrieving an existing hash record"""
        record = {
            'path': '/test/path',
            'current_hash': 'abc123',
            'dirs': ['dir1'],
            'files': ['file1.txt']
        }

        self.db.insert_or_update_hash(record)
        retrieved = self.db.get_hash_record('/test/path')

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['path'], '/test/path')
        self.assertEqual(retrieved['current_hash'], 'abc123')

    def test_get_hash_record_nonexistent(self):
        """Test retrieving a non-existent hash record"""
        result = self.db.get_hash_record('/nonexistent/path')
        self.assertIsNone(result)

    def test_get_single_hash_record_existing(self):
        """Test retrieving just the hash for an existing record"""
        record = {
            'path': '/test/path',
            'current_hash': 'abc123',
            'dirs': ['dir1']
        }

        self.db.insert_or_update_hash(record)
        hash_value = self.db.get_single_hash_record('/test/path')

        self.assertEqual(hash_value, 'abc123')

    def test_get_single_hash_record_nonexistent(self):
        """Test retrieving hash for a non-existent record"""
        result = self.db.get_single_hash_record('/nonexistent/path')
        self.assertIsNone(result)

    def test_get_single_timestamp_existing(self):
        """Test retrieving timestamp for an existing record"""
        record = {
            'path': '/test/path',
            'current_hash': 'abc123'
        }

        self.db.insert_or_update_hash(record)
        timestamp = self.db.get_single_timestamp('/test/path')

        self.assertIsInstance(timestamp, int)
        self.assertGreater(timestamp, 0)

    def test_get_single_timestamp_nonexistent(self):
        """Test retrieving timestamp for a non-existent record"""
        result = self.db.get_single_timestamp('/nonexistent/path')
        self.assertIsNone(result)

    def test_get_oldest_updates_nonexistent_path(self):
        """Test get_oldest_updates with non-existent path"""
        result = self.db.get_oldest_updates('/nonexistent/path')
        self.assertEqual(result, ['/nonexistent/path'])

    def test_get_oldest_updates_existing_path(self):
        """Test get_oldest_updates with existing path"""
        # Create parent record
        parent_record = {
            'path': '/parent',
            'current_hash': 'parent123',
            'dirs': ['child1', 'child2'],
            'files': ['file1.txt']
        }
        self.db.insert_or_update_hash(parent_record)

        # Create child records with different timestamps
        time.sleep(0.01)  # Small delay to ensure different timestamps
        child1_record = {
            'path': '/parent/child1',
            'current_hash': 'child1_hash'
        }
        self.db.insert_or_update_hash(child1_record)

        time.sleep(0.01)
        child2_record = {
            'path': '/parent/child2',
            'current_hash': 'child2_hash'
        }
        self.db.insert_or_update_hash(child2_record)

        time.sleep(0.01)
        file_record = {
            'path': '/parent/file1.txt',
            'current_hash': 'file_hash'
        }
        self.db.insert_or_update_hash(file_record)

        result = self.db.get_oldest_updates('/parent', percent=50)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_get_priority_updates_empty(self):
        """Test get_priority_updates when no priority updates exist"""
        result = self.db.get_priority_updates()
        self.assertEqual(result, [])

    def test_get_priority_updates_with_targets(self):
        """Test get_priority_updates with target hashes"""
        # This test may need to be adapted based on how target_hash is set
        # For now, we'll test the empty case and the structure
        result = self.db.get_priority_updates()
        self.assertIsInstance(result, list)

    def test_put_log_success(self):
        """Test successful log insertion"""
        log_data = {
            'site_id': 'test1',
            'log_level': 'INFO',
            'summary_message': 'Test log message',
            'detailed_message': 'Detailed test information'
        }

        result = self.db.put_log(log_data)
        self.assertTrue(result)

    def test_put_log_missing_summary(self):
        """Test log insertion without summary message"""
        log_data = {
            'site_id': 'test1',
            'log_level': 'INFO',
            'detailed_message': 'Detailed test information'
        }

        result = self.db.put_log(log_data)
        self.assertFalse(result)

    def test_put_log_site_id_too_long(self):
        """Test log insertion without summary message"""
        log_data = {
            'site_id': 'test_site',
            'log_level': 'INFO',
            'summary_message': 'summary test information'
        }

        result = self.db.put_log(log_data)
        self.assertFalse(result)

    def test_put_log_minimal_data(self):
        """Test log insertion with minimal data"""
        log_data = {
            'summary_message': 'Minimal test message'
        }

        result = self.db.put_log(log_data)
        self.assertTrue(result)

    def test_get_logs_default(self):
        """Test getting logs with default parameters"""
        # Insert some test logs
        for i in range(5):
            self.db.put_log({'summary_message': f'Test message {i}'})

        result = self.db.get_logs()

        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 5)

    def test_get_logs_with_limit(self):
        """Test getting logs with limit"""
        # Insert test logs
        for i in range(10):
            self.db.put_log({'summary_message': f'Test message {i}'})

        result = self.db.get_logs(limit=3)

        self.assertIsInstance(result, list)
        self.assertLessEqual(len(result), 3)

    def test_get_logs_with_offset(self):
        """Test getting logs with offset"""
        # Insert test logs
        for i in range(5):
            self.db.put_log({'summary_message': f'Test message {i}'})

        result = self.db.get_logs(offset=2)

        self.assertIsInstance(result, list)

    def test_get_logs_invalid_parameters(self):
        """Test get_logs with invalid parameters"""
        with self.assertRaises(ValueError):
            self.db.get_logs(limit=-1)

        with self.assertRaises(ValueError):
            self.db.get_logs(offset=-1)

        with self.assertRaises(ValueError):
            self.db.get_logs(order_direction='INVALID')

        with self.assertRaises(ValueError):
            self.db.get_logs(order_by='invalid_column')

    def test_delete_log_entry_existing(self):
        """Test deleting an existing log entry"""
        # Insert a log entry
        log_data = {'summary_message': 'Test log for deletion'}
        log_id = self.db.put_log(log_data)

        # Delete the log entry
        result = self.db.delete_log_entry(log_id)
        self.assertTrue(result)

    def test_delete_log_entry_nonexistent(self):
        """Test deleting a non-existent log entry"""
        result = self.db.delete_log_entry(99999)
        self.assertFalse(result)

    def test_life_check(self):
        """Test database life check"""
        result = self.db.life_check()
        self.assertTrue(result)

    def test_delete_hash_entry(self):
        """Test the private _delete_hash_entry method"""
        # Insert a record first
        record = {
            'path': '/test/delete',
            'current_hash': 'delete123'
        }
        self.db.insert_or_update_hash(record)

        # Verify it exists
        self.assertIsNotNone(self.db.get_hash_record('/test/delete'))

        # Delete it
        result = self.db._delete_hash_entry('/test/delete')
        self.assertTrue(result)

        # Verify it's gone
        self.assertIsNone(self.db.get_hash_record('/test/delete'))

    def test_delete_hash_entry_nonexistent(self):
        """Test deleting a non-existent hash entry"""
        result = self.db._delete_hash_entry('/nonexistent/path')
        self.assertFalse(result)

    def test_insert_new_hash_record(self):
        """Test inserting a new hash record"""
        record = {
            'path': '/test/path/new',
            'current_hash': 'abc123',
            'dirs': ['dir1', 'dir2'],
            'files': ['file1.txt', 'file2.txt'],
            'links': ['link1']
        }

        result = self.db.insert_or_update_hash(record)

        self.assertIsNotNone(result)
        self.assertTrue(result)


# class TestMYSQLConnectionMock(unittest.TestCase, DBConnectionTestMixin):
#     """Test cases for MySQL implementation"""
#
#     def setUp(self):
#         """Set up MySQL connection with mock"""
#         # Mock the mysql.connector to avoid actual database connections
#         self.mock_connection = MagicMock()
#         self.mock_cursor = MagicMock()
#         self.mock_connection.cursor.return_value.__enter__.return_value = self.mock_cursor
#         self.mock_connection.cursor.return_value.__exit__.return_value = None
#         self.mock_connection.is_connected.return_value = True
#
#         # Create connection factory that returns our mock
#         def mock_factory(**kwargs):
#             return self.mock_connection
#
#         self.db = MYSQLConnection(
#             host='localhost',
#             database='test_db',
#             user='test_user',
#             password='test_pass',
#             connection_factory=mock_factory
#         )
#
#     def test_mysql_specific_connection_handling(self):
#         """Test MySQL-specific connection handling"""
#         # Test successful connection
#         with self.db._get_connection() as conn:
#             self.assertEqual(conn, self.mock_connection)
#
#         # Test connection closing
#         self.mock_connection.close.assert_called()
#
#     def test_mysql_error_handling(self):
#         """Test MySQL error handling"""
#         from mysql.connector import Error
#
#         # Make the connection factory raise an error
#         def error_factory(**kwargs):
#             raise Error("Connection failed")
#
#         self.db.connection_factory = error_factory
#
#         with self.assertRaises(Error):
#             with self.db._get_connection() as conn:
#                 pass
#
#     def test_mysql_insert_queries(self):
#         """Test that MySQL queries are properly formed"""
#         # Mock fetchone to return None (no existing record)
#         self.mock_cursor.fetchone.return_value = None
#
#         record = {
#             'path': '/test/path',
#             'current_hash': 'abc123',
#             'dirs': ['dir1'],
#             'files': ['file1.txt'],
#             'links': []
#         }
#
#         result = self.db.insert_or_update_hash(record)
#
#         # Verify that execute was called
#         self.mock_cursor.execute.assert_called()
#
#         # Check that the result structure is correct
#         self.assertIsInstance(result, dict)
#         self.assertIn('created', result)
#         self.assertIn('modified', result)
#         self.assertIn('deleted', result)

class TestMYSQLConnection(unittest.TestCase, DBConnectionTestMixin):
    """Test cases for MySQL implementation with real database"""
    @classmethod
    def setUpClass(cls):
        """Set up test database - runs once for all tests"""
        cls.test_db_config = {
            'host':'mysql-squishy-db',
            'database':'squishy_db',
            'user':'your_app_user',
            'password':'your_user_password'
        }

    def setUp(self):
        """Set up MySQL connection with mock"""
        try:
            self.db = MYSQLConnection(
                host=self.test_db_config['host'],
                database=self.test_db_config['database'],
                user=self.test_db_config['user'],
                password=self.test_db_config['password']
            )
        except Exception as e:
            print(f"Error creating database instance: {e}")
            return None

    def tearDown(self):
        """Clean up after each test"""
        if hasattr(self, 'db'):
            self._clear_test_data()

    def _clear_test_data(self):
        """Clear test data from database"""
        try:
            with self.db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM hashtable WHERE path LIKE '/test/%'")
                conn.commit()
        except Exception:
            pass  # Ignore cleanup errors

    def test_mysql_specific_connection_handling(self):
        """Test MySQL-specific connection handling"""
        # Test successful connection
        with self.db._get_connection() as conn:
            self.assertIsNotNone(conn)
            self.assertTrue(conn.is_connected())

        # Connection should be properly managed by context manager
        # The connection might be pooled, so we can't test if it's closed directly

    def test_mysql_error_handling(self):
        """Test MySQL error handling"""
        # Create a connection with invalid credentials to test error handling
        invalid_config = self.test_db_config.copy()
        invalid_config['password'] = 'invalid_password'

        with self.assertRaises(Exception):
            invalid_db = MYSQLConnection(**invalid_config)
            with invalid_db._get_connection() as conn:
                pass

    def test_mysql_insert_queries(self):
        """Test that MySQL queries work with real database"""
        record = {
            'path': '/test/path/mysql_test',
            'current_hash': 'abc123def456',
            'dirs': ['dir1', 'dir2'],
            'files': ['file1.txt', 'file2.py'],
            'links': ['link1']
        }

        # Insert the record
        result = self.db.insert_or_update_hash(record)

        # Verify the result
        self.assertTrue(result)

        # Verify the record was actually inserted
        with self.db._get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(
                    "SELECT * FROM hashtable WHERE path = %s",
                    (record['path'],)
                )
                stored_record = cursor.fetchone()

                self.assertIsNotNone(stored_record)
                self.assertEqual(stored_record['path'], record['path'])
                self.assertEqual(stored_record['current_hash'], record['current_hash'])

    def test_mysql_update_queries(self):
        """Test updating existing records"""
        # First insert a record
        original_record = {
            'path': '/test/path/update_test',
            'current_hash': 'original_hash',
            'dirs': ['original_dir'],
            'files': ['original_file.txt'],
            'links': []
        }

        self.db.insert_or_update_hash(original_record)

        # Update the record
        updated_record = original_record.copy()
        updated_record['current_hash'] = 'updated_hash'
        updated_record['files'] = ['original_file.txt', 'new_file.txt']

        result = self.db.insert_or_update_hash(updated_record)

        # Verify update was successful
        self.assertIsNotNone(result)
        self.assertTrue(result)

        # Verify the record was actually updated
        with self.db._get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(
                    "SELECT * FROM hashtable WHERE path = %s",
                    (updated_record['path'],)
                )
                stored_record = cursor.fetchone()

                self.assertEqual(stored_record['current_hash'], 'updated_hash')

    def test_mysql_connection_recovery(self):
        """Test connection recovery after connection loss"""
        # This test verifies that the connection can be re-established
        # First, verify normal operation
        with self.db._get_connection() as conn:
            self.assertTrue(conn.is_connected())

        # Simulate connection loss by closing the connection pool
        # (This depends on your MYSQLConnection implementation)
        if hasattr(self.db, '_connection_pool'):
            self.db._connection_pool.close()

        # The next operation should re-establish connection
        record = {
            'path': '/test/path/recovery_test',
            'current_hash': 'recovery_hash',
            'dirs': [],
            'files': ['recovery_file.txt'],
            'links': []
        }

        # This should work even after connection loss
        result = self.db.insert_or_update_hash(record)
        self.assertTrue(result)

    def test_insert_new_hash_record(self):
        """Test inserting a new hash record"""
        record = {
            'path': '/test/path/new',
            'current_hash': 'abc123',
            'dirs': ['dir1', 'dir2'],
            'files': ['file1.txt', 'file2.txt'],
            'links': ['link1']
        }
        # remove the record if it exists
        _ = self.db._delete_hash_entry(record['path'])

        result = self.db.insert_or_update_hash(record)

        self.assertIsNotNone(result)
        self.assertTrue(result)


class TestLocalMemoryConnection(unittest.TestCase, DBConnectionTestMixin):
    """Test cases for Local Memory implementation"""

    def setUp(self):
        """Set up local memory connection"""
        self.db = LocalMemoryConnection()

    def test_local_memory_specific_features(self):
        """Test features specific to local memory implementation"""
        # Test clear_all_data
        self.db.put_log({'summary_message': 'Test'})
        self.db.insert_or_update_hash({'path': '/test', 'current_hash': 'hash123'})

        self.db.clear_all_data()

        self.assertEqual(len(self.db.hashtable), 0)
        self.assertEqual(len(self.db.logs), 0)
        self.assertEqual(self.db._next_log_id, 1)

    def test_get_stats(self):
        """Test the get_stats method"""
        # Initially empty
        stats = self.db.get_stats()
        self.assertEqual(stats['hashtable_records'], 0)
        self.assertEqual(stats['log_entries'], 0)
        self.assertEqual(stats['next_log_id'], 1)

        # Add some data
        self.db.insert_or_update_hash({'path': '/test', 'current_hash': 'hash123'})
        self.db.put_log({'summary_message': 'Test log'})

        stats = self.db.get_stats()
        self.assertEqual(stats['hashtable_records'], 1)
        self.assertEqual(stats['log_entries'], 2)
        self.assertEqual(stats['next_log_id'], 3)

    def test_hashed_path_generation(self):
        """Test that hashed paths are generated correctly"""
        test_path = "/test/path"
        hashed = self.db._generate_hashed_path(test_path)

        self.assertIsInstance(hashed, str)
        self.assertEqual(len(hashed), 64)  # SHA256 produces 64 character hex strings

    def test_data_isolation(self):
        """Test that returned data doesn't affect internal storage"""
        record = {'path': '/test', 'current_hash': 'hash123'}
        self.db.insert_or_update_hash(record)

        retrieved = self.db.get_hash_record('/test')
        retrieved['current_hash'] = 'modified'

        # Original should be unchanged
        original = self.db.get_hash_record('/test')
        self.assertEqual(original['current_hash'], 'hash123')


class TestInterfaceCompatibility(unittest.TestCase):
    """Test that both implementations have compatible interfaces"""

    def setUp(self):
        self.local_db = LocalMemoryConnection()

        # Mock MySQL connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.cursor.return_value.__exit__.return_value = None
        mock_connection.is_connected.return_value = True

        def mock_factory(**kwargs):
            return mock_connection

        self.mysql_db = MYSQLConnection(
            host='localhost',
            database='test_db',
            user='test_user',
            password='test_pass',
            connection_factory=mock_factory
        )

    def test_method_signatures_match(self):
        """Test that both implementations have the same method signatures"""
        local_methods = [method for method in dir(self.local_db) if
                         not method.startswith('_') or method == '_delete_hash_entry']
        mysql_methods = [method for method in dir(self.mysql_db) if
                         not method.startswith('_') or method == '_delete_hash_entry']

        # Filter out implementation-specific methods
        exclude_methods = {'clear_all_data', 'get_stats', 'config', 'database', 'connection_factory', 'hashtable',
                           'logs'}

        local_methods = [m for m in local_methods if m not in exclude_methods]
        mysql_methods = [m for m in mysql_methods if m not in exclude_methods]

        self.assertEqual(set(local_methods), set(mysql_methods))

    def test_return_types_compatible(self):
        """Test that both implementations return compatible types"""
        # Test with local implementation
        local_result = self.local_db.insert_or_update_hash({'path': '/test', 'current_hash': 'hash123'})
        local_hash = self.local_db.get_single_hash_record('/test')
        local_record = self.local_db.get_hash_record('/test')
        local_logs = self.local_db.get_logs()
        local_life = self.local_db.life_check()

        # Verify types
        self.assertIsInstance(local_result, bool)
        self.assertIsInstance(local_hash, str)
        self.assertIsInstance(local_record, dict)
        self.assertIsInstance(local_logs, list)
        self.assertIsInstance(local_life, bool)


if __name__ == '__main__':
    # Create a test suite that runs all tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMYSQLConnection))
    suite.addTests(loader.loadTestsFromTestCase(TestLocalMemoryConnection))
    suite.addTests(loader.loadTestsFromTestCase(TestInterfaceCompatibility))

    # mock implementation isn't working yet
    # suite.addTests(loader.loadTestsFromTestCase(TestMYSQLConnectionMock))

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with non-zero code if tests failed
    exit(0 if result.wasSuccessful() else 1)
