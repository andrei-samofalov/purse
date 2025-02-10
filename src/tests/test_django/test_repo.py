import logging

import pytest

from purse.ext.django.repo import PurseDjangoError, UnsavedSessionError
from tests.test_django.conftest import DjangoRepo, UserQuery, UserSession
from tests.test_django.testapp.users.models import User

logging.disable(logging.ERROR)
pytestmark = pytest.mark.django_db


@pytest.mark.asyncio
async def test_repo_can_query(repo):
    assert repo
    assert await repo.query.count() == 0

    user1 = User(name='1')
    user2 = User(name='2')
    user3 = User(name='3')
    async with repo as r:
        await r.session.add(user1)
        await r.session.add(user2)
        await r.session.add(user3)

    assert await repo.query.count() == 3

    ordered = await repo.query.filter(ordering={'name'})
    assert ordered[0] == user1

    desc_ordered = await repo.query.filter(ordering={'-name'})
    assert desc_ordered[0] == user3

    await repo.session.delete_db()


@pytest.mark.asyncio
async def test_model_cannot_save_itself(user):
    with pytest.raises(PurseDjangoError):
        await user.asave()

    assert user.id is None


@pytest.mark.asyncio
async def test_repo_can_save_model(repo, user):
    users = await repo.query.count()
    assert users == 0

    async with repo as r:
        await r.session.add(user)

    users = await repo.query.count()
    assert users == 1

    database_users = await repo.query.filter(name=user.name)
    assert len(database_users) == 1
    assert database_users[0] == user

    await repo.session.delete_db()


async def test_repo_rollback(repo, user):
    """Actually replaces"""
    assert await repo.query.count() == 0
    async with repo as r:
        await r.session.add(user)

    assert user.id is not None

    # it is a bug: repo replaces (updates), not raises integrity
    same_id_user = User(id=user.id, name='another name')
    async with repo as r:
        await r.session.add(same_id_user)

    assert await repo.query.count() == 1

    old_name = await repo.query.filter(name=user.name)
    assert len(old_name) == 0


async def test_another_session_is_blocked(repo):
    user = User(name='user1')
    await repo.session.add(user)
    assert len(repo.session._session) == 1
    assert hasattr(user, "_session_id") and user._session_id == repo.session._id

    another_repo = DjangoRepo(query_dao=UserQuery, commit_dao=UserSession)

    with pytest.raises(PurseDjangoError):
        await another_repo.session.add(user)

    # repo.session.method flush was not called, so user is not in db
    assert await repo.query.count() == 0

    await repo.session.flush()
    # now - it is
    assert await repo.query.count() == 1

    await repo.session.delete_db()


async def test_session_raises_with_unsaved_objects_on_delete(repo, capsys):
    user = User(name='user1')
    await repo.session.add(user)

    with pytest.raises(UnsavedSessionError):
        repo.session.__del__()

        captured = capsys.readouterr().err
        assert "unsaved objects in" in captured
