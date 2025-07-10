from typing import Tuple, Any
from time import time

from .rest_interface import RestProcessorInterface
from .http_client import HttpClient
from .hash_info_validator import HashInfoValidator
from .configuration import config, logger

class RestProcessor(RestProcessorInterface):
    """
    Connector for interacting with the REST API for hash storage operations.

    This class implements the HashStorageInterface required by the MerkleTreeService.
    """

    def __init__(self,
                 rest_api_url: str,
                 http_client: HttpClient,
                 validator: HashInfoValidator=None,
                 ):
        """
        Initialize the RestConnector.

        Args:
            rest_api_url: URL for the REST API
            http_client: HTTP client for making requests
            validator: Validator for hash information (optional) default 'HashInfoValidator()'
        """
        self.rest_api_url = rest_api_url
        self.http_client = http_client
        self.validator = validator or HashInfoValidator()

    def put_hashtable(self, hash_info: dict) -> int:
        """
        Store hash information in the database.

        This method implements the HashStorageInterface.put_hashtable method
        required by the MerkleTreeService.

        Args:
            hash_info: Dictionary containing hash information for files and directories
            session_id: Optional session ID for grouping batches of updates

        Returns:
            int representing the number of updates sent to the REST API that were successful
            TODO update integrity implementation to this return
        """
        # Validate input
        # validation_errors = self.validator.validate(hash_info)
        # if validation_errors:
        #     for error in validation_errors:
        #         logger.error(f"Validation error: {error}")

        send_errors = 0
        for path, item_data in hash_info.items():
            # Skip invalid items
            if self._has_validation_errors(path, item_data):
                send_errors += 1
                continue

            # Build request dict
            request_data = {
                'path': path,
                'current_hash': item_data['current_hash'],
            }
            # Add keys that aren't always present (to ensure minimum data sent)
            for key in ['dirs', 'files', 'links', 'session_id', 'target_hash']:
                if item_data.get(key):
                    request_data[key] = item_data[key]

            # Send update to api
            response = self._db_put("api/hashtable", request_data)
            # Api / process response for hashtable will return True for success, None otherwise
            if not self._process_response(response):
                send_errors += 1
                logger.debug(f"Unsuccessful update for path: {path}")
                continue

        logger.debug("Completed hashtable put requests")
        return len(hash_info.keys()) - send_errors  # Number successfully put to db

    def get_hashtable(self, path: str) -> dict | None:
        """
        Get the complete hash table for a specific path.

        Args:
            path: The path to get the hash table for

        Returns:
            A dictionary containing the hash table, or None if not found or error
        """
        response = self._db_get("api/hashtable", {"path": path})
        # content = self._process_response(response)
        # if content:
        #     for key in ['dirs', 'files', 'links']:
        #         if key in content and isinstance(content[key], str):
        #             # Split by common delimiters (adjust as needed based on data format)
        #             content[key] = [item.strip() for item in content[key].split(',') if item.strip()]
        logger.debug("Processing get hashtable request")
        return self._process_response(response)  # TODO check that content should be json loaded already

    def get_single_hash(self, path: str) -> str | None:
        """
        Get the hash value for a specific path.

        Args:
            path: The path to get the hash for

        Returns:
            The hash value as a string, or None if not found or error
        """
        response = self._db_get("api/hash", {"path": path, 'field': 'hash'})
        logger.debug("Processing get single hash request")
        return self._process_response(response)

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

        # Add files and links in root_path to ensure, if any exist, they are periodically updated
        dirs.extend(base_response.get('files') if base_response.get('files') else [])
        dirs.extend(base_response.get('links') if base_response.get('links') else [])

        # Convert root_path relative items to absolute path strings
        dirs = [f"{root_path}/{relative_dir}" for relative_dir in dirs]

        # Build and sort by timestamp
        dir_timestamps = [(self.get_single_timestamp(directory) or int(time()), directory)
                          for directory in dirs]
        ordered_dirs = [directory for _, directory in sorted(dir_timestamps)]

        # Calculate the number of directories to return
        update_num = max(1, int(len(dirs) * percent / 100) + 1) # Make sure to round up with +1
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
        response = self._db_get("api/hashtable", {"path": path, 'field': 'timestamp'})
        logger.debug("Processing get single timestamp request")
        return self._process_response(response)

    def get_priority_updates(self) -> list | None:
        """
        Get paths that need priority updates.

        Returns:
            A list containing paths as strings that need priority updates, or None if not found or error
        """
        response = self._db_get('api/hashtable', {"path": None, 'field': 'priority'})
        logger.debug("Processing priority updates request")
        return self._process_response(response)

    def get_lifecheck(self) -> dict | None:
        """Get the liveness of the rest api and database."""
        response = self._db_get('api/health')
        content = self._process_response(response)
        logger.debug("Processing life check request")
        return self._process_response(response)

    def put_log(self,
                message: str,
                site_id: str=None,
                timestamp: int=None,
                detailed_message: str=None,
                log_level: str=None,
                session_id: str=None
                ) -> int:
        """
        Store log information in the database.

        This method implements the HashStorageInterface.put_log method
        required by the MerkleTreeService.
        Permitted log levels: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'

        Args:
            message: string containing the log message
            detailed_message: string containing the detailed log message
            log_level: string containing the log level
            session_id: string containing the session id for grouping batches of updates

        Returns:
            int representing the number of updates sent to the REST API that were successfully
            TODO change to return log id of log entry instead of 0 or 1 in integrity
        """
        # Validate input, allow api to set to default if arg is not valid
        log_level = log_level.upper() if log_level and log_level.upper() in config.get('valid_log_levels') else None

        if not message:
            # if validation_errors:
            logger.debug(f"Skipping put_log for invalid item")
            return 0

        # Assemble the log entry
        request_data = { 'summary_message': message }
        # Add keys that aren't always present (to ensure minimum data sent)
        columns = {'detailed_message': detailed_message,
                   'log_level': log_level,
                   'session_id': session_id,
                   'site_id': site_id,
                   'timestamp': timestamp }
        for key, value in columns.items():
            if value:
                request_data[key] = value

        # if session_id: request_data['session_id'] = session_id
        # if detailed_message: request_data['detailed_message'] = detailed_message
        # if log_level: request_data['log_level'] = log_level.upper()

        response = self._db_put("api/logs", request_data)
        logger.debug("Processing log entry request")
        # Api / process response will return True if successful, None otherwise
        if self._process_response(response):
            return 1
        else:
            return 0

    def find_orphaned_entries(self) -> list | None:
        """
        Get all entries that aren't listed by a parent

        Returns:
            A list containing paths in the database that aren't listed by a parent, or None if not found or error
        """
        response = self._db_get('api/hashtable', {"path": None, 'field': 'orphaned'})
        logger.debug("Processing database orphaned entries list request")
        return self._process_response(response)

    def find_untracked_children(self) -> list | None:
        """Get a list of children claimed by a parent but not tracked in the database

        Returns:
            A list containing paths in the database that aren't listed by a parent, or None if not found or error
        """
        response = self._db_get('api/hashtable', {"path": None, 'field': 'untracked'})
        logger.debug("Processing database untracked children list request")
        return self._process_response(response)

    def get_pipeline_updates(self):
        """Get the list of updates from the pipeline that haven't been processed yet.

        Returns:
            A list containing paths in the database that have been updated by the CD pipeline, or None if not found or error
        """
        response = self._db_get('api/pipeline')
        logger.debug("Processing database pipeline updates list request")
        return self._process_response(response)

    def get_site_liveness(self) -> list:
        """
        Get all sites from site_list with their last_updated timestamps and status categories.

        Returns:
            List of dictionaries containing site records with their status categories,
            or empty list if no records found or an error occurred.
            Each dictionary contains: site_name, last_updated, status_category
        """
        response = self._db_get('web/liveness')
        logger.debug("Processing database liveness request")
        return self._process_response(response)


    def get_site_sync_status(self) -> list:
        """
        Get synchronization status for all active sites based on their current hash
        compared to the hash history timeline.

        Returns:
            List of dictionaries containing site records with their sync status categories,
            or empty list if no records found or an error occurred.
            Each dictionary contains: site_name, current_hash, last_updated, sync_category
        """
        response = self._db_get('web/status')
        logger.debug("Processing database site hash status request")
        return self._process_response(response)

    def consolidate_logs(self) -> bool | None:
        """Trigger log consolidation via REST API.

        Returns:
            True if consolidation was completed, None otherwise.
        """
        endpoint = "api/logs"
        params = {"action": "consolidate"}

        response = self._db_get(endpoint, params)
        logger.debug("Processing log consolidation request")
        return self._process_response(response)

    def collect_logs_for_shipping(self) -> list[dict[str, Any]] | None:
        """Retrieve all log entries ready to be sent to the core db via REST API.

        Returns:
            A list of the log entries to be put to the core database log table.
        """
        endpoint = "api/logs"
        params = {"action": "shippable"}

        response = self._db_get(endpoint, params)
        logger.debug("Processing log collection request")
        return self._process_response(response)

    def collect_logs_older_than(self, days: int) -> list[dict[str, Any]] | None:
        """Retrieve all log entries older than the specified number of days.

        Returns:
            A list of the log entries that are older than the specified number of days.
        """
        if not isinstance(days, int):
            logger.error(f"Invalid input for days: {days}. Must be an integer. Returning None.")
            return None
        endpoint = "api/logs"
        params = {"action": "older_than", "days": days}

        response = self._db_get(endpoint, params)
        logger.debug("Processing log collection request")
        return self._process_response(response)

    def delete_log_entries(self, log_ids: list[int]) -> Tuple[bool, list]:
        """
        Delete multiple log entries by their IDs.

        Response data formatting:
         if successful, a list with a single entry representing the number of entries deleted
         if partial success, a list of the log IDs that failed to delete
         and an empty list otherwise

        Args:
            log_ids: List of log entry IDs to delete

        Returns:
            A tuple containing (success, response_data)
        """
        endpoint = "api/logs"
        data = {"log_ids": log_ids}

        response = self._db_delete(endpoint, data)
        data = self._process_response(response)
        status_code, _ = response
        if status_code == 200:
            return True, [data.get('deleted_count')]
        elif status_code == 207:  # Partial success
            return False, data.get('failed_deletes')
        else:
            return False, []

    def get_official_sites(self) -> list[str]:
        """
        Get the current authoritative sites list from the MSSQL table.

        Returns:
            List of site names (strings)
        """
        endpoint = "api/pipeline"
        params = {"action": "sites"}

        response = self._db_get(endpoint, params)
        logger.debug("Processing official sites request")
        return self._process_response(response)

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
            return content.get('data', None)
        elif code == 207:
            return content.get('data', None)

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

    def _db_put(self, endpoint: str, data: dict) -> Tuple[int, Any]:
        """
        Send a PUT request to the REST API.

        Args:
            endpoint: The API endpoint to call
            data: The request data to send

        Returns:
            A tuple containing (status_code, content)
        """
        url = f"{self.rest_api_url}/{endpoint}"
        return self.http_client.post(url, json_data=data)

    def _db_get(self, endpoint: str, params: dict = None) -> Tuple[int, Any]:
        """
        Send a GET request to the REST API.

        Args:
            endpoint: The API endpoint to call
            params: The query parameters to include

        Returns:
            A tuple containing (status_code, content)
        """
        url = f"{self.rest_api_url}/{endpoint}"
        return self.http_client.get(url, params=params)

    def _db_delete(self, endpoint: str, data: dict = None) -> Tuple[int, Any]:
        """
        Send a DELETE request to the REST API.

        Args:
            endpoint: The API endpoint to call
            data: The JSON data to send in the request body

        Returns:
            A tuple containing (status_code, content)
        """
        url = f"{self.rest_api_url}/{endpoint}"
        return self.http_client.delete(url, json_data=data)
