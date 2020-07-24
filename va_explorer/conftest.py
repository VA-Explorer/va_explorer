import pytest
from django.contrib.auth import models

from va_explorer.users.models import User
from va_explorer.users.tests.factories import (
    GroupFactory,
    PermissionFactory,
    UserFactory,
)


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user() -> User:
    return UserFactory()


@pytest.fixture
def group() -> models.Group:
    return GroupFactory()


@pytest.fixture
def permission() -> models.Permission:
    return PermissionFactory()
