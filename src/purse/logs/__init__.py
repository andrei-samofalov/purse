import functools
import logging
from dataclasses import dataclass
import logging.config as _logging_config
from typing import Iterable, Optional

from purse.logs._internal import logger_factory
from purse.logs.logconfig import DEFAULT_FORMAT, make_config_dict
from purse.logs.telegram import (
    BotProtocol,
    ChatId,
    SimpleLoggingBot,
    StopEvent,
    TelegramHandler,
    TelegramLogger,
    configure_bot_exception_hook,
)

__all__ = [
    "TelegramHandler",
    "SimpleLoggingBot",
    "TelegramSetup",
    'default_logger',
    'logger_factory',
    'setup',
]

default_logger = logger_factory('purse')

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
    logger_name: str = 'purse'
    parse_mode: str = 'MARKDOWN'
    logger_level: int | str = logging.INFO
    stop_event: Optional[StopEvent] = None

    def __post_init__(self):
        self.dev_chat_id = self.dev_chat_id or self.log_chat_id


def get_default_logger_name():
    """Return logger name"""
    import pathlib
    f_name = logging.currentframe().f_back.f_code.co_filename
    return pathlib.Path(f_name).stem


def _cut_dev(logger_cls: logging.Logger):
    cutter = {"error", "info", "debug", "exception"}

    def _nope(*args, mthd, **kwargs):
        logging.log(
            logging.WARNING,
            msg=f'telegram logger was not configured, so {mthd!r} method would not work properly.'
        )

    def _patched(fn):
        @functools.wraps(fn)
        def _wrapper(*args, **kwargs):
            if kwargs.pop('to_dev', None):
                _nope(mthd=fn.__name__)
            return fn(*args, **kwargs)

        return _wrapper

    for mthd_name in dir(logger_cls):
        if mthd_name not in cutter:
            continue
        method = getattr(logger_cls, mthd_name)
        setattr(logger_cls, mthd_name, _patched(method))

    for banned_mthd in {'to_dev', 'to_tg'}:
        setattr(
            logger_cls, banned_mthd,
            lambda *args, **kwargs: _nope(*args, mthd=banned_mthd, **kwargs)
        )

    return logger_cls


def setup(
    config_dict: Optional[dict] = None,
    log_level: Optional[int | str] = None,
    *,
    telegram_setup: Optional[TelegramSetup] = None,
    mute_loggers: Iterable[str] = _empty_iterable,
) -> Optional[TelegramLogger]:
    """Setup logging configuration"""

    def _get_handler() -> Optional[TelegramHandler]:
        if not telegram_setup:
            return None

        return TelegramHandler(
            bot=telegram_setup.bot,
            log_chat_id=telegram_setup.log_chat_id,
            send_delay=telegram_setup.send_delay,
            stop_event=telegram_setup.stop_event,
            parse_mode=telegram_setup.parse_mode,
            service_name=telegram_setup.service_name,
        )

    handler_provider = _get_handler if telegram_setup else None
    config_dict = config_dict or make_config_dict(
        log_level=log_level or logging.DEBUG,
        telegram_handler_provider=handler_provider,
    )

    if mute_loggers is _empty_iterable:
        mute_loggers = _default_mute

    for logger_name in mute_loggers:
        config_dict['loggers'].setdefault(logger_name, {})['level'] = logging.ERROR

    tg_logger = _cut_dev(logging.root)
    if telegram_setup:
        tg_handler = _get_handler()
        tg_logger = TelegramLogger(
            tg_handler=tg_handler,
            dev_chat_id=telegram_setup.dev_chat_id,
            name=telegram_setup.logger_name,
            level=telegram_setup.logger_level,
        )
        tg_logger.addHandler(tg_handler)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(telegram_setup.logger_level)
        stream_handler.setFormatter(
            logging.Formatter(fmt=DEFAULT_FORMAT)
        )
        tg_logger.addHandler(stream_handler)
        tg_handler.start()

        configure_bot_exception_hook(tg_logger)

    _logging_config.dictConfig(config=config_dict)
    return tg_logger
