from squishy_integrity import config
from .http_client import HttpClient
from .info_validator import HashInfoValidator
from typing import Tuple, Any

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

    def put_hashtable(self, hash_info: dict) -> dict[str, set]:
        """
        Store hash information in the database and return changes.

        This method implements the HashStorageInterface.put_hashtable method
        required by the MerkleTreeService.

        Args:
            hash_info: Dictionary containing hash information for files and directories

        Returns:
            Dictionary of changes categorized as 'Created', 'Deleted', and 'Modified'
        """
        # Validate input
        validation_errors = self.validator.validate(hash_info)
        if validation_errors:
            for error in validation_errors:
                print(f"Validation error: {error}")

        changes = []

        for path, item_data in hash_info.items():
            # Skip invalid items
            if self._has_validation_errors(path, item_data):
                continue

            request_data = {
                'path': path,
                'current_hash': item_data['current_hash'],
                'dirs': item_data.get('dirs'),
                'files': item_data.get('files'),
                'links': item_data.get('links')
            }

            # Add timestamp if available
            if 'current_dtg_latest' in item_data:
                request_data['current_dtg_latest'] = item_data['current_dtg_latest']

            code, update = self._db_put("api/hashtable", request_data)

            if code != 200:
                print(f"ERROR: REST API returned {code}: {update}")
                continue

            changes.append(update)

        return self._process_changes(changes)

    def get_hashtable(self, path: str) -> dict | None:
        """
        Get the complete hash table for a specific path.

        Args:
            path: The path to get the hash table for

        Returns:
            A dictionary containing the hash table, or None if not found or error
        """
        response = self._db_get("api/hashtable", {"path": path})
        return self._process_response(response)

    def get_single_hash(self, path: str) -> str | None:
        """
        Get the hash value for a specific path.

        Args:
            path: The path to get the hash for

        Returns:
            The hash value as a string, or None if not found or error
        """
        response = self._db_get("api/hash", {"path": path})
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
            print("STATUS: Local database is empty, requesting full hash")
            return [root_path]

        dirs = base_response.get('dirs', [])
        if not dirs:
            print("STATUS: no child directories in database, requesting full hash")
            return [root_path]

        # Build and sort by timestamp
        dir_timestamps = [(self.get_single_timestamp(directory), directory) for directory in dirs]
        ordered_dirs = [directory for _, directory in sorted(dir_timestamps)]

        # Calculate number of directories to return
        update_num = max(1, int(len(dirs) * percent / 100))
        update_num = min(update_num, len(dirs))

        print(f"Returning {update_num} directories for update")
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
        return self._process_response(response)

    def get_priority_updates(self) -> str | None:
        """
        Get paths that need priority updates.

        Returns:
            A string containing paths that need priority updates, or None if not found or error
        """
        response = self._db_get('api/priority')
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
                print(f"ERROR: {error}")
            return True
        return False

    def _process_changes(self, changes: list) -> dict[str, set]:
        """
        Process the changes returned by the REST API.

        This method organizes the changes into categories: 'Created', 'Deleted', and 'Modified'.

        Args:
            changes: List of change dictionaries from the REST API

        Returns:
            Dictionary of changes categorized as 'Created', 'Deleted', and 'Modified'
        """
        sorted_changes = {'Created': set(), 'Deleted': set(), 'Modified': set()}
        for change in changes:
            for key in sorted_changes.keys():
                if key in change:
                    sorted_changes[key].update(set(change[key]))
        return sorted_changes

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
            print(f"CRITICAL: Network error - {content}")
        elif code == 408:
            print(f"WARNING: Request timeout - {content}")
        elif code == 503:
            print(f"WARNING: Service unavailable - {content}")
        elif code == 404:
            print(f"INFO: Resource not found - {content}")
        else:
            print(f"WARNING: REST API returned status code {code} - {content}")

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
