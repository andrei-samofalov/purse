import io
import logging
import queue
import sys
import threading
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Generator, Optional, Protocol

from purse import datetime as dt
from purse.http.clients import get_default_http_client
from purse.signals import prepare_shutdown

ChatId = int | str


class StopEvent(Protocol):
    """Stop event protocol"""

    def is_set(self) -> bool:
        """Return True if internal flag was set"""


class BotProtocol(Protocol):
    """Sync bot protocol"""

    def send_log(self, chat_id: ChatId, text: str, disable_notification: bool, parse_mode: str):
        """Send a log message"""


@dataclass(slots=True, kw_only=True)
class BotTask:
    """Bot task data"""
    message: str
    chat_id: Optional[ChatId] = None
    format_python: bool = True
    mute: bool | Callable[[], bool] = True
    parse_mode: str = "MARKDOWN"

    def __post_init__(self):
        if callable(self.mute):
            self.mute = self.mute()

    def text_parts(self) -> Generator[str, None, None]:
        """Return list of telegram-accepted length of message"""
        text = self.message
        if len(text) > 3000:
            while text:
                part, text = text[:3000], text[3000:]
                yield part
        else:
            yield text


class SimpleLoggingBot(BotProtocol):
    """Simple http.client implementation telegram bot"""

    def __init__(self, token: str):
        self._path = f"/bot{token}"
        self._transport = get_default_http_client()(host='api.telegram.org', use_ssl=True)

    def send_log(self, chat_id: ChatId, text: str, disable_notification: bool, parse_mode: str):
        """Send a log message blocking"""
        self.send_message(
            chat_id=chat_id,
            text=text,
            disable_notification=disable_notification,
            parse_mode=parse_mode,
            disable_web_page_preview=True,
        )

    def send_message(self, chat_id: ChatId, text: str, **kwargs) -> Any:
        """Send a message"""
        try:
            return self._transport.post(
                f"{self._path}/sendMessage",
                data={"text": text, "chat_id": chat_id, **kwargs},
                headers={"Content-Type": "application/json"},
            )
        except Exception as e:
            print(f"Failed to send message to {chat_id}: {e}\n{format_exception(*sys.exc_info())}")


class TelegramLogger(logging.Logger):
    """Telegram adapted logger"""

    def __init__(
        self,
        tg_handler: "TelegramHandler",
        dev_chat_id: Optional[ChatId] = None,
        name: str = 'purse',
        level: int | str = logging.ERROR,
    ):
        super().__init__(name, level)

        self.tg_handler = tg_handler
        self._dev_chat_id = dev_chat_id

    def exception(self, msg, *args, to_dev=False, **kwargs):
        super().exception(msg, *args, **kwargs)
        if to_dev:
            self.to_dev(self._format_error(msg, *args))

    def error(self, msg, *args, to_dev=False, **kwargs):
        super().error(msg, *args, **kwargs)
        if to_dev:
            self.to_dev(self._format_error(msg, *args))

    @classmethod
    def _format_error(cls, err: object, *args) -> str:
        if isinstance(err, BaseException):
            return str(err)
        if isinstance(err, str):
            if args:
                return err % args
            return err

        raise TypeError(err)

    def to_tg(self, message: str, chat_id: Optional[ChatId] = None):
        """Send message to telegram."""
        self.tg_handler.add_to_queue(
            task=BotTask(message=message, chat_id=chat_id, format_python=False)
        )

    def to_dev(self, message: str):
        """Shortcut for developer telegram notify"""
        assert self._dev_chat_id is not None
        self.to_tg(message, chat_id=self._dev_chat_id)

    def start(self):
        """Start telegram handler."""
        self.tg_handler.start()


class TelegramHandler(logging.StreamHandler):
    """Telegram logging handler"""

    def __init__(
        self,
        bot: BotProtocol,
        log_chat_id: ChatId,
        send_delay: float,
        parent_logger: Optional[TelegramLogger] = None,
        parse_mode: str = 'MARKDOWN',
        service_name: Optional[str] = None,
        stop_event: Optional[StopEvent] = None,
    ):
        super().__init__(stream=sys.stderr)
        self._bot = bot
        self._log_chat_id = log_chat_id
        self._send_delay = send_delay
        self._service_text_prefix = f"Service {service_name.upper()}" if service_name else ''
        self._default_parse_mode = parse_mode.upper()
        self._parent_logger = parent_logger

        self._queue: queue.Queue[BotTask] = queue.Queue()
        self._stop_event = stop_event or prepare_shutdown
        self._started = False
        self._last_sent: Optional[datetime] = dt.utcnow()
        self.setLevel(logging.ERROR)
        self.createLock()

    def emit(self, record: logging.LogRecord):
        """Send the specified logging record to the telegram chat."""
        log_entry = self.format(record)
        self.add_to_queue(task=BotTask(message=log_entry))

    def add_to_queue(self, task: BotTask):
        """Add message to queue."""
        self._queue.put(task)

    def _queue_worker(self):
        while not self._stop_event.is_set():
            try:
                if (elapsed := dt.utcnow() - self._last_sent) < timedelta(self._send_delay):
                    sleep_for = self._send_delay - elapsed.seconds
                    time.sleep(sleep_for)

                task = self._queue.get()

                for text in task.text_parts():
                    if task.format_python:
                        text = f'```python {self._service_text_prefix}\n\n {text}```'
                    else:
                        text = f'{self._service_text_prefix}: \n\n`{text.capitalize()}`'

                    self._bot.send_log(
                        chat_id=task.chat_id or self._log_chat_id,
                        text=text,
                        disable_notification=task.mute,
                        parse_mode=task.parse_mode or self._default_parse_mode,
                    )

                    self._last_sent = dt.utcnow()

            except Exception as e:
                logging.log(logging.ERROR, f"Failed to send message: {e}")

    def set_parent_logger(self, logger: TelegramLogger):
        """Set parent Telegram logger."""
        self._parent_logger = logger

    def start(self):
        """Start working queue"""
        if not self._started:
            threading.Thread(target=self._queue_worker, name='tg_log', daemon=True).start()
            self._last_sent = dt.utcnow()
            self._started = True

        return self._started


def configure_bot_exception_hook(tg_logger: TelegramLogger):
    """Configure Logging handler to emit application exceptions to telegram"""

    import sys

    # restart logger
    tg_logger.start()

    def _bot_hook(exc_type, exc_value, exc_traceback):
        text = format_exception(exc_type, exc_value, exc_traceback)
        sys.stderr.write(text)
        tg_logger.to_dev(text)

    sys.excepthook = _bot_hook


def format_exception(exc_type, exc_value, exc_traceback):
    """
    Format and return the specified exception information as a string.

    This default implementation just uses
    traceback.print_exception()
    """
    sio = io.StringIO()
    traceback.print_exception(exc_type, exc_value, exc_traceback, -1, sio)
    sval = sio.getvalue()
    sio.close()

    return sval
