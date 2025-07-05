import unittest
from unittest.mock import Mock, patch
from squishy_integrity.rest_client.rest_processor import RestProcessor
from squishy_integrity import config
from squishy_integrity.rest_client.http_client import HttpClient
from squishy_integrity.rest_client.hash_info_validator import HashInfoValidator


class TestRestProcessor(unittest.TestCase):
    def setUp(self):
        config._set('rest_api_host', "test-api")
        config._set('rest_api_port', "8080")
        self.mock_http_client = Mock(spec=HttpClient)
        self.validator = HashInfoValidator()
        self.rest_processor = RestProcessor(self.mock_http_client, self.validator)

    def test_put_hashtable_validation_valid_1(self):
    # def put_hashtable(self, hash_info: dict) -> int:
        # Arrange
        self.mock_http_client.post.return_value = (200, {"message": "Success", "data": 0})
        valid_hash_info = {
            "/test/path": {
                "current_hash": "hash123"
                # Minimum required for insertion
            }
        }
        # Act
        result = self.rest_processor.put_hashtable(valid_hash_info)
        # Assert
        self.assertEqual(result, 0)

    def test_put_hashtable_validation_invalid(self):
    # def put_hashtable(self, hash_info: dict) -> int:
        # Arrange
        invalid_hash_info = {
            "/test/path": {
                "invalid_key": "value",
                "current_hash": "hash123"
            }
        }
        # Act
        result = self.rest_processor.put_hashtable(invalid_hash_info)
        # Assert
        self.assertEqual(result, 1)

    def test_put_hashtable_validation_valid_2(self):
    # def put_hashtable(self, hash_info: dict) -> int:
        # Arrange
        self.mock_http_client.post.return_value = (200, {"message": "Success", "data": 0})
        valid_hash_info = {
            "/test/path": {
                "current_hash": "hash123",
                "dirs": [],
                "files": [],
                "links": [],
            }
        }
        # Act
        result = self.rest_processor.put_hashtable(valid_hash_info)
        # Assert
        self.assertEqual(result, 0)

    def test_put_hashtable_validation_valid_3(self):
    # def put_hashtable(self, hash_info: dict) -> int:
        # Arrange
        self.mock_http_client.post.return_value = (200, {"message": "Success", "data": 0})
        valid_hash_info = {
            "/test/path": {
                "current_hash": "hash123",
                "dirs": None,
                "files": None,
                "links": None,
            }
        }
        # Act
        result = self.rest_processor.put_hashtable(valid_hash_info)
        # Assert
        self.assertEqual(result, 0)

    def test_get_hashtable_validation_error(self):
        # def get_hashtable(self, path: str) -> dict | None:
        self.mock_http_client.get.return_value = (400, {"message": "path parameter is required"})
        path = " "
        result = self.rest_processor.get_hashtable(path)
        self.assertIsNone(result)

        pass

    def test_get_single_hash_success(self):
        # def get_single_hash(self, path: str) -> str | None:
        # Arrange
        self.mock_http_client.get.return_value = (200, 'hash_value')

        # Act
        result = self.rest_processor.get_single_hash("/test/path")

        # Assert
        self.assertEqual(result, 'hash_value')
        self.mock_http_client.get.assert_called_once_with("http://test-api:8080/api/hash", {'path': '/test/path'})

    def test_get_single_hash_not_found(self):
        # Arrange
        self.mock_http_client.get.return_value = (404, "Not found")

        # Act
        result = self.rest_processor.get_single_hash("/test/path")

        # Assert
        self.assertIsNone(result)

    def test_get_oldest_updates(self):
        # def get_oldest_updates(self, root_path: str, percent: int = 10) -> list[str]:
        pass

    def test_get_single_timestamp(self):
        # def get_single_timestamp(self, path: str) -> float | None:
        # Arrange
        self.mock_http_client.get.return_value = 200, 123456

        # Act
        result = self.rest_processor.get_single_timestamp("/test/path")

        # Assert
        self.assertEqual(result, 123456)
        self.mock_http_client.get.assert_called_once_with("http://test-api:8080/api/timestamp", {'path': '/test/path'})

    def test_get_priority_updates(self):
        # def get_priority_updates(self) -> list | None:
        pass

    def test_put_logs_valid_min(self):
        # Arrange
        self.mock_http_client.post.return_value = (200, {"message": "Success", "data": 0})

        # Act
        result = self.rest_processor.put_log("test_message")

        # Assert
        self.assertEqual(result, 0)
        self.mock_http_client.post.assert_called_once_with("http://test-api:8080/api/logs", {'summary_message': 'test_message'})

    def test_put_logs_valid_complete(self):
        # Arrange
        self.mock_http_client.post.return_value = (200, {"message": "Success", "data": 0})
        log_message = {
            'message': 'test_message',
            'detailed_message': "This is the real message",
            'log_level': "WARNING"}
        processor_message = {
            'summary_message': 'test_message',
            'detailed_message': 'This is the real message',
            'log_level': 'WARNING'}
        # Act
        result = self.rest_processor.put_log(
            log_message['message'],
            log_message['detailed_message'],
            log_message["log_level"]
        )

        # Assert
        self.assertEqual(result, 0)
        self.mock_http_client.post.assert_called_once_with("http://test-api:8080/api/logs", processor_message )

    def test_put_logs_invalid_1(self):
        # Arrange
        self.mock_http_client.post.return_value = 400, {"message": "message required but not found in your request json"}
        log_message = {
            'message': 'test_message',
            'detailed_message': "This is the real message",
            'log_level': "WARNING"}
        # Act
        result = self.rest_processor.put_log(
            '',
            log_message['detailed_message'],
            log_message["log_level"]
        )
        # Assert
        self.assertEqual(result, 1)
        self.mock_http_client.post.assert_not_called()

class TestHashInfoValidator(unittest.TestCase):
    def setUp(self):
        self.validator = HashInfoValidator()

    def test_valid_hash_info(self):
        valid_data = {
            "/test": {
                "current_hash": "hash123",
                "dirs": ["dir1", "dir2"]
            }
        }

        errors = self.validator.validate(valid_data)
        self.assertEqual(errors, [])

    def test_missing_required_key(self):
        invalid_data = {
            "/test": {
                "dirs": ["dir1", "dir2"]
                # Missing 'current_hash'
            }
        }

        errors = self.validator.validate(invalid_data)
        self.assertIn("Missing required key 'current_hash' in item '/test'", errors)
