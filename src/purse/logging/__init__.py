import logging
from dataclasses import dataclass
from logging.config import dictConfig
from typing import Optional, Iterable

from purse.logging.logconfig import TelegramHandlerProvider, make_config_dict
from purse.logging.telegram import (
    TelegramLogger,
    TelegramHandler, SimpleLoggingBot, configure_bot_exception_hook, ChatId, StopEvent, BotProtocol
)

__all__ = [
    "TelegramHandler",
    "SimpleLoggingBot",
    "TelegramSetup",
    'default_logger',
    'setup',
]

default_logger = logging.getLogger('asutils')
_empty_iterable = object()
_default_mute = {
    'asyncio',
    'aiogram.event',
    'aiohttp.access',
    'httpcore',
    'httpx',
}


@dataclass(slots=True, kw_only=True)
class TelegramSetup:
    """Telegram setup"""
    bot: BotProtocol

    log_chat_id: ChatId
    dev_chat_id: Optional[ChatId] = None
    send_delay: float = 1

    service_name: str
    logger_name: str = 'asutils'
    parse_mode: str = 'MARKDOWN'
    logger_level: int | str = logging.INFO
    stop_event: Optional[StopEvent] = None

    def __post_init__(self):
        self.dev_chat_id = self.dev_chat_id or self.log_chat_id


def setup(
    config_dict: Optional[dict] = None,
    log_level: Optional[int | str] = None,
    *,
    telegram_setup: Optional[TelegramSetup] = None,
    mute_loggers: Iterable[str] = _empty_iterable,
) -> Optional[TelegramLogger]:
    """Setup logging configuration"""

    tg_handler = TelegramHandler(
        bot=telegram_setup.bot,
        log_chat_id=telegram_setup.log_chat_id,
        send_delay=telegram_setup.send_delay,
        stop_event=telegram_setup.stop_event,
        parse_mode=telegram_setup.parse_mode,
        service_name=telegram_setup.service_name,
        level=logging.ERROR,
    ) if telegram_setup else None

    config_dict = config_dict or make_config_dict(
        log_level=log_level or logging.DEBUG,
        telegram_handler_provider=lambda: tg_handler,
    )
    if mute_loggers is _empty_iterable:
        mute_loggers = _default_mute

    for logger_name in mute_loggers:
        config_dict['loggers'].setdefault(logger_name, {})['level'] = logging.ERROR

    dictConfig(config=config_dict)

    if telegram_setup:
        tg_logger = TelegramLogger(
            tg_handler=tg_handler,
            dev_chat_id=telegram_setup.dev_chat_id,
            name=telegram_setup.logger_name,
            level=telegram_setup.logger_level,
        )
        tg_handler.set_parent_logger(tg_logger)
        tg_handler.start()

        configure_bot_exception_hook(tg_logger)
        return tg_logger
