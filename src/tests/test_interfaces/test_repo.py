import pytest

from tests.test_interfaces.conftest import User, DoesNotExist


@pytest.mark.asyncio
async def test_user_repo(user_repo, user, does_not_exist):
    await user_repo.add(user)

    all_users = await user_repo.get_all()
    assert len(all_users) == 1

    user_1 = await user_repo.get_one(1)
    assert user_1.id == 1

    results = await user_repo.filter(name="john")
    assert len(results) == 0

    assert user_repo.model is User

    none_user = await user_repo.get_one_or_none(4)
    assert none_user is None

    with pytest.raises(does_not_exist) as exc:
        await user_repo.get_one(4)

    print(f"{exc.value=}")
    assert exc.value == '123User with id=4 does not exist'
