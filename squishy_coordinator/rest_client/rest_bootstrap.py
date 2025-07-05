from .rest_processor import RestProcessor
from .http_client import RequestsHttpClient
from .hash_info_validator import HashInfoValidator

from squishy_integrity import logger


class RestClient:
    rest_api_name: str
    rest_api_port: str

    @property
    def rest_client(self) -> RestProcessor:
        return self.create_rest_connector()

    def create_rest_connector(self) -> RestProcessor:
        try:
            http_client = RequestsHttpClient()
            validator = HashInfoValidator()
            return RestProcessor(http_client, validator)
        except ValueError as e:
            logger.error(f"Unable to bootstrap rest_connector: {e}")
            exit(78)  # Configuration error
