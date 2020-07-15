import pytest

from va_explorer.users.forms import ExtendedUserCreationForm
from va_explorer.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestUserCreationForm:
    def test_email_uniqueness(self):
        # A user with existing_user params exists already.
        existing_user = UserFactory.create()

        form = ExtendedUserCreationForm(
            {
                "first_name": existing_user.first_name,
                "last_name": existing_user.last_name,
                "email": existing_user.email,
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "email" in form.errors

        # A user with proto_user params does not exist yet.
        proto_user = UserFactory.build()

        form = ExtendedUserCreationForm(
            {
                "first_name": proto_user.first_name,
                "last_name": proto_user.last_name,
                "email": proto_user.email,
            }
        )

        assert form.is_valid()

    def test_email_required(self):
        # A user with proto_user params does not exist yet.
        proto_user = UserFactory.build()

        form = ExtendedUserCreationForm(
            {
                "first_name": proto_user.first_name,
                "last_name": proto_user.last_name,
                "email": "",
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "email" in form.errors

    def first_last_name_required(self):
        # A user with proto_user params does not exist yet.
        proto_user = UserFactory.build()

        form = ExtendedUserCreationForm(
            {
                "first_name": "",
                "last_name": proto_user.last_name,
                "email": proto_user.email,
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "first_name" in form.errors

    def test_last_name_required(self):
        # A user with proto_user params does not exist yet.
        proto_user = UserFactory.build()

        form = ExtendedUserCreationForm(
            {
                "first_name": proto_user.first_name,
                "last_name": "",
                "email": proto_user.email,
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "last_name" in form.errors
