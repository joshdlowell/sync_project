from rest_client import RestClient

from .configuration import config
from .merkle_tree_service import MerkleTreeService
from .implementations import StandardFileSystem, RestHashStorage, SHA1HashFunction
from .validators import PathValidator
from .tree_walker import DirectoryTreeWalker
from .file_hasher import FileHasher


class IntegrityCheckFactory:
    """Factory for creating integrity check components"""
    @staticmethod
    def create_service(new_config=None, rest_storage=None) -> MerkleTreeService:
        """Create a fully configured MerkleTreeService"""

        # Set configuration passed from importing package
        if new_config:
            config.update(new_config)

        # Create implementations
        if not rest_storage:  # Attempt to create a connection using local config if none provided
            rest_client = RestClient().create_rest_connector(config.rest_api_url)
            rest_storage = RestHashStorage(rest_client)
        file_system = StandardFileSystem()
        hash_function = SHA1HashFunction()

        # Create components
        path_validator = PathValidator()
        tree_walker = DirectoryTreeWalker(file_system)
        file_hasher = FileHasher(file_system, hash_function)
        config.logger.info("Application configured services with default configuration")

        # Create main service
        return MerkleTreeService(rest_storage, tree_walker, file_hasher, path_validator)
