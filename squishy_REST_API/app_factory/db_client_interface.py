from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional, Any, List


class DBInstanceInterface(ABC):
    """Abstract interface for hash storage operations"""
    # RemoteDBConnection interface methods
    @abstractmethod
    def get_hash_record(self, path: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def insert_or_update_hash(self, record: dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def get_single_hash_record(self, path: str) -> str | None:
        pass

    @abstractmethod
    def get_single_timestamp(self, path: str) -> int | None:
        pass

    @abstractmethod
    def get_priority_updates(self) -> List[str]:
        pass

    @abstractmethod
    def put_log(self, args_dict: dict) -> int | None:
        pass

    @abstractmethod
    def get_logs(self, limit: Optional[int] = None, offset: int = 0,
                 order_by: str = "timestamp", order_direction: str = "DESC",
                 session_id_filter: Optional[str] = None,
                 older_than_days: Optional[int] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def consolidate_logs(self) -> bool:
        pass

    @abstractmethod
    def delete_log_entries(self, log_ids: list[int]) -> tuple[list, list]:
        pass

    @abstractmethod
    def find_orphaned_entries(self) -> list[str]:
        pass

    @abstractmethod
    def find_untracked_children(self) -> list[Any]:
        pass

    @abstractmethod
    def health_check(self) -> dict[str, bool]:
        pass

    @abstractmethod
    def put_remote_hash_status(self, update_list: list[dict[str, str]],
                               site_name: str,
                               drop_existing: bool = False,
                               root_path: str = None
                               ) -> list[str]:
        pass

    ########## CoreDBConnection interface methods
    @abstractmethod
    def get_dashboard_content(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def get_recent_logs(self) -> list:
        pass

    @abstractmethod
    def get_hash_record_count(self) -> int:
        pass

    @abstractmethod
    def get_log_count_last_24h(self, log_level: str='INFO') -> int:
        pass

    @abstractmethod
    def get_site_liveness(self) -> list:
        pass

    @abstractmethod
    def get_site_sync_status(self) -> list:
        pass

    @abstractmethod
    def sync_sites_from_mssql_upsert(self, mssql_sites: List[Dict[str, Any]]) -> bool:
        pass

    # PipelineDBConnection interface methods
    @abstractmethod
    def get_pipeline_updates(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def put_pipeline_hash(self, update_path: str, hash_value: str) -> bool:
        pass

    @abstractmethod
    def get_pipeline_sites(self) -> List[str]:
        pass

    # @abstractmethod
    # def put_pipeline_site_completion(self, site: str) -> bool:
    #     pass


