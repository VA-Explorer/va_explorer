import pytest

from va_explorer.users.models import User, UserPasswordHistory
from va_explorer.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_user_get_absolute_url(user: User):
    assert user.get_absolute_url() == f"/users/{user.id}/"


def test_user_password_history_exists():
    user = UserFactory.create()
    user.set_password("test")
    user.save()

    password_history = UserPasswordHistory.objects.filter(username_id=user)
    assert password_history.count() == 1
