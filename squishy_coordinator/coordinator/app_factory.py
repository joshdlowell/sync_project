from squishy_coordinator import logger, config
from rest_client import RestClient

from .coordinator_service import CoordinatorService
from .implementations import RestStorage
from integrity_check import IntegrityCheckFactory


class CoordinatorFactory:
    """Factory for creating coordinator components"""

    @staticmethod
    def create_service() -> CoordinatorService:

        # Create implementations
        rest_client = RestClient()
        local_storage = RestStorage(rest_client.create_rest_connector(config.get('rest_api_url')))
        core_storage = RestStorage(rest_client.create_rest_connector(config.get('core_api_url')))
        integrity_service = IntegrityCheckFactory.create_service()  # TODO env var ? sets to return updates here or new implementation?

        logger.info("Application configured services with default configuration")

        # Create main service
        return CoordinatorService(local_storage, core_storage, integrity_service)