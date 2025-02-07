import inspect
from types import TracebackType
from typing import Any, Generic, Mapping, Protocol, TypeAlias, TypeGuard, TypeVar

from purse.types import ProtocolType

_SysExcInfoType: TypeAlias = tuple[type[BaseException], BaseException, TracebackType | None] | \
                             tuple[None, None, None]
_ExcInfoType: TypeAlias = None | bool | _SysExcInfoType | BaseException


class LoggerProtocol(Protocol):
    """Logger protocol"""

    def error(
        self,
        msg: object,
        *args: object,
        exc_info: _ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None: ...

    def info(
        self,
        msg: object,
        *args: object,
        exc_info: _ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None: ...


isfun = inspect.isfunction
iscoro = inspect.iscoroutinefunction
getsig = inspect.signature

ProtocolGenericType = TypeVar("ProtocolGenericType", bound=ProtocolType)


class GenericProtocolTypeGuard(Generic[ProtocolGenericType]):
    """Return True if the given object implements the protocol."""

    def __call__(self, cls, protocol: ProtocolType) -> TypeGuard[ProtocolGenericType]:
        return implements_protocol(cls, protocol)


def implements_protocol(cls: Any, protocol: ProtocolType):
    """Return True if the given object implements the protocol."""
    if not isinstance(cls, protocol):
        return False

    for name, member in inspect.getmembers(protocol):
        if name.startswith("__"):
            continue

        protocol_member = getattr(protocol, name)
        if not (isfun(protocol_member) or iscoro(protocol_member)):
            continue

        class_member = getattr(cls, name, None)
        if iscoro(protocol_member) != iscoro(class_member):
            return False

        if getsig(protocol_member) != getsig(class_member):
            return False

    return True
