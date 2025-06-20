"""
Merkle Tree File Integrity System

This module implements a Merkle tree-based file system integrity checker that creates
cryptographic hashes of directory structures and their contents. It provides functionality
to detect changes (created, modified, or deleted files) by comparing current file states
against previously stored hash values.

Key Features:
- Recursive directory traversal with Merkle tree hash generation
- Support for regular files, directories, and symbolic/hard links
- Change detection and tracking (Created/Modified/Deleted files)
- Integration with REST API for hash storage and retrieval
- Efficient partial tree updates when only subdirectories change

Main Functions:
- DFS_merkle(): Entry point for hashing a directory tree and detecting changes
- recompute_root(): Updates parent directory hashes after child changes

Dependencies:
- rest_connector: Custom module for hash storage/retrieval via REST API
- hashlib: For SHA-1 cryptographic hashing
- pathlib: For cross-platform path operations

Usage:
    dir_hash, changes = DFS_merkle('/path/to/root', '/path/to/subdir')

Author: Jdlowel
Created: 06/01/2024
Last Modified: 06/18/2025
"""
import hashlib
from time import time
from pathlib import Path
import rest_connector


def DFS_merkle (root_path: str, dir_path: str) -> tuple[str, dict] | tuple[None, None]:
    """
    Create a Merkle tree hash for a directory and detect file system changes.

    This function serves as the entry point for hashing a directory tree structure.
    It computes cryptographic hashes for all files, directories, and links within
    dir_path, then updates parent directory hashes up to root_path if necessary.

    Args:
        root_path (str): The absolute path to the root directory of the monitored
                        file system tree. Used as the boundary for hash updates.
        dir_path (str): The absolute path to the directory to hash. Must be a
                       subdirectory of or equal to root_path.

    Returns:
        tuple[str, dict] or tuple[None, None]: A tuple containing:
            - dir_path_hash (str): The computed Merkle hash of dir_path
            - changes (dict): Dictionary with keys 'Created', 'Deleted', 'Modified',
                             each containing a set of file paths that changed
            Returns (None, None) if dir_path is not within root_path.

    Raises:
        FileNotFoundError: If dir_path does not exist
        PermissionError: If insufficient permissions to read files/directories

    Example:
        >>> hash_val, changes = DFS_merkle('/home/user/docs', '/home/user/docs/project')
        >>> print(f"Hash: {hash_val}")
        >>> print(f"Modified files: {changes['Modified']}")
    """
    # Validate starting point
    if not dir_path in root_path:
        print(f"ERROR: Requested path is not a child of the given root_path")
        return None, None

    # Dict object to hold changes and tree object containing items to examine
    changes = {'Created': set(), 'Deleted': set(), 'Modified': set()}
    tree_dict = _get_walk(dir_path)
    dir_path_hash = _DFS_merkle(dir_path, changes, tree_dict)
    # Update the parent(s) node hash values based on the new dir_path_hash
    if root_path != dir_path:
        recompute_root(root_path, dir_path, changes)

    return dir_path_hash, changes


def _DFS_merkle (dir_path: str, change_dict: dict, tree_dict: dict) -> str:
    """
    Recursively compute Merkle tree hashes for a directory structure.

    This is the core recursive function that performs depth-first traversal
    of the directory tree, computing hashes for files, links, and subdirectories.
    It builds a complete hash information structure and updates the change
    tracking dictionary.

    Args:
        dir_path (str): The absolute path to the current directory being processed
        change_dict (dict): Dictionary tracking changes with keys 'Created',
                           'Deleted', 'Modified'. Modified in-place during execution.
        tree_dict (dict): Nested dictionary representing the directory structure
                         where keys are directory paths and values contain 'dirs',
                         'files', and 'links' lists for that directory.

    Returns:
        str: The computed Merkle hash for dir_path, incorporating hashes of all
             contained files, directories, and links.

    Note:
        This function modifies change_dict in-place and interacts with the
        REST API via rest_connector to store hash information and detect changes.

        Hash computation order:
        1. Recursively hash subdirectories
        2. Hash symbolic/hard links by their target paths
        3. Hash file contents in 64KB chunks
        4. Combine all hashes to create directory hash

    Side Effects:
        - Updates hash database via REST API calls
        - Modifies change_dict to track detected changes
        - Reads file contents for hash computation
    """
    # Create dict to hold values at this level of the directory tree
    hash_info = {dir_path: {}}
    # Abstracted so that hash function used is defined in only one place
    hash_func = get_hash_func()

    # Add list of dirs, links, and files to the hash entry
    for key in ['dirs', 'files', 'links']:
        hash_info[dir_path][key] = tree_dict[dir_path][key]
        # Create empty dict for each child object listed
        for item in tree_dict[dir_path][key]:
            hash_info[f"{dir_path}/{item}"] = {}

    # Recursively hash child directory contents
    for item in tree_dict[dir_path]['dirs']:
        hash_info[f"{dir_path}/{item}"]["current_hash"] = _DFS_merkle(f"{dir_path}/{item}", change_dict, tree_dict)
        hash_info[f"{dir_path}/{item}"]["current_dtg_latest"] = str(time())

    # Create hashes of symlinks in this directory
    for item in tree_dict[dir_path]['links']:
        hash_info[f"{dir_path}/{item}"]["current_hash"] = perform_hash(get_link_hashable(f"{dir_path}/{item}"))
        hash_info[f"{dir_path}/{item}"]["current_dtg_latest"] = str(time())

    # Create hashes of files in this directory
    for item in tree_dict[dir_path]['files']:
        file_hash = hash_func()
        with open(f"{dir_path}/{item}", 'rb') as f:
            while True:
                data = f.read(65536) # Read in 64kB chunks
                if not data:
                    break
                file_hash.update(data)
        hash_info[f"{dir_path}/{item}"]["current_hash"] = file_hash.hexdigest()
        hash_info[f"{dir_path}/{item}"]["current_dtg_latest"] = str(time())

    # Finally, create hash for the current directory and update changes
    _update_self_hash(hash_info, dir_path, change_dict)

    return hash_info[dir_path]["current_hash"]


# Helper functions
def recompute_root(root_path: str, dir_path: str, change_dict: dict) -> None:
    """
    Recomputes hash values from a changed directory up to the root of the tree.

    When a subdirectory's hash changes, all parent directories up to the root must have
    their hashes recalculated to maintain the integrity of the Merkle tree structure.
    This function traverses upward from the changed directory to the root, updating
    each parent directory's hash based on its current children's hash values.

    Args:
        root_path (str): The absolute path to the root directory of the Merkle tree.
                        This defines the stopping point for hash recalculation.
        dir_path (str): The absolute path to the directory that was changed and needs
                       its parent chain updated. Must be a subdirectory of root_path.
        change_dict (dict): Dictionary tracking changes with keys 'Created', 'Deleted',
                           and 'Modified', each containing a set of affected file paths.
                           Updated in-place as parent directories are processed.

    Returns:
        None: Function modifies change_dict in-place and updates hash storage via
              REST API calls. The root directory's hash will be updated upon completion.

    Raises:
        Implicit exceptions may be raised by:
        - rest_connector.get_hashtable() if hash retrieval fails
        - rest_connector.get_single_hash() if individual hash retrieval fails
        - Path operations if directories don't exist or are inaccessible

    Note:
        This function assumes that dir_path's hash has already been updated and uses
        the REST connector to retrieve existing hash information for parent directories.
        The function works by walking up the directory tree one level at a time until
        it reaches root_path.

    Example:
        If a file in '/root/subdir1/subdir2' changes:
        1. subdir2's hash is updated by the caller
        2. recompute_root('/root', '/root/subdir1/subdir2', changes)
        3. Function updates subdir1's hash, then root's hash
    """
    # This loop will produce the changed root hash
    while dir_path != root_path:
        # Get parent dir and the children of that dir
        dir_path = dir_path.rsplit('/', 1)[0]
        hash_info = {dir_path: {}}
        response = rest_connector.get_hashtable(dir_path)

        # Build dict of hashes to derive dir_path's hash
        for key in ['dirs', 'files', 'links']:
            hash_info[dir_path][key] = {key: response[key]}
            for item in response[key]:
                hash_info[item]['current_hash'] = rest_connector.get_single_hash(item)

        # Calculate the hash for the current directory node based on contents and update changes
        _update_self_hash(hash_info, dir_path, change_dict)


def _get_walk(parent_path: str) -> dict[str, dict[str, list]]:
    """
    Recursively traverse a directory tree and categorize all contained items.

    Walks through all subdirectories starting from parent_path and creates a comprehensive
    mapping of the directory structure. Each directory is catalogued with its contained
    subdirectories, regular files, and symbolic/hard links as separate lists.

    Args:
        parent_path (str): Root directory path to begin traversal from

    Returns:
        dict[str, dict[str, list]]: Nested dictionary where:
            - Outer keys: Full directory paths (str)
            - Inner keys: 'dirs', 'files', 'links' (str)
            - Values: Sorted lists of item names within each category

    Example:
        >>> tree = _get_walk('/home/user/docs')
        >>> tree['/home/user/docs']
        {
            'dirs': ['images', 'reports'],
            'files': ['readme.txt', 'config.json'],
            'links': ['shortcut.lnk']
        }

    Note:
        - All lists are sorted alphabetically for consistent ordering
        - Links include both symbolic links and hard links
        - Directory paths are converted to strings for dictionary keys
        - Uses pathlib.Path.walk() for cross-platform compatibility
    """
    tree_dict = {}

    # Get and iterate over the lists of directories and contents:
    files = Path.walk(Path(parent_path))
    for item in files:
        dir_path, item_dirs, item_files = item  # walk returns a 3-tuple for each dir
        # Re-sort the values from walk since links aren't separated from files
        clean_files, clean_links = [], []
        for i in item_files:
            if (dir_path / i).is_file():
                clean_files.append(i)
            else:
                clean_links.append(i)
        tree_dict[str(dir_path)] = {"dirs": sorted([str(item) for item in item_dirs]),
                               "files": sorted(clean_files),
                               "links": sorted(clean_links)}
    return tree_dict


def _update_self_hash(hash_info: dict, dir_path: str, change_dict: dict) -> None:
    """
    Calculate and update the hash for a directory, then persist changes and track modifications.

    This function computes the Merkle hash for the specified directory based on the hashes
    of its contents (files, subdirectories, and links), updates the hash information with
    a timestamp, persists the data via REST API, and accumulates any detected changes.

    Args:
        hash_info (dict): Dictionary containing hash information for the directory and its
                         contents. Structure: {path: {'current_hash': str, 'current_dtg_latest': str}}
        dir_path (str): Absolute path to the directory being hashed
        change_dict (dict): Dictionary to accumulate changes across the tree traversal.
                           Expected keys: 'Created', 'Deleted', 'Modified' with set values

    Side Effects:
        - Modifies hash_info in-place by adding current_hash and current_dtg_latest for dir_path
        - Updates change_dict in-place with any changes detected during persistence
        - Makes REST API call to persist hash information to external storage

    Note:
        This is a helper function for the DFS Merkle tree implementation and should not
        be called directly from outside the merkle tree generation process.
    """
    # Update the dir_path's hash and current_dtg
    hash_info[dir_path]['current_hash'] = perform_hash(get_dir_hashable(dir_path, hash_info))
    hash_info[dir_path]['current_dtg_latest'] = str(time())

    # Update the database and identify any changes
    changes = rest_connector.put_hashtable(hash_info)

    # Add changes we're interested in to provided change_dict
    for key in change_dict.keys():
        change_dict[key].update(changes[key])


def get_link_hashable(link_path: str) -> str:
    """
    Generate a hashable string representation of a symbolic link.

    Creates a string that uniquely identifies the link by combining the link path
    with its target destination. This ensures that changes to either the link name
    or its target will be detected during integrity checking.

    Args:
        link_path (str): Full path to the symbolic or hard link

    Returns:
        str: Formatted string in the format "link_path -> target_path"

    Raises:
        OSError: If the link path doesn't exist or cannot be read

    Example:
        >>> get_link_hashable("/home/user/mylink")
        "/home/user/mylink -> /home/user/documents/file.txt"

    Note:
        Uses pathlib.Path.readlink() to resolve the link target, which works
        for both symbolic and hard links on supported filesystems.
    """
    return f"{link_path} -> {str(Path(link_path).readlink())}"


def get_dir_hashable(dir_path, hash_info) -> str:
    """
    Generate a hashable string representation of a directory's contents for Merkle tree construction.

    This function creates a deterministic string by concatenating the hashes of all items
    (subdirectories, files, and links) contained within the specified directory. The resulting
    string is used to compute the directory's own hash value in the Merkle tree structure.

    Args:
        dir_path (str): The absolute path to the directory being processed.
        hash_info (dict): A nested dictionary containing hash information for the directory
                         and its contents. Expected structure:
                         {
                             dir_path: {
                                 'dirs': [list of subdirectory names],
                                 'files': [list of file names],
                                 'links': [list of link names]
                             },
                             'dir_path/item_name': {
                                 'current_hash': 'hash_value'
                             }
                         }

    Returns:
        str: A concatenated string of all child item hashes, sorted alphabetically by
             category (dirs, files, links) and then by item name within each category.
             Empty categories are represented with a placeholder string.

    Note:
        The function processes items in a fixed order (dirs, files, links) to ensure
        deterministic hash generation. Items within each category are processed in
        sorted order for consistency.

    Example:
        >>> hash_info = {
        ...     '/home/user': {'dirs': ['subdir'], 'files': ['file.txt'], 'links': []},
        ...     '/home/user/subdir': {'current_hash': 'abc123'},
        ...     '/home/user/file.txt': {'current_hash': 'def456'}
        ... }
        >>> get_dir_hashable('/home/user', hash_info)
        'abc123def456/home/user/links: EMPTY '
    """
    hash_string = ''
    for lists in ['dirs', 'files', 'links']:
        if hash_info[dir_path].get(lists):
            for item in sorted(hash_info[dir_path][lists]):
                hash_string += hash_info[f"{dir_path}/{item}"]['current_hash']
        else:
            hash_string += f"{dir_path}/{lists}: EMPTY "
    return hash_string


def get_hash_func():
    """
    Returns the hash function used throughout the module. Not intended
    to be cryptographically secure, only to "fingerprint" the filestructure

    Returns:
        hashlib hash function: SHA-1 hash function from hashlib
    """
    return hashlib.sha1


def perform_hash(hash_string: str) -> str:
    """
    Generate a hash of the input string using the configured hash function.

    Args:
        hash_string: The string to be hashed

    Returns:
        The hexadecimal representation of the SHA-1 hash
    """
    return get_hash_func()(hash_string.encode()).hexdigest()
