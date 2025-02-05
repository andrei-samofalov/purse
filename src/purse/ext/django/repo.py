import typing as t

from django.db import models

from purse.interfaces.protocols import QueryRepoProtocol, CommitRepoProtocol


class PurseDjangoError(Exception):
    """Purse exception for Django ext."""


class PurseDjangoModel(models.Model):
    """Django model with disabled save method."""

    class Meta:
        abstract = True

    async def asave(self, *args, **kwargs):
        """This method is disabled in PurseDjangoModel."""
        raise PurseDjangoError("direct saving is prohibited, use DjangoQueryRepo context manager")

    def save(self, *args, **kwargs):
        """This method is disabled in PurseDjangoModel."""
        raise PurseDjangoError("direct saving is prohibited, use DjangoQueryRepo context manager")

    async def _asave(self, *args, **kwargs):
        await super().asave(*args, **kwargs)

    async def _save(self, *args, **kwargs):
        await super().save(*args, **kwargs)


DjangoModelType = t.TypeVar("DjangoModelType", bound=PurseDjangoModel)


class DjangoQueryDAO(QueryRepoProtocol[DjangoModelType, int], t.Generic[DjangoModelType]):
    """Django Query Data access object."""

    def __init__(self, objects: models.Manager):
        self._objects = objects

    async def get_one(self, object_pk: int) -> DjangoModelType:
        """Return object by primary key"""
        return await self._objects.aget(pk=object_pk)

    async def get_all(self) -> models.QuerySet[DjangoModelType]:
        """Return all objects in repository"""
        return self._objects.all()

    async def get_one_or_none(self, object_pk: int) -> t.Optional[DjangoModelType]:
        """Return object by pk or None"""
        return await self._objects.filter(pk=object_pk).afirst()

    async def filter(self, **filters: t.Any) -> t.Iterator[DjangoModelType]:
        """Return an iterable of objects filtered by filters"""
        return self._objects.filter(**filters).iterator()

    async def count(self, **filters: t.Any) -> int:
        """Return number of objects in repository filtered by filters"""
        return await self._objects.filter(**filters).acount()


class DjangoCommitDAO(CommitRepoProtocol[DjangoModelType], t.Generic[DjangoModelType]):
    """Django commit data access object."""

    def __init__(self, objects: models.Manager):
        self._session: set[tuple[DjangoModelType, tuple[tuple[str, t.Hashable], ...]]] = set()
        self._objects = objects

    _id = property(lambda self: id(self))

    async def flush(self):
        """Flush objects to database."""
        for obj, save_opts_tuples in self._session:
            save_opts = {
                k: v for k, v in save_opts_tuples
            }
            await obj._asave(**save_opts)

    def _check_obj_session(self, obj: DjangoModelType):
        """Check whether object has a session mark and this mark belongs to cls session."""
        if hasattr(obj, "_session") and obj._session != self._id:
            raise PurseDjangoError(f"{obj} belongs to a different session")

    def _close_session(self):
        self._session = set()

    async def close(self):
        """Flush objects and close the session."""
        await self.flush()
        self._close_session()

    async def add(self, obj: DjangoModelType, **save_options: t.Hashable):
        """Add object to repository,
        save_options nust ba all hashable and would be passed to obj.save method."""
        self._check_obj_session(obj)
        obj._session = id(self)

        self._session.add(
            (obj, tuple((k, v) for k, v in save_options.items()))
        )


class PurseDjangoRepo(QueryRepoProtocol[DjangoModelType, int], t.Generic[DjangoModelType]):
    """Django repo implementation."""
    domain_model: type[DjangoModelType]

    def __init__(
        self,
        commit_dao: type[DjangoCommitDAO],
        query_dao: type[DjangoQueryDAO],
    ) -> None:
        self._objects = t.cast(models.Manager, self.domain_model._default_manager)
        self._commit_dao = commit_dao[DjangoModelType](self._objects)
        self._query_dao = query_dao[DjangoModelType](self._objects)
        self._context = False

    async def __aenter__(self) -> "PurseDjangoRepo[DjangoModelType]":
        self._context = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._context = False
        await self._commit_dao.close()
        # we don't need any rollbacks - Django handles them by itself

    async def add(self, obj: DjangoModelType, **save_options: t.Hashable):
        """Add object to repository,
        save_options nust ba all hashable and would be passed to obj.save method."""
        if not self._context:
            raise PurseDjangoError("using add method outside of context manager is prohibited")
        await self._commit_dao.add(obj, **save_options)

    async def get_one(self, object_pk: int) -> DjangoModelType:
        """Return object by primary key"""
        return await self._query_dao.get_one(object_pk=object_pk)

    async def get_all(self) -> models.QuerySet[DjangoModelType]:
        """Return all objects in repository"""
        return await self._query_dao.get_all()

    async def get_one_or_none(self, object_pk: int) -> t.Optional[DjangoModelType]:
        """Return object by pk or None"""
        return await self._query_dao.get_one_or_none(object_pk=object_pk)

    async def filter(self, **filters: t.Any) -> t.Iterator[DjangoModelType]:
        """Return an iterable of objects filtered by filters"""
        return await self._query_dao.filter(**filters)

    async def count(self, **filters: t.Any) -> int:
        """Return number of objects in repository filtered by filters"""
        return await self._query_dao.count(**filters)
