import abc
from typing import Optional


class BaseClient(metaclass=abc.ABCMeta):
    """Abstract base class for clients."""

    def __init__(self, host: str, port: int = 80, use_ssl=True):
        self.host = host.removeprefix('https://').removeprefix('http://')
        self.port = port if not use_ssl else 443
        self.use_ssl = use_ssl

    @abc.abstractmethod
    def request(self, method, url, data=None, headers=None, params=None):
        """Send an HTTP request."""

    def get(self, url, params: Optional[dict] = None, headers: Optional[dict] = None):
        """Send a GET request to the specified path."""
        return self.request("GET", url, params=params, headers=headers)

    def post(self, url, data: Optional[dict] = None, headers: Optional[dict] = None):
        """Send a POST request to the specified path."""
        if headers is None:
            headers = {"Content-type": "application/json"}
        return self.request("POST", url, data=data, headers=headers)
