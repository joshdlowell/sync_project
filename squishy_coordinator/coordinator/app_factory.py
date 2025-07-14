from squishy_coordinator import logger, config
from rest_client import RestClient
from integrity_check import IntegrityCheckFactory

from .coordinator_service import CoordinatorService
from .implementations import RestClientStorage, MerkleTreeImplementation




class CoordinatorFactory:
    """Factory for creating coordinator components"""

    @staticmethod
    def create_service() -> CoordinatorService:

        # Create implementations
        # local rest api
        rest_client = RestClient().create_rest_connector(config.rest_api_url)
        rest_storage = RestClientStorage(rest_client)
        # core rest api
        rest_client = RestClient().create_rest_connector(config.core_api_url)
        core_rest_storage = RestClientStorage(rest_client)

        merkle_config = None  # Inject custom config dict into Integrity check factory
        integrity_service = IntegrityCheckFactory().create_service(merkle_config, rest_storage)
        merkle_service = MerkleTreeImplementation(integrity_service)


        logger.info("Application configured services with default configuration")

        # Create main service
        return CoordinatorService(rest_storage, core_rest_storage, merkle_service)