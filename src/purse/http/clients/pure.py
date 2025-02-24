import http.client
from http.client import HTTPException
from typing import Optional
from urllib.parse import urlencode

import purse.json
from purse.http.clients.base import BaseClient

hmap = {
    ""
}


class Response:
    """Typed response"""

    def __init__(self, response: http.client.HTTPResponse):
        self._response = response

    status = property(lambda self: self._response.status)
    headers = property(lambda self: self._response.headers)
    url = property(lambda self: self._response.url)

    @property
    def content_type(self):
        """Return the content type of the response"""
        return self._response.getheader("content-type")

    @property
    def data(self):
        """Return appropriate data of a response"""
        payload = self._response.read().decode("utf-8")
        if not self._response.getheader('content-length'):
            return payload
        if self.content_type == "application/json":
            return purse.json.loads(payload)
        return payload


class StatusCodeException(HTTPException):
    """Status code exception"""

    def __init__(self, *, response: "Response"):
        self.response = response

    def __str__(self):
        return f'request to {self.response.url} failed with status code {self.response.status}'


class SimpleHttpClient(BaseClient):

    def _get_connection(self):
        """Create and return an HTTP connection."""
        return {
            True: http.client.HTTPSConnection,
            False: http.client.HTTPConnection,
        }[self.use_ssl](self.host, port=self.port)

    def request(self, method, url, data=None, headers=None, params=None):
        """Send an HTTP request."""
        connection = self._get_connection()
        if headers is None:
            headers = {}
        if params is not None:
            url += '?' + urlencode(params)
        if data is not None:
            # we are using purse.json for encoding Decimals, dates, UUIDs on fly
            data = purse.json.dumps(data)

        connection.request(method, url, body=data, headers=headers)
        response = connection.getresponse()
        response.url = url
        return self._handle_response(Response(response))

    def get(self, url, params: Optional[dict] = None, headers: Optional[dict] = None):
        """Send a GET request to the specified path."""
        return self.request("GET", url, params=params, headers=headers)

    def post(self, path, data: Optional[dict] = None, headers: Optional[dict] = None):
        """Send a POST request to the specified path."""
        if headers is None:
            headers = {"Content-type": "application/json"}
        return self.request("POST", path, data=data, headers=headers)

    @classmethod
    def _handle_response(cls, response: Response) -> str:
        """Handle the HTTP response."""
        if response.status >= 400:
            raise StatusCodeException(response=response)
        return response.data
