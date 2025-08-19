from abc import ABC, abstractmethod
from typing import Tuple, Any, Optional
from time import sleep
import requests

from .configuration import config, logger


class HttpClient(ABC):
    @abstractmethod
    def post(self, url: str, json_data: dict) -> Tuple[int, Any]:
        pass

    @abstractmethod
    def get(self, url: str, params: Optional[dict] = None) -> Tuple[int, Any]:
        pass

    @abstractmethod
    def patch(self, url: str, json_data: Optional[dict] = None) -> Tuple[int, Any]:
        pass


class RequestsHttpClient(HttpClient):
    def __init__(self):
        self.max_retries = config.get('max_retries')
        self.retry_delay = config.get('retry_delay')
        self.long_delay = config.get('long_delay')

    def post(self, url: str, json_data: dict) -> Tuple[int, Any]:
        return self._make_request('post', url, json_data)

    def get(self, url: str, params: Optional[dict] = None) -> Tuple[int, Any]:
        return self._make_request('get', url, params)

    def patch(self, url: str, json_data: Optional[dict] = None) -> Tuple[int, Any]:
        return self._make_request('patch', url, json_data)

    def _make_request(self, method: str, url: str, data: Optional[dict] = None) -> Tuple[int, Any]:
        method_map = {
            'post': lambda: requests.post(url, json=data, timeout=30),
            'get': lambda: requests.get(url, params=data, timeout=30),
            'patch': lambda: requests.patch(url, json=data, timeout=30)
        }

        if method not in method_map:
            return 405, f"'{method}' is not an allowed method."

        total_attempts = 0

        for outer_retry in range(self.max_retries):
            for inner_retry in range(5):
                total_attempts += 1

                try:
                    response = method_map[method]()
                    status_code = response.status_code

                    # Return immediately for 4xx errors (client errors)
                    if 400 <= status_code < 500:
                        return self._handle_response(response, is_error=True)

                    # Handle successful responses
                    if status_code == 200:
                        if total_attempts > 1:
                            logger.info("Success on retry")
                        return self._handle_response(response)

                    # 5xx errors will continue to retry
                    if status_code >= 500:
                        error_message = self._extract_error_message(response)
                        logger.warning(f"Server error on attempt #{total_attempts}: {status_code}, {error_message}")

                except requests.exceptions.Timeout:
                    logger.warning(f"Request timeout on attempt #{total_attempts}: {url}")
                    if self._is_last_attempt(outer_retry, inner_retry):
                        return 408, "Request timeout - server did not respond"

                except requests.exceptions.ConnectionError:
                    logger.warning(f"Connection error on attempt #{total_attempts}: {url}")
                    if self._is_last_attempt(outer_retry, inner_retry):
                        return 503, "Service unavailable - cannot connect to server"

                except requests.exceptions.RequestException as e:
                    logger.warning(f"Request exception on attempt #{total_attempts}: {e}")
                    if self._is_last_attempt(outer_retry, inner_retry):
                        return 500, f"Request failed: {str(e)}"

                sleep(self.retry_delay)

            # Long delay between outer retry cycles
            if outer_retry < self.max_retries - 1:
                logger.error(f"Failed to contact database {url}, pausing before retry.")
                sleep(self.long_delay)

        return 503, "Service unavailable after all retry attempts"

    def _handle_response(self, response, is_error: bool = False) -> Tuple[int, Any]:
        """Extract data from response based on status code and content type."""
        try:
            json_data = response.json()
            if response.status_code == 404 or is_error:
                return response.status_code, json_data.get('message', json_data)
            return response.status_code, json_data.get('data', json_data)
        except ValueError:  # JSON decode error
            return response.status_code, response.text

    def _extract_error_message(self, response) -> str:
        """Extract error message from response."""
        try:
            return response.json().get('message', f'HTTP {response.status_code}')
        except ValueError:
            return f'HTTP {response.status_code}: {response.text}'

    def _is_last_attempt(self, outer_retry: int, inner_retry: int) -> bool:
        """Check if this is the final retry attempt."""
        return outer_retry == self.max_retries - 1 and inner_retry == 4