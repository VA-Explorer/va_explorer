import pytest
from django.test import Client
from va_explorer.users.models import User
from va_explorer.tests.factories import VerbalAutopsyFactory
from va_explorer.va_data_management.views import index, show, edit, save, reset, revert_latest

pytestmark = pytest.mark.django_db

def test_index(user: User):
    client = Client()
    client.user = user
    va = VerbalAutopsyFactory.create()
    response = client.get("/va_data_management/")
    assert response.status_code == 200
    assert bytes(va.Id10007, "utf-8") in response.content
