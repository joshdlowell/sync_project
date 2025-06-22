"""
Merkle Tree File Integrity System

Refactored for improved testability and maintainability.
"""

from .factory import IntegrityCheckFactory
from squishy_integrity.rest_connector import rest_connector

# Create the service instance
_service = IntegrityCheckFactory.create_service(rest_connector)


def DFS_merkle(root_path: str, dir_path: str):
    """
    Entry point for computing Merkle tree hash and detecting changes

    This function maintains backward compatibility with the original API
    while using the new refactored implementation.
    """
    return _service.compute_merkle_tree(root_path, dir_path)


# def recompute_root(root_path: str, dir_path: str, change_dict: dict):
#     """
#     Legacy function for recomputing parent hashes
#
#     Note: This functionality is now handled automatically by compute_merkle_tree
#     """
#     # This is now handled internally by the service
#     pass


# Legacy hash function exports for backward compatibility
def get_hash_func():
    """Returns SHA-1 hash function"""
    import hashlib
    return hashlib.sha1


def perform_hash(hash_string: str) -> str:
    """Generate SHA-1 hash of input string"""
    import hashlib
    return hashlib.sha1(hash_string.encode()).hexdigest()


def get_link_hashable(link_path: str) -> str:
    """Generate hashable representation of a link"""
    from pathlib import Path
    return f"{link_path} -> {str(Path(link_path).readlink())}"


def get_dir_hashable(dir_path: str, hash_info: dict) -> str:
    """Generate hashable representation of directory contents"""
    hash_string = ''
    for category in ['dirs', 'files', 'links']:
        items = hash_info[dir_path].get(category, [])
        if items:
            for item in sorted(items):
                item_path = f"{dir_path}/{item}"
                hash_string += hash_info[item_path]['current_hash']
        else:
            hash_string += f"{dir_path}/{category}: EMPTY "
    return hash_string
