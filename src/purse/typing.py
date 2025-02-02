import inspect
from typing import Generic, TypeGuard, TypeVar, Any

from purse.types import ProtocolType

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
