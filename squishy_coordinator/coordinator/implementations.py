from typing import Dict, Any, Optional, Tuple, List

# from squishy_integrity import logger
from squishy_coordinator import config
from rest_client.rest_interface import RestProcessorInterface
from integrity_check.interfaces import MerkleTreeInterface


class RestClientStorage(RestProcessorInterface):
    """
    RestProcessorInterface interface implementation for interactions
    with the REST API.
    """
    def __init__(self, rest_storage):
        self.rest_client = rest_storage

    def put_hashtable(self, hash_info: dict) -> int:
        return self.rest_client.put_hashtable(hash_info)

    def get_hashtable(self, path: str) -> dict | None:
        return self.rest_client.get_hashtable(path)

    def get_single_hash(self, path: str) -> str | None:
        return self.rest_client.get_single_hash(path)

    def get_oldest_updates(self, root_path: str, percent: int = 10) -> list[str]:
        return self.rest_client.get_oldest_updates(root_path, percent)

    def get_single_timestamp(self, path: str) -> float | None:
        """ Not implemented in coordinator """
        pass

    def get_priority_updates(self) -> list | None:
        return self.rest_client.get_priority_updates()

    def get_health(self) -> dict | None:
        return self.rest_client.get_health()

    def put_log(self,
                message: str,
                site_id: str=None,
                timestamp: int=None,
                detailed_message: str=None,
                log_level: str=None,
                session_id: str=None
                ) -> int:
        return self.rest_client.put_log(message, site_id, timestamp, detailed_message, log_level, session_id)

    def find_orphaned_entries(self) -> list | None:
        return self.rest_client.find_orphaned_entries()

    def find_untracked_children(self) -> list | None:
        return self.rest_client.find_untracked_children()

    def get_pipeline_updates(self):
        pipeline_updates = self.rest_client.get_pipeline_updates()
        for entry in pipeline_updates:
            entry['path'] = f"{config.get('root_path')}{entry['update_path']}" if entry.get('update_path', None) else ''
        return pipeline_updates

    def consolidate_logs(self) -> bool | None:
        return self.rest_client.consolidate_logs()

    def collect_logs_for_shipping(self) -> list[dict[str, Any]] | None:
        return self.rest_client.collect_logs_for_shipping()

    def collect_logs_older_than(self, days: int) -> list[dict[str, Any]] | None:
        return self.rest_client.collect_logs_older_than(days)

    def delete_log_entries(self, log_ids: list[int]) -> Tuple[int, list]:
        return self.rest_client.delete_log_entries(log_ids)

    def get_site_liveness(self) -> list:
        """ Not implemented in coordinator """
        pass

    def get_site_sync_status(self) -> list:
        """ Not implemented in coordinator """
        pass

    def get_official_sites(self) -> list[str]:
        """ Not implemented in coordinator """
        pass

    def put_remote_hash_status(self, status_updates: list[dict[str, str]], site_name: str, root_path: str=None) -> bool:
        return self.rest_client.put_remote_hash_status(status_updates, site_name, root_path)


class MerkleTreeImplementation(MerkleTreeInterface):
    """
    MerkleTreeInterface Interface implementation for Merkle
    tree-based integrity checking
    """
    def __init__(self, merkle_service: MerkleTreeInterface):
        self.merkle_service = merkle_service

    def compute_merkle_tree(self, dir_path: str) -> Optional[str]:
        return self.merkle_service.compute_merkle_tree(dir_path)

    def put_log_w_session(self, message: str, detailed_message: str=None, log_level: str=None) -> int:
        return self.merkle_service.put_log_w_session(message=message, detailed_message=detailed_message, log_level=log_level)

    def remove_redundant_paths_with_priority(self, priority: list, routine: list):
        return self.merkle_service.remove_redundant_paths_with_priority(priority, routine)
