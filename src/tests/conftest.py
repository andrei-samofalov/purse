import asyncio

import pytest_asyncio


@pytest_asyncio.fixture(loop_scope="module")
async def current_loop():
    """
    https://pytest-asyncio.readthedocs.io/en/latest/how-to-guides/change_fixture_loop.html
    """
    return asyncio.get_running_loop()
