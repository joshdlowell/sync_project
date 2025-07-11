from typing import Dict, Optional, Any, List
from time import sleep

from .interfaces import HashStorageInterface, MerkleTreeInterface
from .validators import PathValidator
from .tree_walker import DirectoryTreeWalker
from .file_hasher import FileHasher
from .configuration import config, logger


class MerkleTreeService(MerkleTreeInterface):
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

    def compute_merkle_tree(self, dir_path: str) -> Optional[str]:
        """
        Create a Merkle tree hash for a directory and detect changes

        Args:
            dir_path: Directory to hash (must be within root_path)

        Returns:
            Directory hash string, or None if computation fails
        """
        # Validate paths
        root_path = config.get('root_path')
        logger.debug(f"Validating dir_path ({dir_path}) and root_path ({root_path})")
        if not self.path_validator.validate_root_and_dir_paths(root_path, dir_path):
            logger.error(f"dir_path ({dir_path}) is not a child of root_path ({root_path})")
            return None

        # Find the deepest existing directory within the root path
        target_dir = self._find_deepest_existing_directory(root_path, dir_path)
        if target_dir is None:
            logger.error(f"No valid directory path found from root ({root_path}) to target ({dir_path})")
            return None

        # Get tree structure for the target directory
        tree_dict = self.tree_walker.get_tree_structure(target_dir)
        if tree_dict is False:
            logger.error(f"Failed to get tree structure for {target_dir}")
            return None

        # Check if root is empty (only if we ended up at root)
        if self._is_directory_empty(tree_dict, root_path):
            logger.warning(f"Root path ({root_path}) is empty, check that baseline is available and mounted.")
            return None

        # Check if database and API are reachable before starting
        if not self._check_liveness():
            logger.error("Integrity Check unable to contact database or API.")
        logger.info(f"Integrity Check passed all startup checks.")

        # Compute Merkle tree hash
        logger.info(f"Computing Merkle hash for directory: {target_dir}")
        dir_hash = self._compute_merkle_recursive(target_dir, tree_dict)

        # Update parent hashes if we're not at the root
        if root_path != target_dir:
            logger.info("Recomputing parent hashes")
            self._recompute_parent_hashes(root_path, target_dir)

        logger.info(f"Successfully computed Merkle hash for {dir_path}")
        return dir_hash

    def _compute_merkle_recursive(self, dir_path: str, tree_dict: Dict[str, Any]) -> str:
        """Recursively compute Merkle tree hashes"""
        # create list to hold all hashtable entries generated
        hash_info_list = []
        dir_hash_info = {
            'path': dir_path,
            'current_content_hashes': {},
            'session_id': config.session_id
        }
        hash_info_list.append(dir_hash_info)

        # Add current directory structure to hash info
        for category in ['dirs', 'files', 'links']:
            dir_hash_info[category] = tree_dict[dir_path][category]

        # Hash subdirectories recursively
        for item in tree_dict[dir_path]['dirs']:
            item_path = f"{dir_path}/{item}"
            dir_hash_info["current_content_hashes"][item] = self._compute_merkle_recursive(item_path, tree_dict)

        # Hash links
        for item in tree_dict[dir_path]['links']:
            item_path = f"{dir_path}/{item}"
            dir_hash_info["current_content_hashes"][item] = self.file_hasher.hash_link(item_path)
            hash_info_list.append({
                'path': item_path,
                'current_hash': dir_hash_info["current_content_hashes"][item],
                'session_id': config.session_id
            })

        # Hash files
        for item in tree_dict[dir_path]['files']:
            item_path = f"{dir_path}/{item}"
            dir_hash_info["current_content_hashes"][item] = self.file_hasher.hash_file(item_path)
            hash_info_list.append({
                'path': item_path,
                'current_hash': dir_hash_info["current_content_hashes"][item],
                'session_id': config.session_id
            })

        # Get the directory hash (updated in place)
        self._get_directory_hash(dir_hash_info)
        # Update the database with hash information learned in this directory
        self._put_to_hash_database(hash_info_list)
        logger.debug(f"Returning from merkle recursive for {dir_path}")
        return dir_hash_info["current_hash"]

    def put_log_w_session(self, message: str, detailed_message: str=None) -> int:
        return self.hash_storage.put_log(message=message, detailed_message=detailed_message, session_id=config.session_id)

    def _find_deepest_existing_directory(self, root_path: str, dir_path: str) -> Optional[str]:
        """
        Find the deepest existing directory by walking up from dir_path to root_path

        Args:
            root_path: Root directory boundary
            dir_path: Starting directory path

        Returns:
            Path to deepest existing directory, or None if root doesn't exist
        """
        current_path = dir_path

        while True:
            logger.debug(f"Checking if directory exists: {current_path}")
            tree_dict = self.tree_walker.get_tree_structure(current_path)

            if tree_dict is not False:
                logger.debug(f"Found existing directory: {current_path}")
                return current_path

            # If we've reached the root and it doesn't exist, that's an error
            if current_path == root_path:
                logger.error(f"Root path does not exist: {root_path}")
                return None

            # Move up one directory level
            parent_path = current_path.rsplit('/', 1)[0]

            # Prevent infinite loop - if rsplit doesn't change the path, we're at filesystem root
            if parent_path == current_path or parent_path == '':
                logger.error(f"Reached filesystem root without finding valid directory")
                return None

            current_path = parent_path

    def _is_directory_empty(self, tree_dict: Dict[str, Dict[str, List[str]]], dir_path: str) -> bool:
        """
        Check if a directory is empty (no files, dirs, or links)

        Args:
            tree_dict: Tree structure dictionary
            dir_path: Directory path to check

        Returns:
            True if directory is empty, False otherwise
        """
        if dir_path not in tree_dict:
            return True

        dir_contents = tree_dict[dir_path]
        return (len(dir_contents.get('dirs', [])) == 0 and
                len(dir_contents.get('files', [])) == 0 and
                len(dir_contents.get('links', [])) == 0)

    def _check_liveness(self):
        repeats = 5
        while repeats:
            repeats -= 1
            status = self.hash_storage.get_health()
            if not status or not status.get('status') == 'healthy':
                logger.critical(f"REST API is not reachable will attempt {repeats} more times")
            else:
                logger.info("REST API and Database are reachable")
                return True
            sleep(30)
        return False

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
        that are at deeper than given min_depth.

        Args:
            items: List of path strings
            min_depth: Depth of the shallowest path consolidation (default 1)

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

    def _get_directory_hash(self, hash_info: Dict[str, Any]):
        """Update directory hash and track changes"""
        if not hash_info.get('path', None):
            logger.error(f"Failed to get_directory_hash for hash_info with not path key")
            return
        # Compute directory hash
        logger.debug(f"Updating directory hash for {hash_info.get('path', None)}...")
        hash_info['current_hash'] = self.file_hasher.hash_directory(hash_info)

    def _recompute_parent_hashes(self, root_path: str, dir_path: str):
        """Recompute parent directory hashes up to root"""
        current_path = dir_path

        while current_path != root_path:
            # Collect hashes for the current level's parent
            current_path = (current_path.rsplit('/', 1))[0]
            parent_info = self.hash_storage.get_hashtable(current_path)
            if not parent_info:
                logger.error(f"Failed to get parent info from database for path {current_path}")
                return

            # Collect and recompute parent hash information
            dir_hash_info = {'path': current_path, 'current_content_hashes': {}, 'session_id': config.session_id}
            for category in ['dirs', 'files', 'links']:
                items = parent_info.get(category)
                if not items:
                    continue
                dir_hash_info[category] = items
                for item in items:
                    item_path = f"{current_path}/{item}"
                    dir_hash_info['current_content_hashes'][item] = self.hash_storage.get_single_hash(item_path)

            logger.debug(f"Collected existing content hashes for {current_path} recalculation")
            logger.debug(f"Updating directory hash for {dir_hash_info.get('path', None)}...")
            self._get_directory_hash(dir_hash_info)
            self._put_to_hash_database(dir_hash_info)

    def _put_to_hash_database(self, hash_info: List[Dict[str, Any]] | Dict[str, Any]):
        """Put hash info to database"""
        if isinstance(hash_info, dict):
            hash_info = [hash_info]

        for item in hash_info:
            db_entry = {
                item['path']: {
                    'path': item['path'],
                    'session_id': item.get('session_id', None),
                    'current_hash': item['current_hash'],
                    'dirs': item.get('dirs', []),
                    'files': item.get('files', []),
                    'links': item.get('links', [])
                }
            }
            logger.debug(f"Sending hashtable entry for {item['path']}")
            self.hash_storage.put_hashtable(db_entry)