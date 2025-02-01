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
        '': {
            'level': "DEBUG",
            'handlers': [
                'console',
            ],
            'propagate': False,
        },
        'asyncio': {
            'level': 'WARNING',
        },
        'aiogram.event': {
            'level': 'WARNING',
        },
        'aiohttp.access': {
            'level': 'WARNING',
        },
        'httpcore': {
            'level': 'WARNING',
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
    enable_telegram: bool = True,
    telegram_handler_provider: Optional[TelegramHandlerProvider] = None,
) -> dict:
    """Make default config with provided log level"""
    conf = DEFAULT_CONFIG.copy()

    if enable_telegram:
        telegram_conf = TELEGRAM_CONF.copy()
        telegram_conf["()"] = telegram_handler_provider
        conf['handlers']['telegram'] = telegram_conf
        conf['loggers']['']['handlers'].append('telegram')

        tg_base.configure_bot_exception_hook(
            telegram_handler_provider()
        )

    conf['loggers']['']['level'] = logging.getLevelName(log_level)
    return conf
