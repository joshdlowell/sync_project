"""
Tests for the REST API package.

This module contains tests for the REST API endpoints.
"""
import json
import unittest
from unittest.mock import patch, MagicMock

from squishy_REST_API.tests.conftest import BaseTestCase


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
    """Test cases for the /hash endpoint."""

    def test_get_hash_not_found(self):
        """Test GET /hash endpoint with a path that doesn't exist."""
        # Make request to endpoint
        response = self.client.get('/hash?nonexistent_path')

        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Path not found')

    def test_get_hash_success(self):
        """Test GET /hash endpoint with a path that exists."""
        # Mock the database response
        with patch('REST_API_package.routes.db_instance') as mock_db:
            # Configure mock to return a hash value
            mock_db.get_single_hash_record.return_value = 'test_hash_value'

            # Make request to endpoint
            response = self.client.get('/hash?test_path')

            # Check response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['message'], 'Success')
            self.assertEqual(data['data'], 'test_hash_value')

            # Verify mock was called correctly
            mock_db.get_single_hash_record.assert_called_once_with('test_path')


class HashtableEndpointTestCase(APITestCase):
    """Test cases for the /hashtable endpoint."""

    def test_post_hashtable_missing_path(self):
        """Test POST /hashtable endpoint with missing path."""
        # Make request to endpoint with missing path
        response = self.client.post(
            '/hashtable',
            data=json.dumps({'current_hash': 'test_hash'}),
            content_type='application/json'
        )

        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('path required', data['message'])

    def test_post_hashtable_success(self):
        """Test POST /hashtable endpoint with valid data."""
        # Mock the database response
        with patch('REST_API_package.routes.db_instance') as mock_db:
            # Configure mock to return changes
            mock_db.insert_or_update_hash.return_value = {
                'modified': ['test_path'],
                'created': [],
                'deleted': []
            }

            # Make request to endpoint
            response = self.client.post(
                '/hashtable',
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


class PriorityEndpointTestCase(APITestCase):
    """Test cases for the /priority endpoint."""

    def test_get_priority_missing_root_path(self):
        """Test GET /priority endpoint with missing root_path parameter."""
        # Make request to endpoint without root_path
        response = self.client.get('/priority')

        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('root_path parameter is required', data['message'])

    def test_get_priority_invalid_percent(self):
        """Test GET /priority endpoint with invalid percent parameter."""
        # Make request to endpoint with invalid percent
        response = self.client.get('/priority?root_path=/test&percent=invalid')

        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Invalid percent parameter', data['message'])

    def test_get_priority_success(self):
        """Test GET /priority endpoint with valid parameters."""
        # Mock the database response
        with patch('REST_API_package.routes.db_instance') as mock_db:
            # Configure mock to return a list of directories
            mock_db.get_oldest_updates.return_value = [
                '/test/dir1',
                '/test/dir2'
            ]

            # Make request to endpoint
            response = self.client.get('/priority?root_path=/test&percent=20')

            # Check response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['message'], 'Success')
            self.assertEqual(data['data'], ['/test/dir1', '/test/dir2'])

            # Verify mock was called correctly
            mock_db.get_oldest_updates.assert_called_once_with('/test', 20)


if __name__ == '__main__':
    unittest.main()
