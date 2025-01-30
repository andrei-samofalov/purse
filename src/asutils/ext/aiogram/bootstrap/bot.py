import contextlib
from typing import Optional, Iterable

from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.session.base import BaseSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import BaseStorage

try:
    from aiogram import Bot, Dispatcher, Router, BaseMiddleware

except ImportError:
    raise ImportError('aiogram is not installed')

_empty_iterable = frozenset()


def get_dispatcher(
    *routes: Router,
    name: Optional[str] = None,
    storage: Optional[BaseStorage] = None,
    middlewares: Iterable[type[BaseMiddleware]] = _empty_iterable,
) -> Dispatcher:
    """Setup and return aiogram.Dispatcher"""
    dp = Dispatcher(storage=storage, name=name)
    for middleware in middlewares:
        dp.update.middleware(middleware())

    setup_routers(dp, *routes)

    return dp


def setup_routers(dp: Dispatcher, *routers: Router) -> None:
    """Include routers to dispatcher parent router"""
    dp.include_routers(*routers)


def get_bot(
    token: str,
    session: Optional[BaseSession] = None,
    parse_mode: Optional[ParseMode] = ParseMode.HTML,
):
    """Create and return an aiogram.Bot."""
    return Bot(
        token=token,
        session=session,
        default=DefaultBotProperties(parse_mode=parse_mode),
    )


@contextlib.asynccontextmanager
async def bot_context(token: str, parse_mode: Optional[ParseMode] = ParseMode.HTML):
    """Async context manager for aiogram.Bot."""
    async with AiohttpSession() as session:
        yield get_bot(token, session=session, parse_mode=parse_mode)
