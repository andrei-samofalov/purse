import asyncio
import contextvars
import datetime
import functools
import inspect
import typing as t
import warnings

P = t.ParamSpec("P")
T = t.TypeVar("T")
DatetimeType = t.TypeVar("DatetimeType", datetime.date, datetime.datetime, float)
FunctionOrCoroutine = t.Union[t.Callable[[P], T | t.Awaitable[T]], t.Coroutine[t.Any, t.Any, T]]


async def acall(fn_or_coro: FunctionOrCoroutine, *args: P.args, **kwargs: P.kwargs) -> T:
    """Call the function or coroutine."""
    if inspect.iscoroutine(fn_or_coro):
        if args or kwargs:
            warnings.warn(f'{fn_or_coro} is a coroutine but args or/and kwargs were passed.')
        return await fn_or_coro

    wrapped = functools.partial(fn_or_coro, *args, **kwargs)
    if inspect.iscoroutinefunction(fn_or_coro):
        return await wrapped()

    loop = asyncio.get_event_loop()
    context = contextvars.copy_context()
    wrapped = functools.partial(context.run, wrapped)
    return await loop.run_in_executor(None, wrapped)


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


class _FuncParams(t.NamedTuple):
    """Helper for func call"""
    args: list[t.Any]
    kwargs: dict[str, t.Any]


def _filter_kwargs(func, **kwargs):
    sig = inspect.signature(func)
    mandatory_kinds = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    pos_args = []
    valid_kwargs = {}
    missing_args = []

    for name, param in sig.parameters.items():
        if name in kwargs:
            if param.kind is inspect.Parameter.POSITIONAL_ONLY:
                pos_args.append(kwargs[name])
            else:
                valid_kwargs[name] = kwargs[name]
        elif param.default is inspect.Parameter.empty and param.kind in mandatory_kinds:
            missing_args.append(name)

    if missing_args:
        raise TypeError(
            f"Missing required arguments for {func.__name__}: {', '.join(missing_args)}"
        )

    return _FuncParams(args=pos_args, kwargs=valid_kwargs)


SyncFunc = t.TypeVar("SyncFunc")


def _is_sync_func(func: t.Callable[..., t.Any]) -> t.TypeGuard[SyncFunc]:
    return not isinstance(func, t.Awaitable)


def call_with_filtered_kwargs(func: SyncFunc, **kwargs):
    """Call the function with filtered args and kwargs based on func signature.

    Accepts only sync functions as a first argument.
    """
    assert _is_sync_func(func)
    params = _filter_kwargs(func, **kwargs)
    return func(*params.args, **params.kwargs)


async def acall_with_filtered_kwargs(func: FunctionOrCoroutine, **kwargs):
    """Async call the function with filtered args and kwargs based on func signature.

    This helper accepts both async and sync functions as a first argument.
    """
    params = _filter_kwargs(func, **kwargs)
    return await acall(func, *params.args, **params.kwargs)
