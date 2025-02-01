import http.client
import json
from typing import Optional
from urllib.parse import urlencode

from purse.http.clients.base import BaseClient


class SimpleHttpClient(BaseClient):

    def _get_connection(self):
        """Create and return an HTTP connection."""
        if self.use_ssl:
            return http.client.HTTPSConnection(self.host, self.port)
        else:
            return http.client.HTTPConnection(self.host, self.port)

    def request(self, method, url, data=None, headers=None, params=None):
        """Send an HTTP request."""
        connection = self._get_connection()
        if headers is None:
            headers = {}
        if params is not None:
            url += '?' + urlencode(params)
        if data is not None:
            data = json.dumps(data)
        connection.request(method, url, body=data, headers=headers)
        response = connection.getresponse()
        return self._handle_response(response)

    def get(self, url, params: Optional[dict] = None, headers: Optional[dict] = None):
        """Send a GET request to the specified path."""
        return self.request("GET", url, params=params, headers=headers)

    def post(self, path, data: Optional[dict] = None, headers: Optional[dict] = None):
        """Send a POST request to the specified path."""
        if headers is None:
            headers = {"Content-type": "application/json"}
        return self.request("POST", path, data=data, headers=headers)

    @classmethod
    def _handle_response(cls, response: http.client.HTTPResponse) -> str:
        """Handle the HTTP response."""
        if response.status != 200:
            raise Exception(f"Request failed with status {response.status}")
        return response.read().decode()
