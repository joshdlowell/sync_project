from typing import Optional, Dict, Any, List

from .db_interfaces import RemoteDBConnection, CoreDBConnection, PipelineDBConnection


class DBInstance(RemoteDBConnection, CoreDBConnection, PipelineDBConnection):
    def __init__(self,
                 remote_db: Optional[RemoteDBConnection] = None,
                 core_db: Optional[CoreDBConnection] = None,
                 pipeline_db: Optional[PipelineDBConnection] = None):
        self.remote_db = remote_db
        self.core_db = core_db
        self.pipeline_db = pipeline_db

    # RemoteDBConnection interface methods
    def get_hash_record(self, path: str) -> Optional[Dict[str, Any]]:
        if not self.remote_db:
            raise NotImplementedError("RemoteDBConnection implementation not provided")
        return self.remote_db.get_hash_record(path)

    def insert_or_update_hash(self, record: dict[str, Any]) -> bool:
        if not self.remote_db:
            raise NotImplementedError("RemoteDBConnection implementation not provided")
        return self.remote_db.insert_or_update_hash(record)

    def get_single_field(self, path: str, field: str) -> str | int | None:
        if not self.remote_db:
            raise NotImplementedError("RemoteDBConnection implementation not provided")
        return self.remote_db.get_single_field(path, field)

    def get_priority_updates(self) -> List[str]:
        if not self.remote_db:
            raise NotImplementedError("RemoteDBConnection implementation not provided")
        return self.remote_db.get_priority_updates()

    def put_log(self, args_dict: dict) -> int | None:
        if not self.remote_db:
            raise NotImplementedError("RemoteDBConnection implementation not provided")
        return self.remote_db.put_log(args_dict)

    def get_logs(self, limit: Optional[int] = None, offset: int = 0,
                 order_by: str = "timestamp", order_direction: str = "DESC",
                 session_id_filter: Optional[str] = None,
                 older_than_days: Optional[int] = None) -> List[Dict[str, Any]]:
        if not self.remote_db:
            raise NotImplementedError("RemoteDBConnection implementation not provided")
        return self.remote_db.get_logs(limit=limit,
                                       offset=offset,
                                       order_by=order_by,
                                       order_direction=order_direction,
                                       session_id_filter=session_id_filter,
                                       older_than_days=older_than_days
                                       )

    def delete_log_entries(self, log_ids: list[int]) -> tuple[int, list]:
        if not self.remote_db:
            raise NotImplementedError("RemoteDBConnection implementation not provided")
        return self.remote_db.delete_log_entries(log_ids)

    def consolidate_logs(self) -> bool:
        """
        Consolidate log entries by session ID, grouping and deduplicating JSON-encoded detailed messages.

        Returns:
            bool: True if consolidation was successful, False otherwise
        """
        if not self.remote_db:
            raise NotImplementedError("RemoteDBConnection implementation not provided")
        return self.remote_db.consolidate_logs()

    def health_check(self) -> dict[str, bool]:
        if not self.remote_db:
            raise NotImplementedError("RemoteDBConnection implementation not provided")
        return self.remote_db.health_check()

    def find_orphaned_entries(self) -> list[str]:
        if not self.remote_db:
            raise NotImplementedError("RemoteDBConnection implementation not provided")
        return self.remote_db.find_orphaned_entries()

    def find_untracked_children(self) -> list[Any]:
        if not self.remote_db:
            raise NotImplementedError("RemoteDBConnection implementation not provided")
        return self.remote_db.find_untracked_children()

    # CoreDBConnection interface methods
    def get_dashboard_content(self) -> dict[str, Any]:
        if not self.core_db:
            raise NotImplementedError("CoreDBConnection implementation not provided")
        return self.core_db.get_dashboard_content()

    def get_recent_logs(self, log_level: str = None, site_id: str = None) -> list:
        if not self.core_db:
            raise NotImplementedError("CoreDBConnection implementation not provided")
        return self.core_db.get_recent_logs(log_level, site_id)

    def get_hash_record_count(self) -> int:
        if not self.core_db:
            raise NotImplementedError("CoreDBConnection implementation not provided")
        return self.core_db.get_hash_record_count()

    def get_log_count_last_24h(self, log_level: str) -> int:
        if not self.core_db:
            raise NotImplementedError("CoreDBConnection implementation not provided")
        return self.core_db.get_log_count_last_24h(log_level)

    def get_site_liveness(self) -> list:
        if not self.core_db:
            raise NotImplementedError("CoreDBConnection implementation not provided")
        return self.core_db.get_site_liveness()

    def get_site_sync_status(self) -> list:
        if not self.core_db:
            raise NotImplementedError("CoreDBConnection implementation not provided")
        return self.core_db.get_site_sync_status()

    def put_remote_hash_status(self, update_list: list[dict[str, str]],
                               site_name: str,
                               drop_existing: bool = False,
                               root_path: str = None
                               ) -> list[str]:
        if not self.core_db:
            raise NotImplementedError("CoreDBConnection implementation not provided")
        return self.core_db.put_remote_hash_status(update_list, site_name, drop_existing, root_path)

    def sync_sites_from_mssql_upsert(self, mssql_sites: List[Dict[str, Any]]) -> bool:
        if not self.core_db:
            raise NotImplementedError("CoreDBConnection implementation not provided")
        return self.core_db.sync_sites_from_mssql_upsert(mssql_sites)

    # PipelineDBConnection interface methods
    def get_pipeline_updates(self) -> List[Dict[str, Any]]:
        if not self.pipeline_db:
            raise NotImplementedError("PipelineDBConnection implementation not provided")
        return self.pipeline_db.get_pipeline_updates()

    def put_pipeline_hash(self, update_path: str, hash_value: str) -> bool:
        if not self.pipeline_db:
            raise NotImplementedError("PipelineDBConnection implementation not provided")
        return self.pipeline_db.put_pipeline_hash(update_path, hash_value)

    def get_official_sites(self) -> List[Dict[str, Any]]:
        if not self.pipeline_db:
            raise NotImplementedError("PipelineDBConnection implementation not provided")
        return self.pipeline_db.get_official_sites()

    # def put_pipeline_site_completion(self, site: str) -> bool:
    #     if not self.pipeline_db:
    #         raise NotImplementedError("PipelineDBConnection implementation not provided")
    #     return self.pipeline_db.put_pipeline_site_completion(site)

    def pipeline_health_check(self) -> Dict[str, bool] | None:
        if not self.pipeline_db:
            return None
        return self.pipeline_db.pipeline_health_check()
