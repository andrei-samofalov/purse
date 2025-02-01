import logging
from logging.config import dictConfig
from typing import Optional, Iterable

from purse.logging.logconfig import TelegramHandlerProvider, make_config_dict
from purse.logging.telegram import TelegramHandler, SimpleLoggingBot

__all__ = [
    "TelegramHandler",
    "SimpleLoggingBot",
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


def setup(
    config_dict: Optional[dict] = None,
    log_level: Optional[int | str] = None,
    *,
    enable_telegram: bool = True,
    telegram_handler_provider: Optional[TelegramHandlerProvider] = None,
    mute_loggers: Iterable[str] = _empty_iterable,
) -> None:
    """Setup logging configuration"""

    if enable_telegram:
        assert telegram_handler_provider is not None, \
            "you must provide `telegram_handler_provider` if `enable_telegram` is True"

    config_dict = config_dict or make_config_dict(
        log_level=log_level or logging.DEBUG,
        enable_telegram=enable_telegram,
        telegram_handler_provider=telegram_handler_provider,
    )
    if mute_loggers is _empty_iterable:
        mute_loggers = _default_mute

    for logger_name in mute_loggers:
        config_dict['loggers'].setdefault(logger_name, {})['level'] = "WARNING"

    dictConfig(config=config_dict)
