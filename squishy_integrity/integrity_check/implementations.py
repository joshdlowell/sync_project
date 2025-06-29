import hashlib
from pathlib import Path
from typing import Dict, Set, Any, Optional
from .interfaces import FileSystemInterface, HashStorageInterface, HashFunction


class StandardFileSystem(FileSystemInterface):
    """Standard file system implementation using pathlib"""

    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def is_file(self, path: str) -> bool:
        return Path(path).is_file()

    def is_dir(self, path: str) -> bool:
        return Path(path).is_dir()

    def walk(self, path: str):
        return Path(path).walk()

    def read_file_chunks(self, path: str, chunk_size: int = 65536):
        with open(path, 'rb') as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                yield data

    def readlink(self, path: str) -> str:
        return str(Path(path).readlink())


class RestHashStorage(HashStorageInterface):
    """Hash storage implementation using REST connector"""
    def __init__(self, rest_processor):
        self.rest_processor = rest_processor

    def put_hashtable(self, hash_info: Dict[str, Any]) -> Dict[str, Set[str]]:
        return self.rest_processor.put_hashtable(hash_info)

    def get_hashtable(self, path: str) -> Optional[Dict[str, Any]]:
        return self.rest_processor.get_hashtable(path)

    def get_single_hash(self, path: str) -> Optional[str]:
        return self.rest_processor.get_single_hash(path)

    def get_oldest_updates(self, root_path: str, percent: int = 10) -> list[str]:
        return self.rest_processor.get_oldest_updates(root_path, percent)

    def get_priority_updates(self) -> list[str] | None:
        return self.rest_processor.get_priority_updates()


class SHA1HashFunction(HashFunction):
    """SHA-1 hash function implementation"""

    def create_hasher(self):
        return hashlib.sha1()

    def hash_string(self, data: str) -> str:
        return hashlib.sha1(data.encode()).hexdigest()
