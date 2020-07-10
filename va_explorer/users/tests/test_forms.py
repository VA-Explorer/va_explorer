import pytest

from va_explorer.users.forms import ExtendedUserCreationForm
from va_explorer.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestUserCreationForm:
    def test_email_uniqueness(self):
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

        # Creating a user.
        form.save()

        # The user with proto_user params already exists,
        # hence cannot be created.
        form = ExtendedUserCreationForm(
            {
                "first_name": proto_user.first_name,
                "last_name": proto_user.last_name,
                "email": proto_user.email,
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "email" in form.errors
