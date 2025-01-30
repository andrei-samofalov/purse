import asyncio
import signal
from collections.abc import Callable
from logging import getLogger
from typing import Optional

prepare_shutdown = asyncio.Event()
"""Use this event in your code."""

logger = getLogger('asutils.signals')
HandleShutdownCallable = Callable[[signal.Signals, asyncio.Event], None]


def _default_handle_shutdown(sig: signal.Signals, kill_event: asyncio.Event) -> None:
    """Handle shutdown."""
    prepare_shutdown.set()
    logger.info(f"Received {sig.name}, starting shutdown...")
    kill_event.set()


def create_listeners(handle_shutdown: HandleShutdownCallable):
    """Create loop listeners for SIGINT and SIGTERM."""
    loop = asyncio.get_running_loop()
    kill_event = asyncio.Event()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig,
            handle_shutdown,
            sig, kill_event
        )

    return kill_event


def setup(handle_shutdown_callable: Optional[HandleShutdownCallable] = None):
    """Setup application kill event and return it."""
    return create_listeners(handle_shutdown_callable or _default_handle_shutdown)
