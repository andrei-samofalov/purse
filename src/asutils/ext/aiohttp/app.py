from typing import Optional

try:
    from aiohttp import web

except ImportError:
    raise ImportError('aiohttp is not installed.')

from logging import getLogger, Logger

from aiohttp.abc import AbstractRouter
from aiohttp.typedefs import Handler

_logger = getLogger('asutils.aiohttp.app')
AiohttpRoute = tuple[str, str, Handler | AbstractRouter, Optional[str]]


def get_aiohttp_app(*routes: AiohttpRoute, **initkwargs):
    """Create an aiohttp app instance."""
    app = web.Application(**initkwargs)
    setup_routers(app, *routes)
    return app


def setup_routers(app: web.Application, *routes: AiohttpRoute):
    """Setup application routes."""
    for route in routes:
        method, path, handler, name = route
        app.router.add_route(method, path, handler, name=name)


async def listen_and_serve(
    app: web.Application,
    web_host: str,
    web_port: int,
    logger: Logger = _logger,
    handle_signals: bool = True,
) -> None:
    """Start non-blocking web server."""
    runner = web.AppRunner(app, handle_signals=handle_signals)
    await runner.setup()
    site = web.TCPSite(runner, web_host, web_port)
    logger.info(f"running app on {site.name}")

    await site.start()
