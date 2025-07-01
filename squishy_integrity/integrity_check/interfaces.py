from abc import ABC, abstractmethod
from typing import Dict, Set, Tuple, Optional, Any, List


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
    def get_oldest_updates(self, root_path: str, percent: int = 10) -> list[str]:
        pass

    @abstractmethod
    def get_priority_updates(self) -> list[str] | None:
        pass

    @abstractmethod
    def get_lifecheck(self) -> dict | None:
        pass


class HashFunction(ABC):
    """Abstract interface for hash operations"""

    @abstractmethod
    def create_hasher(self):
        pass

    @abstractmethod
    def hash_string(self, data: str) -> str:
        pass
