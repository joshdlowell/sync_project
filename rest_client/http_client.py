from abc import ABC, abstractmethod
from typing import Tuple, Any

from .configuration import config, logger


class HttpClient(ABC):

    @abstractmethod
    def post(self, url: str, json_data: dict) -> Tuple[int, Any]:
        pass

    @abstractmethod
    def get(self, url: str, params: dict = None) -> Tuple[int, Any]:
        pass

    @abstractmethod
    def patch(self, url: str, json_data: dict = None) -> Tuple[int, Any]:
        pass


class RequestsHttpClient(HttpClient):
    def __init__(self):
        self.max_retries = config.get('max_retries')
        self.retry_delay = config.get('retry_delay')
        self.long_delay = config.get('long_delay')

    def post(self, url: str, json_data: dict) -> Tuple[int, Any]:
        return self._make_request('post', url, json_data)

    def get(self, url: str, params: dict = None) -> Tuple[int, Any]:
        return self._make_request('get', url, params)

    def patch(self, url: str, json_data: dict = None) -> Tuple[int, Any]:
        return self._make_request('patch', url, json_data)

    def _make_request(self, method: str, url: str, data: dict = None) -> Tuple[int, Any]:
        import requests
        from time import sleep

        for i in range(self.max_retries):
            for j in range(5):
                try:
                    if method == 'post':
                        response = requests.post(url, json=data, timeout=30)  # Add timeout
                    elif method == 'get':
                        response = requests.get(url, params=data, timeout=30)  # Add timeout
                    elif method == 'patch':
                        response = requests.patch(url, json=data, timeout=30)  # Add timeout
                    else:
                        return 405, f"'{method}' is not an allowed method."

                    # Handle successful responses
                    if response.status_code == 200:
                        try:
                            return response.status_code, response.json().get('data')
                        except ValueError:  # JSON decode error
                            return response.status_code, response.text

                    # Handle 404 specifically
                    if response.status_code == 404:
                        try:
                            return response.status_code, response.json().get('message')
                        except ValueError:
                            return response.status_code, response.text

                    # Handle other HTTP error codes
                    try:
                        error_message = response.json().get('message', f'HTTP {response.status_code}')
                    except ValueError:
                        error_message = f'HTTP {response.status_code}: {response.text}'

                    logger.warning(f"Unable to contact database on attempt #{i * 5 + j + 1}")
                    logger.warning(f"{response.status_code}, {error_message}")

                except requests.exceptions.Timeout:
                    logger.warning(f"Request timeout on attempt #{i * 5 + j + 1}: {url}")
                    if i == self.max_retries - 1 and j == 4:  # Last attempt
                        return 408, "Request timeout - server did not respond"

                except requests.exceptions.ConnectionError:
                    logger.warning(f"Connection error on attempt #{i * 5 + j + 1}: {url}")
                    if i == self.max_retries - 1 and j == 4:  # Last attempt
                        return 503, "Service unavailable - cannot connect to server"

                except requests.exceptions.RequestException as e:
                    logger.warning(f"Request exception on attempt #{i * 5 + j + 1}: {e}")
                    if i == self.max_retries - 1 and j == 4:  # Last attempt
                        return 500, f"Request failed: {str(e)}"

                sleep(self.retry_delay)

            logger.error(f"Failed to contact database {url}, pausing before retry.")
            sleep(self.long_delay)

        # Return an error status
        return 503, "Service unavailable after all retry attempts"
