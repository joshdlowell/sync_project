import unittest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List

from squishy_REST_API.db_implementation import DBInstance
from squishy_REST_API.db_interfaces import RemoteDBConnection, CoreDBConnection, PipelineDBConnection


class TestDBInstance(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_remote_db = Mock(spec=RemoteDBConnection)
        self.mock_core_db = Mock(spec=CoreDBConnection)
        self.mock_pipeline_db = Mock(spec=PipelineDBConnection)

        self.db_instance = DBInstance(
            remote_db=self.mock_remote_db,
            core_db=self.mock_core_db,
            pipeline_db=self.mock_pipeline_db
        )

    def test_init_with_all_dbs(self):
        """Test initialization with all database types."""
        self.assertEqual(self.db_instance.remote_db, self.mock_remote_db)
        self.assertEqual(self.db_instance.core_db, self.mock_core_db)
        self.assertEqual(self.db_instance.pipeline_db, self.mock_pipeline_db)

    def test_init_with_none_dbs(self):
        """Test initialization with None database types."""
        db_instance = DBInstance()
        self.assertIsNone(db_instance.remote_db)
        self.assertIsNone(db_instance.core_db)
        self.assertIsNone(db_instance.pipeline_db)

    # RemoteDBConnection interface tests
    def test_get_hash_record_success(self):
        """Test get_hash_record with successful remote db call."""
        expected_result = {'path': '/test', 'hash': 'abc123'}
        self.mock_remote_db.get_hash_record.return_value = expected_result

        result = self.db_instance.get_hash_record('/test')

        self.mock_remote_db.get_hash_record.assert_called_once_with('/test')
        self.assertEqual(result, expected_result)

    def test_get_hash_record_no_remote_db(self):
        """Test get_hash_record when no remote db is configured."""
        db_instance = DBInstance()

        with self.assertRaises(NotImplementedError) as context:
            db_instance.get_hash_record('/test')

        self.assertIn("RemoteDBConnection implementation not provided", str(context.exception))

    def test_insert_or_update_hash_success(self):
        """Test insert_or_update_hash with successful remote db call."""
        record = {'path': '/test', 'current_hash': 'abc123'}
        self.mock_remote_db.insert_or_update_hash.return_value = True

        result = self.db_instance.insert_or_update_hash(record)

        self.mock_remote_db.insert_or_update_hash.assert_called_once_with(record)
        self.assertTrue(result)

    def test_get_single_field_success(self):
        """Test get_single_field with successful remote db call."""
        self.mock_remote_db.get_single_field.return_value = 'abc123'

        result = self.db_instance.get_single_field('/test', 'current_hash')

        self.mock_remote_db.get_single_field.assert_called_once_with('/test', 'current_hash')
        self.assertEqual(result, 'abc123')

    def test_get_priority_updates_success(self):
        """Test get_priority_updates with successful remote db call."""
        expected_paths = ['/path1', '/path2']
        self.mock_remote_db.get_priority_updates.return_value = expected_paths

        result = self.db_instance.get_priority_updates()

        self.mock_remote_db.get_priority_updates.assert_called_once()
        self.assertEqual(result, expected_paths)

    def test_put_log_success(self):
        """Test put_log with successful remote db call."""
        log_entry = {'message': 'test log'}
        self.mock_remote_db.put_log.return_value = 123

        result = self.db_instance.put_log(log_entry)

        self.mock_remote_db.put_log.assert_called_once_with(log_entry)
        self.assertEqual(result, 123)

    def test_get_logs_success(self):
        """Test get_logs with successful remote db call."""
        expected_logs = [{'log_id': 1, 'message': 'test'}]
        self.mock_remote_db.get_logs.return_value = expected_logs

        result = self.db_instance.get_logs(limit=10, offset=0)

        self.mock_remote_db.get_logs.assert_called_once_with(
            limit=10, offset=0, order_by="timestamp", order_direction="DESC",
            session_id_filter=None, older_than_days=None
        )
        self.assertEqual(result, expected_logs)

    def test_delete_log_entries_success(self):
        """Test delete_log_entries with successful remote db call."""
        log_ids = [1, 2, 3]
        expected_result = ([1, 2, 3], [])
        self.mock_remote_db.delete_log_entries.return_value = expected_result

        result = self.db_instance.delete_log_entries(log_ids)

        self.mock_remote_db.delete_log_entries.assert_called_once_with(log_ids)
        self.assertEqual(result, expected_result)

    def test_health_check_success(self):
        """Test health_check with successful remote db call."""
        expected_result = {'local_db': True}
        self.mock_remote_db.health_check.return_value = expected_result

        result = self.db_instance.health_check()

        self.mock_remote_db.health_check.assert_called_once()
        self.assertEqual(result, expected_result)

    def test_find_orphaned_entries_success(self):
        """Test find_orphaned_entries with successful remote db call."""
        expected_paths = ['/orphaned1', '/orphaned2']
        self.mock_remote_db.find_orphaned_entries.return_value = expected_paths

        result = self.db_instance.find_orphaned_entries()

        self.mock_remote_db.find_orphaned_entries.assert_called_once()
        self.assertEqual(result, expected_paths)

    def test_find_untracked_children_success(self):
        """Test find_untracked_children with successful remote db call."""
        expected_paths = ['/untracked1', '/untracked2']
        self.mock_remote_db.find_untracked_children.return_value = expected_paths

        result = self.db_instance.find_untracked_children()

        self.mock_remote_db.find_untracked_children.assert_called_once()
        self.assertEqual(result, expected_paths)

    # CoreDBConnection interface tests
    def test_get_dashboard_content_success(self):
        """Test get_dashboard_content with successful core db call."""
        expected_content = {'sync_current': 5, 'live_current': 3}
        self.mock_core_db.get_dashboard_content.return_value = expected_content

        result = self.db_instance.get_dashboard_content()

        self.mock_core_db.get_dashboard_content.assert_called_once()
        self.assertEqual(result, expected_content)

    def test_get_dashboard_content_no_core_db(self):
        """Test get_dashboard_content when no core db is configured."""
        db_instance = DBInstance()

        with self.assertRaises(NotImplementedError) as context:
            db_instance.get_dashboard_content()

        self.assertIn("CoreDBConnection implementation not provided", str(context.exception))

    def test_get_recent_logs_success(self):
        """Test get_recent_logs with successful core db call."""
        expected_logs = [{'log_id': 1, 'message': 'test'}]
        self.mock_core_db.get_recent_logs.return_value = expected_logs

        result = self.db_instance.get_recent_logs()

        self.mock_core_db.get_recent_logs.assert_called_once()
        self.assertEqual(result, expected_logs)

    def test_get_hash_record_count_success(self):
        """Test get_hash_record_count with successful core db call."""
        self.mock_core_db.get_hash_record_count.return_value = 1000

        result = self.db_instance.get_hash_record_count()

        self.mock_core_db.get_hash_record_count.assert_called_once()
        self.assertEqual(result, 1000)

    def test_get_log_count_last_24h_success(self):
        """Test get_log_count_last_24h with successful core db call."""
        self.mock_core_db.get_log_count_last_24h.return_value = 50

        result = self.db_instance.get_log_count_last_24h('ERROR')

        self.mock_core_db.get_log_count_last_24h.assert_called_once_with('ERROR')
        self.assertEqual(result, 50)

    # PipelineDBConnection interface tests
    def test_get_pipeline_updates_success(self):
        """Test get_pipeline_updates with successful pipeline db call."""
        expected_updates = [{'path': '/test', 'hash': 'abc123'}]
        self.mock_pipeline_db.get_pipeline_updates.return_value = expected_updates

        result = self.db_instance.get_pipeline_updates()

        self.mock_pipeline_db.get_pipeline_updates.assert_called_once()
        self.assertEqual(result, expected_updates)

    def test_get_pipeline_updates_no_pipeline_db(self):
        """Test get_pipeline_updates when no pipeline db is configured."""
        db_instance = DBInstance()

        with self.assertRaises(NotImplementedError) as context:
            db_instance.get_pipeline_updates()

        self.assertIn("PipelineDBConnection implementation not provided", str(context.exception))

    def test_put_pipeline_hash_success(self):
        """Test put_pipeline_hash with successful pipeline db call."""
        self.mock_pipeline_db.put_pipeline_hash.return_value = True

        result = self.db_instance.put_pipeline_hash('/test', 'abc123')

        self.mock_pipeline_db.put_pipeline_hash.assert_called_once_with('/test', 'abc123')
        self.assertTrue(result)

    def test_get_official_sites_success(self):
        """Test get_official_sites with successful pipeline db call."""
        expected_sites = ['site1', 'site2', 'site3']
        self.mock_pipeline_db.get_official_sites.return_value = expected_sites

        result = self.db_instance.get_official_sites()

        self.mock_pipeline_db.get_official_sites.assert_called_once()
        self.assertEqual(result, expected_sites)

    def test_put_pipeline_site_completion_success(self):
        """Test put_pipeline_site_completion with successful pipeline db call."""
        self.mock_pipeline_db.put_pipeline_site_completion.return_value = True

        result = self.db_instance.put_pipeline_site_completion('site1')

        self.mock_pipeline_db.put_pipeline_site_completion.assert_called_once_with('site1')
        self.assertTrue(result)

    def test_pipeline_health_check_success(self):
        """Test pipeline_health_check with successful pipeline db call."""
        expected_result = {'pipeline_db': True}
        self.mock_pipeline_db.pipeline_health_check.return_value = expected_result

        result = self.db_instance.pipeline_health_check()

        self.mock_pipeline_db.pipeline_health_check.assert_called_once()
        self.assertEqual(result, expected_result)

    def test_pipeline_health_check_no_pipeline_db(self):
        """Test pipeline_health_check when no pipeline db is configured."""
        db_instance = DBInstance()

        result = db_instance.pipeline_health_check()

        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()