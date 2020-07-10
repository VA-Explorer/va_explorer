import pytest
from django.urls import resolve, reverse

from va_explorer.users.models import User

pytestmark = pytest.mark.django_db


def test_detail(user: User):
    assert reverse("users:detail", kwargs={"pk": user.id}) == f"/users/{user.id}/"
    assert resolve(f"/users/{user.id}/").view_name == "users:detail"


def test_update(user: User):
    assert (
        reverse("users:update", kwargs={"pk": user.id}) == f"/users/update/{user.id}/"
    )
    assert resolve(f"/users/update/{user.id}/").view_name == "users:update"


def test_redirect():
    assert reverse("users:redirect") == "/users/~redirect/"
    assert resolve("/users/~redirect/").view_name == "users:redirect"
