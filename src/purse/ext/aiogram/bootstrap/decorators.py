import asyncio
import functools
from typing import Callable, Awaitable, Optional
from typing import ParamSpec, TypeVar

from aiogram.exceptions import TelegramBadRequest, TelegramNotFound, TelegramForbiddenError

from purse.logging import default_logger as logger

P = ParamSpec("P")
T = TypeVar("T")

ToDecorate = Callable[[P], Awaitable[T]]
Decorated = Callable[[P], Awaitable[Optional[T]]]


def tg_pass(func: ToDecorate) -> Decorated:
    """A decorator that make func ignore some aiogram exceptions"""

    @functools.wraps(func)
    async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> Optional[T]:
        try:
            result = await func(*args, **kwargs)
        except (TelegramBadRequest, TelegramNotFound, TelegramForbiddenError) as ex:
            return logger.error(ex)

        return result

    return _wrapper


@tg_pass
async def call(arg: int) -> int:
    return arg + 2


async def main():
    w = await call(2)
    print(w)


if __name__ == '__main__':
    asyncio.run(main())
