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
        logger.error(f"Validating dir_path ({dir_path}) and root_path ({root_path})")
        if not self.path_validator.validate_root_and_dir_paths(root_path, dir_path):
            logger.error(f"Not a child of the given root_path ({root_path})")
            return None, None

        # TODO push change handling to rest
        # Initialize change tracking
        changes = {'Created': set(), 'Deleted': set(), 'Modified': set()}
        # Get directory tree structure
        # TODO add circuit breaker for empty baseline
        tree_dict = self.tree_walker.get_tree_structure(dir_path)

        # Compute Merkle tree hash
        dir_hash = self._compute_merkle_recursive(dir_path, changes, tree_dict)

        # Update parent hashes if necessary
        logger.debug("Starting to recompute parent hashes")
        if root_path != dir_path:
            self._recompute_parent_hashes(root_path, dir_path)

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
        logger.debug("Combined and deduplicated paths lists")
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

        # Hash links
        for item in tree_dict[dir_path]['links']:
            item_path = f"{dir_path}/{item}"
            hash_info[item_path]["current_hash"] = self.file_hasher.hash_link(item_path)

        # Hash files
        for item in tree_dict[dir_path]['files']:
            item_path = f"{dir_path}/{item}"
            hash_info[item_path]["current_hash"] = self.file_hasher.hash_file(item_path)

        # Hash the directory itself and update changes
        self._update_directory_hash(hash_info, dir_path, changes)
        logger.debug(f"Returning from merkle recursive for {dir_path}")
        return hash_info[dir_path]["current_hash"]

    def _update_directory_hash(self, hash_info: Dict[str, Any], dir_path: str, changes: Dict[str, Set[str]]):
        """Update directory hash and track changes"""
        # Compute directory hash
        logger.debug(f"Updating directory hash for {dir_path}...")
        hash_info[dir_path]['current_hash'] = self.file_hasher.hash_directory(dir_path, hash_info)

        # TODO push changes management to rest
        # Store hash info and get changes
        detected_changes = self.hash_storage.put_hashtable(hash_info)
        logger.debug(f"Info sent to hash storage for {dir_path}")
        # Merge changes
        for category in changes.keys():
            changes[category].update(detected_changes[category])

    def _recompute_parent_hashes(self, root_path: str, dir_path: str):
        """Recompute parent directory hashes up to root"""
        current_path = dir_path

        while current_path != root_path:
            # Collect hashes for the current level's parent
            current_path = (current_path.rsplit('/', 1))[0]
            parent_info = self.hash_storage.get_hashtable(current_path)

            # Collect parent hash information
            hash_string = ''
            for category in ['dirs', 'files', 'links']:
                items = parent_info.get(category, [])
                if items:
                    for item in sorted(items):
                        item_path = f"{current_path}/{item}"
                        hash_string += self.hash_storage.get_single_hash(item_path)
                else:
                    hash_string += f"{current_path}/{category}: EMPTY "
            dir_hash = self.file_hasher.hash_string(hash_string)
            new_parent_info = {
                current_path: {
                    'path': current_path,
                    'current_hash': dir_hash,
                    'dirs': parent_info['dirs'],
                    'files': parent_info['files'],
                    'links': parent_info['links']
                }
            }
            logger.debug(f"Collected parent hashes for {dir_path}")
            self.hash_storage.put_hashtable(new_parent_info)

        logger.debug(f"Updated hashtable with parent hashes for {dir_path}")
