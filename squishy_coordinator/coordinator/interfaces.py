from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional, Any, List


# class FileSystemInterface(ABC):
#     """Abstract interface for file system operations"""
#
#     @abstractmethod
#     def exists(self, path: str) -> bool:
#         pass
#
#     @abstractmethod
#     def is_file(self, path: str) -> bool:
#         pass
#
#     @abstractmethod
#     def is_dir(self, path: str) -> bool:
#         pass
#
#     @abstractmethod
#     def walk(self, path: str) -> List[Tuple[str | None, list[str] | None, list[str] | None]]:
#         pass
#
#     @abstractmethod
#     def read_file_chunks(self, path: str, chunk_size: int = 65536):
#         pass
#
#     @abstractmethod
#     def readlink(self, path: str) -> str:
#         pass
#
#
# class HashStorageInterface(ABC):
#     """Abstract interface for hash storage operations"""
#
#     @abstractmethod
#     def put_hashtable(self, hash_info: Dict[str, Any]) -> int:
#         pass
#
#     @abstractmethod
#     def get_hashtable(self, path: str) -> Optional[Dict[str, Any]]:
#         pass
#
#     @abstractmethod
#     def get_single_hash(self, path: str) -> Optional[str]:
#         pass
#
#     @abstractmethod
#     def get_oldest_updates(self, percent: int = 10) -> list[str]:
#         pass
#
#     @abstractmethod
#     def get_priority_updates(self) -> list[str] | None:
#         pass
#
#     @abstractmethod
#     def get_health(self) -> dict | None:
#         pass
#
#     @abstractmethod
#     def put_log(self, message: str, detailed_message: str=None, log_level: str=None, session_id: str=None) -> int:
#         pass
#
#
#
# class HashFunction(ABC):
#     """Abstract interface for hash operations"""
#
#     @abstractmethod
#     def create_hasher(self):
#         pass
#
#     @abstractmethod
#     def hash_string(self, data: str) -> str:
#         pass
#
# class PersistentStorageInterface(ABC):
#     """Abstract interface for hash storage operations"""
#
#     @abstractmethod
#     def put_hashtable(self, hash_info: Dict[str, Any]) -> int:
#         pass
#
#     @abstractmethod
#     def get_hashtable(self, path: str) -> Optional[Dict[str, Any]]:
#         pass
#
#     @abstractmethod
#     def get_single_hash(self, path: str) -> Optional[str]:
#         pass
#
#     @abstractmethod
#     def get_oldest_updates(self, root_path: str, percent: int = 10) -> list[str]:
#         pass
#
#     @abstractmethod
#     def get_priority_updates(self) -> list[str] | None:
#         pass
#
#     @abstractmethod
#     def get_health(self) -> dict | None:
#         pass
#
#     @abstractmethod
#     def put_log(self,
#                 message: str,
#                 site_id: str=None,
#                 timestamp: int=None,
#                 detailed_message: str=None,
#                 log_level: str=None,
#                 session_id: str=None
#                 ) -> int:
#         pass
#
#     @abstractmethod
#     def find_orphaned_entries(self) -> list[str]:
#         pass
#
#     @abstractmethod
#     def find_untracked_children(self) -> list[str]:
#         pass
#
#     @abstractmethod
#     def get_pipeline_updates(self) -> list[str]:
#         pass
#
#     @abstractmethod
#     def consolidate_logs(self) -> bool:
#         pass
#
#     @abstractmethod
#     def collect_logs_to_ship(self) -> list[dict[str, Any]] | None:
#         pass
#
#     @abstractmethod
#     def delete_log_entries(self, log_ids: list[int]) -> Tuple[bool, list]:
#         pass
#
#     @abstractmethod
#     def collect_logs_older_than(self, days: int) -> list[dict[str, Any]] | None:
#         pass

