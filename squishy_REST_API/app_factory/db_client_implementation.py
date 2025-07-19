from typing import Dict, Tuple, Optional, Any, List
from datetime import datetime

# from .db_client_interface import DBClientInterface, CoreDBClientInterface, DBInstanceInterface
from .db_client_interface import DBInstanceInterface
from squishy_REST_API import config


# class RemoteDBStorage(DBClientInterface):
#     """Hash storage implementation using REST connector"""
#     def __init__(self, local_db_instance):
#         self.local_db_instance = local_db_instance
#
#     def get_hash_record(self, path: str) -> Dict[str, Any] | None:
#         return self.local_db_instance.get_hash_record(path)
#
#     def insert_or_update_hash(self, record: Dict[str, Any]) -> bool:
#         return self.local_db_instance.insert_or_update_hash(record)
#
#     def get_single_hash_record(self, path: str) -> str | None:
#         field_data = self.local_db_instance.get_single_field(path, 'current_hash')
#         if isinstance(field_data, str):
#             return field_data
#         else:
#             return None
#
#     def get_single_timestamp(self, path: str) -> int | None:
#         field_data = self.local_db_instance.get_single_field(path, 'current_dtg_latest')
#         if isinstance(field_data, int):
#             return field_data
#         else:
#             return None
#
#     def get_priority_updates(self) -> List[str]:
#         return self.local_db_instance.get_priority_updates()
#
#     def put_log(self, args_dict: dict) -> int:
#         return self.local_db_instance.put_log(args_dict)
#
#     def get_logs(self, limit: Optional[int] = None, offset: int = 0,
#                  order_by: str = "timestamp", order_direction: str = "DESC",
#                  session_id_filter: Optional[str] = None,
#                  older_than_days: Optional[int] = None) -> List[Dict[str, Any]]:
#         return self.local_db_instance.get_logs(limit, offset, order_by,
#                                                order_direction, session_id_filter,
#                                                older_than_days)
#
#     def consolidate_logs(self) -> bool:
#         return self.local_db_instance.consolidate_logs()
#
#     def delete_log_entries(self, log_ids: list[int]) -> tuple[list, list]:
#         return self.local_db_instance.delete_log_entries(log_ids)
#
#     def find_orphaned_entries(self) -> list[str]:
#         return self.local_db_instance.find_orphaned_entries()
#
#     def find_untracked_children(self) -> list[Any]:
#         return self.local_db_instance.find_untracked_children()
#
#     def heath_check(self) -> dict:
#         return self.local_db_instance.health_check()
#
#
# class CoreDBStorage(DBClientInterface, CoreDBClientInterface):
#     """Hash storage implementation using REST connector"""
#     def __init__(self, local_db_instance, pipeline_db_instance):
#         self.local_db_instance = local_db_instance
#         self.pipeline_db_instance = pipeline_db_instance
#
#     # Remote client implementations
#     def get_hash_record(self, path: str) -> Dict[str, Any] | None:
#         return self.local_db_instance.get_hash_record(path)
#
#     def insert_or_update_hash(self, record: Dict[str, Any]) -> bool:
#         return self.local_db_instance.insert_or_update_hash(record)
#
#     def get_single_hash_record(self, path: str) -> str | None:
#         field_data = self.local_db_instance.get_single_field(path, 'current_hash')
#         if isinstance(field_data, str):
#             return field_data
#         else:
#             return None
#
#     def get_single_timestamp(self, path: str) -> int | None:
#         field_data = self.local_db_instance.get_single_field(path, 'current_dtg_latest')
#         if isinstance(field_data, int):
#             return field_data
#         else:
#             return None
#
#     def get_priority_updates(self) -> List[str]:
#         return self.local_db_instance.get_priority_updates()
#
#     def put_log(self, args_dict: dict) -> int:
#         return self.local_db_instance.put_log(args_dict)
#
#     def get_logs(self, limit: Optional[int] = None, offset: int = 0,
#                  order_by: str = "timestamp", order_direction: str = "DESC",
#                  session_id_filter: Optional[str] = None,
#                  older_than_days: Optional[int] = None) -> List[Dict[str, Any]]:
#         return self.local_db_instance.get_logs(limit, offset, order_by,
#                                                order_direction, session_id_filter,
#                                                older_than_days)
#
#     def consolidate_logs(self) -> bool:
#         return self.local_db_instance.consolidate_logs()
#
#     def delete_log_entries(self, log_ids: list[int]) -> tuple[list, list]:
#         return self.local_db_instance.delete_log_entries(log_ids)
#
#     def find_orphaned_entries(self) -> list[str]:
#         return self.local_db_instance.find_orphaned_entries()
#
#     def find_untracked_children(self) -> list[Any]:
#         return self.local_db_instance.find_untracked_children()
#
#     def heath_check(self) -> dict:
#         return self.local_db_instance.health_check()
#
#     # Remote client core site only implementations
#     def put_remote_site_status(self) -> bool:
#         return self.local_db_instance.put_remote_site_status()
#
#     # Core client core site only implementations
#     def get_pipeline_updates(self) -> List[Dict[str, Any]]:
#         """Get TeamCity updates that haven't been processed yet."""
#         return self.pipeline_db_instance.get_pipeline_updates()
#
#     def put_pipeline_hash(self, update_path: str, hash_value: str) -> bool:
#         """Put calculated hash back into the database for a specific update path."""
#         return self.pipeline_db_instance.put_pipeline_hash(update_path, hash_value)
#
#     def get_pipeline_sites(self) -> List[str]:
#         """Get the current authoritative sites list from the MSSQL table."""
#         return self.pipeline_db_instance.get_official_sites()
#
#     def put_pipeline_site_completion(self, site: str) -> bool:
#         return self.pipeline_db_instance.put_pipeline_site_completion


class DBInstance(DBInstanceInterface):
    """Hash storage implementation using REST connector"""
    def __init__(self, local_db_instance):
        self.local_db_instance = local_db_instance

    def get_hash_record(self, path: str) -> Dict[str, Any] | None:
        return self.local_db_instance.get_hash_record(path)

    def insert_or_update_hash(self, record: Dict[str, Any]) -> bool:
        return self.local_db_instance.insert_or_update_hash(record)

    def get_single_hash_record(self, path: str) -> str | None:
        field_data = self.local_db_instance.get_single_field(path, 'current_hash')
        if isinstance(field_data, str):
            return field_data
        else:
            return None

    def get_single_timestamp(self, path: str) -> datetime | None:
        field_data = self.local_db_instance.get_single_field(path, 'current_dtg_latest')
        if isinstance(field_data, datetime):
            return field_data
        else:
            return None

    def get_priority_updates(self) -> List[str]:
        return self.local_db_instance.get_priority_updates()

    def put_log(self, args_dict: dict) -> int:
        site_id = args_dict.get('site_id')
        if not site_id or 'local' == site_id:
            args_dict['site_id'] = config.site_name
        return self.local_db_instance.put_log(args_dict)

    def get_logs(self, limit: Optional[int] = None, offset: int = 0,
                 order_by: str = "timestamp", order_direction: str = "DESC",
                 session_id_filter: Optional[str] = None,
                 older_than_days: Optional[int] = None) -> List[Dict[str, Any]]:
        return self.local_db_instance.get_logs(limit, offset, order_by,
                                               order_direction, session_id_filter,
                                               older_than_days)

    def consolidate_logs(self) -> bool:
        return self.local_db_instance.consolidate_logs()

    def delete_log_entries(self, log_ids: list[int]) -> tuple[list, list]:
        return self.local_db_instance.delete_log_entries(log_ids)

    def find_orphaned_entries(self) -> list[str]:
        return self.local_db_instance.find_orphaned_entries()

    def find_untracked_children(self) -> list[Any]:
        return self.local_db_instance.find_untracked_children()

    def health_check(self) -> dict[str, bool]:
        return self.local_db_instance.health_check()

    def put_remote_site_status(self) -> bool:
        return self.local_db_instance.put_remote_site_status()

    ########## Core client core site only implementations
    def get_dashboard_content(self) -> dict[str, Any]:
        return self.local_db_instance.get_dashboard_content()

    def get_recent_logs(self, log_level: str = None, site_id: str = None) -> list:
        return self.local_db_instance.get_recent_logs(log_level, site_id)

    def get_hash_record_count(self) -> int:
        return self.local_db_instance.get_hash_record_count()

    def get_log_count_last_24h(self, log_level: str='INFO') -> int:
        return self.local_db_instance.get_log_count_last_24h(log_level)

    def get_site_liveness(self) -> list:
        return self.local_db_instance.get_site_liveness()

    def get_site_sync_status(self) -> list:
        return self.local_db_instance.get_site_sync_status()

    ########## Pipeline client core site only implementations
    def get_pipeline_updates(self) -> List[Dict[str, Any]]:
        """Get TeamCity updates that haven't been processed yet."""
        return self.local_db_instance.get_pipeline_updates()

    def put_pipeline_hash(self, update_path: str, hash_value: str) -> bool:
        """Put calculated hash back into the database for a specific update path."""
        return self.local_db_instance.put_pipeline_hash(update_path, hash_value)

    def get_pipeline_sites(self) -> List[str]:
        """Get the current authoritative sites list from the MSSQL table."""
        return self.local_db_instance.get_official_sites()

    def put_pipeline_site_completion(self, site: str) -> bool:
        return self.local_db_instance.put_pipeline_site_completion()
