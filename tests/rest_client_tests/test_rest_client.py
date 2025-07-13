import unittest
from unittest.mock import Mock, patch
from rest_client.rest_processor import RestProcessor
from rest_client.configuration.config import Config
from rest_client.http_client import HttpClient
from rest_client.hash_info_validator import HashInfoValidator


class TestRestProcessor(unittest.TestCase):
    def setUp(self):
        # Create a test config with required settings
        test_config = {
            'rest_api_host': 'test-api',
            'rest_api_port': 8080,
            'hash_validator_required_keys': {'path', 'target_hash'},
            'hash_validator_keys': {'path', 'target_hash', 'current_hash', 'current_dtg_latest',
                                    'dirs', 'files', 'links', 'session_id'},
            'valid_log_levels': {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        }
        self.config = Config(test_config)

        self.mock_http_client = Mock(spec=HttpClient)
        self.validator = HashInfoValidator()
        self.rest_api_url = "http://test-api:8080"
        self.rest_processor = RestProcessor(self.rest_api_url, self.mock_http_client, self.validator)

    def test_put_hashtable_valid_single_item(self):
        """Test put_hashtable with valid single item"""
        # Arrange
        self.mock_http_client.post.return_value = (200, {"data": True})
        valid_hash_info = {
            "/test/path": {
                "path": "/test/path",
                "target_hash": "target123",
                "current_hash": "hash123"
            }
        }

        # Act
        result = self.rest_processor.put_hashtable(valid_hash_info)

        # Assert
        self.assertEqual(result, 1)  # 1 successful update
        self.mock_http_client.post.assert_called_once()

    def test_put_hashtable_valid_multiple_items(self):
        """Test put_hashtable with multiple valid items"""
        # Arrange
        self.mock_http_client.post.return_value = (200, {"data": True})
        valid_hash_info = {
            "/test/path1": {
                "path": "/test/path1",
                "target_hash": "target123",
                "current_hash": "hash123"
            },
            "/test/path2": {
                "path": "/test/path2",
                "target_hash": "target456",
                "current_hash": "hash456",
                "dirs": ["subdir1", "subdir2"]
            }
        }

        # Act
        result = self.rest_processor.put_hashtable(valid_hash_info)

        # Assert
        self.assertEqual(result, 2)  # 2 successful updates
        self.assertEqual(self.mock_http_client.post.call_count, 2)

    def test_put_hashtable_invalid_item(self):
        """Test put_hashtable with invalid item (missing required keys)"""
        # Arrange
        invalid_hash_info = {
            "/test/path": {
                "current_hash": "hash123"
                # Missing required 'path' and 'target_hash'
            }
        }

        # Act
        result = self.rest_processor.put_hashtable(invalid_hash_info)

        # Assert
        self.assertEqual(result, 0)  # 0 successful updates
        self.mock_http_client.post.assert_not_called()

    def test_put_hashtable_mixed_valid_invalid(self):
        """Test put_hashtable with mix of valid and invalid items"""
        # Arrange
        self.mock_http_client.post.return_value = (200, {"data": True})
        mixed_hash_info = {
            "/test/valid": {
                "path": "/test/valid",
                "target_hash": "target123",
                "current_hash": "hash123"
            },
            "/test/invalid": {
                "current_hash": "hash456"
                # Missing required keys
            }
        }

        # Act
        result = self.rest_processor.put_hashtable(mixed_hash_info)

        # Assert
        self.assertEqual(result, 1)  # 1 successful update
        self.mock_http_client.post.assert_called_once()

    def test_put_hashtable_api_error(self):
        """Test put_hashtable when API returns error"""
        # Arrange
        self.mock_http_client.post.return_value = (400, {"error": "Bad request"})
        valid_hash_info = {
            "/test/path": {
                "path": "/test/path",
                "target_hash": "target123",
                "current_hash": "hash123"
            }
        }

        # Act
        result = self.rest_processor.put_hashtable(valid_hash_info)

        # Assert
        self.assertEqual(result, 0)  # 0 successful updates due to API error

    def test_get_hashtable_success(self):
        """Test get_hashtable with successful response"""
        # Arrange
        expected_data = {
            "path": "/test/path",
            "current_hash": "hash123",
            "dirs": ["dir1", "dir2"]
        }
        self.mock_http_client.get.return_value = (200, expected_data)

        # Act
        result = self.rest_processor.get_hashtable("/test/path")

        # Assert
        self.assertEqual(result, expected_data)
        self.mock_http_client.get.assert_called_once_with(
            "http://test-api:8080/api/hashtable",
            params={"path": "/test/path"}
        )

    def test_get_hashtable_not_found(self):
        """Test get_hashtable with 404 response"""
        # Arrange
        self.mock_http_client.get.return_value = (404, "Not found")

        # Act
        result = self.rest_processor.get_hashtable("/test/path")

        # Assert
        self.assertIsNone(result)

    def test_get_single_hash_success(self):
        """Test get_single_hash with successful response"""
        # Arrange
        self.mock_http_client.get.return_value = (200, "hash_value")

        # Act
        result = self.rest_processor.get_single_hash("/test/path")

        # Assert
        self.assertEqual(result, "hash_value")
        self.mock_http_client.get.assert_called_once_with(
            "http://test-api:8080/api/hashtable",
            params={"path": "/test/path", "field": "hash"}
        )

    def test_get_single_hash_not_found(self):
        """Test get_single_hash with 404 response"""
        # Arrange
        self.mock_http_client.get.return_value = (404, "Not found")

        # Act
        result = self.rest_processor.get_single_hash("/test/path")

        # Assert
        self.assertIsNone(result)

    def test_get_single_timestamp_success(self):
        """Test get_single_timestamp with successful response"""
        # Arrange
        self.mock_http_client.get.return_value = (200, 1234567890.0)

        # Act
        result = self.rest_processor.get_single_timestamp("/test/path")

        # Assert
        self.assertEqual(result, 1234567890.0)
        self.mock_http_client.get.assert_called_once_with(
            "http://test-api:8080/api/hashtable",
            params={"path": "/test/path", "field": 'timestamp'}
        )

    def test_get_priority_updates_success(self):
        """Test get_priority_updates with successful response"""
        # Arrange
        expected_paths = ["/path1", "/path2", "/path3"]
        self.mock_http_client.get.return_value = (200, expected_paths)

        # Act
        result = self.rest_processor.get_priority_updates()

        # Assert
        self.assertEqual(result, expected_paths)
        self.mock_http_client.get.assert_called_once_with("http://test-api:8080/api/hashtable", params={'path':None, 'field':'priority'})

    def test_get_lifecheck_success(self):
        """Test get_lifecheck with successful response"""
        # Arrange
        expected_data = {"status": "healthy", "database": "connected"}
        self.mock_http_client.get.return_value = (200, expected_data)

        # Act
        result = self.rest_processor.get_health()

        # Assert
        self.assertEqual(result, expected_data)
        self.mock_http_client.get.assert_called_once_with("http://test-api:8080/api/health", params=None)

    def test_put_log_valid_minimal(self):
        """Test put_log with minimal valid data"""
        # Arrange
        self.mock_http_client.post.return_value = (200, {"data": True})

        # Act
        result = self.rest_processor.put_log("test_message")

        # Assert
        self.assertEqual(result, 1)
        self.mock_http_client.post.assert_called_once_with(
            "http://test-api:8080/api/logs",
            json_data={"summary_message": "test_message", 'log_level': 'INFO'}
        )

    def test_put_log_valid_complete(self):
        """Test put_log with all optional parameters"""
        # Arrange
        self.mock_http_client.post.return_value = (200, {"data": True})

        # Act
        result = self.rest_processor.put_log(
            message="test_message",
            site_id="site123",
            timestamp=1234567890,
            detailed_message="detailed info",
            log_level="WARNING",
            session_id="session123"
        )

        # Assert
        self.assertEqual(result, 1)
        expected_data = {
            "summary_message": "test_message",
            "site_id": "site123",
            "timestamp": 1234567890,
            "detailed_message": "detailed info",
            "log_level": "WARNING",
            "session_id": "session123"
        }
        self.mock_http_client.post.assert_called_once_with(
            "http://test-api:8080/api/logs",
            json_data=expected_data
        )

    def test_put_log_invalid_empty_message(self):
        """Test put_log with empty message"""
        # Act
        result = self.rest_processor.put_log("")

        # Assert
        self.assertEqual(result, 0)
        self.mock_http_client.post.assert_not_called()

    def test_put_log_invalid_log_level(self):
        """Test put_log with invalid log level (should be filtered out)"""
        # Arrange
        self.mock_http_client.post.return_value = (200, {"data": True})

        # Act
        result = self.rest_processor.put_log("test_message", log_level="INVALID")

        # Assert
        self.assertEqual(result, 1)
        self.mock_http_client.post.assert_called_once_with(
            "http://test-api:8080/api/logs",
            json_data={'summary_message': 'test_message', 'log_level': 'INFO'}  # invalid log_level should be set to default
        )

    def test_put_log_api_error(self):
        """Test put_log when API returns error"""
        # Arrange
        self.mock_http_client.post.return_value = (400, {"error": "Bad request"})

        # Act
        result = self.rest_processor.put_log("test_message")

        # Assert
        self.assertEqual(result, 0)

    def test_delete_log_entries_success(self):
        """Test delete_log_entries with successful response"""
        # Arrange
        self.mock_http_client.delete.return_value = (200, {"deleted_count": 5})

        # Act
        success, data = self.rest_processor.delete_log_entries([1, 2, 3, 4, 5])

        # Assert
        self.assertTrue(success)
        self.assertEqual(data, [5])
        self.mock_http_client.delete.assert_called_once_with(
            "http://test-api:8080/api/logs",
            json_data={"log_ids": [1, 2, 3, 4, 5]}
        )

    def test_delete_log_entries_partial_success(self):
        """Test delete_log_entries with partial success (207 status)"""
        # Arrange
        self.mock_http_client.delete.return_value = (207, {"failed_deletes": [3, 5]})

        # Act
        success, data = self.rest_processor.delete_log_entries([1, 2, 3, 4, 5])

        # Assert
        self.assertFalse(success)
        self.assertEqual(data, [3, 5])

    def test_delete_log_entries_failure(self):
        """Test delete_log_entries with failure response"""
        # Arrange
        self.mock_http_client.delete.return_value = (400, {"error": "Bad request"})

        # Act
        success, data = self.rest_processor.delete_log_entries([1, 2, 3])

        # Assert
        self.assertFalse(success)
        self.assertEqual(data, [])

    @patch('rest_client.rest_processor.time')
    def test_get_oldest_updates_empty_database(self, mock_time):
        """Test get_oldest_updates when database is empty"""
        # Arrange
        mock_time.return_value = 1234567890
        self.mock_http_client.get.return_value = (200, {"data": None})

        # Act
        result = self.rest_processor.get_oldest_updates("/baseline")

        # Assert
        self.assertEqual(result, ["/baseline"])

    @patch('rest_client.rest_processor.time')
    def test_get_oldest_updates_no_dirs(self, mock_time):
        """Test get_oldest_updates when no child directories exist"""
        # Arrange
        mock_time.return_value = 1234567890
        base_response = {"current_dtg_latest": 1234567890, "dirs": []}
        self.mock_http_client.get.return_value = (200, {"data": base_response})

        # Act
        result = self.rest_processor.get_oldest_updates("/baseline")

        # Assert
        self.assertEqual(result, ["/baseline"])

    @patch('rest_client.rest_processor.time')
    def test_get_oldest_updates_with_dirs(self, mock_time):
        """Test get_oldest_updates with directories"""
        # Arrange
        mock_time.return_value = 1234567890
        base_response = {
            "current_dtg_latest": 1234567890,
            "dirs": ["dir1", "dir2", "dir3"]
        }

        # Mock the get_hashtable call
        self.mock_http_client.get.side_effect = [
            (200, base_response),  # get_hashtable call
            (200, 1234567800),  # get_single_timestamp for dir1
            (200, 1234567850),  # get_single_timestamp for dir2
            (200, 1234567820),  # get_single_timestamp for dir3
        ]

        # Act
        result = self.rest_processor.get_oldest_updates("/baseline", 50)  # 50% = 2 dirs

        # Assert
        # self.assertEqual(len(result), 2)
        self.assertIn("/baseline/dir1", result)  # oldest
        self.assertIn("/baseline/dir3", result)  # second oldest
        self.assertEqual(len(result), 2)


class TestHashInfoValidator(unittest.TestCase):
    def setUp(self):
        # Create a test config
        test_config = {
            'hash_validator_required_keys': {'path', 'target_hash'},
            'hash_validator_keys': {'path', 'target_hash', 'current_hash', 'current_dtg_latest',
                                    'dirs', 'files', 'links', 'session_id'}
        }
        self.config = Config(test_config)
        self.validator = HashInfoValidator()

    def test_valid_hash_info_minimal(self):
        """Test validation with minimal valid data"""
        valid_data = {
            "/test": {
                "path": "/test",
                "current_hash": "hash123"
            }
        }

        errors = self.validator.validate(valid_data)
        self.assertEqual(errors, [])

    def test_valid_hash_info_complete(self):
        """Test validation with complete valid data"""
        valid_data = {
            "/test": {
                "path": "/test",
                "target_hash": "hash123",
                "current_hash": "hash456",
                "dirs": ["dir1", "dir2"],
                "files": ["file1.txt"],
                "links": ["link1"],
                "session_id": "session123"
            }
        }

        errors = self.validator.validate(valid_data)
        self.assertEqual(errors, [])

    def test_missing_required_keys(self):
        """Test validation with missing required keys"""
        invalid_data = {
            "/test": {
                "current_hash": "hash123"
                # Missing 'path' and 'target_hash'
            }
        }

        errors = self.validator.validate(invalid_data)
        self.assertIn("Missing required key 'path' in item '/test'", errors)

    def test_invalid_keys(self):
        """Test validation with invalid keys"""
        invalid_data = {
            "/test": {
                "path": "/test",
                "target_hash": "hash123",
                "invalid_key": "value"
            }
        }

        errors = self.validator.validate(invalid_data)
        self.assertIn("Invalid key 'invalid_key' in item '/test'", errors)

    def test_multiple_items_mixed_validation(self):
        """Test validation with multiple items having mixed validity"""
        mixed_data = {
            "/test1": {
                "path": "/test1",
                "target_hash": "hash123"  # Valid
            },
            "/test2": {
                "target_hash": "hash456"  # Missing 'path'
            },
            "/test3": {
                "path": "/test3",
                "target_hash": "hash789",
                "invalid_key": "value"  # Invalid key
            }
        }

        errors = self.validator.validate(mixed_data)
        self.assertIn("Missing required key 'path' in item '/test2'", errors)
        self.assertIn("Invalid key 'invalid_key' in item '/test3'", errors)
        # Should not have errors for /test1


if __name__ == '__main__':
    unittest.main()