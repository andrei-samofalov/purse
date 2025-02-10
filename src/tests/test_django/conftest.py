import pytest

from purse.ext.django.repo import DjangoCommitDAO, DjangoQueryDAO, PurseDjangoRepo
from tests.test_django.testapp.users.models import User

pytestmark = pytest.mark.django_db


class UserQuery(DjangoQueryDAO[User]):
    pass


class UserSession(DjangoCommitDAO[User]):
    pass


class DjangoRepo(PurseDjangoRepo[User, UserSession, UserQuery]):
    domain_model = User


@pytest.fixture(scope="function")
def user():
    yield User(name="user")


@pytest.fixture(scope="function")
def repo(django_db_blocker):
    yield DjangoRepo(query_dao=UserQuery, commit_dao=UserSession)
    with django_db_blocker.unblock():
        User.objects.all().delete()
