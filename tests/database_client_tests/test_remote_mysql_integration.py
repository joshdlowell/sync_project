import datetime
import unittest
import os
import mysql.connector
from mysql.connector import Error
import json
import time

from database_client.remote_mysql import  RemoteMYSQLConnection
# from squishy_REST_API.remote_mysql import RemoteMYSQLConnection


class TestRemoteMYSQLIntegration(unittest.TestCase):
    """
    Integration tests for RemoteMYSQLConnection.

    These tests require a real MySQL database to be available.
    Set environment variables:
    - MYSQL_HOST
    - MYSQL_DATABASE
    - MYSQL_USER
    - MYSQL_PASSWORD
    - MYSQL_PORT (optional, defaults to 3306)
    """

    @classmethod
    def setUpClass(cls):
        """Set up test database connection."""
        cls.db_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'database': os.getenv('MYSQL_DATABASE', 'squishy_db'),
            'user': os.getenv('MYSQL_USER', 'your_app_user'),
            'password': os.getenv('MYSQL_PASSWORD', 'your_user_password'),
            'port': int(os.getenv('MYSQL_PORT', 3306))
        }

        # Skip tests if database config is not provided
        if not all([cls.db_config['host'], cls.db_config['database'],
                    cls.db_config['user'], cls.db_config['password']]):
            raise unittest.SkipTest("MySQL database configuration not provided")

        # Test connection
        try:
            with mysql.connector.connect(**cls.db_config) as conn:
                pass
        except Error as e:
            raise unittest.SkipTest(f"Cannot connect to MySQL database: {e}")

        cls.db_conn = RemoteMYSQLConnection(**cls.db_config)
        cls._setup_test_tables()

    @classmethod
    def _setup_test_tables(cls):
        """Set up test tables."""
        try:
            with mysql.connector.connect(**cls.db_config) as conn:
                with conn.cursor() as cursor:
                    # Create hashtable if it doesn't exist
                    cursor.execute("""
                                   CREATE TABLE IF NOT EXISTS hashtable
                                   (
                                       path               VARCHAR(500) PRIMARY KEY,
                                       current_hash       VARCHAR(64),
                                       prev_hash          VARCHAR(64),
                                       current_dtg_latest BIGINT,
                                       prev_dtg_latest    BIGINT,
                                       current_dtg_first  BIGINT,
                                       dirs               JSON,
                                       files              JSON,
                                       links              JSON,
                                       target_hash        VARCHAR(64)
                                   )
                                   """)

                    # Create logs table if it doesn't exist
                    cursor.execute("""
                                   CREATE TABLE IF NOT EXISTS logs
                                   (
                                       log_id           INT AUTO_INCREMENT PRIMARY KEY,
                                       site_id          VARCHAR(100),
                                       log_level        VARCHAR(20),
                                       timestamp        DATETIME DEFAULT CURRENT_TIMESTAMP,
                                       session_id       VARCHAR(100),
                                       summary_message  TEXT,
                                       detailed_message TEXT
                                   )
                                   """)

                    conn.commit()
        except Error as e:
            raise unittest.SkipTest(f"Cannot set up test tables: {e}")

    def setUp(self):
        """Clean up test data before each test."""
        self._cleanup_test_data()

    def tearDown(self):
        """Clean up test data after each test."""
        self._cleanup_test_data()

    def _cleanup_test_data(self):
        """Remove test data from database."""
        try:
            with mysql.connector.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM hashtable WHERE path LIKE '/test/%'")
                    cursor.execute("DELETE FROM logs WHERE summary_message LIKE 'Test%'")
                    conn.commit()
        except Error:
            pass  # Ignore cleanup errors

    def test_health_check_real_db(self):
        """Test health check with real database."""
        result = self.db_conn.health_check()

        self.assertEqual(result, {'local_db': True})

    def test_insert_and_get_hash_record(self):
        """Test inserting and retrieving a hash record."""
        test_record = {
            'path': '/test/integration/path',
            'current_hash': 'abc123def456',
            'dirs': ['subdir1', 'subdir2'],
            'files': ['file1.txt', 'file2.txt'],
            'links': ['link1'],
            'target_hash': 'target123'
        }

        # Insert record
        success = self.db_conn.insert_or_update_hash(test_record)
        self.assertTrue(success)

        # Retrieve record
        retrieved = self.db_conn.get_hash_record('/test/integration/path')

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['path'], '/test/integration/path')
        self.assertEqual(retrieved['current_hash'], 'abc123def456')
        self.assertEqual(retrieved['dirs'], ['subdir1', 'subdir2'])
        self.assertEqual(retrieved['files'], ['file1.txt', 'file2.txt'])
        self.assertEqual(retrieved['links'], ['link1'])
        self.assertEqual(retrieved['target_hash'], 'target123')
        self.assertIsNotNone(retrieved['current_dtg_latest'])

    def test_update_existing_hash_record(self):
        """Test updating an existing hash record."""
        # Insert initial record
        initial_record = {
            'path': '/test/integration/update',
            'current_hash': 'initial_hash',
            'dirs': ['initial_dir'],
            'files': ['initial_file.txt'],
            'links': []
        }

        success = self.db_conn.insert_or_update_hash(initial_record)
        self.assertTrue(success)

        # Get initial timestamp
        initial_retrieved = self.db_conn.get_hash_record('/test/integration/update')
        initial_timestamp = initial_retrieved['current_dtg_latest']

        # Wait a moment to ensure timestamp difference
        time.sleep(1)

        # Update with new hash
        updated_record = {
            'path': '/test/integration/update',
            'current_hash': 'updated_hash',
            'dirs': ['updated_dir'],
            'files': ['updated_file.txt'],
            'links': ['updated_link']
        }

        success = self.db_conn.insert_or_update_hash(updated_record)
        self.assertTrue(success)

        # Verify update
        updated_retrieved = self.db_conn.get_hash_record('/test/integration/update')

        self.assertEqual(updated_retrieved['current_hash'], 'updated_hash')
        self.assertEqual(updated_retrieved['prev_hash'], 'initial_hash')
        self.assertEqual(updated_retrieved['dirs'], ['updated_dir'])
        self.assertEqual(updated_retrieved['files'], ['updated_file.txt'])
        self.assertEqual(updated_retrieved['links'], ['updated_link'])
        self.assertGreater(updated_retrieved['current_dtg_latest'], initial_timestamp)

    def test_get_single_field(self):
        """Test getting a single field from hash record."""
        # Insert test record
        test_record = {
            'path': '/test/integration/single_field',
            'current_hash': 'single_field_hash',
            'dirs': [],
            'files': [],
            'links': []
        }
        insert_time = datetime.datetime.now(tz=datetime.timezone.utc)
        self.db_conn.insert_or_update_hash(test_record)

        # Test getting hash
        hash_result = self.db_conn.get_single_field('/test/integration/single_field', 'current_hash')
        self.assertEqual(hash_result, 'single_field_hash')

        # Test getting timestamp
        timestamp_result = self.db_conn.get_single_field('/test/integration/single_field', 'current_dtg_latest')
        self.assertIsInstance(timestamp_result, datetime.datetime)
        self.assertGreater(timestamp_result.astimezone(datetime.timezone.utc), insert_time)

    def test_get_priority_updates(self):
        """Test getting priority updates."""
        # Insert records with different target hashes
        test_records = [
            {
                'path': '/test/integration/priority1',
                'current_hash': 'current1',
                'target_hash': 'target1',
                'dirs': [],
                'files': [],
                'links': []
            },
            {
                'path': '/test/integration/priority2',
                'current_hash': 'current2',
                'target_hash': 'current2',  # Same as current, should not appear
                'dirs': [],
                'files': [],
                'links': []
            },
            {
                'path': '/test/integration/priority3',
                'current_hash': 'current3',
                'target_hash': 'target3',
                'dirs': [],
                'files': [],
                'links': []
            }
        ]

        for record in test_records:
            self.db_conn.insert_or_update_hash(record)

        priority_updates = self.db_conn.get_priority_updates()

        # Should only include paths where target_hash != current_hash
        self.assertIn('/test/integration/priority1', priority_updates)
        self.assertNotIn('/test/integration/priority2', priority_updates)
        self.assertIn('/test/integration/priority3', priority_updates)

    def test_put_and_get_logs(self):
        """Test inserting and retrieving log entries."""
        log_entry = {
            'site_id': 'test1',
            'log_level': 'INFO',
            'session_id': 'test_session',
            'summary_message': 'Test integration log',
            'detailed_message': 'This is a test log entry for integration testing'
        }

        # Insert log
        log_id = self.db_conn.put_log(log_entry)
        self.assertIsNotNone(log_id)
        self.assertIsInstance(log_id, int)

        # Get logs
        logs = self.db_conn.get_logs(limit=10)

        # Find our log entry
        test_log = None
        for log in logs:
            if log['log_id'] == log_id:
                test_log = log
                break

        self.assertIsNotNone(test_log)
        self.assertEqual(test_log['site_id'], 'test1')
        self.assertEqual(test_log['log_level'], 'INFO')
        self.assertEqual(test_log['session_id'], 'test_session')
        self.assertEqual(test_log['summary_message'], 'Test integration log')
        self.assertEqual(test_log['detailed_message'], 'This is a test log entry for integration testing')

    def test_delete_log_entries(self):
        """Test deleting log entries."""
        # Insert test logs
        log_ids = []
        for i in range(3):
            log_entry = {
                'summary_message': f'Test log {i}',
                'detailed_message': f'Test log details {i}'
            }
            log_id = self.db_conn.put_log(log_entry)
            log_ids.append(log_id)

        # Delete logs
        deleted_count, failed_deletes = self.db_conn.delete_log_entries(log_ids)

        self.assertEqual(deleted_count, 3)
        self.assertEqual(failed_deletes, [])

        # Verify logs are deleted
        for log_id in log_ids:
            logs = self.db_conn.get_logs(limit=1000)
            log_exists = any(log['log_id'] == log_id for log in logs)
            self.assertFalse(log_exists, f"Log {log_id} should have been deleted")

    def test_get_logs_with_filters(self):
        """Test getting logs with various filters."""
        # Insert test logs with different properties
        test_logs = [
            {
                'log_level': 'INFO',
                'session_id': 'session1',
                'summary_message': 'Test info log',
                'detailed_message': 'Info details'
            },
            {
                'log_level': 'ERROR',
                'session_id': 'session2',
                'summary_message': 'Test error log',
                'detailed_message': 'Error details'
            },
            {
                'log_level': 'DEBUG',
                'session_id': None,
                'summary_message': 'Test debug log',
                'detailed_message': 'Debug details'
            }
        ]

        inserted_ids = []
        for log_entry in test_logs:
            log_id = self.db_conn.put_log(log_entry)
            inserted_ids.append(log_id)

        # Test limit and offset
        limited_logs = self.db_conn.get_logs(limit=2, offset=0)
        self.assertLessEqual(len(limited_logs), 2)

        # Test session_id filter
        session1_logs = self.db_conn.get_logs(session_id_filter='session1')
        self.assertTrue(all(log['session_id'] == 'session1' for log in session1_logs))

        # Test null session_id filter
        null_session_logs = self.db_conn.get_logs(session_id_filter='null')
        self.assertTrue(all(log['session_id'] is None for log in null_session_logs))

        # Test ordering
        asc_logs = self.db_conn.get_logs(order_by='log_id', order_direction='ASC', limit=5)
        if len(asc_logs) > 1:
            self.assertLessEqual(asc_logs[0]['log_id'], asc_logs[1]['log_id'])

    def test_recursive_delete_functionality(self):
        """Test that deleting records with children works correctly."""
        # Insert parent and child records
        parent_record = {
            'path': '/test/integration/parent',
            'current_hash': 'parent_hash',
            'dirs': ['child_dir'],
            'files': ['child_file.txt'],
            'links': ['child_link']
        }

        child_records = [
            {
                'path': '/test/integration/parent/child_dir',
                'current_hash': 'child_dir_hash',
                'dirs': [],
                'files': [],
                'links': []
            },
            {
                'path': '/test/integration/parent/child_file.txt',
                'current_hash': 'child_file_hash',
                'dirs': [],
                'files': [],
                'links': []
            },
            {
                'path': '/test/integration/parent/child_link',
                'current_hash': 'child_link_hash',
                'dirs': [],
                'files': [],
                'links': []
            }
        ]

        # Insert all records
        self.db_conn.insert_or_update_hash(parent_record)
        for child_record in child_records:
            self.db_conn.insert_or_update_hash(child_record)

        # Update parent to remove children (should trigger recursive delete)
        updated_parent = {
            'path': '/test/integration/parent',
            'current_hash': 'parent_hash_updated',
            'dirs': [],
            'files': [],
            'links': []
        }

        success = self.db_conn.insert_or_update_hash(updated_parent)
        self.assertTrue(success)

        # Verify children were deleted
        for child_record in child_records:
            result = self.db_conn.get_hash_record(child_record['path'])
            self.assertIsNone(result, f"Child record {child_record['path']} should have been deleted")

        # Verify parent still exists
        parent_result = self.db_conn.get_hash_record('/test/integration/parent')
        self.assertIsNotNone(parent_result)
        self.assertEqual(parent_result['current_hash'], 'parent_hash_updated')


if __name__ == '__main__':
    unittest.main()