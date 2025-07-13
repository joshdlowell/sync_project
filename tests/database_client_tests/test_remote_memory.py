import unittest
import json
from unittest.mock import patch
import os

from database_client.remote_memory import RemoteInMemoryConnection


class TestRemoteInMemoryConnection(unittest.TestCase):
    """Test cases for the RemoteInMemoryConnection class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.initial_data = {
            '/test/path': {
                'current_hash': 'abc123',
                'prev_hash': None,
                'current_dtg_latest': 1234567890,
                'prev_dtg_latest': None,
                'current_dtg_first': 1234567890,
                'dirs': ['subdir1', 'subdir2'],
                'files': ['file1.txt', 'file2.txt'],
                'links': ['link1'],
                'target_hash': 'target123'
            }
        }

        self.db_conn = RemoteInMemoryConnection(initial_data=self.initial_data)


        test_env_vars = {
            'LOCAL_DB_USER': 'test-user',
            'LOCAL_DB_PASSWORD': 'test-secret-key',
            'SITE_NAME': 'test1',
            'API_SECRET_KEY': 'test-secret-key',
            # Add other required env vars here
        }

        # Store original values to restore later
        self.original_env = {}
        for key, value in test_env_vars.items():
            self.original_env[key] = os.environ.get(key)
            os.environ[key] = value

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original environment variables
        for key, original_value in self.original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value

    # def test_init_with_initial_data(self):
    #     """Test initialization with initial data."""
    #     self.assertEqual(len(self.db_conn.hashtable), 1)
    #     self.assertIn('/test/path', self.db_conn.hashtable.keys())
    #     self.assertEqual(self.db_conn.hashtable['/test/path']['current_hash'], 'abc123')

    def test_init_without_initial_data(self):
        """Test initialization without initial data."""
        db_conn = RemoteInMemoryConnection()
        self.assertEqual(len(db_conn.hashtable), 0)

    def test_get_hash_record_existing(self):
        """Test getting an existing hash record."""
        update_record = {
            'path': '/test/path',
            'current_hash': 'abc123',  # Different hash
            'dirs': ['new_subdir'],
            'files': ['new_file.txt'],
            'links': [],
            'target_hash': 'updated_target'
        }

        with patch('time.time', return_value=1234567900):
            result = self.db_conn.insert_or_update_hash(update_record)
        result = self.db_conn.get_hash_record('/test/path')

        self.assertIsNotNone(result)
        self.assertEqual(result['path'], '/test/path')
        self.assertEqual(result['current_hash'], 'abc123')
        self.assertEqual(result['dirs'], ['new_subdir'])
        self.assertEqual(result['files'], ['new_file.txt'])
        self.assertEqual(result['links'], [])

    def test_get_hash_record_nonexistent(self):
        """Test getting a non-existent hash record."""
        result = self.db_conn.get_hash_record('/nonexistent/path')

        self.assertIsNone(result)

    def test_get_hash_record_empty_path(self):
        """Test getting hash record with empty path."""
        with self.assertRaises(ValueError) as context:
            self.db_conn.get_hash_record('')

        self.assertIn("path value must be provided", str(context.exception))

    def test_insert_new_hash_record(self):
        """Test inserting a new hash record."""
        new_record = {
            'path': '/new/path',
            'current_hash': 'new_hash_123',
            'dirs': ['new_dir'],
            'files': ['new_file.txt'],
            'links': [],
            'target_hash': 'new_target'
        }

        with patch('time.time', return_value=1234567900):
            result = self.db_conn.insert_or_update_hash(new_record)

        self.assertTrue(result)
        self.assertIn('/new/path', self.db_conn.hashtable.keys())

        stored_record = self.db_conn.hashtable['/new/path']
        self.assertEqual(stored_record['current_hash'], 'new_hash_123')
        self.assertEqual(stored_record['dirs'], ['new_dir'])
        self.assertEqual(stored_record['files'], ['new_file.txt'])
        self.assertEqual(stored_record['links'], [])
        self.assertEqual(stored_record['target_hash'], 'new_target')
        self.assertEqual(stored_record['current_dtg_latest'], 1234567900)
        self.assertEqual(stored_record['current_dtg_first'], 1234567900)

    def test_update_existing_hash_record_unchanged(self):
        """Test updating existing hash record with unchanged hash."""
        update_record = {
            'path': '/test/path',
            'current_hash': 'abc123',  # Same hash
            'dirs': ['subdir1', 'subdir2'],
            'files': ['file1.txt', 'file2.txt'],
            'links': ['link1'],
            'target_hash': 'updated_target'
        }

        with patch('time.time', return_value=1234567900):
            result = self.db_conn.insert_or_update_hash(update_record)

        self.assertTrue(result)

        stored_record = self.db_conn.hashtable['/test/path']
        self.assertEqual(stored_record['current_hash'], 'abc123')
        self.assertEqual(stored_record['target_hash'], 'updated_target')
        self.assertEqual(stored_record['current_dtg_latest'], 1234567900)
        self.assertEqual(stored_record['current_dtg_first'], 1234567900)  # Unchanged

    def test_update_existing_hash_record_changed(self):
        """Test updating existing hash record with changed hash."""
        update_record = {
            'path': '/test/path',
            'current_hash': 'abc123',  # Different hash
            'dirs': ['new_subdir'],
            'files': ['new_file.txt'],
            'links': [],
            'target_hash': 'updated_target',
        }

        with patch('time.time', return_value=1234567890):
            result = self.db_conn.insert_or_update_hash(update_record)

        update_record = {
            'path': '/test/path',
            'current_hash': 'new_hash_456',  # Different hash
            'dirs': ['new_subdir'],
            'files': ['new_file.txt'],
            'links': [],
            'target_hash': 'updated_target',
        }

        with patch('time.time', return_value=1234567900):
            result = self.db_conn.insert_or_update_hash(update_record)

        self.assertTrue(result)

        stored_record = self.db_conn.hashtable['/test/path']
        self.assertEqual(stored_record['current_hash'], 'new_hash_456')
        self.assertEqual(stored_record['prev_hash'], 'abc123')
        self.assertEqual(stored_record['current_dtg_latest'], 1234567900)
        self.assertEqual(stored_record['prev_dtg_latest'], 1234567890)
        self.assertEqual(stored_record['current_dtg_first'], 1234567900)
        self.assertEqual(stored_record['dirs'], ['new_subdir'])
        self.assertEqual(stored_record['files'], ['new_file.txt'])
        self.assertEqual(stored_record['links'], [])

    def test_insert_or_update_hash_missing_fields(self):
        """Test insert_or_update_hash with missing required fields."""
        # Missing path
        with self.assertRaises(ValueError):
            self.db_conn.insert_or_update_hash({'current_hash': 'abc123'})

        # Missing current_hash
        with self.assertRaises(ValueError):
            self.db_conn.insert_or_update_hash({'path': '/test/path'})

    def test_insert_or_update_hash_invalid_field_types(self):
        """Test insert_or_update_hash with invalid field types."""
        invalid_record = {
            'path': '/test/path',
            'current_hash': 'abc123',
            'dirs': 'not_a_list'  # Should be a list
        }

        with self.assertRaises(ValueError) as context:
            self.db_conn.insert_or_update_hash(invalid_record)

        self.assertIn("must be lists", str(context.exception))

    def test_get_single_field_existing(self):
        """Test getting single field from existing record."""
        # Test getting hash
        update_record = {
            'path': '/test/path',
            'current_hash': 'abc123',  # Different hash
            'dirs': ['new_subdir'],
            'files': ['new_file.txt'],
            'links': [],
            'target_hash': 'updated_target'
        }

        with patch('time.time', return_value=1234567900):
            result = self.db_conn.insert_or_update_hash(update_record)
        hash_result = self.db_conn.get_single_field('/test/path', 'current_hash')
        self.assertEqual(hash_result, 'abc123')

        # Test getting timestamp
        timestamp_result = self.db_conn.get_single_field('/test/path', 'current_dtg_latest')
        self.assertEqual(timestamp_result, 1234567900)

    def test_get_single_field_nonexistent(self):
        """Test getting single field from non-existent record."""
        result = self.db_conn.get_single_field('/nonexistent/path', 'current_hash')
        self.assertIsNone(result)

    def test_get_single_field_invalid_field(self):
        """Test getting invalid field name."""
        with self.assertRaises(ValueError) as context:
            self.db_conn.get_single_field('/test/path', 'invalid_field')

        self.assertIn("Invalid field name", str(context.exception))

    def test_get_single_field_missing_params(self):
        """Test get_single_field with missing parameters."""
        with self.assertRaises(ValueError):
            self.db_conn.get_single_field('', 'current_hash')

        with self.assertRaises(ValueError):
            self.db_conn.get_single_field('/test/path', '')

    def test_get_priority_updates(self):
        """Test getting priority updates."""
        # Add records with different target hashes
        self.db_conn.hashtable['/priority/path1'] = {
            'current_hash': 'current1',
            'target_hash': 'target1'  # Different from current
        }

        self.db_conn.hashtable['/priority/path2'] = {
            'current_hash': 'current2',
            'target_hash': 'current2'  # Same as current
        }

        self.db_conn.hashtable['/priority/path3'] = {
            'current_hash': 'current3',
            'target_hash': None  # No target hash
        }

        self.db_conn.hashtable['/priority/path4'] = {
            'current_hash': 'current4',
            'target_hash': 'target4'  # Different from current
        }

        priority_updates = self.db_conn.get_priority_updates()

        # Should include paths where target_hash is not None and != current_hash
        self.assertIn('/priority/path1', priority_updates)
        self.assertNotIn('/priority/path2', priority_updates)  # Same hash
        self.assertNotIn('/priority/path3', priority_updates)  # No target hash
        self.assertIn('/priority/path4', priority_updates)

    def test_put_log(self):
        """Test inserting log entries."""
        log_entry = {
            'site_id': 'test_site',
            'log_level': 'INFO',
            'session_id': 'test_session',
            'summary_message': 'Test log message',
            'detailed_message': 'Test log details'
        }

        with patch('time.time', return_value=1234567900):
            log_id = self.db_conn.put_log(log_entry)

        self.assertIsInstance(log_id, int)
        self.assertGreater(log_id, -1)
        log_ids = [entry['log_id'] for entry in self.db_conn.logs]
        self.assertIn(log_id, log_ids)

        stored_log = self.db_conn.logs[log_id]
        self.assertEqual(stored_log['site_id'], 'test_site')
        self.assertEqual(stored_log['log_level'], 'INFO')
        self.assertEqual(stored_log['session_id'], 'test_session')
        self.assertEqual(stored_log['summary_message'], 'Test log message')
        self.assertEqual(stored_log['detailed_message'], 'Test log details')
        self.assertEqual(stored_log['timestamp'], 1234567900)

    def test_put_log_missing_summary_message(self):
        """Test put_log with missing summary_message."""
        log_entry = {
            'detailed_message': 'Test details'
        }

        with self.assertRaises(ValueError) as context:
            self.db_conn.put_log(log_entry)

        self.assertIn("summary_message", str(context.exception))

    def test_put_log_with_message_field(self):
        """Test put_log with legacy 'message' field."""
        log_entry = {
            'message': 'Legacy message field'
        }

        log_id = self.db_conn.put_log(log_entry)

        stored_log = self.db_conn.logs[log_id]
        self.assertEqual(stored_log['summary_message'], 'Legacy message field')

    def test_get_logs_basic(self):
        """Test basic log retrieval."""
        # Insert test logs
        for i in range(5):
            log_entry = {
                'summary_message': f'Test log {i}',
                'detailed_message': f'Test log details {i}',
                'log_level': 'INFO' if i % 2 == 0 else 'ERROR'
            }
            with patch('time.time', return_value=1234567900 + i):
                self.db_conn.put_log(log_entry)

        # Get all logs
        logs = self.db_conn.get_logs()

        self.assertEqual(len(logs), 5)
        # Should be ordered by timestamp DESC by default
        self.assertGreater(logs[0]['timestamp'], logs[1]['timestamp'])

    def test_get_logs_with_limit_and_offset(self):
        """Test log retrieval with limit and offset."""
        # Insert test logs
        for i in range(10):
            log_entry = {
                'summary_message': f'Test log {i}',
                'log_level': 'INFO'
            }
            with patch('time.time', return_value=1234567900 + i):
                self.db_conn.put_log(log_entry)

        # Test limit
        limited_logs = self.db_conn.get_logs(limit=3)
        self.assertEqual(len(limited_logs), 3)

        # Test offset
        offset_logs = self.db_conn.get_logs(limit=3, offset=3)
        self.assertEqual(len(offset_logs), 3)

        # Verify they're different logs
        self.assertNotEqual(limited_logs[0]['log_id'], offset_logs[0]['log_id'])

    def test_get_logs_with_session_id_filter(self):
        """Test log retrieval with session_id filter."""
        # Insert logs with different session IDs
        test_logs = [
            {'summary_message': 'Session 1 log', 'session_id': 'session1'},
            {'summary_message': 'Session 2 log', 'session_id': 'session2'},
            {'summary_message': 'No session log', 'session_id': None}
        ]

        for log_entry in test_logs:
            self.db_conn.put_log(log_entry)

        # Test specific session filter
        session1_logs = self.db_conn.get_logs(session_id_filter='session1')
        self.assertEqual(len(session1_logs), 1)
        self.assertEqual(session1_logs[0]['session_id'], 'session1')

        # Test null session filter
        null_session_logs = self.db_conn.get_logs(session_id_filter='null')
        self.assertEqual(len(null_session_logs), 1)
        self.assertIsNone(null_session_logs[0]['session_id'])

    def test_get_logs_with_date_filter(self):
        """Test log retrieval with date filter."""
        # Insert logs with different timestamps
        current_time = 1234567900

        test_logs = [
            {'summary_message': 'Recent log', 'timestamp': current_time},
            {'summary_message': 'Old log', 'timestamp': current_time - (2 * 24 * 60 * 60)},  # 2 days ago
            {'summary_message': 'Very old log', 'timestamp': current_time - (10 * 24 * 60 * 60)}  # 10 days ago
        ]

        for log_entry in test_logs:
            with patch('time.time', return_value=log_entry['timestamp']):
                self.db_conn.put_log(log_entry)

        # Filter logs older than 1 day
        with patch('time.time', return_value=current_time):
            old_logs = self.db_conn.get_logs(older_than_days=1)

        self.assertEqual(len(old_logs), 2)  # Should exclude recent log
        self.assertNotIn('Recent log', [log['summary_message'] for log in old_logs])

    def test_get_logs_ordering(self):
        """Test log retrieval with different ordering."""
        # Insert logs with different log levels
        test_logs = [
            {'summary_message': 'Info log', 'log_level': 'INFO'},
            {'summary_message': 'Error log', 'log_level': 'ERROR'},
            {'summary_message': 'Debug log', 'log_level': 'DEBUG'}
        ]

        for log_entry in test_logs:
            self.db_conn.put_log(log_entry)

        # Test ordering by log_level ASC
        ordered_logs = self.db_conn.get_logs(order_by='log_level', order_direction='ASC')
        log_levels = [log['log_level'] for log in ordered_logs]
        self.assertEqual(log_levels, sorted(log_levels))

        # Test ordering by log_id DESC
        id_ordered_logs = self.db_conn.get_logs(order_by='log_id', order_direction='DESC')
        log_ids = [log['log_id'] for log in id_ordered_logs]
        self.assertEqual(log_ids, sorted(log_ids, reverse=True))

    def test_get_logs_invalid_parameters(self):
        """Test get_logs with invalid parameters."""
        # Invalid limit
        with self.assertRaises(ValueError):
            self.db_conn.get_logs(limit=0)

        with self.assertRaises(ValueError):
            self.db_conn.get_logs(limit=-1)

        # Invalid offset
        with self.assertRaises(ValueError):
            self.db_conn.get_logs(offset=-1)

        # Invalid order direction
        with self.assertRaises(ValueError):
            self.db_conn.get_logs(order_direction='INVALID')

        # Invalid order_by column
        with self.assertRaises(ValueError):
            self.db_conn.get_logs(order_by='invalid_column')

        # Invalid older_than_days
        with self.assertRaises(ValueError):
            self.db_conn.get_logs(older_than_days=0)

    def test_delete_log_entries(self):
        """Test deleting log entries."""
        # Insert test logs
        log_ids = []
        for i in range(5):
            log_entry = {
                'summary_message': f'Test log {i}',
                'log_level': 'INFO'
            }
            log_id = self.db_conn.put_log(log_entry)
            log_ids.append(log_id)

        # Delete some logs
        delete_ids = [log_ids[0], log_ids[2], log_ids[4]]
        deleted_count, failed_deletes = self.db_conn.delete_log_entries(delete_ids)

        self.assertEqual(deleted_count, 3)
        self.assertEqual(failed_deletes, [])

        # Verify logs were deleted
        for log_id in delete_ids:
            self.assertNotIn(log_id, self.db_conn.logs)

        # Verify remaining logs still exist
        remaining_ids = [log_ids[1], log_ids[3]]
        log_ids = [entry['log_id'] for entry in self.db_conn.logs]
        for log_id in remaining_ids:

            self.assertIn(log_id, log_ids)

    def test_delete_log_entries_nonexistent(self):
        """Test deleting non-existent log entries."""
        deleted_count, failed_deletes = self.db_conn.delete_log_entries([999, 1000])

        self.assertEqual(deleted_count, 0)
        self.assertEqual(failed_deletes, [999, 1000])

    def test_delete_log_entries_mixed(self):
        """Test deleting mix of existing and non-existent log entries."""
        # Insert one log
        log_entry = {'summary_message': 'Test log'}
        existing_id = self.db_conn.put_log(log_entry)

        # Try to delete existing and non-existent
        deleted_count, failed_deletes = self.db_conn.delete_log_entries([existing_id, 999])

        self.assertEqual(deleted_count, 1)
        self.assertEqual(failed_deletes, [999])
        self.assertNotIn(existing_id, self.db_conn.logs)

    def test_delete_log_entries_invalid_input(self):
        """Test delete_log_entries with invalid input."""
        # Empty list
        with self.assertRaises(ValueError):
            self.db_conn.delete_log_entries([])

        # Non-list input
        with self.assertRaises(ValueError):
            self.db_conn.delete_log_entries("not_a_list")

        # Non-integer values
        with self.assertRaises(ValueError):
            self.db_conn.delete_log_entries(['a', 'b'])

    def test_delete_log_entries_single_id(self):
        """Test delete_log_entries with single ID."""
        log_entry = {'summary_message': 'Test log'}
        log_id = self.db_conn.put_log(log_entry)

        deleted_count, failed_deletes = self.db_conn.delete_log_entries([log_id])

        self.assertEqual(deleted_count, 1)
        self.assertEqual(failed_deletes, [])
        self.assertNotIn(log_id, self.db_conn.logs)

    def test_health_check(self):
        """Test health check."""
        result = self.db_conn.health_check()

        self.assertEqual(result, {'local_db': True})

    def test_find_orphaned_entries(self):
        """Test finding orphaned entries."""
        # Add some test data
        self.db_conn.hashtable['/root'] = {
            'dirs': ['child1'],
            'files': ['file1.txt'],
            'links': ['link1']
        }

        # Add child that exists in parent
        self.db_conn.hashtable['/root/child1'] = {
            'dirs': [], 'files': [], 'links': []
        }

        # Add orphaned entry (not listed in any parent)
        self.db_conn.hashtable['/root/orphaned'] = {
            'dirs': [], 'files': [], 'links': []
        }

        with patch.object(self.db_conn, 'config', {'root_path': '/root'}):
            orphaned = self.db_conn.find_orphaned_entries()

        self.assertIn('/root/orphaned', orphaned)
        self.assertNotIn('/root/child1', orphaned)

    def test_find_untracked_children(self):
        """Test finding untracked children."""
        # Add parent with children that don't exist as entries
        self.db_conn.hashtable['/root'] = {
            'dirs': ['missing_dir'],
            'files': ['missing_file.txt'],
            'links': ['missing_link']
        }

        untracked = self.db_conn.find_untracked_children()

        self.assertIn('/root/missing_dir', untracked)
        self.assertIn('/root/missing_file.txt', untracked)
        self.assertIn('/root/missing_link', untracked)

    # def test_comprehensive_workflow(self):
    #     """Test a comprehensive workflow with multiple operations."""
    #     # Start with empty database
    #     db_conn = RemoteInMemoryConnection()
    #
    #     # Insert initial records
    #     records = [
    #         {
    #             'path': '/project',
    #             'current_hash': 'project_hash',
    #             'dirs': ['src', 'docs'],
    #             'files': ['README.md'],
    #             'links': [],
    #             'target_hash': 'project_target'
    #         },
    #         {
    #             'path': '/project/src',
    #             'current_hash': 'src_hash',
    #             'dirs': [],
    #             'files': ['main.py', 'utils.py'],
    #             'links': [],
    #             'target_hash': 'src_target'
    #         }
    #     ]
    #
    #     for record in records:
    #         success = db_conn.insert_or_update_hash(record)
    #         self.assertTrue(success)
    #
    #     # Verify records were inserted
    #     self.assertEqual(len(db_conn.hashtable), 2)
    #
    #     # Get priority updates
    #     priority_updates = db_conn.get_priority_updates()
    #     self.assertEqual(len(priority_updates), 2)  # Both have different target hashes
    #
    #     # Update one record to match target
    #     updated_record = {
    #         'path': '/project',
    #         'current_hash': 'project_target',  # Now matches target
    #         'dirs': ['src', 'docs'],
    #         'files': ['README.md'],
    #         'links': [],
    #         'target_hash': 'project_target'
    #     }
    #
    #     success = db_conn.insert_or_update_hash(updated_record)
    #     self.assertTrue(success)
    #
    #     # Check priority updates again
    #     priority_updates = db_conn.get_priority_updates()
    #     self.assertEqual(len(priority_updates), 1)  # Only /project/src should remain
    #     self.assertIn('/project/src', priority_updates)
    #
    #     # Test logging
    #     log_entry = {
    #         'summary_message': 'Workflow test completed',
    #         'detailed_message': 'All operations completed successfully',
    #         'log_level': 'INFO'
    #     }
    #
    #     log_id = db_conn.put_log(log_entry)
    #     self.assertIsNotNone(log_id)
    #
    #     # Verify log was stored
    #     logs = db_conn.get_logs(limit=1)
    #     self.assertEqual(len(logs), 1)
    #     self.assertEqual(logs[0]['summary_message'], 'Workflow test completed')
    #
    #     # Test health check
    #     health = db_conn.health_check()
    #     self.assertEqual(health, {'local_db': True})


if __name__ == '__main__':
    unittest.main()