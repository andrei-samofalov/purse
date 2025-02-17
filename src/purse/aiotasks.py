import asyncio
import unittest
from collections.abc import Callable, Awaitable
from unittest.mock import patch

CoroType = Callable[[asyncio.Event], Awaitable[...]]


def create_shielded_task(coro: CoroType) -> asyncio.Task:
    """Create a shielded task for an infinite-loop coroutine."""
    stop = asyncio.Event()

    async def _wrapper():
        while not stop.is_set():
            try:
                await asyncio.shield(coro(stop))
            except asyncio.CancelledError:
                stop.set()

    return asyncio.create_task(_wrapper())


class Example:
    def __init__(self):
        self._task: asyncio.Task | None = None

    async def _example_worker(self, stop_event: asyncio.Event):
        while not stop_event.is_set():
            await asyncio.sleep(1)
            print("Hello world")

    def start(self):
        self._task = create_shielded_task(self._example_worker)
        print('task started')

    def stop(self):
        if self._task:
            self._task.cancel()
            print('task stopped')


class TestExample(unittest.IsolatedAsyncioTestCase):
    async def test_example(self):
        example = Example()

        with patch("builtins.print") as mock_print:
            example.start()
            await asyncio.sleep(0.1)
            example.stop()
            await asyncio.sleep(1)

        mock_print.assert_any_call("task started")
        mock_print.assert_any_call("task stopped")
        mock_print.assert_any_call("Hello world")


if __name__ == "__main__":
    unittest.main()
