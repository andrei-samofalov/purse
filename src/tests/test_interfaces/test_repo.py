import operator

import pytest

from tests.test_interfaces.conftest import User


@pytest.mark.asyncio
async def test_user_repo(user_repo, user, does_not_exist):
    await user_repo.add(user)

    all_users = await user_repo.get_all()
    assert len(all_users) == 1

    user_1 = await user_repo.get_one(1)
    assert user_1.id == 1

    results = await user_repo.filter(name="john")
    assert len(results) == 0

    assert user_repo.domain_model is User

    none_user = await user_repo.get_one_or_none(4)
    assert none_user is None

    with pytest.raises(does_not_exist) as exc:
        await user_repo.get_one(4)

    assert exc.value.__str__() == "User with primary key 4 does not exist"

    nope_list = await user_repo.filter(name="nope")
    assert len(nope_list) == 0

    elise = User(id=2, name='Elise')
    await user_repo.add(elise)
    assert await user_repo.count() == 2

    assert await user_repo.get_one(2) == elise

    sorted_users = await user_repo.get_all(order_by='-id')
    assert len(sorted_users) == 2
    assert sorted_users[0] == elise

    maybe_elise = await user_repo.filter(name__iexact="elise")
    assert len(maybe_elise) == 1
    assert maybe_elise[0] == elise

    elise.payments.append(4)
    await user_repo.add(elise)
    assert await user_repo.count() == 2

    maybe_elise = await user_repo.filter(payments__contains=4)
    assert len(maybe_elise) == 1
    assert maybe_elise[0] == elise

    maybe_elise = await user_repo.filter(name__in=['Elise', "Alice"])
    assert len(maybe_elise) == 1
    assert maybe_elise[0] == elise


def test_contains():

    container = [1, 2]
    value = 1

    assert operator.contains(container, value)
