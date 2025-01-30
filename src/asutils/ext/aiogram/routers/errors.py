import functools
from collections.abc import Callable, Awaitable
from logging import getLogger, Logger
from typing import Optional, Any

try:
    from aiogram import Router, Bot
    from aiogram.enums.update_type import UpdateType
    from aiogram.exceptions import TelegramForbiddenError
    from aiogram.types import ErrorEvent, Update
    from aiogram.utils.markdown import hcode, hbold
except ImportError:
    raise ImportError(
        "aiogram is not installed. Please install it and try again."
    )

_logger = getLogger("bot.errors")

CodeFormatCallable = Callable[[Any], str]
HandleForbiddenCallable = Callable[[Update], Awaitable[None]]
ExtractContextCallable = Callable[[Update], Awaitable[dict[str, Any]]]


def make_error_router(
    bot: Bot,
    dev_chat_id: int,
    logger: Logger = _logger,
    code_fn: CodeFormatCallable = hcode,
    bold_fn: CodeFormatCallable = hbold,
    handle_forbidden_fn: Optional[HandleForbiddenCallable] = None,
    extract_context_fn: Optional[ExtractContextCallable] = None,
    router_name: Optional[str] = "errors",
    print_exception: bool = True,
    log_exception: bool = True,
) -> Router:
    """Make an error aiogram router."""
    router = Router(name=router_name)

    @router.errors()
    async def error_handler(exception: ErrorEvent):
        """Send errors to developer"""
        if print_exception:
            print(exception.model_dump_json(indent=2, exclude_none=True, exclude={"exception"}))

        event_type = exception.update.event_type
        exc = code_fn(exception.exception)
        send_msg_to_dev = functools.partial(bot.send_message, chat_id=dev_chat_id)

        ctx = {} if not extract_context_fn else await extract_context_fn(exception.update)
        ctx_text = "\n".join([f"{ctx_key}: {ctx_val}" for ctx_key, ctx_val in ctx.items()])

        if event_type == UpdateType.CALLBACK_QUERY:
            event = exception.update.callback_query
            await send_msg_to_dev(
                text=f"{bold_fn(exc)}\n\n"
                     f"Chat ID:  {code_fn(event.message.chat.id)}\n"
                     f"User ID:  {code_fn(event.from_user.id)}\n"
                     f"Message:  \n{code_fn(event.message.text)}\n"
                     f"Callback Data:  {code_fn(event.data)}\n"
                     f"{ctx_text}"
            )

        elif event_type == UpdateType.MESSAGE:
            event = exception.update.message
            await send_msg_to_dev(
                text=f"{bold_fn(exc)}\n\n"
                     f"Chat ID:  {code_fn(event.chat.id)}\n"
                     f"User ID:  {code_fn(event.from_user.id)}\n"
                     f"Message:  {code_fn(event.text)}\n"
                     f"{ctx_text}"
            )
        elif isinstance(exception.exception, TelegramForbiddenError):
            if handle_forbidden_fn:
                await handle_forbidden_fn(exception.update)
            return

        else:
            await send_msg_to_dev(text=f"{bold_fn('Error:')}\n{exc}\n{ctx_text}")

        if log_exception:
            logger.exception(exception.exception)

    return router
