import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from .configuration import config, logger
from .interfaces import FileSystemInterface, HashStorageInterface, HashFunction


class StandardFileSystem(FileSystemInterface):
    """Standard file system implementation using pathlib"""

    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def is_file(self, path: str) -> bool:
        return Path(path).is_file()

    def is_dir(self, path: str) -> bool:
        return Path(path).is_dir()

    def walk(self, path: str) -> List[Tuple[str | None, list[str] | None, list[str] | None]]:
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                raise OSError(f"Path does not exist: {path}")

            # Convert generator to list
            return list(path_obj.walk())
        except OSError as e:
            logger.error(f"Failed to walk path {path}: {e}")
            return [(None, None, None)]

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

    def put_hashtable(self, hash_info: Dict[str, Any]) -> int:
        return self.rest_processor.put_hashtable(hash_info)

    def get_hashtable(self, path: str) -> Optional[Dict[str, Any]]:
        return self.rest_processor.get_hashtable(path)

    def get_single_hash(self, path: str) -> Optional[str]:
        return self.rest_processor.get_single_hash(path)

    def get_oldest_updates(self, percent: int = 10) -> list[str]:
        return self.rest_processor.get_oldest_updates(config.get('root_path'), percent)

    def get_priority_updates(self) -> list[str] | None:
        return self.rest_processor.get_priority_updates()

    def get_health(self) -> dict | None:
        return self.rest_processor.get_health()

    def put_log(self, message: str, detailed_message: str=None, log_level: str=None, session_id: str=None) -> int:
        return self.rest_processor.put_log(message=message, detailed_message=detailed_message, log_level=log_level, session_id=session_id)


class SHA1HashFunction(HashFunction):
    """SHA-1 hash function implementation"""

    def create_hasher(self):
        return hashlib.sha1()

    def hash_string(self, data: str) -> str:
        return hashlib.sha1(data.encode()).hexdigest()
