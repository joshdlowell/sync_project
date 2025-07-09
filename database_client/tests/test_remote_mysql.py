import unittest
from unittest.mock import Mock, MagicMock, patch, call
import json
from mysql.connector import Error

from squishy_REST_API.remote_mysql import RemoteMYSQLConnection


class TestRemoteMYSQLConnection(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_connection_factory = Mock()
        self.mock_connection = Mock()
        self.mock_cursor = Mock()

        # Configure mock chain
        self.mock_connection_factory.return_value = self.mock_connection
        self.mock_connection.__enter__ = Mock(return_value=self.mock_connection)
        self.mock_connection.__exit__ = Mock(return_value=None)
        self.mock_connection.cursor.return_value = self.mock_cursor
        self.mock_cursor.__enter__ = Mock(return_value=self.mock_cursor)
        self.mock_cursor.__exit__ = Mock(return_value=None)
        self.mock_connection.is_connected.return_value = True

        self.db_config = {
            'host': 'localhost',
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_pass',
            'port': 3306,
            'autocommit': True,
            'raise_on_warnings': True
        }

        self.db_conn = RemoteMYSQLConnection(
            connection_factory=self.mock_connection_factory,
            **self.db_config
        )

    def test_init_with_all_params(self):
        """Test initialization with all parameters."""
        self.assertEqual(self.db_conn.config['host'], 'localhost')
        self.assertEqual(self.db_conn.config['database'], 'test_db')
        self.assertEqual(self.db_conn.config['user'], 'test_user')
        self.assertEqual(self.db_conn.config['password'], 'test_pass')
        self.assertEqual(self.db_conn.config['port'], 3306)
        self.assertEqual(self.db_conn.database, 'test_db')

    def test_init_with_default_port(self):
        """Test initialization with default port."""
        db_conn = RemoteMYSQLConnection(
            host='localhost',
            database='test_db',
            user='test_user',
            password='test_pass'
        )
        self.assertEqual(db_conn.config['port'], 3306)

    def test_get_connection_success(self):
        """Test successful database connection."""
        with self.db_conn._get_connection() as conn:
            self.assertEqual(conn, self.mock_connection)

        self.mock_connection_factory.assert_called_once_with(**self.db_config)
        self.mock_connection.close.assert_called_once()

    def test_get_connection_error(self):
        """Test database connection error."""
        self.mock_connection_factory.side_effect = Error("Connection failed")

        with self.assertRaises(Error):
            with self.db_conn._get_connection():
                pass

    def test_get_hash_record_success(self):
        """Test successful hash record retrieval."""
        expected_result = {
            'path': '/test/path',
            'current_hash': 'abc123',
            'dirs': ['dir1', 'dir2'],
            'files': ['file1.txt'],
            'links': []
        }

        self.mock_cursor.fetchone.return_value = expected_result

        result = self.db_conn.get_hash_record('/test/path')

        self.mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM hashtable WHERE path = %s", ('/test/path',)
        )
        self.assertEqual(result, expected_result)

    def test_get_hash_record_not_found(self):
        """Test hash record not found."""
        self.mock_cursor.fetchone.return_value = None

        result = self.db_conn.get_hash_record('/nonexistent/path')

        self.assertIsNone(result)

    def test_get_hash_record_missing_path(self):
        """Test get_hash_record with missing path."""
        with self.assertRaises(ValueError) as context:
            self.db_conn.get_hash_record('')

        self.assertIn("path value must be provided", str(context.exception))

    def test_get_hash_record_database_error(self):
        """Test get_hash_record with database error."""
        self.mock_connection_factory.side_effect = Error("Database error")

        result = self.db_conn.get_hash_record('/test/path')

        self.assertIsNone(result)

    def test_insert_or_update_hash_new_record(self):
        """Test inserting new hash record."""
        record = {
            'path': '/new/path',
            'current_hash': 'abc123',
            'dirs': ['dir1'],
            'files': ['file1.txt'],
            'links': [],
            'target_hash': 'def456',
            'session_id': 'session123'
        }

        # Mock that record doesn't exist
        self.mock_cursor.fetchone.return_value = None
        self.mock_cursor.rowcount = 1

        # Mock put_log method
        with patch.object(self.db_conn, 'put_log') as mock_put_log:
            mock_put_log.return_value = 1

            result = self.db_conn.insert_or_update_hash(record)

        self.assertTrue(result)
        self.assertEqual(self.mock_cursor.execute.call_count, 2)  # SELECT + INSERT
        mock_put_log.assert_called_once()

    def test_insert_or_update_hash_existing_record_unchanged(self):
        """Test updating existing hash record with unchanged hash."""
        record = {
            'path': '/existing/path',
            'current_hash': 'abc123',
            'dirs': ['dir1'],
            'files': ['file1.txt'],
            'links': [],
            'target_hash': 'def456',
            'session_id': 'session123'
        }

        # Mock existing record with same hash
        self.mock_cursor.fetchone.return_value = (
            'abc123', ['dir1'], [], ['file1.txt'], 'def456'
        )
        self.mock_cursor.rowcount = 1

        with patch.object(self.db_conn, 'put_log') as mock_put_log:
            mock_put_log.return_value = 1

            result = self.db_conn.insert_or_update_hash(record)

        self.assertTrue(result)
        # Should use UPDATE query for unchanged hash
        calls = self.mock_cursor.execute.call_args_list
        self.assertIn("UPDATE hashtable", calls[1][0][0])
        self.assertIn("current_dtg_latest = UNIX_TIMESTAMP()", calls[1][0][0])

    def test_insert_or_update_hash_existing_record_changed(self):
        """Test updating existing hash record with changed hash."""
        record = {
            'path': '/existing/path',
            'current_hash': 'xyz789',
            'dirs': ['dir1'],
            'files': ['file1.txt'],
            'links': [],
            'target_hash': 'def456',
            'session_id': 'session123'
        }

        # Mock existing record with different hash
        self.mock_cursor.fetchone.return_value = (
            'abc123', ['dir1'], [], ['file1.txt'], 'def456'
        )
        self.mock_cursor.rowcount = 1

        with patch.object(self.db_conn, 'put_log') as mock_put_log:
            mock_put_log.return_value = 1

            result = self.db_conn.insert_or_update_hash(record)

        self.assertTrue(result)
        # Should use UPDATE query for changed hash
        calls = self.mock_cursor.execute.call_args_list
        self.assertIn("prev_hash", calls[1][0][0])
        self.assertIn("current_hash", calls[1][0][0])

    def test_insert_or_update_hash_missing_required_fields(self):
        """Test insert_or_update_hash with missing required fields."""
        record = {'path': '/test/path'}  # Missing current_hash

        with self.assertRaises(ValueError) as context:
            self.db_conn.insert_or_update_hash(record)

        self.assertIn("current_hash", str(context.exception))

    def test_insert_or_update_hash_invalid_field_types(self):
        """Test insert_or_update_hash with invalid field types."""
        record = {
            'path': '/test/path',
            'current_hash': 'abc123',
            'dirs': 'not_a_list'  # Should be a list
        }

        with self.assertRaises(ValueError) as context:
            self.db_conn.insert_or_update_hash(record)

        self.assertIn("must be lists", str(context.exception))

    def test_get_single_field_success(self):
        """Test successful single field retrieval."""
        self.mock_cursor.fetchone.return_value = ('abc123',)

        result = self.db_conn.get_single_field('/test/path', 'current_hash')

        self.mock_cursor.execute.assert_called_once_with(
            "SELECT current_hash FROM hashtable WHERE path = %s", ('/test/path',)
        )
        self.assertEqual(result, 'abc123')

    def test_get_single_field_not_found(self):
        """Test single field not found."""
        self.mock_cursor.fetchone.return_value = None

        result = self.db_conn.get_single_field('/test/path', 'current_hash')

        self.assertIsNone(result)

    def test_get_single_field_missing_params(self):
        """Test get_single_field with missing parameters."""
        with self.assertRaises(ValueError):
            self.db_conn.get_single_field('', 'current_hash')

        with self.assertRaises(ValueError):
            self.db_conn.get_single_field('/test/path', '')

    def test_get_single_field_invalid_field(self):
        """Test get_single_field with invalid field name."""
        with self.assertRaises(ValueError) as context:
            self.db_conn.get_single_field('/test/path', 'invalid_field')

        self.assertIn("Invalid field name", str(context.exception))

    def test_get_priority_updates_success(self):
        """Test successful priority updates retrieval."""
        mock_paths = [('/path1',), ('/path2',), ('/path1/subpath',)]
        self.mock_cursor.fetchall.return_value = mock_paths

        result = self.db_conn.get_priority_updates()

        # Should return deepest paths only
        self.assertIn('/path2', result)
        self.assertIn('/path1/subpath', result)
        self.assertNotIn('/path1', result)  # Should be excluded as it has descendants

    def test_get_priority_updates_empty(self):
        """Test priority updates with no results."""
        self.mock_cursor.fetchall.return_value = []

        result = self.db_conn.get_priority_updates()

        self.assertEqual(result, [])

    def test_put_log_success(self):
        """Test successful log entry insertion."""
        log_entry = {
            'site_id': 'test_site',
            'log_level': 'INFO',
            'session_id': 'session123',
            'summary_message': 'Test message',
            'detailed_message': 'Test details'
        }

        self.mock_cursor.rowcount = 1
        self.mock_cursor.lastrowid = 456

        with patch('squishy_REST_API.remote_mysql.config') as mock_config:
            mock_config.site_name = 'default_site'

            result = self.db_conn.put_log(log_entry)

        self.assertEqual(result, 456)
        self.mock_cursor.execute.assert_called_once()

    def test_put_log_missing_required_field(self):
        """Test put_log with missing required field."""
        log_entry = {}  # Missing summary_message

        with self.assertRaises(ValueError) as context:
            self.db_conn.put_log(log_entry)

        self.assertIn("summary_message", str(context.exception))

    def test_put_log_with_message_field(self):
        """Test put_log with legacy 'message' field."""
        log_entry = {
            'message': 'Test message'
        }

        self.mock_cursor.rowcount = 1
        self.mock_cursor.lastrowid = 789

        with patch('squishy_REST_API.remote_mysql.config') as mock_config:
            mock_config.site_name = 'default_site'

            result = self.db_conn.put_log(log_entry)

        self.assertEqual(result, 789)
        # Should have created summary_message from message
        args = self.mock_cursor.execute.call_args[0][1]
        self.assertEqual(args['summary_message'], 'Test message')

    def test_health_check_success(self):
        """Test successful health check."""
        self.mock_cursor.fetchall.return_value = [(1,)]

        result = self.db_conn.health_check()

        self.assertEqual(result, {'local_db': True})
        self.mock_cursor.execute.assert_called_once_with("SELECT 1;")

    def test_health_check_failure(self):
        """Test failed health check."""
        self.mock_connection_factory.side_effect = Error("Connection failed")

        result = self.db_conn.health_check()

        self.assertEqual(result, {'local_db': False})

    def test_delete_log_entries_success(self):
        """Test successful log entry deletion."""
        log_ids = [1, 2, 3]

        # Mock successful deletions
        self.mock_cursor.rowcount = 1

        deleted_count, failed_deletes = self.db_conn.delete_log_entries(log_ids)

        self.assertEqual(deleted_count, 3)
        self.assertEqual(failed_deletes, [])
        self.assertEqual(self.mock_cursor.execute.call_count, 3)

    def test_delete_log_entries_partial_failure(self):
        """Test log entry deletion with partial failures."""
        log_ids = [1, 2, 3]

        # Mock first deletion succeeds, second fails, third succeeds
        self.mock_cursor.rowcount = 1
        side_effects = [None, None, None]  # All execute calls succeed
        rowcount_values = [1, 0, 1]  # But second one affects 0 rows

        self.mock_cursor.execute.side_effect = side_effects

        # We need to mock rowcount to return different values
        with patch.object(self.mock_cursor, 'rowcount', side_effect=rowcount_values):
            deleted_count, failed_deletes = self.db_conn.delete_log_entries(log_ids)

        self.assertEqual(deleted_count, 2)
        self.assertEqual(failed_deletes, [2])

    def test_delete_log_entries_invalid_input(self):
        """Test delete_log_entries with invalid input."""
        # Test with empty list
        with self.assertRaises(ValueError):
            self.db_conn.delete_log_entries([])

        # Test with non-list input
        with self.assertRaises(ValueError):
            self.db_conn.delete_log_entries("not_a_list")

        # Test with non-integer values
        with self.assertRaises(ValueError):
            self.db_conn.delete_log_entries(['a', 'b', 'c'])

    def test_delete_log_entries_single_id(self):
        """Test delete_log_entries with single ID."""
        self.mock_cursor.rowcount = 1

        deleted_count, failed_deletes = self.db_conn.delete_log_entries(123)

        self.assertEqual(deleted_count, 1)
        self.assertEqual(failed_deletes, [])
        self.mock_cursor.execute.assert_called_once_with(
            "DELETE FROM logs WHERE log_id = %s", (123,)
        )


if __name__ == '__main__':
    unittest.main()
