from typing import Dict, List

from .interfaces import FileSystemInterface
from .configuration import logger

class DirectoryTreeWalker:
    """Handles directory tree traversal and categorization"""

    def __init__(self, file_system: FileSystemInterface):
        self.file_system = file_system

    def get_tree_structure(self, parent_path: str) -> Dict[str, Dict[str, List[str]]] | bool:
        """
        Recursively traverse directory tree and categorize items

        Args:
            parent_path: Root directory path to begin traversal

        Returns:
            Dictionary mapping directory paths to their contents, or False if parent_path doesn't exist
        """
        walk_results = self.file_system.walk(parent_path)

        # Early check for failed walk
        if not walk_results or walk_results[0] == (None, None, None):
            logger.warning(f"Parent path does not exist or is inaccessible: {parent_path}")
            return False

        tree_dict = {}
        for dir_path, item_dirs, item_files in walk_results:
            # Separate files from links
            clean_files, clean_links = self._categorize_files(dir_path, item_files)

            tree_dict[str(dir_path)] = {
                "dirs": sorted([str(item) for item in item_dirs]),
                "files": sorted(clean_files),
                "links": sorted(clean_links)
            }
        logger.debug("Cleaned and sorted files lists from get_tree_structure")
        logger.debug("Collected local baseline file tree")
        return tree_dict

    def _categorize_files(self, dir_path, item_files):
        """Separate regular files from links"""
        clean_files, clean_links = [], []

        for item in item_files:
            full_path = f"{str(dir_path)}/{item}"
            if self.file_system.is_file(full_path):
                clean_files.append(item)
            else:
                clean_links.append(item)
        return clean_files, clean_links
