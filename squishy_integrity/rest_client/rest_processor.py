from typing import Tuple, Any
from time import time

from squishy_integrity import config, logger
from .http_client import HttpClient
from .hash_info_validator import HashInfoValidator


class RestProcessor:
    """
    Connector for interacting with the REST API for hash storage operations.

    This class implements the HashStorageInterface required by the MerkleTreeService.
    """

    def __init__(self, http_client: HttpClient, validator: HashInfoValidator = None):
        """
        Initialize the RestConnector.

        Args:
            config: Configuration for the REST API
            http_client: HTTP client for making requests
            validator: Validator for hash information (optional)
        """
        # self.config = config
        self.http_client = http_client
        self.validator = validator or HashInfoValidator()

    def put_hashtable(self, hash_info: dict, session_id: str=None) -> int:
        """
        Store hash information in the database.

        This method implements the HashStorageInterface.put_hashtable method
        required by the MerkleTreeService.

        Args:
            hash_info: Dictionary containing hash information for files and directories

        Returns:
            int representing the number of updates sent to the REST API that were unsuccessful
        """
        # Validate input
        validation_errors = self.validator.validate(hash_info)
        if validation_errors:
            for error in validation_errors:
                logger.error(f"Validation error: {error}")

        send_errors = 0
        for path, item_data in hash_info.items():
            # Skip invalid items
            if self._has_validation_errors(path, item_data):
                send_errors += 1
                logger.debug(f"Skipping put_hashtable for invalid item: {path} with data: {item_data}")
                continue

            request_data = {
                'session_id': session_id,
                'path': path,
                'current_hash': item_data['current_hash'],
                'dirs': item_data.get('dirs'),
                'files': item_data.get('files'),
                'links': item_data.get('links')
            }

            code, update = self._db_put("api/hashtable", request_data)

            if code != 200:
                send_errors += 1
                logger.debug(f"Unsuccessful update for path: {path}")
                logger.error(f"REST API returned {code}: {update}")
                continue

        logger.debug("Completed hashtable put request")
        return send_errors

    def get_hashtable(self, path: str) -> dict | None:
        """
        Get the complete hash table for a specific path.

        Args:
            path: The path to get the hash table for

        Returns:
            A dictionary containing the hash table, or None if not found or error
        """
        response = self._db_get("api/hashtable", {"path": path})
        content = self._process_response(response)
        if content:
            for key in ['dirs', 'files', 'links']:
                if key in content and isinstance(content[key], str):
                    # Split by common delimiters (adjust as needed based on data format)
                    content[key] = [item.strip() for item in content[key].split(',') if item.strip()]
        return content

    def get_single_hash(self, path: str) -> str | None:
        """
        Get the hash value for a specific path.

        Args:
            path: The path to get the hash for

        Returns:
            The hash value as a string, or None if not found or error
        """
        response = self._db_get("api/hash", {"path": path})
        content = self._process_response(response)
        return content.get('data') if content else None

    def get_oldest_updates(self, root_path: str, percent: int = 10) -> list[str]:
        """
        Get a list of directories that need to be updated based on their age.

        This method retrieves the oldest directories (based on timestamps) that 
        should be updated. The number of directories is determined by the percent
        parameter.

        Args:
            root_path: The root directory to start from
            percent: The percentage of directories to return (default: 10%)

        Returns:
            A list of directory paths that need to be updated
        """
        base_response = self.get_hashtable(root_path)

        if not base_response or not base_response.get('current_dtg_latest'):
            logger.info("Database is empty, requesting full hash")
            return [root_path]

        dirs = base_response.get('dirs', [])
        if not dirs:
            logger.info("no child directories in database, requesting full hash")
            return [root_path]
        dirs = [f"{root_path}/{relative_dir}" for relative_dir in dirs]
        # Build and sort by timestamp
        dir_timestamps = [(self.get_single_timestamp(directory) or int(time()), directory)
                          for directory in dirs]
        ordered_dirs = [directory for _, directory in sorted(dir_timestamps)]

        # Calculate number of directories to return
        update_num = max(1, int(len(dirs) * percent / 100))
        update_num = min(update_num, len(dirs))

        logger.info(f"Returning {update_num} directories for update")
        return ordered_dirs[:update_num]

    def get_single_timestamp(self, path: str) -> float | None:
        """
        Get the timestamp for a specific path.

        Args:
            path: The path to get the timestamp for

        Returns:
            The timestamp as a float, or None if not found or error
        """
        response = self._db_get("api/timestamp", {"path": path})
        content = self._process_response(response)
        logger.debug("Returning single timestamp request")
        return content.get('data') if content else None

    def get_priority_updates(self) -> list | None:
        """
        Get paths that need priority updates.

        Returns:
            A string containing paths that need priority updates, or None if not found or error
        """
        response = self._db_get('api/priority')
        content = self._process_response(response)
        logger.debug("Returning priority updates request")
        return content.get('data') if content else None

    def get_life_check(self) -> dict | None:
        """Get the liveness of the rest api and database."""
        response = self._db_get('api/lifecheck')
        content = self._process_response(response)
        logger.debug("Getting life check")
        return content.get('data') if content else None

    def put_log(self, message: str, detailed_message: str=None, log_level: str=None) -> int:
        """
        Store log information in the database.

        This method implements the HashStorageInterface.put_log method
        required by the MerkleTreeService.
        Permitted log levels: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'

        Args:
            message: string containing the log message
            detailed_message: string containing the detailed log message
            log_level: string containing the log level

        Returns:
            int representing the number of updates sent to the REST API that were unsuccessful
        """
        # Validate input
        validation_errors = message and log_level.upper() in config.VALID_LOG_LEVELS if log_level else True
        if validation_errors:
            logger.debug(f"Skipping put_log for invalid item")
            return 1

        # Assemble the log entry
        request_data = { 'summary_message': message }
        if detailed_message: request_data['detailed_message'] = detailed_message
        if log_level: request_data['log_level'] = log_level.upper()

        code, update = self._db_put("api/hashtable", request_data)

        if code != 200:
            send_errors += 1
            logger.debug(f"Unsuccessful update for path: {path}")
            logger.error(f"REST API returned {code}: {update}")
            continue

        logger.debug("Completed hashtable put request")
        return send_errors

    def _has_validation_errors(self, path: str, item_data: dict) -> bool:
        """
        Check if an item has validation errors.

        Args:
            path: The path of the item
            item_data: The data for the item

        Returns:
            True if there are validation errors, False otherwise
        """
        errors = self.validator._validate_item(path, item_data)
        if errors:
            for error in errors:
                logger.error(error)
            return True
        return False

    # def _process_changes(self, changes: list) -> dict[str, set]:
    #     """
    #     Process the changes returned by the REST API.
    #
    #     This method organizes the changes into categories: 'Created', 'Deleted', and 'Modified'.
    #
    #     Args:
    #         changes: List of change dictionaries from the REST API
    #
    #     Returns:
    #         Dictionary of changes categorized as 'Created', 'Deleted', and 'Modified'
    #     """
    #     sorted_changes = {'Created': set(), 'Deleted': set(), 'Modified': set()}
    #     for change in changes:
    #         for key in sorted_changes.keys():
    #             if key in change:
    #                 sorted_changes[key].update(set(change[key]))
    #     return sorted_changes

    def _process_response(self, response: Tuple[int, Any]) -> Any:
        """
        Process the response from the REST API.

        Args:
            response: A tuple containing (status_code, content)

        Returns:
            The content if status_code is 200, None otherwise
        """
        code, content = response

        if code == 200:
            return content

        # Handle specific error cases
        if code == 0:
            logger.critical(f"Network error - {content}")
        elif code == 408:
            logger.warning(f"Request timeout - {content}")
        elif code == 503:
            logger.warning(f"Service unavailable - {content}")
        elif code == 404:
            logger.info(f"Resource not found - {content}")
        else:
            logger.warning(f"REST API returned status code {code} - {content}")

        return None

    def _db_put(self, endpoint: str, request: dict) -> Tuple[int, Any]:
        """
        Send a PUT request to the REST API.

        Args:
            endpoint: The API endpoint to call
            request: The request data to send

        Returns:
            A tuple containing (status_code, content)
        """
        url = f"{config.rest_api_url}/{endpoint}"
        return self.http_client.post(url, request)

    def _db_get(self, endpoint: str, params: dict = None) -> Tuple[int, Any]:
        """
        Send a GET request to the REST API.

        Args:
            endpoint: The API endpoint to call
            params: The query parameters to include

        Returns:
            A tuple containing (status_code, content)
        """
        url = f"{config.rest_api_url}/{endpoint}"
        return self.http_client.get(url, params)
