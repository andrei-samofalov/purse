import logging
from logging.config import dictConfig
from typing import Optional, Iterable

default_logger = logging.getLogger('asutils')

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
    }
}
_empty_iterable = frozenset()


def make_config_dict(log_level: int | str) -> dict:
    """Make default config with provided log level"""
    conf = DEFAULT_CONFIG.copy()
    conf['loggers']['']['level'] = logging.getLevelName(log_level)
    return DEFAULT_CONFIG


def setup_logging(
    config_dict: Optional[dict] = None,
    *,
    mute_loggers: Iterable[str] = _empty_iterable,
) -> None:
    """Setup logging configuration"""
    config_dict = config_dict or make_config_dict(log_level=logging.INFO)
    for logger_name in mute_loggers:
        config_dict['loggers'].setdefault(logger_name, {})['level'] = "WARNING"

    dictConfig(config=config_dict)
