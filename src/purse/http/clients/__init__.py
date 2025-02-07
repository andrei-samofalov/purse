from purse.http.clients.base import BaseClient

httpx_installed = True
try:
    import httpx  # noqa: F401
except ImportError:
    httpx_installed = False

requests_installed = True
try:
    import requests  # noqa: F401
except ImportError:
    requests_installed = False


def get_default_http_client(use_simple: bool = False) -> type[BaseClient]:
    """Return the default http client depended on installed packages."""

    if use_simple:
        from .pure import SimpleHttpClient
        return SimpleHttpClient

    if httpx_installed:
        from .httpx import HTTPXClient
        return HTTPXClient

    if requests_installed:
        from .requests import RequestsClient
        return RequestsClient

    from .pure import SimpleHttpClient
    return SimpleHttpClient
