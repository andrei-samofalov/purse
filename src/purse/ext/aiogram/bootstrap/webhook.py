import asyncio
import logging
from collections.abc import Callable, Awaitable
from typing import Any, Optional

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError
from aiogram.types import User, BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

from purse import func
from purse.logging import logger_factory

FailureCallable = Callable[[Bot, TelegramAPIError], Any | Awaitable[Any]]
SuccessCallable = Callable[[Bot, User], Any | Awaitable[Any]]

_logger = logger_factory('ext.aiogram', include_project=True)


def _default_on_failure(bot: Bot, error: TelegramAPIError):
    _logger.error(f"couldn't start bot {bot.id}: {error}")


async def setup_webhook(
    app: web.Application,
    bot: Bot,
    dp: Dispatcher,
    web_domain: str,
    bot_hook: str,
    commands: list[BotCommand],
    on_failure: Optional[FailureCallable] = _default_on_failure,
    on_success: Optional[SuccessCallable] = None,
    logger: logging.Logger = _logger,
    timeout: Optional[float] = 3,
) -> None:
    """Configure bot webhook."""
    try:
        me = await bot.get_me()
        await asyncio.wait_for(bot.set_my_commands(commands), timeout)
    except (asyncio.TimeoutError, asyncio.CancelledError, TelegramAPIError) as exc:
        return await func.acall(on_failure, *(bot, exc))

    if not bot_hook.startswith('/'):
        bot_hook = f'/{bot_hook}'

    url = f"{web_domain}{bot_hook}"

    try:
        await bot.delete_webhook()
        webhook_set = await bot.set_webhook(
            url=url,
            drop_pending_updates=True,
            allowed_updates=dp.resolve_used_update_types(),
        )
        log_msg = (
            f"running webhook for bot @{me.username} on {url}"
        )
        if not webhook_set:
            log_msg += " FAILED"

    except TelegramAPIError as exc:
        await func.acall(on_failure, *(bot, exc))
        return logger.error(f"can't start bot {bot.id} {exc}")

    logger.info(log_msg)

    if on_success is not None:
        await func.acall(on_success, *(bot, me))

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=bot_hook)
