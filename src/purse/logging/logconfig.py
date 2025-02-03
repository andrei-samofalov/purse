import logging
from collections.abc import Callable
from typing import Optional

from purse.logging import telegram as tg_base

TelegramHandlerProvider = Callable[[], tg_base.TelegramHandler]

DEFAULT_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '[%(asctime)s] %(levelname)-5s | %(name)s:%(lineno)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'loggers': {
        'root': {
            'level': "DEBUG",
            'handlers': [
                'console',
            ],
            'propagate': False,
        },
        'asyncio': {
            'level': 'ERROR',
        },
        'aiogram.event': {
            'level': 'ERROR',
        },
        'aiohttp.access': {
            'level': 'ERROR',
        },
        'httpcore': {
            'level': 'ERROR',
        },
    }
}

TELEGRAM_CONF = {
    'level': 'ERROR',
    'formatter': 'console',
    '()': TelegramHandlerProvider,
}


def make_config_dict(
    log_level: int | str = logging.DEBUG,
    telegram_handler_provider: Optional[TelegramHandlerProvider] = None,
) -> dict:
    """Make default config with provided log level"""
    conf = DEFAULT_CONFIG.copy()

    if telegram_handler_provider:
        telegram_conf = TELEGRAM_CONF.copy()
        telegram_conf["()"] = telegram_handler_provider
        conf['handlers']['telegram'] = telegram_conf
        conf['loggers']['root']['handlers'].append('telegram')

    conf['loggers']['root']['level'] = logging.getLevelName(log_level)
    return conf
