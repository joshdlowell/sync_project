from typing import Dict, List

from .interfaces import FileSystemInterface
from .configuration import config


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
            config.logger.warning(f"Parent path does not exist or is inaccessible: {parent_path}")
            return False

        tree_dict = {}
        for dir_path, item_dirs, item_files in walk_results:
            # Categorize all items found in item_files
            categorized = self._categorize_files(dir_path, item_files)

            tree_dict[str(dir_path)] = {
                "dirs": sorted([str(item) for item in item_dirs]),
                "files": sorted(categorized["files"]),
                "links": sorted(categorized["links"]),
                "special": sorted(categorized["special"])
            }
        config.logger.debug("Collected and sorted local baseline file tree")
        return tree_dict

    def _categorize_files(self, dir_path, item_files):
        """Categorize items into files, links, and special files"""
        categorized = {
            "files": [],
            "links": [],
            "special": []
        }

        for item in item_files:
            full_path = f"{str(dir_path)}/{item}"

            if self.file_system.is_link(full_path):
                categorized["links"].append(item)
            elif self.file_system.is_readable_file(full_path):
                categorized["files"].append(item)
            else:
                # Socket files, FIFOs, device files, etc.
                categorized["special"].append(item)
                config.logger.debug(f"Categorized {full_path} as special file")

        return categorized