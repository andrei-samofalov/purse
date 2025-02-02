import dataclasses
import typing as t

import pytest

from purse.dataclasses import DataClassProtocol
from purse.interfaces.memorepo import MemoryRepo, \
    PK, Model, make_memory_repo


class DoesNotExist(Exception):
    """Does not exist"""

    def __init__(self, model: type[Model], id: int) -> None:
        self.model_name = model.__name__
        self.id = id

    def __str__(self):
        return f"{self.model_name} with {self.id} does not exist"


@dataclasses.dataclass
class DomainModel(DataClassProtocol, t.Generic[PK]):
    id: PK

    def as_dict(self):
        """return model as a dict"""
        return dataclasses.asdict(self)


@dataclasses.dataclass
class User(DomainModel[int]):
    pass


class UserFilterParams(t.TypedDict):
    id: int


class UserMemoryRepo(MemoryRepo[int, User]):
    pass


@pytest.fixture(scope="module")
def user():
    """return test user"""
    return User(id=1)


@pytest.fixture(scope="module")
def does_not_exist():
    """return doesnotexist error class"""
    return DoesNotExist


@pytest.fixture(scope="module")
def user_repo_cls():
    """return pre-configured user repo"""
    return make_memory_repo(
        name='UserRepo',
        domain_model=User,
        domain_pk=int,
        filter_params=UserFilterParams,
        does_not_exist=DoesNotExist,
        to_domain_fn=lambda user_dict: User(**user_dict),
    )


@pytest.fixture(scope="module")
def user_repo(user_repo_cls):
    """return pre-configured user repo"""
    return user_repo_cls()
