from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional, Any, List


class FileSystemInterface(ABC):
    """Abstract interface for file system operations"""

    @abstractmethod
    def exists(self, path: str) -> bool:
        pass

    @abstractmethod
    def is_file(self, path: str) -> bool:
        pass

    @abstractmethod
    def is_dir(self, path: str) -> bool:
        pass

    @abstractmethod
    def walk(self, path: str) -> List[Tuple[str | None, list[str] | None, list[str] | None]]:
        pass

    @abstractmethod
    def read_file_chunks(self, path: str, chunk_size: int = 65536):
        pass

    @abstractmethod
    def readlink(self, path: str) -> str:
        pass

    @abstractmethod
    def is_link(self, path: str) -> bool:
        """Check if path is a symbolic link"""
        pass

    @abstractmethod
    def is_readable_file(self, path: str) -> bool:
        """Check if path is a readable regular file"""
        pass

    @abstractmethod
    def get_file_metadata(self, path: str) -> Dict[str, Any]:
        """Get file metadata including type, mode, size, etc."""
        pass


class HashStorageInterface(ABC):
    """Abstract interface for hash storage operations"""

    @abstractmethod
    def put_hashtable(self, hash_info: Dict[str, Any]) -> int:
        pass

    @abstractmethod
    def get_hashtable(self, path: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_single_hash(self, path: str) -> Optional[str]:
        pass

    @abstractmethod
    def get_oldest_updates(self, percent: int = 10) -> list[str]:
        pass

    @abstractmethod
    def get_priority_updates(self) -> list[str] | None:
        pass

    @abstractmethod
    def get_health(self) -> dict | None:
        pass

    @abstractmethod
    def put_log(self, message: str, detailed_message: str=None, log_level: str=None, session_id: str=None) -> int:
        pass


class HashFunction(ABC):
    """Abstract interface for hash operations"""

    @abstractmethod
    def create_hasher(self):
        pass

    @abstractmethod
    def hash_string(self, data: str) -> str:
        pass

class MerkleTreeInterface(ABC):
    """Abstract interface for Merkle tree integrity checking"""

    @abstractmethod
    def compute_merkle_tree(self, dir_path: str) -> Optional[str]:
        """
        Create a Merkle tree hash for a directory and detect changes

        Args:
            dir_path: Directory to hash (must be within root_path)

        Returns:
            Directory hash string, or None if computation fails
        """
        pass

    @abstractmethod
    def put_log_w_session(self, message: str, detailed_message: str=None, log_level: str=None) -> int:
        """
        Send a log entry to the local database via REST API.
        Leverages the integrity service to add the current session_id to the log entry

        Args:
            message: The log entry summary_message
            detailed_message: The log entry detailed_message (optional)
            log_level: The log entry log_level (optional: default if None)

        Returns:
            int representing the number of updates sent to the REST API that were successful
        """
        pass

    @abstractmethod
    def remove_redundant_paths_with_priority(self, priority: list, routine: list):
        """
        Remove redundant paths from the provided lists while preserving priority order.

        Args:
            priority: list of paths that should be processed first
            routine: list of paths for hash recomputing

        Returns:
            Combined, deduplicated list of paths with priority items first
        """
        pass