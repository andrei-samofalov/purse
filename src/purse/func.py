import datetime
import inspect
import typing as t
import warnings

P = t.ParamSpec("P")
T = t.TypeVar("T")
DatetimeType = t.TypeVar("DatetimeType", datetime.date, datetime.datetime, float)
FunctionOrCoroutine = t.Union[t.Callable[[P], T | t.Awaitable[T]], t.Coroutine[t.Any, t.Any, T]]


async def acall(fn_or_coro: FunctionOrCoroutine, *args: P.args, **kwargs: P.kwargs) -> T:
    """Call the function or coroutine."""

    if inspect.iscoroutinefunction(fn_or_coro):
        return await fn_or_coro(*args, **kwargs)

    if inspect.iscoroutine(fn_or_coro):
        if args or kwargs:
            warnings.warn(f'{fn_or_coro} is a coroutine but args or kwargs were passed.')
        return await fn_or_coro

    return fn_or_coro(*args, **kwargs)


def range_compare(a: DatetimeType, b: tuple[DatetimeType, DatetimeType]) -> bool:
    """Return b[1] < a <= b[0] for datetime types including float."""
    if not isinstance(b, tuple):
        return False

    start, end = b
    return end < a <= start


def contains(a: t.Any, b: t.Container[t.Any]) -> bool:
    """Return a in b. Compared to operator.contains signature changed"""
    return a in b


def are_strings(a: t.Any, b: t.Any) -> bool:
    """Return a and b are strings."""
    return isinstance(a, str) and isinstance(b, str)
