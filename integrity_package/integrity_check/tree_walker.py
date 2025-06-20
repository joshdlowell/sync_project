from typing import Dict, List
from .interfaces import FileSystemInterface


class DirectoryTreeWalker:
    """Handles directory tree traversal and categorization"""

    def __init__(self, file_system: FileSystemInterface):
        self.file_system = file_system

    def get_tree_structure(self, parent_path: str) -> Dict[str, Dict[str, List[str]]]:
        """
        Recursively traverse directory tree and categorize items

        Args:
            parent_path: Root directory path to begin traversal

        Returns:
            Dictionary mapping directory paths to their contents
        """
        tree_dict = {}

        for item in self.file_system.walk(parent_path):
            dir_path, item_dirs, item_files = item

            # Separate files from links
            clean_files, clean_links = self._categorize_files(dir_path, item_files)

            tree_dict[str(dir_path)] = {
                "dirs": sorted([str(item) for item in item_dirs]),
                "files": sorted(clean_files),
                "links": sorted(clean_links)
            }

        return tree_dict

    def _categorize_files(self, dir_path, item_files):
        """Separate regular files from links"""
        clean_files, clean_links = [], []

        for item in item_files:
            full_path = str(dir_path / item)
            if self.file_system.is_file(full_path):
                clean_files.append(item)
            else:
                clean_links.append(item)

        return clean_files, clean_links
