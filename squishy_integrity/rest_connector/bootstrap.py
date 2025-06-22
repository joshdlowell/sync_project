from .rest_connector import RestConnector
from .configuration import Config
from .client import RequestsHttpClient
from .validator import HashInfoValidator

def create_rest_connector() -> RestConnector:
    try:
        config = Config.from_env()
        http_client = RequestsHttpClient()
        validator = HashInfoValidator()
        return RestConnector(config, http_client, validator)
    except ValueError as e:
        print(f"ERROR: Unable to bootstrap rest_connector: {e}")
        exit(78)  # Configuration error

