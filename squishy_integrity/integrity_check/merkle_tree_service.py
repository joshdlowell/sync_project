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

    def remove_redundant_paths_with_priority(self, priority: list, routine: list):
        """
        Remove redundant paths from the provided lists while preserving priority order.

        Args:
            priority: list of paths that should be processed first
            routine: list of paths for hash recomputing

        Returns:
            Combined, deduplicated list of paths with priority items first
        """
        # Check and clean args
        priority = priority or []
        routine = routine or []
        # Remove root dir only if there are multiple entries in the lists
        for items in [priority, routine]:
            if len(items) <= 1:
                continue
            # Find the root directory
            root_dir = None
            for item in items:
                root_name = [part for part in item.split('/') if part][0]
                if root_name:
                    potential_root = '/' + root_name
                    if root_dir is None:
                        root_dir = potential_root
                        break
            # Remove root_dir in-place
            while root_dir in items:
                items.remove(root_dir)

        # Deduplicate the priority list first
        priority = self._remove_redundant_paths(priority, 1)
        # Deduplicate and return the combined lists
        combined = priority + routine
        return self._remove_redundant_paths(combined, 1)

    def _remove_redundant_paths(self, items: list, min_depth: int = 1) -> list:
        """
        Returns a list of path strings containing only the deepest common parents
        that are at least as deep as root + 1.

        Args:
            items: List of path strings
            root_depth: Depth of the root path (default 0)

        Returns:
            List of non-redundant path strings
        """
        if not items:
            return []

        # Filter paths to ensure they're at least min_depth deep
        filtered_items = []

        for path in items:
            # Count depth by number of separators (assuming '/' as separator)
            depth = path.count('/') if path.startswith('/') else path.count('/') + 1
            if depth >= min_depth:
                filtered_items.append(path)

        if not filtered_items:
            return []

        # Remove redundant paths - keep only the deepest common parents
        result = []

        for current in filtered_items:
            should_add = True
            items_to_remove = []

            for i, existing in enumerate(result):
                if current.startswith(existing + '/') or current == existing:
                    # Current is child of existing or same - don't add current
                    should_add = False
                    break
                elif existing.startswith(current + '/'):
                    # Existing is child of current - mark existing for removal
                    items_to_remove.append(i)

            if should_add:
                # Remove children that are deeper than current
                for i in reversed(items_to_remove):  # Remove in reverse order to maintain indices
                    result.pop(i)
                result.append(current)

        return result

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
