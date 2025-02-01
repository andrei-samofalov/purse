from purse import imports
from purse.http.clients import BaseClient

imports.ensure_installed('requests')

import requests


class RequestsClient(BaseClient):

    @property
    def _base_url(self):
        port_postfix = "" if not self.port or self.port == 443 else f":{self.port}"
        schema_suffix = "https://" if self.use_ssl else "http://"
        return f"{schema_suffix}{self.host}{port_postfix}"

    def request(self, method, url, data=None, headers=None, params=None):
        url = f"{self._base_url}{url}"
        return requests.request(method, url, json=data, headers=headers, params=params)
