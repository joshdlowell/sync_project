import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from squishy_integrity import logger
from .interfaces import FileSystemInterface, HashFunction, PersistentStorageInterface


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


class RestStorage(PersistentStorageInterface):
    """Hash storage implementation using REST connector"""
    def __init__(self, rest_processor):
        self.rest_processor = rest_processor

    def put_hashtable(self, hash_info: Dict[str, Any]) -> int:
        return self.rest_processor.put_hashtable(hash_info)

    def get_hashtable(self, path: str) -> Optional[Dict[str, Any]]:
        return self.rest_processor.get_hashtable(path)

    def get_single_hash(self, path: str) -> Optional[str]:
        return self.rest_processor.get_single_hash(path)

    def get_oldest_updates(self, root_path: str, percent: int = 10) -> list[str]:
        return self.rest_processor.get_oldest_updates(root_path, percent)

    def get_priority_updates(self) -> list[str] | None:
        return self.rest_processor.get_priority_updates()

    def get_lifecheck(self) -> dict | None:
        return self.rest_processor.get_lifecheck()

    def put_log(self,
                message: str,
                site_id: str=None,
                timestamp: int=None,
                detailed_message: str=None,
                log_level: str=None,
                session_id: str=None
                ) -> int:
        return self.rest_processor.put_log(message, site_id, timestamp, detailed_message, log_level, session_id)

    def find_orphaned_entries(self) -> list[str]:
        return self.rest_processor.find_orphaned_entries()

    def find_untracked_children(self) -> list[str]:
        return self.rest_processor.find_untracked_children()

    def get_pipeline_updates(self) -> list[str]:
        return self.rest_processor.get_pipeline_updates()

    def consolidate_logs(self) -> bool:
        return self.rest_processor.consolidate_logs()

    def collect_logs_to_ship(self) -> list[dict[str, Any]] | None:
        return self.rest_processor.collect_logs_to_ship()

    def delete_log_entries(self, log_ids: list[int]) -> Tuple[bool, list]:
        return self.rest_processor.delete_log_entries(log_ids)

    def collect_logs_older_than(self, days: int) -> list[dict[str, Any]] | None:
        return self.rest_processor.collect_logs_older_than(days)


class SHA1HashFunction(HashFunction):
    """SHA-1 hash function implementation"""

    def create_hasher(self):
        return hashlib.sha1()

    def hash_string(self, data: str) -> str:
        return hashlib.sha1(data.encode()).hexdigest()
