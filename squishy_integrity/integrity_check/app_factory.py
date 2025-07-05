from squishy_integrity import logger
from squishy_integrity.rest_client import RestClient
from .merkle_tree_service import MerkleTreeService
from .implementations import StandardFileSystem, RestHashStorage, SHA1HashFunction
from .validators import PathValidator
from .tree_walker import DirectoryTreeWalker
from .file_hasher import FileHasher


class IntegrityCheckFactory:
    """Factory for creating integrity check components"""

    @staticmethod
    def create_service() -> MerkleTreeService:
        """Create a fully configured MerkleTreeService"""

        # Create implementations
        storage_system = RestClient()
        hash_storage = RestHashStorage(storage_system)
        file_system = StandardFileSystem()
        hash_function = SHA1HashFunction()

        # Create components

        path_validator = PathValidator()
        tree_walker = DirectoryTreeWalker(file_system)
        file_hasher = FileHasher(file_system, hash_function)
        logger.info("Application configured services with default configuration")

        # Create main service
        return MerkleTreeService(hash_storage, tree_walker, file_hasher, path_validator)
