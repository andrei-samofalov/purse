from asutils.logger import default_logger

try:
    from aiohttp import web
except ImportError:
    raise ImportError('aiohttp is not installed.')

try:
    from aiogram.exceptions import TelegramAPIError
    from aiogram import Bot, Dispatcher
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler
except ImportError:
    raise ImportError('aiogram is not installed.')

import logging


async def configure_webhook(
    app: web.Application,
    bot: Bot,
    dp: Dispatcher,
    web_domain: str,
    bot_hook: str = '/bot',
    logger: logging.Logger = default_logger,
) -> None:
    """Configure bot webhook."""
    try:
        await bot.delete_webhook()
        me = await bot.get_me()
    except TelegramAPIError as e:
        exit(e)

    if not bot_hook.startswith('/'):
        bot_hook = f'/{bot_hook}'

    url = f"{web_domain}{bot_hook}"

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

    logger.info(log_msg)
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=bot_hook)
