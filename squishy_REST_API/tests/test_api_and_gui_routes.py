"""
Tests for the REST API package.

This module contains tests for the REST API endpoints.
"""
import json
import unittest
from unittest.mock import patch, MagicMock

import squishy_REST_API
from squishy_REST_API.app_factory.app_factory import RESTAPIFactory
from squishy_REST_API.database_client.local_memory import LocalMemoryConnection


class BaseTestCase(unittest.TestCase):
    """Base test case for all tests."""

    def create_app(self):
        """Create and configure a Flask application for testing."""
        # Create mock database instances
        self.mock_db_instance = MagicMock()
        self.mock_core_db_instance = MagicMock()

        # Create test configuration
        test_config = {
            'TESTING': True,
            'DEBUG': False,
            'db_instance': self.mock_db_instance,
            'core_db_instance': self.mock_core_db_instance
        }

        # Create application with test configuration
        return RESTAPIFactory.create_app(test_config)

    def create_test_client(self, app):
        """Create a test client for the Flask application."""
        return app.test_client()

    def create_mock_db(self):
        """Create a mock database for testing."""
        # Create an in-memory database or mock
        return LocalMemoryConnection()


class APITestCase(BaseTestCase):
    """Base test case for API tests."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create application with test configuration
        self.app = self.create_app()

        # Create test client
        self.client = self.create_test_client(self.app)

        # Create mock database
        self.mock_db = self.create_mock_db()

        self.db = LocalMemoryConnection()


class HashEndpointTestCase(APITestCase):
    """Test cases for the /api/hash endpoint."""

    def test_get_hash_success(self):
        """Test GET /api/hash endpoint with a path that exists."""
        # Configure mock to return a hash value
        self.mock_db_instance.get_single_hash_record.return_value = 'test_hash_value'

        # Make request to endpoint
        response = self.client.get('/api/hash?path=test_path')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], 'test_hash_value')

        # Verify mock was called correctly
        self.mock_db_instance.get_single_hash_record.assert_called_once_with('test_path')

    def test_get_hash_not_found(self):
        """Test GET /api/hash endpoint with a path that doesn't exist."""
        # Configure mock to return None (not found)
        self.mock_db_instance.get_single_hash_record.return_value = None

        # Make request to endpoint
        response = self.client.get('/api/hash?path=nonexistent_path')

        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Path not found')


class HashtableEndpointTestCase(APITestCase):
    """Test cases for the /api/hashtable endpoint."""

    def test_get_hashtable_success(self):
        """Test GET /api/hashtable endpoint with a path that exists."""
        # Configure mock to return a record
        mock_record = {
            'path': 'test_path',
            'current_hash': 'test_hash',
            'current_dtg_latest': 123456789.0
        }
        self.mock_db_instance.get_hash_record.return_value = mock_record

        # Make request to endpoint
        response = self.client.get('/api/hashtable?path=test_path')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], mock_record)

        # Verify mock was called correctly
        self.mock_db_instance.get_hash_record.assert_called_once_with('test_path')

    def test_get_hashtable_not_found(self):
        """Test GET /api/hashtable endpoint with a path that doesn't exist."""
        # Configure mock to return None (not found)
        self.mock_db_instance.get_hash_record.return_value = None

        # Make request to endpoint
        response = self.client.get('/api/hashtable?path=nonexistent_path')

        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Path not found')

    def test_get_hashtable_missing_path(self):
        """Test GET /api/hashtable endpoint with missing path parameter."""
        # Make request to endpoint without path
        response = self.client.get('/api/hashtable')

        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'path parameter is required')

    def test_post_hashtable_missing_path(self):
        """Test POST /api/hashtable endpoint with missing path."""
        # Make request to endpoint with missing path
        response = self.client.post(
            '/api/hashtable',
            data=json.dumps({'current_hash': 'test_hash'}),
            content_type='application/json'
        )

        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('path required', data['message'])

    def test_post_hashtable_success(self):
        """Test POST /api/hashtable endpoint with valid data."""
        # Configure mock to return success
        self.mock_db_instance.insert_or_update_hash.return_value = True

        # Make request to endpoint
        request_data = {
            'path': 'test_path',
            'current_hash': 'test_hash',
            'current_dtg_latest': 123456789.0
        }
        response = self.client.post(
            '/api/hashtable',
            data=json.dumps(request_data),
            content_type='application/json'
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], True)

        # Verify mock was called correctly
        self.mock_db_instance.insert_or_update_hash.assert_called_once_with(record=request_data)

    def test_post_hashtable_db_error(self):
        """Test POST /api/hashtable endpoint with database error."""
        # Configure mock to return failure
        self.mock_db_instance.insert_or_update_hash.return_value = False

        # Make request to endpoint
        request_data = {
            'path': 'test_path',
            'current_hash': 'test_hash',
            'current_dtg_latest': 123456789.0
        }
        response = self.client.post(
            '/api/hashtable',
            data=json.dumps(request_data),
            content_type='application/json'
        )

        # Check response
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('Database error', data['message'])


class TimestampEndpointTestCase(APITestCase):
    """Test cases for the /api/timestamp endpoint."""

    def test_get_timestamp_success(self):
        """Test GET /api/timestamp endpoint with a path that exists."""
        # Configure mock to return a timestamp
        self.mock_db_instance.get_single_timestamp.return_value = 123456789.0

        # Make request to endpoint
        response = self.client.get('/api/timestamp?path=test_path')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], 123456789.0)

        # Verify mock was called correctly
        self.mock_db_instance.get_single_timestamp.assert_called_once_with('test_path')

    def test_get_timestamp_not_found(self):
        """Test GET /api/timestamp endpoint with a path that doesn't exist."""
        # Configure mock to return None (not found)
        self.mock_db_instance.get_single_timestamp.return_value = None

        # Make request to endpoint
        response = self.client.get('/api/timestamp?path=nonexistent_path')

        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Path not found')


class PriorityEndpointTestCase(APITestCase):
    """Test cases for the /api/priority endpoint."""

    def test_get_priority_success(self):
        """Test GET /api/priority endpoint."""
        # Configure mock to return priority data
        mock_priority_data = [
            {'path': 'path1', 'last_updated': 123456789.0},
            {'path': 'path2', 'last_updated': 123456790.0}
        ]
        self.mock_db_instance.get_priority_updates.return_value = mock_priority_data

        # Make request to endpoint
        response = self.client.get('/api/priority')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], mock_priority_data)

        # Verify mock was called correctly
        self.mock_db_instance.get_priority_updates.assert_called_once()


class LifecheckEndpointTestCase(APITestCase):
    """Test cases for the /api/lifecheck endpoint."""

    def test_get_lifecheck_success(self):
        """Test GET /api/lifecheck endpoint."""
        # Configure mock to return lifecheck data
        self.mock_db_instance.life_check.return_value = True

        # Make request to endpoint
        response = self.client.get('/api/lifecheck')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], {'api': True, 'db': True})

        # Verify mock was called correctly
        self.mock_db_instance.life_check.assert_called_once()

    def test_get_lifecheck_db_down(self):
        """Test GET /api/lifecheck endpoint with database down."""
        # Configure mock to return lifecheck data
        self.mock_db_instance.life_check.return_value = False

        # Make request to endpoint
        response = self.client.get('/api/lifecheck')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], {'api': True, 'db': False})

        # Verify mock was called correctly
        self.mock_db_instance.life_check.assert_called_once()


class LogsEndpointTestCase(APITestCase):
    """Test cases for the /api/logs endpoint."""

    def test_post_logs_missing_message(self):
        """Test POST /api/logs endpoint with missing summary_message."""
        # Make request to endpoint with missing summary_message
        response = self.client.post(
            '/api/logs',
            data=json.dumps({'log_level': 'INFO'}),
            content_type='application/json'
        )

        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('message required', data['message'])

    def test_post_logs_success(self):
        """Test POST /api/logs endpoint with valid data."""
        # Configure mock to return success
        self.mock_db_instance.put_log.return_value = True

        # Make request to endpoint
        request_data = {
            'summary_message': 'Test log message',
            'log_level': 'INFO',
            'site_id': 'test_site'
        }
        response = self.client.post(
            '/api/logs',
            data=json.dumps(request_data),
            content_type='application/json'
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], 0)

        # Verify mock was called correctly
        self.mock_db_instance.put_log.assert_called()

    def test_post_logs_db_error(self):
        """Test POST /api/logs endpoint with database error."""
        # Configure mock to return failure
        self.mock_db_instance.put_log.return_value = False

        # Make request to endpoint
        request_data = {
            'summary_message': 'Test log message',
            'log_level': 'INFO',
            'site_id': 'test_site'
        }
        response = self.client.post(
            '/api/logs',
            data=json.dumps(request_data),
            content_type='application/json'
        )

        # Check response
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('Database error', data['message'])


class GUITestCase(APITestCase):
    """Base test case for GUI tests."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create application with test configuration first
        self.app = self.create_app()

        # Create test client
        self.client = self.create_test_client(self.app)

        # Create mock database
        self.mock_db = self.create_mock_db()
        self.db = LocalMemoryConnection()

        # Patch config.is_core to True to enable GUI routes
        self.config_patch = patch('squishy_REST_API.app_factory.app_factory.config')
        self.mock_config = self.config_patch.start()
        self.mock_config.is_core = True

    def tearDown(self):
        """Clean up after each test."""
        self.config_patch.stop()


class DashboardEndpointTestCase(GUITestCase):
    """Test cases for the / (dashboard) endpoint."""

    def test_dashboard_success(self):
        """Test GET / endpoint."""
        # Configure mock to return dashboard data
        mock_dashboard_data = {
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
        self.mock_core_db_instance.get_dashboard_content.return_value = mock_dashboard_data

        # Make request to endpoint
        response = self.client.get('/')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard', response.data)  # Check for dashboard title in HTML

        # Verify mock was called correctly
        self.mock_core_db_instance.get_dashboard_content.assert_called_once()


class HashtableDetailEndpointTestCase(GUITestCase):
    """Test cases for the /web/hashtable/<path:file_path> endpoint."""

    def test_hashtable_detail_success(self):
        """Test GET /web/hashtable/<path:file_path> endpoint with a path that exists."""
        # Configure mock to return a record
        mock_record = {
            'path': '/test_path',
            'current_hash': 'test_hash',
            'current_dtg_latest': 123456789,
            'current_dtg_first': 123456780,
            'prev_dtg_latest': 123456770,
            'files': 'file1,file2',
            'dirs': 'dir1,dir2',
            'links': 'link1,link2'
        }
        self.mock_db_instance.get_hash_record.return_value = mock_record

        # Make request to endpoint
        response = self.client.get('/web/hashtable/test_path')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'test_hash', response.data)  # Check for hash value in HTML

        # Verify mock was called correctly
        self.mock_db_instance.get_hash_record.assert_called_once_with('/test_path')

    def test_hashtable_detail_not_found(self):
        """Test GET /web/hashtable/<path:file_path> endpoint with a path that doesn't exist."""
        # Configure mock to return None (not found)
        self.mock_db_instance.get_hash_record.return_value = None

        # Make request to endpoint
        response = self.client.get('/web/hashtable/nonexistent_path')

        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'not found', response.data.lower())  # Check for error message in HTML

        # Verify mock was called correctly
        self.mock_db_instance.get_hash_record.assert_called_once_with('/nonexistent_path')


class LivenessEndpointTestCase(GUITestCase):
    """Test cases for the /web/liveness endpoint."""

    def test_liveness_success(self):
        """Test GET /web/liveness endpoint."""
        mock_liveness_data = [
            {'site_name': 'site1', 'status_category': 'live_1_behind', 'last_updated': 123456789},
            {'site_name': 'site2', 'status_category': 'live_l24_behind', 'last_updated': 123456790}
        ]
        self.mock_core_db_instance.get_site_liveness.return_value = mock_liveness_data

        # Make request to endpoint
        response = self.client.get('/web/liveness')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Site Liveness', response.data)  # Check for title in HTML

        # Verify mock was called correctly
        self.mock_core_db_instance.get_site_liveness.assert_called_once()


class LogsWebEndpointTestCase(GUITestCase):
    """Test cases for the /web/logs endpoint."""

    def test_logs_no_filters(self):
        """Test GET /web/logs endpoint without filters."""
        # Configure mock to return logs data and site IDs
        mock_logs_data = [
            {'timestamp': 123456789.0, 'log_level': 'INFO', 'summary_message': 'Test log 1', 'site_id': 'site1'},
            {'timestamp': 123456790.0, 'log_level': 'ERROR', 'summary_message': 'Test log 2', 'site_id': 'site2'}
        ]
        self.mock_core_db_instance.get_recent_logs.return_value = mock_logs_data
        self.mock_core_db_instance.get_valid_site_ids.return_value = ['site1', 'site2', 'site3']

        # Make request to endpoint
        response = self.client.get('/web/logs')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logs', response.data)  # Check for title in HTML

        # Verify mocks were called correctly
        self.mock_core_db_instance.get_recent_logs.assert_called_once_with(log_level=None, site_id=None)
        self.mock_core_db_instance.get_valid_site_ids.assert_called_once()

    def test_logs_with_filters(self):
        """Test GET /web/logs endpoint with filters."""
        # Configure mocks
        mock_logs_data = [
            {'timestamp': 123456789, 'log_level': 'ERROR', 'summary_message': 'Test error log',
             'site_id': 'site1'}
        ]
        self.mock_core_db_instance.get_recent_logs.return_value = mock_logs_data
        self.mock_core_db_instance.get_valid_site_ids.return_value = ['site1', 'site2', 'site3']

        # Mock the config for valid log levels
        with patch('squishy_REST_API.app_factory.gui_routes.config') as mock_config:
            mock_config.VALID_LOG_LEVELS = ['INFO', 'WARNING', 'ERROR']

            # Make request to endpoint with filters
            response = self.client.get('/web/logs?log_level=ERROR&site_id=site1')

            # Check response
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Logs', response.data)  # Check for title in HTML
            self.assertIn(b'Test error log', response.data)  # Check for filtered log message

            # Verify mocks were called correctly
            self.mock_core_db_instance.get_recent_logs.assert_called_once_with(log_level='ERROR', site_id='site1')
            self.mock_core_db_instance.get_valid_site_ids.assert_called_once()


class HashStatusEndpointTestCase(GUITestCase):
    """Test cases for the /web/status endpoint."""

    def test_hash_status_success(self):
        """Test GET /web/status endpoint."""
        # Configure mock to return hash sync status data
        mock_sync_data = [
            {'site_name': 'site1', 'current_hash': 'synced', 'last_updated': 123456789.0, 'sync_category': 'sync_1_behind'},
            {'site_name': 'site2', 'current_hash': 'out_of_sync', 'last_updated': 123456790.0, 'sync_category': 'sync_l24_behind'}
        ]
        self.mock_core_db_instance.get_site_sync_status.return_value = mock_sync_data

        # Make request to endpoint
        response = self.client.get('/web/status')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hash Status', response.data)  # Check for title in HTML

        # Verify mock was called correctly
        self.mock_core_db_instance.get_site_sync_status.assert_called_once()


if __name__ == '__main__':
    unittest.main()