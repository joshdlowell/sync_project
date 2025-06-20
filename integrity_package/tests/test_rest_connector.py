import unittest
from unittest.mock import Mock, patch
from integrity_package.rest_connector.rest_connector import RestConnector
from integrity_package.rest_connector.configuration import Config
from integrity_package.rest_connector.client import HttpClient
from integrity_package.rest_connector.validator import HashInfoValidator


class TestRestConnector(unittest.TestCase):
    def setUp(self):
        self.config = Config("test-api", "8080")
        self.mock_http_client = Mock(spec=HttpClient)
        self.validator = HashInfoValidator()
        self.rest_connector = RestConnector(self.config, self.mock_http_client, self.validator)

    def test_get_single_hash_success(self):
        # Arrange
        self.mock_http_client.get.return_value = (200, "test_hash")

        # Act
        result = self.rest_connector.get_single_hash("/test/path")

        # Assert
        self.assertEqual(result, "test_hash")
        self.mock_http_client.get.assert_called_once_with("http://test-api:8080/hash", "/test/path")

    def test_get_single_hash_not_found(self):
        # Arrange
        self.mock_http_client.get.return_value = (404, "Not found")

        # Act
        result = self.rest_connector.get_single_hash("/test/path")

        # Assert
        self.assertIsNone(result)

    def test_put_hashtable_validation_error(self):
        # Arrange
        invalid_hash_info = {
            "/test/path": {
                "invalid_key": "value",
                "current_hash": "hash123"
                # Missing required 'current_dtg_latest'
            }
        }

        # Act
        with patch('builtins.print') as mock_print:
            result = self.rest_connector.put_hashtable(invalid_hash_info)

        # Assert
        self.assertEqual(result, {'Created': set(), 'Deleted': set(), 'Modified': set()})
        mock_print.assert_called()


class TestHashInfoValidator(unittest.TestCase):
    def setUp(self):
        self.validator = HashInfoValidator()

    def test_valid_hash_info(self):
        valid_data = {
            "/test": {
                "current_hash": "hash123",
                "current_dtg_latest": "2023-01-01",
                "dirs": ["dir1", "dir2"]
            }
        }

        errors = self.validator.validate(valid_data)
        self.assertEqual(errors, [])

    def test_missing_required_key(self):
        invalid_data = {
            "/test": {
                "current_hash": "hash123"
                # Missing 'current_dtg_latest'
            }
        }

        errors = self.validator.validate(invalid_data)
        self.assertIn("Missing required key 'current_dtg_latest' in item '/test'", errors)

