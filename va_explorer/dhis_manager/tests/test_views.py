import pytest
from django.contrib.auth.models import Permission
from django.test import Client

from va_explorer.tests.factories import (
    GroupFactory,
    UserFactory,
)
from va_explorer.users.models import User

pytestmark = pytest.mark.django_db

@pytest.fixture
def view_dhisstatus_group():
    can_view_dhisstatus = Permission.objects.filter(
        codename="view_dhisstatus"
    ).first()
    return GroupFactory.create(permissions=[can_view_dhisstatus])


@pytest.fixture
def change_dhisstatus_group():
    can_change_dhisstatus = Permission.objects.filter(
        codename="change_dhisstatus"
    ).first()
    return GroupFactory.create(permissions=[can_change_dhisstatus])


# Get the index and make sure 200 is returned
def test_index_with_valid_permission(user: User, view_dhisstatus_group):
    user = UserFactory.create(groups=[view_dhisstatus_group])
    client = Client()
    client.force_login(user=user)
    response = client.get("/dhis/")
    assert response.status_code == 200


# Request the index without permissions and make sure 403 is returned
def test_index_without_valid_permission(user: User):
    client = Client()
    client.force_login(user=user)

    response = client.get("/dhis/")
    assert response.status_code == 403


