import abc
import typing as t
import uuid

PKType = t.TypeVar("PKType", int, uuid.UUID, tuple)
ModelType = t.TypeVar("ModelType")


@t.runtime_checkable
class DoesNotExistProtocol(t.Protocol[ModelType]):
    """Protocol for DoesNotExist exceptions"""

    def __init__(self, model_name: str, primary_key: PKType) -> None: ...  # noqa


class CommitRepoProtocol(t.Generic[ModelType], metaclass=abc.ABCMeta):
    """CommitRepo interface"""

    @abc.abstractmethod
    async def add(self, obj: ModelType):
        """Add object to repository"""

    # async def update(self, obj: ModelType):
    #     """Update object in repository"""


class QueryRepoProtocol(t.Generic[ModelType, PKType], metaclass=abc.ABCMeta):
    """QueryRepo interface"""

    @abc.abstractmethod
    async def get_one(self, object_pk: PKType) -> ModelType:
        """Return object by primary key"""

    @abc.abstractmethod
    async def get_all(self):
        """Return all objects in repository"""

    @abc.abstractmethod
    async def get_one_or_none(self, object_pk: PKType) -> t.Optional[ModelType]:
        """Return object by pk or None"""

    @abc.abstractmethod
    async def filter(self, **filters: t.Any) -> t.Iterable[ModelType]:
        """Return an iterable of objects filtered by filters"""

    @abc.abstractmethod
    async def count(self, **filters: t.Any) -> int:
        """Return number of objects in repository filtered by filters"""
