import abc
import operator
import threading
import typing as t
import uuid
from datetime import date, datetime
from types import MappingProxyType

from purse.dataclasses import DataClassProtocol

PK = t.TypeVar("PK", int, uuid.UUID)
Model = t.TypeVar("Model", bound=DataClassProtocol)

ExceptionMeta = type(Exception)


class DoesNotExistExceptionProtocol(t.Protocol, metaclass=ExceptionMeta):
    """Protocol for DoesNotExist exceptions"""
    model: type[Model]
    object_id: PK

    def __init__(self, model: type[Model], object_id: PK) -> None: ...


class RepoProtocol(t.Generic[PK, Model], metaclass=abc.ABCMeta):
    """Repo interface"""

    @abc.abstractmethod
    async def add(self, obj: Model):
        """Add object to repository"""

    @abc.abstractmethod
    async def get_one(self, object_id: PK) -> Model:
        """Return object by id"""

    @abc.abstractmethod
    async def get_all(self):
        """Return all objects in repository"""

    @abc.abstractmethod
    async def get_one_or_none(self, object_id: PK) -> t.Optional[Model]:
        """Return object by id or None"""

    @abc.abstractmethod
    async def filter(self, **filters: t.Any) -> t.Iterable[Model]:
        """Return an iterable of objects filtered by filters"""

    @abc.abstractmethod
    async def update_by_id(self, object_id: PK, **updates: t.Any) -> None:
        """Update object with provided data"""

    @abc.abstractmethod
    async def update_by_filters(self, filters: t.Mapping[str, t.Any], **updates: t.Any) -> None:
        """Update objects matches to filters with provided data"""


DatetimeType = t.TypeVar("DatetimeType", date, datetime, float)


def _range_compare(a: DatetimeType, b: tuple[DatetimeType, DatetimeType]) -> bool:
    if not isinstance(b, tuple):
        return False

    start, end = b
    return end < a <= start


FilterMap = t.Mapping[str, t.Callable[[t.Any, t.Any], bool]]

DEFAULT_FILTER_MAP: FilterMap = {
    "eq": operator.eq,
    "ne": operator.ne,
    "gt": operator.gt,
    "gte": operator.ge,
    "lt": operator.lt,
    "lte": operator.le,
    "range": _range_compare,
    "in": operator.contains,
    "icontains": lambda a, b: isinstance(a, str) and b.lower() in a.lower(),
    "startswith": lambda a, b: isinstance(a, str) and a.startswith(b),
    "endswith": lambda a, b: isinstance(a, str) and a.endswith(b),
}


class MemoryRepo(RepoProtocol[PK, Model], t.Generic[PK, Model]):
    """Memory implementation of RepoProtocol"""

    def __init__(
        self,
        domain_model: type[Model],
        does_not_exist: type[DoesNotExistExceptionProtocol],
        to_domain_fn: t.Callable[[dict], Model],
        filter_map: FilterMap = MappingProxyType(DEFAULT_FILTER_MAP),
    ):
        self._model = domain_model
        self._storage: dict[PK, dict] = {}
        self._does_not_exist = does_not_exist
        self._to_domain_fn = to_domain_fn
        self._filter_map = filter_map
        self._lock = threading.RLock()

    def to_domain(self, obj: dict) -> Model:
        """Create and return domain model from dict object"""
        return self._to_domain_fn(obj)

    async def add(self, obj: Model):
        self._storage[obj.id] = obj.as_dict()

    async def get_all(self, order_by: t.Optional[str] = None) -> list[Model]:
        objects = list(self._storage.values())
        return self._apply_ordering(objects, order_by)

    async def get_one(self, object_id: PK) -> Model:
        try:
            result = self._storage[object_id]
        except KeyError:
            raise self._does_not_exist(self._model, object_id=object_id)

        return self.to_domain(result)

    async def get_one_or_none(self, object_id: PK) -> t.Optional[Model]:
        try:
            return await self.get_one(object_id)
        except self._does_not_exist:
            return None

    def _apply_filters(self, obj: dict, filters: dict) -> bool:
        """Apply filtering logic based on operators"""
        for key, value in filters.items():
            field, op = key.split("__", 1) if "__" in key else (key, "eq")

            if field not in obj:
                return False

            obj_value = obj[field]

            if op in self._filter_map and not self._filter_map[op](obj_value, value):
                return False

        return True

    def _apply_ordering(self, objects: list[dict], order_by: t.Optional[str]) -> list[Model]:
        """Sort objects based on order_by field"""
        if order_by:
            reverse = order_by.startswith("-")
            key = order_by.lstrip("-")
            objects.sort(key=lambda obj: obj.get(key), reverse=reverse)
        return [self.to_domain(obj) for obj in objects]

    async def _filter(self, **filters: t.Any):
        for obj in self._storage.values():
            if self._apply_filters(obj, filters):
                yield obj

    async def filter(self, order_by: t.Optional[str] = None, **filters: t.Any) -> t.List[Model]:
        objects = [obj async for obj in self._filter(**filters)]
        return self._apply_ordering(objects, order_by)

    async def _do_update(self, obj: dict, **updates) -> None:
        with self._lock:
            obj.update(**updates)

    async def update_by_id(self, object_id: PK, **updates: t.Any) -> None:
        await self.update_by_filters(id=object_id, **updates)

    async def update_by_filters(self, filters: dict, **updates) -> None:
        """Mass update objects by given filters"""
        async for obj in self._filter(**filters):
            await self._do_update(obj, **updates)


def make_memory_repo(
    domain_model: type[Model],
    does_not_exist: type[DoesNotExistExceptionProtocol],
    to_domain_fn: t.Callable[[dict], Model],
    filter_map: FilterMap = MappingProxyType(DEFAULT_FILTER_MAP),
):
    return MemoryRepo(
        domain_model=domain_model,
        does_not_exist=does_not_exist,
        to_domain_fn=to_domain_fn,
        filter_map=filter_map,
    )
