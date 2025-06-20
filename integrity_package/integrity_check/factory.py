from .merkle_tree_service import MerkleTreeService
from .implementations import StandardFileSystem, RestHashStorage, SHA1HashFunction #, SystemTimeProvider,
from .validators import PathValidator
from .tree_walker import DirectoryTreeWalker
from .file_hasher import FileHasher


class IntegrityCheckFactory:
    """Factory for creating integrity check components"""

    @staticmethod
    def create_service(rest_connector) -> MerkleTreeService:
        """Create a fully configured MerkleTreeService"""

        # Create implementations
        file_system = StandardFileSystem()
        hash_storage = RestHashStorage(rest_connector)
        # time_provider = SystemTimeProvider()
        hash_function = SHA1HashFunction()

        # Create components
        path_validator = PathValidator()
        tree_walker = DirectoryTreeWalker(file_system)
        file_hasher = FileHasher(file_system, hash_function) #, time_provider)

        # Create main service
        return MerkleTreeService(hash_storage, tree_walker, file_hasher, path_validator)
