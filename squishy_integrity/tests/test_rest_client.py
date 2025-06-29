import unittest
from unittest.mock import Mock, patch
from squishy_integrity.rest_client.rest_processor import RestProcessor
from squishy_integrity import config
from squishy_integrity.rest_client.http_client import HttpClient
from squishy_integrity.rest_client.hash_info_validator import HashInfoValidator
from squishy_integrity.rest_client import RestClient


class TestRestProcessor(unittest.TestCase):
    def setUp(self):
        config._set('rest_api_host', "test-api")
        config._set('rest_api_port', "8080")
        self.mock_http_client = Mock(spec=HttpClient)
        self.validator = HashInfoValidator()
        self.rest_connector = RestProcessor(self.mock_http_client, self.validator)

    def test_put_hashtable_validation_error(self):
    # def put_hashtable(self, hash_info: dict) -> dict[str, set]:
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

    def test_get_hashtable_validation_error(self):
        # def get_hashtable(self, path: str) -> dict | None:
        pass

    def test_get_single_hash_success(self):
        # def get_single_hash(self, path: str) -> str | None:
        # Arrange
        self.mock_http_client.get.return_value = (200, {"message": "Success", "data": 'hash_value'})

        # Act
        result = self.rest_connector.get_single_hash("/test/path")

        # Assert
        self.assertEqual(result, 'hash_value')
        self.mock_http_client.get.assert_called_once_with("http://test-api:8080/api/hash", "/test/path")

    def test_get_single_hash_not_found(self):
        # Arrange
        self.mock_http_client.get.return_value = (404, "Not found")

        # Act
        result = self.rest_connector.get_single_hash("/test/path")

        # Assert
        self.assertIsNone(result)

    def test_get_oldest_updates(self):
        # def get_oldest_updates(self, root_path: str, percent: int = 10) -> list[str]:
        pass

    def test_get_single_timestamp(self):
        # def get_single_timestamp(self, path: str) -> float | None:
        pass

    def test_get_priority_updates(self):
        # def get_priority_updates(self) -> list | None:
        pass


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


# # For mock http client
# class RequestsHttpClient(HttpClient):
#     def __init__(self):
#         self.max_retries = config.get('max_retries')
#         self.retry_delay = config.get('retry_delay')
#         self.long_delay = config.get('long_delay')
#
#     def post(self, url: str, json_data: dict) -> Tuple[int, Any]:
#         return self._make_request('post', url, json_data)
#
#     def get(self, url: str, params: dict = None) -> Tuple[int, Any]:
#         return self._make_request('get', url, params)