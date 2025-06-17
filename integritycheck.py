#!/bin/python3
import hashlib
# import subprocess
from time import time
# from os import path, walk, stat
from pathlib import Path
import dbapi


def DFS_merkle (root_path: str, dir_path: str):
    """
    Base case function for creating a Merkle tree structured hash of content and structure on baseline
    takes a path which is used as the root directory for hashing. When this hashing is complete the parent
    tree nodes are updated to reflect the new hash of dir_path, but no other files are rehashed.
    Returns the new hash values of dir_path, baseline root (which may be the same value if dir_path
    is baseline) and, hash values changed above dir_path in the tree.
    """
    # Validate starting point
    if not dir_path in root_path:
        print(f"ERROR: Requested path is not a child of the given root_path")
        return None, None

    # Dict object to hold changes and tree object to examine
    changes = {'Created': set(), 'Deleted': set(), 'Modified': set()}
    tree_dict = _get_walk(dir_path)
    dir_path_hash = _DFS_merkle(dir_path, changes, tree_dict)
    # Update the parent node(s) hash values based on the new local_root_hash
    if root_path != dir_path:
        recompute_root(root_path, dir_path, changes)

    return dir_path_hash, changes


def _DFS_merkle (dir_path, change_dict, tree_dict):
    """
    Recursive function for creating a Merkle tree structured hash of content and structure on baseline
    takes dir_path which is used as the root directory for hashing, tree_dict which is a dictionary of
    'dirs', 'files', and 'links' where the root node is dir_path and,
    merkle_files_path which is the
    location that the hash file information should be stored.
    Updates the files at merkle_files_path and Returns the new hash values of dir path.
    """
    hash_info = {dir_path: {}}
    # Abstracted so that hash function used is defined in only one place
    hash_func = get_hash_func()

    # Add list of dirs, links, and files to the hash entry
    for key in ['dirs', 'files', 'links']:
        hash_info[dir_path][key] = tree_dict[dir_path][key]
        for item in tree_dict[dir_path][key]:
            hash_info[f"{dir_path}/{item}"] = {}

    # Recursively hash child directory contents
    for item in tree_dict[dir_path]['dirs']:
        hash_info[f"{dir_path}/{item}"]["current_hash"] = _DFS_merkle(f"{dir_path}/{item}", change_dict, tree_dict)
        hash_info[f"{dir_path}/{item}"]["current_dtg_latest"] = str(time())

    # Create hashes of symlinks and hardlinks
    for item in tree_dict[dir_path]['links']:
        hash_info[f"{dir_path}/{item}"]["current_hash"] = perform_hash(get_link_hashable(f"{dir_path}/{item}"))
        hash_info[f"{dir_path}/{item}"]["current_dtg_latest"] = str(time())

    # Create hashes of actual files in this directory
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
def recompute_root(root_path, dir_path, change_dict):
    """
    ་Takes a path. Uses the given information to recalculate hashes in the tree from that point
    to the root

    :param root_path:
    :param change_dict:
    :param dir_path:
    :return:
    """
    # This loop will produce the changed root hash
    while dir_path != root_path:
        # Get parent dir and the children of that dir
        dir_path = dir_path.rsplit('/', 1)[0]
        hash_info = {dir_path: {}}
        response = dbapi.get_hashtable(dir_path)

        # Build dict of hashes to derive dir_path's hash
        for key in ['dirs', 'files', 'links']:
            hash_info[dir_path][key] = {key: response[key]}
            for item in response[key]:
                hash_info[item]['current_hash'] = dbapi.get_single_hash(item)

        # Calculate the hash for the current directory node based on contents and update changes
        _update_self_hash(hash_info, dir_path, change_dict)


def _get_walk(parent_path) -> dict[str, dict[str, list]]:
    """
    Takes a 'root node' and returns a dictionary with every child directory as keys and a
    dict as the value containing the 'dirs', 'files' and, 'links' contained in that directory
    :param parent_path:
    :return:
    """
    tree_dict = {}
    files = Path.walk(Path(parent_path))
    # Iterate over the list of directories and contents for item in files:
    for item in files:
        dir_path, item_dirs, item_files = item  # walk returns a 3-tuple for each dir
        # Re-sort the values from walk since links aren't separated
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


def _update_self_hash(hash_info, dir_path, change_dict):
    hash_info[dir_path]['current_hash'] = perform_hash(get_dir_hashable(dir_path, hash_info))
    hash_info[dir_path]['current_dtg_latest'] = str(time())

    # Update the database and identify any changes
    changes = dbapi.put_hashtable(hash_info)

    # Add changes we're interested in to provided change_dict
    for key in change_dict.keys():
        change_dict[key].update(changes[key])


def get_link_hashable(link_path) -> str:
    """
    Returns a string containing link attributes that will uniquely identify 'link_path' for data integrity purposes.
    """
    return f"{link_path} -> {str(Path(link_path).readlink())}"


def get_dir_hashable(dir_path, hash_info) -> str:
    hash_string = ''
    for lists in ['dirs', 'files', 'links']:
        if hash_info[dir_path].get(lists):
            for item in sorted(hash_info[dir_path][lists]):
                hash_string += hash_info[f"{dir_path}/{item}"]['current_hash']
        else:
            hash_string += f"{dir_path}/{lists}: EMPTY "
    return hash_string


def get_hash_func(): return hashlib.sha1


def perform_hash(hash_string: str) -> str:
    return get_hash_func()(hash_string.encode()).hexdigest()
