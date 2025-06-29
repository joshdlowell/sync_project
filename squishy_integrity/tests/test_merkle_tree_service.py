import unittest
from unittest.mock import Mock, patch, mock_open
from squishy_integrity.integrity_check.merkle_tree_service import MerkleTreeService
from squishy_integrity.integrity_check.implementations import SHA1HashFunction


class TestMerkleTreeService(unittest.TestCase):
    def setUp(self):
        self.mock_hash_storage = Mock()
        self.mock_tree_walker = Mock()
        self.mock_file_hasher = Mock()
        self.mock_path_validator = Mock()

        self.service = MerkleTreeService(
            self.mock_hash_storage,
            self.mock_tree_walker,
            self.mock_file_hasher,
            self.mock_path_validator
        )

    def test_compute_merkle_tree_invalid_path(self):
        # Arrange
        self.mock_path_validator.validate_root_and_dir_paths.return_value = False

        # Act
        result = self.service.compute_merkle_tree("/root", "/invalid")

        # Assert
        self.assertEqual(result, (None, None))
        self.mock_path_validator.validate_root_and_dir_paths.assert_called_once_with("/root", "/invalid")

    def test_compute_merkle_tree_valid_path(self):
        # Arrange
        self.mock_path_validator.validate_root_and_dir_paths.return_value = True
        self.mock_tree_walker.get_tree_structure.return_value = {
            "/test": {"dirs": [], "files": ["file1.txt"], "links": []}
        }
        self.mock_file_hasher.hash_file.return_value = "file_hash_123"
        self.mock_file_hasher.hash_directory.return_value = "dir_hash_456"
        self.mock_hash_storage.put_hashtable.return_value = {
            'Created': set(), 'Deleted': set(), 'Modified': set()
        }

        # Act
        dir_hash, changes = self.service.compute_merkle_tree("/test", "/test")

        # Assert
        self.assertEqual(dir_hash, "dir_hash_456")
        self.assertIsInstance(changes, dict)
        self.assertIn('Created', changes)
        self.assertIn('Deleted', changes)
        self.assertIn('Modified', changes)

    def test_remove_redundant_paths_no_change(self):
        # Arrange
        priority_list = ['/root/dir1', '/root/dir2']
        routine_list = ['/root/dir3']
        return_value = priority_list + routine_list

        self.assertEqual(self.service.remove_redundant_paths_with_priority(priority_list, routine_list), return_value,
                         "Paths were removed when they shouldn't have been")

    def test_remove_redundant_paths_with_change_1(self):
        # Arrange
        priority_list = ['/root/dir1', '/root/dir2']
        routine_list = ['/root/dir1']

        self.assertEqual(self.service.remove_redundant_paths_with_priority(priority_list, routine_list), priority_list,
                         "Failed to remove routine list entry that should have been")

    def test_remove_redundant_paths_with_change_2(self):
        # Arrange
        priority_list = ['/root/dir1', '/root/dir2/dir3/file.txt', '/root/dir2/dir3', '/root/dir2/dir4']
        routine_list = ['/root/dir1']
        return_list = ['/root/dir1', '/root/dir2/dir3', '/root/dir2/dir4']

        self.assertEqual(self.service.remove_redundant_paths_with_priority(priority_list, routine_list), return_list,
                         "Failed to remove priority list items that share parent")

    def test_remove_redundant_paths_with_change_3(self):
        # Arrange
        priority_list = ['/root/dir1', '/root/dir2/dir3', '/root/dir4/common_dir']
        routine_list = ['/root/dir4/common_dir/file.txt', '/root/dir4/common_dir/dir4/file2.txt',]
        return_list = ['/root/dir1', '/root/dir2/dir3', '/root/dir4/common_dir']

        self.assertEqual(self.service.remove_redundant_paths_with_priority(priority_list, routine_list), return_list,
                         "Failed to remove routine list items that share parent")

    def test_remove_redundant_paths_with_change_root_1(self):
        # Arrange
        priority_list = ['/root', '/root/dir1', '/root/dir2/dir3']
        routine_list = ['/root/dir4/common_dir', '/root/dir4/common_dir/file.txt', '/root/dir4/common_dir/dir4/file2.txt',]
        bad_return_list = ['/root']
        return_list = ['/root/dir1', '/root/dir2/dir3', '/root/dir4/common_dir']

        self.assertNotEqual(self.service.remove_redundant_paths_with_priority(priority_list, routine_list), bad_return_list,
                         "Returned only root path when is shouldn't have")
        self.assertEqual(self.service.remove_redundant_paths_with_priority(priority_list, routine_list), return_list,
                         "Returned Incorrect list contents")

    def test_remove_redundant_paths_with_change_root_2(self):
        # Arrange
        priority_list = []
        routine_list = ['/root']

        self.assertEqual(self.service.remove_redundant_paths_with_priority(priority_list, routine_list),
                         routine_list,
                         "Returned '/root' when it should have")

    def test_remove_redundant_paths_with_change_root_3(self):
        # Arrange
        priority_list = ['/root']
        routine_list = ['/root']

        self.assertEqual(self.service.remove_redundant_paths_with_priority(priority_list, routine_list),
                         routine_list,
                         "Returned '/root' when it should have")

    def test_remove_redundant_paths_no_priority(self):
        # Arrange
        priority_list = []
        routine_list = ['/root/dir1', '/root/dir2']

        self.assertEqual(self.service.remove_redundant_paths_with_priority(priority_list, routine_list), routine_list,
                         "Failed to handle only empty routine list")

    def test_remove_redundant_paths_no_routine(self):
        # Arrange
        priority_list = ['/root/dir1', '/root/dir2']
        routine_list = []

        self.assertEqual(self.service.remove_redundant_paths_with_priority(priority_list, routine_list), priority_list,
                         "Failed to handle only empty routine list")

    def test_remove_redundant_paths_no_lists_1(self):
        # Arrange
        priority_list = []
        routine_list = []
        return_value = []

        self.assertEqual(self.service.remove_redundant_paths_with_priority(priority_list, routine_list), return_value,
                         "Failed to handle empty list inputs")

    def test_remove_redundant_paths_no_lists_2(self):
        # Arrange
        priority_list = None
        routine_list = None
        return_value = []

        self.assertEqual(self.service.remove_redundant_paths_with_priority(priority_list, routine_list), return_value,
                         "Failed to handle 'NoneType' inputs")


class TestFileHasher(unittest.TestCase):
    def setUp(self):
        self.mock_file_system = Mock()
        self.hash_function = SHA1HashFunction()

        from squishy_integrity.integrity_check.file_hasher import FileHasher
        self.file_hasher = FileHasher(
            self.mock_file_system,
            self.hash_function
        )

    def test_hash_file(self):
        # Arrange
        test_content = [b"hello", b"world"]
        self.mock_file_system.read_file_chunks.return_value = iter(test_content)

        # Act
        result = self.file_hasher.hash_file("/test/file.txt")

        # Assert
        expected_hash = self.hash_function.create_hasher()
        for chunk in test_content:
            expected_hash.update(chunk)
        self.assertEqual(result, expected_hash.hexdigest())

    def test_hash_link(self):
        # Arrange
        self.mock_file_system.readlink.return_value = "/target/path"

        # Act
        result = self.file_hasher.hash_link("/test/link")

        # Assert
        expected_input = "/test/link -> /target/path"
        expected_hash = self.hash_function.hash_string(expected_input)
        self.assertEqual(result, expected_hash)


class TestDirectoryTreeWalker(unittest.TestCase):
    def setUp(self):
        self.mock_file_system = Mock()

        from squishy_integrity.integrity_check.tree_walker import DirectoryTreeWalker
        self.walker = DirectoryTreeWalker(self.mock_file_system)

    def test_get_tree_structure(self):
        # Arrange
        mock_walk_result = [
            ("/test", ["subdir"], ["file1.txt", "link1"])
        ]
        self.mock_file_system.walk.return_value = mock_walk_result
        self.mock_file_system.is_file.side_effect = lambda x: "file1.txt" in x

        # Act
        result = self.walker.get_tree_structure("/test")

        # Assert
        expected = {
            "/test": {
                "dirs": ["subdir"],
                "files": ["file1.txt"],
                "links": ["link1"]
            }
        }
        self.assertEqual(result, expected)


class TestPathValidator(unittest.TestCase):
    def setUp(self):
        from squishy_integrity.integrity_check.validators import PathValidator
        self.validator = PathValidator()

    def test_validate_root_and_dir_paths_valid(self):
        # Act & Assert
        self.assertTrue(self.validator.validate_root_and_dir_paths("/root", "/root/subdir"))
        self.assertTrue(self.validator.validate_root_and_dir_paths("/root", "/root"))

    def test_validate_root_and_dir_paths_invalid(self):
        # Act & Assert
        self.assertFalse(self.validator.validate_root_and_dir_paths("/root", "/other"))


# Mock implementations for testing
class MockFileSystem:
    def __init__(self):
        self.files = {}
        self.dirs = set()
        self.links = {}

    def add_file(self, path: str, content: bytes):
        self.files[path] = content

    def add_dir(self, path: str):
        self.dirs.add(path)

    def add_link(self, path: str, target: str):
        self.links[path] = target

    def exists(self, path: str) -> bool:
        return path in self.files or path in self.dirs or path in self.links

    def is_file(self, path: str) -> bool:
        return path in self.files

    def is_dir(self, path: str) -> bool:
        return path in self.dirs

    def read_file_chunks(self, path: str, chunk_size: int = 65536):
        if path in self.files:
            content = self.files[path]
            for i in range(0, len(content), chunk_size):
                yield content[i:i + chunk_size]

    def readlink(self, path: str) -> str:
        return self.links.get(path, "")


class MockHashStorage:
    def __init__(self):
        self.storage = {}

    def put_hashtable(self, hash_info):
        self.storage.update(hash_info)
        return {'Created': set(), 'Deleted': set(), 'Modified': set()}

    def get_hashtable(self, path):
        return self.storage.get(path)

    def get_single_hash(self, path):
        item = self.storage.get(path, {})
        return item.get('current_hash')
