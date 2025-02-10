import dataclasses
import typing as t

import pytest

from purse.dataclasses import DataClassProtocol
from purse.interfaces.protocols import PKType
from purse.interfaces.repo.memory import DoesNotExist, MemoryQueryRepo


@dataclasses.dataclass
class DomainModel(DataClassProtocol, t.Generic[PKType]):
    id: PKType

    def as_dict(self):
        """return model as a dict"""
        return dataclasses.asdict(self)


@dataclasses.dataclass
class User(DomainModel[int]):
    name: str
    payments: list[int] = dataclasses.field(default_factory=list)


class UserFilterParams(t.TypedDict):
    id: int
    name: str
    payments: list[int]


class UserMemoryRepo(MemoryQueryRepo[int, User]):
    pass


@pytest.fixture(scope="module")
def user():
    """return test user"""
    return User(id=1, name='John')


@pytest.fixture(scope="module")
def does_not_exist():
    """return doesnotexist error class"""
    return DoesNotExist


@pytest.fixture(scope="module")
def user_repo():
    """return pre-configured user repo"""

    class UserRepo(MemoryQueryRepo[int, User]):
        domain_model = User
        filter_params = UserFilterParams
        to_domain_fn = lambda user_dict: User(**user_dict)

    return UserRepo()
