from contextlib import suppress
from typing import TypeVar, Literal

from aiogram.enums import ContentType
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import CallbackQuery, Message
from aiogram.utils.formatting import Text

from purse.logging import logger_factory
from purse.typing import LoggerProtocol

_logger = logger_factory('ext.aiogram.bootstrap', include_project=True)

TelegramMessageEvent = TypeVar("TelegramMessageEvent", CallbackQuery, Message)
FormattingMap = Literal['as_html', 'as_markdown', 'as_pretty_string']


async def handle_event(
    event: TelegramMessageEvent,
    logger: LoggerProtocol = _logger,
    text_format: FormattingMap = 'as_html',
    **message_kwargs
):
    """Guarantees message sending by the event type."""
    if (text := message_kwargs.get('text')) and isinstance(text, Text):
        try:
            message_kwargs['text'] = getattr(text, text_format)()
        except Exception as ex:
            logger.error(f"Failed to parse the Text message: {ex}")

    with suppress(TelegramForbiddenError):
        if isinstance(event, Message):
            return await event.answer(**message_kwargs)

        try:
            if event.message.content_type == ContentType.PHOTO:
                message_kwargs['caption'] = message_kwargs.pop('text', None)
                return await event.message.edit_caption(**message_kwargs)
            else:
                return await event.message.edit_text(**message_kwargs)
        except TelegramBadRequest as ex:
            logger.error(ex)
            return await event.message.answer(**message_kwargs)
