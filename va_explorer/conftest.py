import pytest
from django.contrib.auth import models

from va_explorer.tests.factories import (
    GroupFactory,
    LocationFactory,
    PermissionFactory,
    UserFactory,
)
from va_explorer.users.models import User
from va_explorer.va_data_management.models import Location


@pytest.fixture(autouse=True)
def _media_storage(settings, tmpdir):
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


@pytest.fixture
def location() -> Location:
    return LocationFactory()
