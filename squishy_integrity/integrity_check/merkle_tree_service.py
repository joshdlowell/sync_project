from typing import Dict, Set, Tuple, Optional, Any
from .interfaces import HashStorageInterface
from .validators import PathValidator
from .tree_walker import DirectoryTreeWalker
from .file_hasher import FileHasher

from squishy_integrity import logger


class MerkleTreeService:
    """Main service for Merkle tree integrity checking"""

    def __init__(self,
                 hash_storage: HashStorageInterface,
                 tree_walker: DirectoryTreeWalker,
                 file_hasher: FileHasher,
                 path_validator: PathValidator):
        self.hash_storage = hash_storage
        self.tree_walker = tree_walker
        self.file_hasher = file_hasher
        self.path_validator = path_validator

    def compute_merkle_tree(self, root_path: str, dir_path: str) -> Tuple[Optional[str], Optional[Dict[str, Set[str]]]]:
        """
        Create a Merkle tree hash for a directory and detect changes

        Args:
            root_path: Root directory of the monitored tree
            dir_path: Directory to hash (must be within root_path)

        Returns:
            Tuple of (directory_hash, changes_dict) or (None, None) if invalid
        """
        # Validate paths
        if not self.path_validator.validate_root_and_dir_paths(root_path, dir_path):
            # print(f"ERROR: Requested path is not a child of the given root_path")
            logger.error(f"Requested path ({dir_path}) is not a child of the given root_path ({root_path})")
            return None, None

        # Initialize change tracking
        changes = {'Created': set(), 'Deleted': set(), 'Modified': set()}

        # Get directory tree structure
        tree_dict = self.tree_walker.get_tree_structure(dir_path)

        # Compute Merkle tree hash
        dir_hash = self._compute_merkle_recursive(dir_path, changes, tree_dict)

        # Update parent hashes if necessary
        if root_path != dir_path:
            self._recompute_parent_hashes(root_path, dir_path, changes)

        return dir_hash, changes

    def remove_redundant_paths_with_priority(self, priority, routine):
        """Simplified version with better performance"""

        # Combine and deduplicate while preserving priority order
        seen = set()
        combined = []

        for path in priority + routine:
            if path not in seen:
                combined.append(path)
                seen.add(path)

        # Remove redundant children
        result = []
        # import os
        for current in combined:
            # current_norm = os.path.normpath(current)
            is_redundant = False

            for existing in result:
                # existing_norm = os.path.normpath(existing)
                # If current is child of existing, it's redundant
                # if current_norm.startswith(existing_norm + os.sep):
                if current.startswith(existing):
                    is_redundant = True
                    break
                # If existing is child of current, remove existing and add current
                # elif existing_norm.startswith(current_norm + os.sep):
                elif existing.startswith(current):

                    result.remove(existing)
                    break

            if not is_redundant:
                result.append(current)

        return result

    def _compute_merkle_recursive(self, dir_path: str, changes: Dict[str, Set[str]], tree_dict: Dict[str, Any]) -> str:
        """Recursively compute Merkle tree hashes"""
        # Initialize hash info for this directory
        hash_info = {dir_path: {}}

        # Add directory structure to hash info
        for category in ['dirs', 'files', 'links']:
            hash_info[dir_path][category] = tree_dict[dir_path][category]

            # Initialize hash info for each item
            for item in tree_dict[dir_path][category]:
                item_path = f"{dir_path}/{item}"
                hash_info[item_path] = {}

        # Hash subdirectories recursively
        for item in tree_dict[dir_path]['dirs']:
            item_path = f"{dir_path}/{item}"
            hash_info[item_path]["current_hash"] = self._compute_merkle_recursive(item_path, changes, tree_dict)
            # hash_info[item_path]["current_dtg_latest"] = self.file_hasher.get_current_timestamp()

        # Hash links
        for item in tree_dict[dir_path]['links']:
            item_path = f"{dir_path}/{item}"
            hash_info[item_path]["current_hash"] = self.file_hasher.hash_link(item_path)
            # hash_info[item_path]["current_dtg_latest"] = self.file_hasher.get_current_timestamp()

        # Hash files
        for item in tree_dict[dir_path]['files']:
            item_path = f"{dir_path}/{item}"
            hash_info[item_path]["current_hash"] = self.file_hasher.hash_file(item_path)
            # hash_info[item_path]["current_dtg_latest"] = self.file_hasher.get_current_timestamp()

        # Hash the directory itself and update changes
        self._update_directory_hash(hash_info, dir_path, changes)

        return hash_info[dir_path]["current_hash"]

    def _update_directory_hash(self, hash_info: Dict[str, Any], dir_path: str, changes: Dict[str, Set[str]]):
        """Update directory hash and track changes"""
        # Compute directory hash
        hash_info[dir_path]['current_hash'] = self.file_hasher.hash_directory(dir_path, hash_info)
        # hash_info[dir_path]['current_dtg_latest'] = self.file_hasher.get_current_timestamp()

        # Store hash info and get changes
        detected_changes = self.hash_storage.put_hashtable(hash_info)

        # Merge changes
        for category in changes.keys():
            changes[category].update(detected_changes[category])

    def _recompute_parent_hashes(self, root_path: str, dir_path: str, changes: Dict[str, Set[str]]):
        """Recompute parent directory hashes up to root"""
        current_path = dir_path

        while current_path != root_path:
            # Move to parent directory
            current_path = current_path.rsplit('/', 1)[0]

            # Get existing hash info for parent
            parent_info = self.hash_storage.get_hashtable(current_path)
            if not parent_info:
                continue

            # Build hash info for parent
            hash_info = {current_path: parent_info}

            # Get hashes for all children
            for category in ['dirs', 'files', 'links']:
                for item in parent_info[category]:
                    item_hash = self.hash_storage.get_single_hash(item)
                    if item_hash:
                        hash_info[item] = {'current_hash': item_hash}

            # Update parent hash
            self._update_directory_hash(hash_info, current_path, changes)
