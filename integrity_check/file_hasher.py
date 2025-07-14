from typing import Dict, Any

from .interfaces import FileSystemInterface, HashFunction
from .configuration import config


class FileHasher:
    """Handles hashing of files, directories, and links"""

    def __init__(self, file_system: FileSystemInterface, hash_function: HashFunction):
        self.file_system = file_system
        self.hash_function = hash_function
        # self.time_provider = time_provider

    def hash_file(self, file_path: str) -> str:
        """Hash a regular file by reading its contents"""
        hasher = self.hash_function.create_hasher()

        for chunk in self.file_system.read_file_chunks(file_path):
            hasher.update(chunk)

        return hasher.hexdigest()

    def hash_link(self, link_path: str) -> str:
        """Hash a symbolic link by its path and target"""
        link_representation = self._get_link_representation(link_path)
        return self.hash_function.hash_string(link_representation)

    def hash_directory(self, hash_info: Dict[str, Any]) -> str | None:
        """Hash a directory based on its contents"""
        if not hash_info.get('path', None):
            config.logger.error(f"Failed to hash_directory for hash_info with no path key")
            return None
        config.logger.debug("Getting directory hashable string...")
        dir_representation = self._get_directory_representation(hash_info)
        return self.hash_function.hash_string(dir_representation)

    def hash_empty_type(self, full_path: str, category: str = 'dirs', return_string: bool=False) -> str:
        """Provides a standardized way to Hash an empty directory by its path"""
        hash_string = f"{full_path}/{category}: EMPTY "

        if return_string:
            return hash_string
        return self.hash_function.hash_string(hash_string)

    def hash_string(self, hashable: str) -> str:
        """Hash a string using the Filehasher methods"""
        return self.hash_function.hash_string(hashable)

    def _get_link_representation(self, link_path: str) -> str:
        """Get string representation of a link for hashing"""
        target = self.file_system.readlink(link_path)
        return f"{link_path} -> {target}"

    def _get_directory_representation(self, hash_info: Dict[str, Any]) -> str:
        """Get string representation of directory contents for hashing"""
        hash_string = ''

        for category in ['dirs', 'files', 'links']:
            items = hash_info.get(category, [])
            if items and len(items) > 0:
                for item in sorted(items):
                    hash_string += hash_info['current_content_hashes'][item]
            else:
                hash_string += self.hash_empty_type(hash_info['path'], category, return_string=True)

        return hash_string
