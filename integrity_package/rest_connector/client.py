from abc import ABC, abstractmethod
from typing import Tuple, Any


class HttpClient(ABC):
    @abstractmethod
    def post(self, url: str, json_data: dict) -> Tuple[int, Any]:
        pass

    @abstractmethod
    def get(self, url: str, params: dict = None) -> Tuple[int, Any]:
        pass


class RequestsHttpClient(HttpClient):
    def __init__(self, max_retries: int = 3, retry_delay: int = 5, long_delay: int = 60):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.long_delay = long_delay

    def post(self, url: str, json_data: dict) -> Tuple[int, Any]:
        return self._make_request('post', url, json_data)

    def get(self, url: str, params: dict = None) -> Tuple[int, Any]:
        return self._make_request('get', url, params)

    def _make_request(self, method: str, url: str, data: dict = None) -> Tuple[int, Any]:
        import requests
        from time import sleep

        for i in range(self.max_retries):
            for j in range(5):
                try:
                    if method == 'post':
                        response = requests.post(url, json=data)
                    elif method == 'get':
                        response = requests.get(url, params=data)
                    else:
                        return 405, f"'{method}' is not an allowed method."

                except requests.exceptions.RequestException as e:
                    print(f"Request exception: {e}")
                    return 0, e

                if response.status_code == 200:
                    return response.status_code, response.json().get('data')
                if response.status_code == 404:
                    return response.status_code, response.json().get('message')

                print(f"ERROR: Unable to contact database on attempt #{i * 5 + j + 1}")
                print(f"ERROR {response.status_code}, {response.json().get('message')}")
                sleep(self.retry_delay)

            print(f"ERROR: Failed to contact database {url}, pausing.")
            sleep(self.long_delay)

        exit(69)  # Service unavailable
