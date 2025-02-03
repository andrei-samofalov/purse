from purse import imports
from purse.http.clients.base import BaseClient
from purse.logging import default_logger as logger

imports.ensure_installed("httpx")

import httpx


class HTTPXClient(BaseClient):

    @property
    def _base_url(self):
        port_postfix = "" if not self.port or self.port == 443 else f":{self.port}"
        schema_suffix = "https://" if self.use_ssl else "http://"
        return f"{schema_suffix}{self.host}{port_postfix}"

    def request(self, method, url, data=None, headers=None, params=None):
        if headers is None:
            headers = {}
        if params is None:
            params = {}

        with httpx.Client(base_url=self._base_url, timeout=10) as client:
            response = client.request(method, url, json=data, headers=headers, params=params)
            if response.status_code != httpx.codes.OK:
                logger.error(response.text)
            return response
