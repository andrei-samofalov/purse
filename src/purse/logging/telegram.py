import logging
import queue
import sys
from collections.abc import Callable
from datetime import timedelta
from threading import Thread
from typing import Generator, Optional, Any, Protocol

from purse import system, datetime as dt
from purse.http.clients import get_default_http_client
from purse.signals import prepare_shutdown

LAST_SENT = None
ChatId = int | str


class BotProtocol(Protocol):
    """Sync bot protocol"""

    def send_log(self, chat_id: ChatId, text: str, disable_notification: bool, parse_mode: str):
        """Send a log message"""


class SimpleLoggingBot(BotProtocol):
    """Simple http.client implementation telegram bot"""

    def __init__(self, token: str):
        self._path = f"/bot{token}"
        self._transport = get_default_http_client()(host='api.telegram.org', use_ssl=True)

    def send_log(self, chat_id: ChatId, text: str, disable_notification: bool, parse_mode: str):
        """Send a log message in a thread"""
        Thread(
            target=self.send_message,
            args=(chat_id, text),
            kwargs={
                "disable_notification": disable_notification,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            }
        ).start()

    def send_message(self, chat_id: ChatId, text: str, **kwargs) -> Any:
        """Send a message"""
        return self._transport.post(
            f"{self._path}/sendMessage",
            data={"text": text, "chat_id": chat_id, **kwargs},
            headers={"Content-Type": "application/json"},
        )


class StopEvent(Protocol):

    def is_set(self) -> bool: ...


class TelegramLogger(logging.Logger):
    """Telegram adapted logger"""

    def __init__(
        self,
        tg_handler: "TelegramHandler",
        dev_chat_id: Optional[ChatId] = None,
        name: str = 'asutils',
        level=logging.INFO,
        stop_event: Optional[StopEvent] = prepare_shutdown
    ):
        super().__init__(name, level)

        self.tg_handler = tg_handler
        self._stop_event = stop_event
        self._dev_chat_id = dev_chat_id
        self._msg_queue = queue.Queue()

        self._started = False

    def _worker(self):
        while not self._stop_event.is_set():
            print('waiting for message...')
            msg, chat_id = self._msg_queue.get()
            print('received message: {}'.format(msg))
            self.tg_handler.to_tg(msg, chat_id=chat_id)

    def to_tg(self, msg: str, chat_id: Optional[str | int] = None):
        """Send message to telegram."""
        if not self._started:
            cmd = system.get_start_cmd()
            return sys.stderr.write(
                f"telegram logger not started\n({cmd})\n\n{msg}"
            )
        self._msg_queue.put((msg, chat_id))

    def to_dev(self, msg: str):
        """Shortcut отправки сообщения в телегу разработчику"""
        assert self._dev_chat_id is not None
        self.to_tg(msg, chat_id=self._dev_chat_id)

    def start(self):
        """Start working queue"""
        if not self._started:
            Thread(target=self._worker, name='tg_log', daemon=True).start()
            self._started = True

        return self._started


class TelegramHandler(logging.Handler):
    """Telegram logging handler"""

    def __init__(
        self,
        bot: BotProtocol,
        notify_chat_id: int | str,
        parse_mode: str = 'MARKDOWN',
        send_delay: float = 4,
        service_name: Optional[str] = None,
        level=logging.NOTSET,
    ):
        self._bot = bot
        self._notify_chat_id = notify_chat_id
        self._send_delay = send_delay
        self._service_text_prefix = f"Service {service_name.upper()}" if service_name else ''
        self._default_parse_mode = parse_mode.upper()
        super().__init__(level)

    def emit(self, record: logging.LogRecord):
        """Send the specified logging record to the telegram chat."""
        log_entry = self.format(record)
        try:
            self._send_bot_notification(text=log_entry)
        except Exception as ex:
            print(ex)

    def send_log(self, msg: str):
        """Send the specified message to the telegram chat."""
        if not msg:
            return print('message is empty')

        try:
            self._send_bot_notification(text=msg)
        except Exception as ex:
            print(ex)

    def _send_bot_notification(
        self,
        text,
        is_python: bool = True,
        mute: bool | Callable[[], bool] = True,
        **kwargs
    ):
        """Async bot notification"""

        chat_id = kwargs.get('chat_id', self._notify_chat_id)
        parse_mode = kwargs.pop('parse_mode', self._default_parse_mode)
        mute = mute if not callable(mute) else mute()

        global LAST_SENT

        for text in _get_parts(text):
            now = dt.utcnow()
            if LAST_SENT:
                while now - LAST_SENT < timedelta(seconds=self._send_delay):
                    continue

            if is_python:
                text = f'```python {self._service_text_prefix}\n\n {text}```'
            else:
                text = f'{self._service_text_prefix}: \n\n`{text.capitalize()}`'

            self._bot.send_log(
                chat_id=chat_id,
                text=text,
                disable_notification=mute,
                parse_mode=parse_mode,
            )

            LAST_SENT = now

    def to_tg(self, message, **kwargs):
        """Отправляет сообщение посредством бота напрямую"""
        self._send_bot_notification(text=message, is_python=False, **kwargs)


def _get_parts(text: str) -> Generator[str, None, None]:
    """Return list of telegram-accepted length of message"""
    if len(text) > 3000:

        while text:
            part, text = text[:3000], text[3000:]
            yield part
    else:
        yield text


def configure_bot_exception_hook(tg_handler: TelegramHandler):
    """Configure Logging handler to emit application exceptions to telegram"""
    import io
    import traceback
    import sys

    def format_exception(exc_type, exc_value, exc_traceback):
        """
        Format and return the specified exception information as a string.

        This default implementation just uses
        traceback.print_exception()
        """

        with io.StringIO() as sio:
            traceback.print_exception(exc_type, exc_value, exc_traceback, -1, sio)
        return sio.read()

    def _bot_hook(exc_type, exc_value, exc_traceback):
        text = format_exception(exc_type, exc_value, exc_traceback)
        sys.stderr.write(text)
        tg_handler.send_log(text)

    sys.excepthook = _bot_hook
