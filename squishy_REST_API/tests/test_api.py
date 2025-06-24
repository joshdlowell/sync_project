"""
Tests for the REST API package.

This module contains tests for the REST API endpoints.
"""
import json
import unittest
from unittest.mock import patch, MagicMock
from squishy_REST_API.app_factory.app_factory import create_app
from squishy_REST_API.DB_connections.local_memory import LocalMemoryConnection

# from squishy_REST_API.tests.conftest import BaseTestCase
class BaseTestCase(unittest.TestCase):
    """Base test case for all tests."""

    def create_app(self):
        """Create and configure a Flask application for testing."""
        # Create test configuration
        test_config = {
            'TESTING': True,
            'DEBUG': False,
        }

        # Create application with test configuration
        return create_app(test_config)

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


class HashEndpointTestCase(APITestCase):
    """Test cases for the /api/hash endpoint."""

    def test_get_hash_not_found(self):
        """Test GET /api/hash endpoint with a path that doesn't exist."""
        # Make request to endpoint
        response = self.client.get('/api/hash?nonexistent_path')

        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Path not found')

    def test_get_hash_success(self):
        """Test GET /api/hash endpoint with a path that exists."""
        # Mock the database response
        with patch('squishy_REST_API.app_factory.api_routes.db_instance') as mock_db:
            # Configure mock to return a hash value
            mock_db.get_single_hash_record.return_value = 'test_hash_value'

            # Make request to endpoint
            response = self.client.get('/api/hash?test_path')

            # Check response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['message'], 'Success')
            self.assertEqual(data['data'], 'test_hash_value')

            # Verify mock was called correctly
            mock_db.get_single_hash_record.assert_called_once_with('test_path')


class HashtableEndpointTestCase(APITestCase):
    """Test cases for the /api/hashtable endpoint."""

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
        # Mock the database response
        with patch('squishy_REST_API.app_factory.api_routes.db_instance') as mock_db:
            # Configure mock to return changes
            mock_db.insert_or_update_hash.return_value = {
                'modified': ['test_path'],
                'created': [],
                'deleted': []
            }

            # Make request to endpoint
            response = self.client.post(
                '/api/hashtable',
                data=json.dumps({
                    'path': 'test_path',
                    'current_hash': 'test_hash',
                    'current_dtg_latest': 123456789.0
                }),
                content_type='application/json'
            )

            # Check response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['message'], 'Success')
            self.assertIn('modified', data['data'])
            self.assertEqual(data['data']['modified'], ['test_path'])

            # Verify mock was called correctly
            mock_db.insert_or_update_hash.assert_called_once()
            # First argument should be path
            self.assertEqual(mock_db.insert_or_update_hash.call_args[1]['path'], 'test_path')
            # Other arguments should be in kwargs
            self.assertEqual(mock_db.insert_or_update_hash.call_args[1]['current_hash'], 'test_hash')


class TimestampEndpointTestCase(APITestCase):
    """Test cases for the /api/timestamp endpoint."""

    def test_get_timestamp_not_found(self):
        """Test GET /api/timestamp endpoint with a path that doesn't exist."""
        # Make request to endpoint
        response = self.client.get('/api/hash?nonexistent_path')

        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Path not found')

    def test_get_timestamp_success(self):
        """Test GET /api/timestamp endpoint with a path that exists."""
        # Mock the database response
        with patch('squishy_REST_API.app_factory.api_routes.db_instance') as mock_db:
            # Configure mock to return a hash value
            mock_db.get_single_timestamp.return_value = 123456

            # Make request to endpoint
            response = self.client.get('/api/timestamp?test_path')

            # Check response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['message'], 'Success')
            self.assertEqual(data['data'], 123456)

            # Verify mock was called correctly
            mock_db.get_single_timestamp.assert_called_once_with('test_path')


class PriorityEndpointTestCase(APITestCase):
    """Test cases for the /api/priority endpoint."""

    def test_get_priority_missing_root_path(self):
        """Test GET /api/priority endpoint with missing root_path parameter."""
        # Make request to endpoint without root_path
        response = self.client.get('/api/priority')

        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('root_path parameter is required', data['message'])

    def test_get_priority_invalid_percent(self):
        """Test GET /api/priority endpoint with invalid percent parameter."""
        # Make request to endpoint with invalid percent
        response = self.client.get('/api/priority?root_path=/test&percent=invalid')

        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Invalid percent parameter', data['message'])

    def test_get_priority_success(self):
        """Test GET /api/priority endpoint with valid parameters."""
        # Mock the database response
        with patch('squishy_REST_API.app_factory.api_routes.db_instance') as mock_db:
            # Configure mock to return a list of directories
            mock_db.get_oldest_updates.return_value = [
                '/test/dir1',
                '/test/dir2'
            ]

            # Make request to endpoint
            response = self.client.get('/api/priority?root_path=/test&percent=20')

            # Check response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['message'], 'Success')
            self.assertEqual(data['data'], ['/test/dir1', '/test/dir2'])

            # Verify mock was called correctly
            mock_db.get_oldest_updates.assert_called_once_with('/test', 20)

class LifeCheckEndpointTestCase(APITestCase):
    """Test cases for the /api/lifecheck endpoint."""

    def test_get_lifecheck_db_down(self):
        """Test GET /api/timestamp endpoint, mock a db down response."""
        # Mock the database response
        with patch('squishy_REST_API.app_factory.api_routes.db_instance') as mock_db:
            # Configure mock to return a db down response
            mock_db.lifecheck.return_value = {'message': 'Success', 'data':{'api': True, 'db': False}}
        # Make request to endpoint
        response = self.client.get('/api/lifecheck')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data']['db'], False)
        self.assertEqual(data['data']['api'], True)
        # Verify mock was called correctly
        mock_db.lifecheck.assert_called_once()

    def test_get_lifecheck_success(self):
        """Test GET /api/timestamp endpoint, mock a full success response."""
        # Mock the database response
        with patch('squishy_REST_API.app_factory.api_routes.db_instance') as mock_db:
            # Configure mock to return a db down response
            mock_db.lifecheck.return_value = {'message': 'Success', 'data':{'api': True, 'db': True}}
        # Make request to endpoint
        response = self.client.get('/api/lifecheck')

        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Success')
        self.assertEqual(data['data']['db'], True)
        self.assertEqual(data['data']['api'], True)
        # Verify mock was called correctly
        mock_db.lifecheck.assert_called_once()


if __name__ == '__main__':
    unittest.main()
