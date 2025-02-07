import operator
import threading
import typing as t
from types import MappingProxyType

from purse import func
from purse.interfaces.protocols import (
    DoesNotExistProtocol,
    ModelType,
    PKType,
    QueryRepoProtocol,
)

FilterMap = t.Mapping[str, t.Callable[[t.Any, t.Any], bool]]


class DoesNotExist(Exception):
    """Does not exist"""

    def __init__(self, model_name: str, primary_key: int) -> None:
        self.model_name = model_name
        self.primary_key = primary_key

    def __str__(self):
        return f"{self.model_name} with primary key {self.primary_key} does not exist"


class EmptyModel:
    """Default empty model"""

    def __init__(self, **kwargs: t.Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


DEFAULT_FILTER_MAP: FilterMap = {
    "eq": operator.eq,
    "ne": operator.ne,
    "gt": operator.gt,
    "gte": operator.ge,
    "lt": operator.lt,
    "lte": operator.le,
    "range": func.range_compare,
    "in": func.contains,
    "contains": operator.contains,
    "iexact": lambda a, b: func.are_strings(a, b) and a.lower() == b.lower(),
    "icontains": lambda a, b: func.are_strings(a, b) and b.lower() in a.lower(),
    "startswith": lambda a, b: func.are_strings(a, b) and a.startswith(b),
    "endswith": lambda a, b: func.are_strings(a, b) and a.endswith(b),
}


class MemoryQueryRepo(QueryRepoProtocol[ModelType, PKType], t.Generic[ModelType, PKType]):
    """Memory implementation of QueryRepoProtocol"""
    domain_model: type[ModelType] = EmptyModel
    to_domain_fn: t.Callable[[dict], ModelType] = lambda d: EmptyModel(**d)
    does_not_exist: type[DoesNotExistProtocol] = DoesNotExist
    filter_params: type[t.TypedDict]
    filter_map: FilterMap = MappingProxyType(DEFAULT_FILTER_MAP)

    def __init__(
        self,
        filter_params: t.Optional[type[t.TypedDict]] = None,
        filter_map: t.Optional[FilterMap] = None,
    ):
        cls = self.__class__
        self._storage: dict[PKType, dict] = {}
        self._to_domain_fn = staticmethod(cls.to_domain_fn)
        self._filter_params = filter_params or cls.filter_params
        self._filter_map = filter_map or cls.filter_map
        self._lock = threading.RLock()

    def to_domain(self, obj: dict) -> ModelType:
        """Create and return domain model from dict object"""
        return self._to_domain_fn(obj)

    async def add(self, obj: ModelType):
        self._storage[obj.id] = obj.as_dict()

    async def get_all(self, order_by: t.Optional[str] = None) -> list[ModelType]:
        objects = list(self._storage.values())
        return self._apply_ordering(objects, order_by)

    async def get_one(self, object_pk: PKType) -> ModelType:
        try:
            result = self._storage[object_pk]
        except KeyError:
            raise self.does_not_exist(self.domain_model.__name__, primary_key=object_pk)

        return self.to_domain(result)

    async def get_one_or_none(self, object_id: PKType) -> t.Optional[ModelType]:
        try:
            return await self.get_one(object_id)
        except self.does_not_exist:
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

    def _apply_ordering(self, objects: list[dict], order_by: t.Optional[str]) -> list[ModelType]:
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

    async def filter(self, order_by: t.Optional[str] = None, **filters: t.Any) -> t.List[ModelType]:
        objects = [obj async for obj in self._filter(**filters)]
        return self._apply_ordering(objects, order_by)

    async def count(self, **filters: t.Any) -> int:
        return sum([1 async for _ in self._filter(**filters)])

    async def _do_update(self, obj: dict, **updates) -> None:
        with self._lock:
            obj.update(**updates)

    async def update_by_id(self, object_id: PKType, **updates: t.Any) -> None:
        await self.update_by_filters(id=object_id, **updates)

    async def update_by_filters(self, filters: dict, **updates) -> None:
        """Mass update objects by given filters"""
        async for obj in self._filter(**filters):
            await self._do_update(obj, **updates)
