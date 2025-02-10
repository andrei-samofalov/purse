import os
import typing as t
from functools import cached_property

from django.db import models

from purse.interfaces.protocols import (
    CommitRepoProtocol,
    OrderingType,
    PKType,
    QueryRepoProtocol,
    empty_set,
)


class PurseDjangoError(Exception):
    """Purse exception for Django ext."""


class UnsavedSessionError(PurseDjangoError):
    """Unsaved session exception for Django ext."""


class PurseDjangoModel(models.Model):
    """Django model with disabled save method."""

    class Meta:
        abstract = True

    async def asave(self, *args, **kwargs):
        """Save the object to database."""
        if not hasattr(self, "_session_id"):
            raise PurseDjangoError(
                "direct saving is prohibited, use DjangoQueryRepo context manager "
                "or DjangoCommitDAO."
            )
        await super().asave(*args, **kwargs)

    def save(self, *args, **kwargs):
        """Save the object to database."""
        if not hasattr(self, "_session_id"):
            raise PurseDjangoError(
                "direct saving is prohibited, use DjangoQueryRepo context manager "
                "or DjangoCommitDAO."
            )
        super().save(*args, **kwargs)


DjangoModelType = t.TypeVar("DjangoModelType", bound=PurseDjangoModel)


class DjangoQueryDAO(
    QueryRepoProtocol[DjangoModelType],
    t.Generic[DjangoModelType],
):
    """Django Query Data access object."""

    def __init__(self, objects: models.Manager):
        self._objects = objects

    async def exists(self, **filters: t.Any) -> bool:
        """Return True if objects with given filters exist."""
        return await super().exists(**filters)

    async def get_one(self, object_pk: PKType) -> DjangoModelType:
        """Return object by primary key"""
        return await self._objects.aget(pk=object_pk)

    async def get_all(self, ordering: OrderingType = empty_set) -> models.QuerySet[DjangoModelType]:
        """Return all objects in repository"""
        return self._objects.order_by(*ordering).all()

    async def get_one_or_none(self, object_pk: PKType) -> t.Optional[DjangoModelType]:
        """Return object by pk or None"""
        return await self._objects.filter(pk=object_pk).afirst()

    async def filter(
        self, ordering: OrderingType = empty_set, **filters: t.Any
    ) -> t.Container[DjangoModelType]:
        """Return an iterable of objects filtered by filters"""
        return self._objects.filter(**filters).order_by(*ordering)

    async def count(self, **filters: t.Any) -> int:
        """Return number of objects in repository filtered by filters"""
        return await self._objects.filter(**filters).acount()


class DjangoCommitDAO(CommitRepoProtocol[DjangoModelType], t.Generic[DjangoModelType]):
    """Django commit data access object."""

    def __init__(self, objects: models.Manager):
        self._session: list[tuple[DjangoModelType, tuple[tuple[str, t.Hashable], ...]]] = []
        self._objects = objects

    def __del__(self):
        if self._session:
            raise UnsavedSessionError(f"unsaved objects in {self.__class__.__name__}")

    _id = cached_property(lambda self: id(self))

    async def flush(self):
        """Flush objects to database."""
        for obj, save_opts_tuples in self._session:
            save_opts = {
                k: v for k, v in save_opts_tuples
            }
            await obj.asave(**save_opts)

    def _check_obj_session(self, obj: DjangoModelType):
        """Check whether object has a session mark and this mark belongs to cls session."""
        if hasattr(obj, "_session_id") and getattr(obj, "_session_id") != self._id:
            raise PurseDjangoError(f"{obj} belongs to a different session")

    def _close_session(self):
        self._session = []

    async def delete_db(self):
        """Delete all objects in database."""
        await self._objects.all().adelete()

    async def close(self):
        """Flush objects and close the session."""
        await self.flush()
        self._close_session()

    async def add(self, obj: DjangoModelType, **save_options: t.Hashable):
        """Add object to repository,
        save_options nust ba all hashable and would be passed to obj.save method."""
        self._check_obj_session(obj)
        obj._session_id = self._id

        self._session.append(
            (obj, tuple((k, v) for k, v in save_options.items()))
        )


DjangoCommitDAOType = t.TypeVar("DjangoCommitDAOType", bound=DjangoCommitDAO)
DjangoQueryDAOType = t.TypeVar("DjangoQueryDAOType", bound=DjangoQueryDAO)


class PurseDjangoRepo(t.Generic[DjangoModelType, DjangoCommitDAOType, DjangoQueryDAOType]):
    """Django repo implementation."""
    domain_model: type[DjangoModelType]

    def __init__(
        self,
        commit_dao: type[DjangoCommitDAOType],
        query_dao: type[DjangoQueryDAOType],
    ) -> None:
        _objects = t.cast(models.Manager, getattr(self.domain_model, "_default_manager"))
        self.query: DjangoQueryDAOType = query_dao(_objects)
        self.session: DjangoCommitDAOType = commit_dao(_objects)
        self._context = False
        assert os.environ.setdefault('DJANGO_ALLOW_ASYNC_UNSAFE', 'false') == 'true'

    async def __aenter__(self) -> t.Self:
        self._context = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._context = False
        await self.session.close()
        # we don't need any rollbacks - Django handles them by itself
