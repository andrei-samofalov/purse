import asyncio
import inspect
import logging
import warnings
from collections.abc import Coroutine, Hashable
from typing import Optional

from purse.logging import default_logger

warnings.filterwarnings("ignore", category=RuntimeWarning)


class Waiter:
    """Waiter service"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or default_logger
        self._waiters: dict[int, asyncio.Task] = {}

    def add(
        self,
        coro: Coroutine,
        timeout: float,
        identity: Optional[Hashable] = None,
    ):
        """Add a coroutine to the waiters."""
        waiter_id = identity or id(coro)
        # cancel waiter if present
        self.cancel(waiter=waiter_id, reason='re-adding')

        async def _wait():
            try:
                await asyncio.sleep(timeout)
                await coro

            except asyncio.CancelledError:
                coro.close()
            except Exception as e:
                raise e
            finally:
                self.cancel(waiter_id, reason="task done")

        self._logger.info(f'added {coro} to waiters as {waiter_id}')
        self._waiters[waiter_id] = asyncio.create_task(_wait())

    def cancel(self, waiter: Hashable | Coroutine, reason: Optional[str] = 'not provided'):
        """Cancel the waiter."""
        if inspect.iscoroutine(waiter):
            waiter = id(waiter)

        if (task := self._waiters.pop(waiter, None)) is not None:
            task.cancel()
            self._logger.info(f'task {task} ({waiter}) was canceled: {reason}')

        else:
            self._logger.info(f'no task for {waiter}: {reason}')
