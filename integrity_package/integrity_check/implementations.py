import hashlib
# from time import time
from pathlib import Path
from typing import Dict, Set, Any, Optional
from .interfaces import FileSystemInterface, HashStorageInterface, HashFunction  # TimeProvider, HashFunction


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

    def __init__(self, rest_connector):
        self.rest_connector = rest_connector

    def put_hashtable(self, hash_info: Dict[str, Any]) -> Dict[str, Set[str]]:
        return self.rest_connector.put_hashtable(hash_info)

    def get_hashtable(self, path: str) -> Optional[Dict[str, Any]]:
        return self.rest_connector.get_hashtable(path)

    def get_single_hash(self, path: str) -> Optional[str]:
        return self.rest_connector.get_single_hash(path)


# class SystemTimeProvider(TimeProvider):
#     """System time provider implementation"""
#
#     def current_time(self) -> float:
#         return time()


class SHA1HashFunction(HashFunction):
    """SHA-1 hash function implementation"""

    def create_hasher(self):
        return hashlib.sha1()

    def hash_string(self, data: str) -> str:
        return hashlib.sha1(data.encode()).hexdigest()
