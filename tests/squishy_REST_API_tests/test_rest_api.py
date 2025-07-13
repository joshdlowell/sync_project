"""
Tests for the REST API package.

This module contains tests for the REST API endpoints.
"""
import os
import json
import unittest
from unittest.mock import patch, MagicMock

# from squishy_REST_API.app_factory.app_factory import RESTAPIFactory
# from squishy_REST_API.app_factory.db_client_implementation import DBInstance


class BaseTestCase(unittest.TestCase):
    """Base test case for all tests."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Set required environment variables before importing
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

        # Now safe to import
        from squishy_REST_API.app_factory.app_factory import RESTAPIFactory
        from squishy_REST_API.app_factory.db_client_implementation import DBInstance

        self.RESTAPIFactory = RESTAPIFactory
        self.DBInstance = DBInstance

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original environment variables
        for key, original_value in self.original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value

    def create_app(self, is_core=False):
        """Create and configure a Flask application for testing."""
        # Create mock database client
        self.mock_db_client = MagicMock()

        # Create DBInstance wrapper with mock
        self.mock_db_instance = self.DBInstance(self.mock_db_client)

        # Patch the DBInstance methods we'll use in tests
        self.mock_db_instance.get_hash_record = MagicMock()
        self.mock_db_instance.insert_or_update_hash = MagicMock()
        self.mock_db_instance.get_single_hash_record = MagicMock()
        self.mock_db_instance.get_single_timestamp = MagicMock()
        self.mock_db_instance.get_priority_updates = MagicMock()
        self.mock_db_instance.put_log = MagicMock()
        self.mock_db_instance.get_logs = MagicMock()
        self.mock_db_instance.health_check = MagicMock()
        self.mock_db_instance.find_orphaned_entries = MagicMock()
        self.mock_db_instance.find_untracked_children = MagicMock()
        self.mock_db_instance.consolidate_logs = MagicMock()
        self.mock_db_instance.delete_log_entries = MagicMock()

        # Core-only methods
        if is_core:
            self.mock_db_instance.get_dashboard_content = MagicMock()
            self.mock_db_instance.get_recent_logs = MagicMock()
            self.mock_db_instance.get_hash_record_count = MagicMock()
            self.mock_db_instance.get_log_count_last_24h = MagicMock()
            self.mock_db_instance.get_site_liveness = MagicMock()
            self.mock_db_instance.get_site_sync_status = MagicMock()
            self.mock_db_instance.get_pipeline_updates = MagicMock()
            self.mock_db_instance.put_pipeline_hash = MagicMock()
            self.mock_db_instance.get_pipeline_sites = MagicMock()
            self.mock_db_instance.put_pipeline_site_completion = MagicMock()

        # Create test configuration
        test_config = {
            'TESTING': True,
            'DEBUG': False,
            'SECRET_KEY': 'test-secret-key',
            'db_instance': self.mock_db_instance
        }

        # Mock the config to control is_core behavior
        with patch('squishy_REST_API.app_factory.app_factory.config') as mock_config:
            mock_config.is_core = is_core
            mock_config.site_name = 'TEST'
            mock_config.database_config = {
                'remote_type': 'mock',
                'remote_config': {},
                'core_type': 'mock' if is_core else None,
                'core_config': {} if is_core else None,
                'pipeline_type': 'mock' if is_core else None,
                'pipeline_config': {} if is_core else None,
            }

            # Create application with test configuration
            return self.RESTAPIFactory.create_app(test_config)

    def create_test_client(self, app):
        """Create a test client for the Flask application."""
        return app.test_client()


class APITestCase(BaseTestCase):
    """Base test case for API tests."""

    def setUp(self):
        """Set up test environment before each test."""
        # Set required environment variables before importing
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

        # Now safe to import
        from squishy_REST_API.app_factory.app_factory import RESTAPIFactory
        from squishy_REST_API.app_factory.db_client_implementation import DBInstance

        self.RESTAPIFactory = RESTAPIFactory
        self.DBInstance = DBInstance

        # Create application with test configuration (not core)
        self.app = self.create_app(is_core=False)

        # Create test client
        self.client = self.create_test_client(self.app)


class HashtableEndpointTestCase(APITestCase):
    """Test cases for the /api/hashtable endpoint."""

    def test_get_hashtable_record_success(self):
        """Test GET /api/hashtable?field=record with a path that exists."""
        # Configure mock to return a record
        mock_record = {
            'path': 'test_path',
            'current_hash': 'test_hash',
            'current_dtg_latest': 123456789
        }
        self.mock_db_instance.get_hash_record.return_value = mock_record

        # Make request to endpoint
        response = self.client.get('/api/hashtable?path=test_path&field=record')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], mock_record)

        # Verify mock was called correctly
        self.mock_db_instance.get_hash_record.assert_called_once_with('test_path')

    def test_get_hashtable_hash_success(self):
        """Test GET /api/hashtable?field=hash with a path that exists."""
        # Configure mock to return a hash value
        self.mock_db_instance.get_single_hash_record.return_value = 'test_hash_value'

        # Make request to endpoint
        response = self.client.get('/api/hashtable?path=test_path&field=hash')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], 'test_hash_value')

        # Verify mock was called correctly
        self.mock_db_instance.get_single_hash_record.assert_called_once_with('test_path')

    def test_get_hashtable_timestamp_success(self):
        """Test GET /api/hashtable?field=timestamp with a path that exists."""
        # Configure mock to return a timestamp
        self.mock_db_instance.get_single_timestamp.return_value = 123456789

        # Make request to endpoint
        response = self.client.get('/api/hashtable?path=test_path&field=timestamp')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], 123456789)

        # Verify mock was called correctly
        self.mock_db_instance.get_single_timestamp.assert_called_once_with('test_path')

    def test_get_hashtable_priority_updates(self):
        """Test GET /api/hashtable?field=priority."""
        # Configure mock to return priority data
        mock_priority_data = ['path1', 'path2', 'path3']
        self.mock_db_instance.get_priority_updates.return_value = mock_priority_data

        # Make request to endpoint
        response = self.client.get('/api/hashtable?field=priority')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], mock_priority_data)

        # Verify mock was called correctly
        self.mock_db_instance.get_priority_updates.assert_called_once()

    def test_get_hashtable_untracked_children(self):
        """Test GET /api/hashtable?field=untracked."""
        # Configure mock to return untracked children
        mock_untracked_data = ['path1', 'path2']
        self.mock_db_instance.find_untracked_children.return_value = mock_untracked_data

        # Make request to endpoint
        response = self.client.get('/api/hashtable?field=untracked')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], mock_untracked_data)

        # Verify mock was called correctly
        self.mock_db_instance.find_untracked_children.assert_called_once()

    def test_get_hashtable_orphaned_entries(self):
        """Test GET /api/hashtable?field=orphaned."""
        # Configure mock to return orphaned entries
        mock_orphaned_data = ['path1', 'path2']
        self.mock_db_instance.find_orphaned_entries.return_value = mock_orphaned_data

        # Make request to endpoint
        response = self.client.get('/api/hashtable?field=orphaned')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], mock_orphaned_data)

        # Verify mock was called correctly
        self.mock_db_instance.find_orphaned_entries.assert_called_once()

    def test_get_hashtable_invalid_field(self):
        """Test GET /api/hashtable with invalid field parameter."""
        # Make request to endpoint with invalid field
        response = self.client.get('/api/hashtable?path=test_path&field=invalid')

        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Invalid field parameter', data['message'])

    def test_get_hashtable_not_found(self):
        """Test GET /api/hashtable with a path that doesn't exist."""
        # Configure mock to return None (not found)
        self.mock_db_instance.get_hash_record.return_value = None

        # Make request to endpoint
        response = self.client.get('/api/hashtable?path=nonexistent_path')

        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Path not found')

    def test_post_hashtable_success(self):
        """Test POST /api/hashtable with valid data."""
        # Configure mock to return success
        self.mock_db_instance.insert_or_update_hash.return_value = True

        # Make request to endpoint
        request_data = {
            'path': 'test_path',
            'current_hash': 'test_hash',
            'current_dtg_latest': 123456789
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
        """Test POST /api/hashtable with database error."""
        # Configure mock to return failure
        self.mock_db_instance.insert_or_update_hash.return_value = False

        # Make request to endpoint
        request_data = {
            'path': 'test_path',
            'current_hash': 'test_hash',
            'current_dtg_latest': 123456789
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


class LogsEndpointTestCase(APITestCase):
    """Test cases for the /api/logs endpoint."""

    def test_post_logs_success(self):
        """Test POST /api/logs with valid data."""

        # put_log is called during rest_api startup
        self.mock_db_instance.put_log.assert_called_once()

        # Configure mock to return success
        self.mock_db_instance.put_log.return_value = 1

        # Make request to endpoint
        request_data = {
            'summary_message': 'Test log message',
            'log_level': 'INFO',
            'site_id': 'TEST'
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
        self.assertEqual(data['data'], True)

        # Verify mock was called correctly a second time
        self.assertTrue(self.mock_db_instance.put_log.call_count == 2)

    def test_post_logs_db_error(self):
        """Test POST /api/logs with database error."""
        # Configure mock to return failure
        self.mock_db_instance.put_log.return_value = False

        # Make request to endpoint
        request_data = {
            'summary_message': 'Test log message',
            'log_level': 'INFO',
            'site_id': 'TEST'
        }
        response = self.client.post(
            '/api/logs',
            data=json.dumps(request_data),
            content_type='application/json'
        )

        # Check response
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('Error adding log entry', data['message'])

    def test_get_logs_consolidate(self):
        """Test GET /api/logs?action=consolidate."""
        # Configure mock to return success
        self.mock_db_instance.consolidate_logs.return_value = True

        # Make request to endpoint
        response = self.client.get('/api/logs?action=consolidate')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], True)

        # Verify mock was called correctly
        self.mock_db_instance.consolidate_logs.assert_called_once()

    def test_get_logs_shippable(self):
        """Test GET /api/logs?action=shippable."""
        # Configure mock to return logs data
        mock_logs_data = [
            {'id': 1, 'summary_message': 'Test log 1'},
            {'id': 2, 'summary_message': 'Test log 2'}
        ]
        self.mock_db_instance.get_logs.return_value = mock_logs_data

        # Make request to endpoint
        response = self.client.get('/api/logs?action=shippable')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], mock_logs_data)

        # Verify mock was called correctly
        self.mock_db_instance.get_logs.assert_called_once_with(session_id_filter='null')

    def test_get_logs_invalid_action(self):
        """Test GET /api/logs with invalid action parameter."""
        # Make request to endpoint with invalid action
        response = self.client.get('/api/logs?action=invalid')

        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Invalid or missing \'action\' parameter', data['message'])

    def test_delete_logs_success(self):
        """Test DELETE /api/logs with valid data."""
        # Configure mock to return success
        self.mock_db_instance.delete_log_entries.return_value = ([1, 2, 3], [])

        # Make request to endpoint
        request_data = {'log_ids': [1, 2, 3]}
        response = self.client.delete(
            '/api/logs',
            data=json.dumps(request_data),
            content_type='application/json'
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data']['deleted_count'], [1, 2, 3])

        # Verify mock was called correctly
        self.mock_db_instance.delete_log_entries.assert_called_once_with([1, 2, 3])

    def test_delete_logs_partial_success(self):
        """Test DELETE /api/logs with partial success."""
        # Configure mock to return partial success
        self.mock_db_instance.delete_log_entries.return_value = ([1, 2], [3])

        # Make request to endpoint
        request_data = {'log_ids': [1, 2, 3]}
        response = self.client.delete(
            '/api/logs',
            data=json.dumps(request_data),
            content_type='application/json'
        )

        # Check response
        self.assertEqual(response.status_code, 207)  # Multi-Status for partial success
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Partial success')
        self.assertEqual(data['data']['deleted_count'], [1, 2])
        self.assertEqual(data['data']['failed_deletes'], [3])

    def test_delete_logs_missing_body(self):
        """Test DELETE /api/logs with missing request body."""
        # Make request to endpoint without body
        response = self.client.delete('/api/logs')

        # Check response
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('Internal server error', data['message'])


class HealthCheckEndpointTestCase(APITestCase):
    """Test cases for the health check endpoints."""

    def test_health_check_success(self):
        """Test GET /api/health with healthy services."""
        # Configure mock to return healthy status
        self.mock_db_instance.health_check.return_value = {'database': True}

        # Make request to endpoint
        response = self.client.get('/api/health')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data']['status'], 'healthy')
        self.assertTrue(data['data']['services']['api'])
        self.assertTrue(data['data']['services']['database'])

        # Verify mock was called correctly
        self.mock_db_instance.health_check.assert_called_once()

    def test_health_check_unhealthy(self):
        """Test GET /api/health with unhealthy database."""
        # Configure mock to return unhealthy status
        self.mock_db_instance.health_check.return_value = {'database': False}

        # Make request to endpoint
        response = self.client.get('/api/health')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data']['status'], 'unhealthy')
        self.assertTrue(data['data']['services']['api'])
        self.assertFalse(data['data']['services']['database'])

    def test_lifecheck_alias(self):
        """Test that /api/lifecheck is an alias for /api/health."""
        # Configure mock to return healthy status
        self.mock_db_instance.health_check.return_value = {'database': True}

        # Make request to endpoint
        response = self.client.get('/api/lifecheck')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['data']['status'], 'healthy')

    def test_health_alias(self):
        """Test that /health is an alias for /api/health."""
        # Configure mock to return healthy status
        self.mock_db_instance.health_check.return_value = {'database': True}

        # Make request to endpoint
        response = self.client.get('/health')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['data']['status'], 'healthy')


class CoreAPITestCase(BaseTestCase):
    """Base test case for Core API tests."""

    def setUp(self):
        """Set up test environment before each test."""
        # Set required environment variables before importing
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

        # Now safe to import
        from squishy_REST_API.app_factory.app_factory import RESTAPIFactory
        from squishy_REST_API.app_factory.db_client_implementation import DBInstance

        self.RESTAPIFactory = RESTAPIFactory
        self.DBInstance = DBInstance

        # Create application with test configuration (core site)
        self.app = self.create_app(is_core=True)

        # Create test client
        self.client = self.create_test_client(self.app)


class PipelineEndpointTestCase(CoreAPITestCase):
    """Test cases for the /api/pipeline endpoint (core sites only)."""

    def test_get_pipeline_updates(self):
        """Test GET /api/pipeline?action=updates."""
        # Configure mock to return pipeline updates
        mock_updates = [
            {'update_path': '/path1', 'hash_value': 'hash1'},
            {'update_path': '/path2', 'hash_value': 'hash2'}
        ]
        self.mock_db_instance.get_pipeline_updates.return_value = mock_updates

        # Make request to endpoint
        response = self.client.get('/api/pipeline?action=updates')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], mock_updates)

        # Verify mock was called correctly
        self.mock_db_instance.get_pipeline_updates.assert_called_once()

    def test_get_pipeline_sites(self):
        """Test GET /api/pipeline?action=sites."""
        # Configure mock to return sites
        mock_sites = ['SITE1', 'SITE2', 'SITE3']
        self.mock_db_instance.get_pipeline_sites.return_value = mock_sites

        # Make request to endpoint
        response = self.client.get('/api/pipeline?action=sites')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], mock_sites)

        # Verify mock was called correctly
        self.mock_db_instance.get_pipeline_sites.assert_called_once()

    def test_get_pipeline_invalid_action(self):
        """Test GET /api/pipeline with invalid action."""
        # Make request to endpoint with invalid action
        response = self.client.get('/api/pipeline?action=invalid')

        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Invalid \'action\' parameter', data['message'])

    def test_post_pipeline_hash_success(self):
        """Test POST /api/pipeline with action=hash."""
        # Configure mock to return success
        self.mock_db_instance.put_pipeline_hash.return_value = True

        # Make request to endpoint
        request_data = {
            'action': 'hash',
            'update_path': '/test/path',
            'hash_value': 'test_hash_value'
        }
        response = self.client.post(
            '/api/pipeline',
            data=json.dumps(request_data),
            content_type='application/json'
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data'], True)

        # Verify mock was called correctly
        self.mock_db_instance.put_pipeline_hash.assert_called_once_with('/test/path', 'test_hash_value')

    def test_post_pipeline_hash_missing_data(self):
        """Test POST /api/pipeline with action=hash but missing required data."""
        # Make request to endpoint with missing data
        request_data = {
            'action': 'hash',
            'update_path': '/test/path'
            # Missing hash_value
        }
        response = self.client.post(
            '/api/pipeline',
            data=json.dumps(request_data),
            content_type='application/json'
        )

        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Both \'update_path\' and \'hash_value\' are required', data['message'])

    def test_post_pipeline_hash_db_error(self):
        """Test POST /api/pipeline with action=hash and database error."""
        # Configure mock to return failure
        self.mock_db_instance.put_pipeline_hash.return_value = False

        # Make request to endpoint
        request_data = {
            'action': 'hash',
            'update_path': '/test/path',
            'hash_value': 'test_hash_value'
        }
        response = self.client.post(
            '/api/pipeline',
            data=json.dumps(request_data),
            content_type='application/json'
        )

        # Check response
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('Failed to update pipeline hash', data['message'])

    def test_post_pipeline_invalid_action(self):
        """Test POST /api/pipeline with invalid action."""
        # Make request to endpoint with invalid action
        request_data = {'action': 'invalid'}
        response = self.client.post(
            '/api/pipeline',
            data=json.dumps(request_data),
            content_type='application/json'
        )

        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Invalid \'action\' parameter', data['message'])

    # def test_post_pipeline_missing_body(self):
    #     """Test POST /api/pipeline with missing request body."""
    #     # Make request to endpoint without body
    #     response = self.client.post('/api/pipeline')
    #
    #     # Check response
    #     self.assertEqual(response.status_code, 500)
    #     data = json.loads(response.data)
    #     self.assertIn('Request body required', data['message'])


class GUITestCase(CoreAPITestCase):
    """Base test case for GUI tests (core sites only)."""

    def setUp(self):
        """Set up test environment before each test."""
        super().setUp()
        # GUI tests inherit from CoreAPITestCase which sets up core site


class DashboardEndpointTestCase(GUITestCase):
    """Test cases for the / (dashboard) endpoint."""

    def test_dashboard_success(self):
        """Test GET / endpoint."""
        # Configure mock to return dashboard data
        mock_dashboard_data = {
            'crit_error_count': 0,
            'hash_record_count': 1000,
            'sync_current': 5,
            'sync_1_behind': 2,
            'sync_l24_behind': 1,
            'sync_g24_behind': 0,
            'sync_unknown': 0,
            'live_current': 4,
            'live_1_behind': 3,
            'live_l24_behind': 1,
            'live_inactive': 0,
        }
        self.mock_db_instance.get_dashboard_content.return_value = mock_dashboard_data

        # Make request to endpoint
        response = self.client.get('/')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard', response.data)

        # Verify mock was called correctly
        self.mock_db_instance.get_dashboard_content.assert_called_once()

    def test_dashboard_alias(self):
        """Test GET /dashboard endpoint."""
        # Configure mock to return dashboard data
        mock_dashboard_data = {
            'crit_error_count': 0,
            'hash_record_count': 1000,
        }
        self.mock_db_instance.get_dashboard_content.return_value = mock_dashboard_data

        # Make request to endpoint
        response = self.client.get('/dashboard')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard', response.data)


class HashtableDetailEndpointTestCase(GUITestCase):
    """Test cases for the /web/hashtable/<path:file_path> endpoint."""

    def test_hashtable_detail_success(self):
        """Test GET /web/hashtable/<path:file_path> with a path that exists."""
        # Configure mock to return a record
        mock_record = {
            'path': '/test_path',
            'current_hash': 'test_hash',
            'current_dtg_latest': 123456789,
            'current_dtg_first': 123456780,
            'prev_dtg_latest': 123456770,
            'files': ['file1', 'file2'],
            'dirs': ['dir1', 'dir2'],
            'links': ['link1', 'link2']
        }
        self.mock_db_instance.get_hash_record.return_value = mock_record

        # Make request to endpoint
        response = self.client.get('/web/hashtable/test_path')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'test_hash', response.data)

        # Verify mock was called correctly
        self.mock_db_instance.get_hash_record.assert_called_once_with('/test_path')

    def test_hashtable_detail_not_found(self):
        """Test GET /web/hashtable/<path:file_path> with a path that doesn't exist."""
        # Configure mock to return None (not found)
        self.mock_db_instance.get_hash_record.return_value = None

        # Make request to endpoint
        response = self.client.get('/web/hashtable/nonexistent_path')

        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'not found', response.data.lower())

        # Verify mock was called correctly
        self.mock_db_instance.get_hash_record.assert_called_once_with('/nonexistent_path')


class LivenessEndpointTestCase(GUITestCase):
    """Test cases for the /web/liveness endpoint."""

    def test_liveness_success(self):
        """Test GET /web/liveness endpoint."""
        mock_liveness_data = [
            {'site_name': 'SITE1', 'status_category': 'live_current', 'last_updated': 123456789},
            {'site_name': 'SITE2', 'status_category': 'live_1_behind', 'last_updated': 123456790}
        ]
        self.mock_db_instance.get_site_liveness.return_value = mock_liveness_data

        # Make request to endpoint
        response = self.client.get('/web/liveness')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Site Liveness', response.data)

        # Verify mock was called correctly
        self.mock_db_instance.get_site_liveness.assert_called_once()


class HashStatusEndpointTestCase(GUITestCase):
    """Test cases for the /web/status endpoint."""

    def test_hash_status_success(self):
        """Test GET /web/status endpoint."""
        # Configure mock to return hash sync status data
        mock_sync_data = [
            {'site_name': 'SITE1', 'current_hash': 'hash1', 'last_updated': 123456789, 'sync_category': 'sync_current'},
            {'site_name': 'SITE2', 'current_hash': 'hash2', 'last_updated': 123456790, 'sync_category': 'sync_1_behind'}
        ]
        self.mock_db_instance.get_site_sync_status.return_value = mock_sync_data

        # Make request to endpoint
        response = self.client.get('/web/status')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hash Status', response.data)

        # Verify mock was called correctly
        self.mock_db_instance.get_site_sync_status.assert_called_once()


class ErrorHandlerTestCase(APITestCase):
    """Test cases for error handlers."""

    def test_404_api_endpoint(self):
        """Test 404 error handling for API endpoints."""
        # Make request to non-existent API endpoint
        response = self.client.get('/api/nonexistent')

        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Not Found')
        self.assertIn('API resource was not found', data['message'])

    def test_405_method_not_allowed(self):
        """Test 405 error handling for API endpoints."""
        # Make PUT request to GET-only endpoint
        response = self.client.put('/api/hashtable')

        # Check response
        self.assertEqual(response.status_code, 405)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Method Not Allowed')
        self.assertIn('Method \'PUT\' not allowed', data['message'])


class ConfigTestCase(unittest.TestCase):
    """Test cases for configuration handling."""

    @patch.dict('os.environ', {
        'SITE_NAME': 'TEST',
        'LOCAL_DB_USER': 'test_user',
        'LOCAL_DB_PASSWORD': 'test_pass',
        'API_SECRET_KEY': 'test_secret'
    })
    def test_config_from_environment(self):
        """Test configuration loading from environment variables."""
        from squishy_REST_API.configuration.config import Config

        # Create new config instance
        config = Config()

        # Check that environment variables were loaded
        self.assertEqual(config.get('site_name'), 'TEST')
        self.assertEqual(config.get('db_user'), 'test_user')
        self.assertEqual(config.get('db_password'), 'test_pass')
        self.assertEqual(config.get('secret_key'), 'test_secret')


    @patch.dict('os.environ', {
        'SITE_NAME': 'TEST',
        'LOCAL_DB_USER': 'test_user',

        'API_SECRET_KEY': 'test_secret'
    })
    def test_config_validation_missing_required(self):
        """Test configuration validation with missing required keys."""
        from squishy_REST_API.configuration.config import Config, ConfigError

        # Try to create config with missing required values
        with self.assertRaises(ConfigError) as cm:
            config = Config()
            config._set('db_user', None)
            config._set('site_name', 'TEST')

        self.assertIn('Missing required configuration keys', str(cm.exception))


if __name__ == '__main__':
    unittest.main()