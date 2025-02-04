import inspect
import warnings
from collections.abc import Callable, Awaitable, Coroutine
from typing import ParamSpec, TypeVar, Union, Any

P = ParamSpec("P")
T = TypeVar("T")
FunctionOrCoroutine = Union[Callable[[P], T | Awaitable[T]], Coroutine[Any, Any, T]]


async def func_call(fn_or_coro: FunctionOrCoroutine, *args: P.args, **kwargs: P.kwargs) -> T:
    """Call the function or coroutine."""

    if inspect.iscoroutinefunction(fn_or_coro):
        return await fn_or_coro(*args, **kwargs)

    if inspect.iscoroutine(fn_or_coro):
        if args or kwargs:
            warnings.warn(f'{fn_or_coro} is a coroutine but args or kwargs were passed.')
        return await fn_or_coro

    return fn_or_coro(*args, **kwargs)
