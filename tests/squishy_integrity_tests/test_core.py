import unittest
from unittest.mock import Mock, patch, MagicMock
from time import time
from squishy_integrity.core import (
    get_paths_to_process,
    process_paths,
    main,
    performance_monitor
)


class TestCore(unittest.TestCase):
    def setUp(self):
        self.mock_merkle_service = Mock()
        self.mock_hash_storage = Mock()
        self.mock_merkle_service.hash_storage = self.mock_hash_storage

    def test_get_paths_to_process(self):
        """Test get_paths_to_process function."""
        # Arrange
        priority_paths = ['/priority1', '/priority2']
        routine_paths = ['/routine1', '/routine2']
        deduplicated_paths = ['/priority1', '/priority2', '/routine1']

        self.mock_hash_storage.get_priority_updates.return_value = priority_paths
        self.mock_hash_storage.get_oldest_updates.return_value = routine_paths
        self.mock_merkle_service.remove_redundant_paths_with_priority.return_value = deduplicated_paths

        # Act
        result = get_paths_to_process(self.mock_merkle_service)

        # Assert
        self.assertEqual(result, deduplicated_paths)
        self.mock_hash_storage.get_priority_updates.assert_called_once()
        self.mock_hash_storage.get_oldest_updates.assert_called_once()
        self.mock_merkle_service.remove_redundant_paths_with_priority.assert_called_once_with(
            priority_paths, routine_paths
        )

    def test_process_paths_all_successful(self):
        """Test process_paths with all paths processed successfully."""
        # Arrange
        paths = ['/path1', '/path2', '/path3']
        max_runtime_min = 10

        # Act
        processed_count, total_count = process_paths(
            self.mock_merkle_service, paths, max_runtime_min
        )

        # Assert
        self.assertEqual(processed_count, 3)
        self.assertEqual(total_count, 3)
        self.assertEqual(self.mock_merkle_service.compute_merkle_tree.call_count, 3)

    def test_process_paths_with_exception(self):
        """Test process_paths with one path failing."""
        # Arrange
        paths = ['/path1', '/path2', '/path3']
        max_runtime_min = 10

        # Make second path fail
        self.mock_merkle_service.compute_merkle_tree.side_effect = [
            None,  # Success
            Exception("Test error"),  # Failure
            None  # Success
        ]

        # Act
        processed_count, total_count = process_paths(
            self.mock_merkle_service, paths, max_runtime_min
        )

        # Assert
        self.assertEqual(processed_count, 2)  # Only 2 successful
        self.assertEqual(total_count, 3)
        self.assertEqual(self.mock_merkle_service.compute_merkle_tree.call_count, 3)

    @patch('squishy_integrity.core.time')
    def test_process_paths_time_limit_reached(self, mock_time):
        """Test process_paths with time limit reached."""
        # Arrange
        paths = ['/path1', '/path2', '/path3']
        max_runtime_min = 1

        # Mock time to simulate time limit reached after first path
        mock_time.side_effect = [
            1000,  # Initial time
            1000,  # First check (within limit)
            1100  # Second check (over limit)
        ]

        # Act
        processed_count, total_count = process_paths(
            self.mock_merkle_service, paths, max_runtime_min
        )

        # Assert
        self.assertEqual(processed_count, 1)  # Only first path processed
        self.assertEqual(total_count, 3)
        self.assertEqual(self.mock_merkle_service.compute_merkle_tree.call_count, 1)

    def test_performance_monitor_context_manager(self):
        """Test performance_monitor context manager."""
        # Arrange
        operation_name = "Test Operation"

        # Act & Assert
        with performance_monitor(self.mock_merkle_service, operation_name):
            pass  # Simulate work

        # Verify logging calls
        self.assertEqual(self.mock_merkle_service.put_log_w_session.call_count, 2)
        calls = self.mock_merkle_service.put_log_w_session.call_args_list

        # Check start log
        self.assertEqual(calls[0][1]['message'], "START SESSION")
        self.assertEqual(calls[0][1]['detailed_message'], "Starting Merkle compute")

        # Check finish log
        self.assertEqual(calls[1][1]['message'], "FINISH SESSION")
        self.assertEqual(calls[1][1]['detailed_message'], "Completed Merkle compute")

    def test_performance_monitor_with_exception(self):
        """Test performance_monitor context manager with exception."""
        # Arrange
        operation_name = "Test Operation"

        # Act & Assert
        with self.assertRaises(ValueError):
            with performance_monitor(self.mock_merkle_service, operation_name):
                raise ValueError("Test error")

        # Verify finish log is still called
        self.assertEqual(self.mock_merkle_service.put_log_w_session.call_count, 2)

    @patch('squishy_integrity.core.IntegrityCheckFactory')
    @patch('squishy_integrity.core.config')
    def test_main_successful(self, mock_config, mock_factory):
        """Test main function successful execution."""
        # Arrange
        mock_config.get.return_value = 5
        mock_service = Mock()
        mock_service.hash_storage.get_priority_updates.return_value = []
        mock_service.hash_storage.get_oldest_updates.return_value = ['/test']
        mock_service.remove_redundant_paths_with_priority.return_value = ['/test']
        mock_factory.create_service.return_value = mock_service

        # Act
        result = main()

        # Assert
        self.assertEqual(result, 0)
        mock_factory.create_service.assert_called_once_with(None)
        mock_service.compute_merkle_tree.assert_called_once_with('/test')

    # @patch('squishy_integrity.core.IntegrityCheckFactory')
    # @patch('squishy_integrity.core.config')
    # def test_main_with_exception(self, mock_config, mock_factory):
    #     """Test main function with exception."""
    #     # Arrange
    #     mock_config.get.return_value = 5
    #     mock_factory.create_service.side_effect = Exception("Test error")
    #
    #     # Act
    #     result = main()
    #
    #     # Assert
    #     self.assertEqual(result, 1)

    @patch('squishy_integrity.core.get_paths_to_process')
    @patch('squishy_integrity.core.IntegrityCheckFactory')
    @patch('squishy_integrity.core.config')
    def test_main_no_paths_to_process(self, mock_config, mock_factory, mock_get_paths):
        """Test main function with no paths to process."""
        # Arrange
        mock_config.get.return_value = 5
        mock_service = Mock()
        mock_factory.create_service.return_value = mock_service
        mock_get_paths.return_value = []

        # Act
        result = main()

        # Assert
        self.assertEqual(result, 0)
        mock_service.compute_merkle_tree.assert_not_called()