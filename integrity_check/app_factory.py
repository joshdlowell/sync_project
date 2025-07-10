# from squishy_integrity import logger # TODO update to use own config and logger (maybe environment determines return type / db send
# from squishy_integrity.rest_client import RestClient
from .configuration import config, logger
from rest_client import RestClient
from .merkle_tree_service import MerkleTreeService
from .implementations import StandardFileSystem, RestHashStorage, SHA1HashFunction
from .validators import PathValidator
from .tree_walker import DirectoryTreeWalker
from .file_hasher import FileHasher


class IntegrityCheckFactory:
    """Factory for creating integrity check components"""
    @staticmethod
    def create_service(new_config=None) -> MerkleTreeService:
        """Create a fully configured MerkleTreeService"""

        # Set configuration passed from importing package
        # config = Config(config)
        # logger = config.logger
        if new_config:
            config.update(new_config)
        # Create implementations

        rest_client = RestClient()
        hash_storage = RestHashStorage(rest_client.create_rest_connector(config.get('rest_api_url')))
        # core_storage = RestStorage(rest_client.create_rest_connector(config.get('core_api_url')))
        # integrity_service = IntegrityCheckFactory.create_service()


        file_system = StandardFileSystem()
        # rest_service = (RestClient()).rest_client
        # rest_service = RestClient.create_rest_connector(config.get('rest_api_url'))
        # hash_storage = RestHashStorage(rest_service)
        hash_function = SHA1HashFunction()

        # Create components
        path_validator = PathValidator()
        tree_walker = DirectoryTreeWalker(file_system)
        file_hasher = FileHasher(file_system, hash_function)
        logger.info("Application configured services with default configuration")

        # Create main service
        return MerkleTreeService(hash_storage, tree_walker, file_hasher, path_validator)
