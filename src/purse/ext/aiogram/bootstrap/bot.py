import asyncio
import contextlib
import warnings
from typing import Optional, Reversible

from aiogram import BaseMiddleware, Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.session.base import BaseSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import BaseStorage

from purse.logging import logger_factory
from purse.signals import prepare_shutdown, shutdown_complete

logger = logger_factory('ext.aiogram.bot', include_project=True)
_empty_iterable = frozenset()


def get_dispatcher(
    *routes: Router,
    name: Optional[str] = None,
    storage: Optional[BaseStorage] = None,
    middlewares: Reversible[type[BaseMiddleware]] = _empty_iterable,
    update_middlewares: Reversible[type[BaseMiddleware]] = _empty_iterable,
    message_middlewares: Reversible[type[BaseMiddleware]] = _empty_iterable,
    query_middlewares: Reversible[type[BaseMiddleware]] = _empty_iterable,
) -> Dispatcher:
    """Setup and return aiogram.Dispatcher"""
    if middlewares:
        warnings.warn(
            "middlewares parameter is deprecated, use update_middlewares instead",
            DeprecationWarning,
        )
        update_middlewares = middlewares

    dp = Dispatcher(storage=storage, name=name)
    for middleware in reversed(update_middlewares):
        dp.update.middleware(middleware())

    for middleware in message_middlewares:
        dp.message.middleware(middleware())

    for middleware in query_middlewares:
        dp.callback_query.middleware(middleware())

    setup_routers(dp, *routes)

    return dp


def setup_routers(dp: Dispatcher, *routers: Router) -> None:
    """Include routers to dispatcher parent router"""
    dp.include_routers(*routers)


class SessionFactory:
    """Self-closing AiohttpSession factory (singleton though)"""

    def __init__(
        self,
        prepare_shutdown_event: Optional[asyncio.Event] = None,
        shutdown_complete_event: Optional[asyncio.Event] = None,
    ) -> None:
        self._shutdown_event = prepare_shutdown_event or prepare_shutdown
        self._shutdown_complete = shutdown_complete_event or shutdown_complete
        self._session: Optional[AiohttpSession] = None

    def get_session(self):
        """Return aiogram session, which be closed when prepare shutdown event would be set"""
        if self._session is None:
            self._session = AiohttpSession()

            async def _close_session():
                logger.info('session close scheduled.')
                await self._shutdown_event.wait()
                await self._session.close()
                logger.info('global session closed.')
                self._shutdown_complete.set()

            asyncio.shield(asyncio.create_task(_close_session()))

        return self._session


session_factory = SessionFactory()


def get_bot(
    token: str,
    session: Optional[BaseSession] = None,
    parse_mode: Optional[ParseMode] = ParseMode.HTML,
):
    """Create and return an aiogram.Bot."""
    return Bot(
        token=token,
        session=session or session_factory.get_session(),
        default=DefaultBotProperties(parse_mode=parse_mode),
    )


@contextlib.asynccontextmanager
async def bot_context(token: str, parse_mode: Optional[ParseMode] = ParseMode.HTML):
    """Async context manager for aiogram.Bot."""
    async with AiohttpSession() as session:
        yield get_bot(token, session=session, parse_mode=parse_mode)
