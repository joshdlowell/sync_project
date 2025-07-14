from .rest_processor import RestProcessor
from .http_client import RequestsHttpClient
from .hash_info_validator import HashInfoValidator
from .configuration import logger


class RestClient:

    def create_rest_connector(self, url: str) -> RestProcessor:
        """
        Create and configure a REST API connector for hash storage operations.

        This method initializes a RestProcessor instance with the necessary components
        including HTTP client, validator, and logging configuration.

        Args:
            url (str): The REST API URL endpoint for hash storage operations

        Returns:
            RestProcessor: Configured REST API processor instance ready for hash
                storage operations.

        Raises:
            TypeError: If url is not a string or if log_level is not a string when provided.
            ValueError: If url is empty or contains only whitespace.
            ImportError: If required dependencies (requests) are not available.
            AttributeError: If the config module or its get() method is not accessible.

        Note:
            - The method creates new instances of RequestsHttpClient and HashInfoValidator
            - Invalid log_level values will default to 'INFO' without raising an exception
            - The logging configuration is handled internally and should not raise exceptions
              under normal circumstances
        """
        # Input validation
        if not isinstance(url, str):
            raise TypeError("url must be a string")
        if not url.strip():
            raise ValueError("url cannot be empty or contain only whitespace")

        # Collect components
        http_client = RequestsHttpClient()
        validator = HashInfoValidator()

        logger.info(f"Creating REST API client for {url}")
        return RestProcessor(url, http_client, validator)
