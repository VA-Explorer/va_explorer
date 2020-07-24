import pytest
from django.test import RequestFactory

from va_explorer.users.forms import ExtendedUserCreationForm, UserUpdateForm
from va_explorer.users.tests.factories import GroupFactory, NewUserFactory

pytestmark = pytest.mark.django_db


class TestUserCreationForm:
    def test_valid_form(self, rf: RequestFactory):
        # A user with proto_user params does not exist yet.
        proto_user = NewUserFactory.build()
        group = GroupFactory.create()

        form = ExtendedUserCreationForm(
            {"name": proto_user.name, "email": proto_user.email, "groups": [group]}
        )

        # Note: The form expects a request object to be set in order to save it
        request = rf.get("/fake-url/")
        form.request = request

        assert form.is_valid()

    def test_email_uniqueness(self):
        # A user with existing_user params exists already.
        existing_user = NewUserFactory.create()
        group = GroupFactory.create()

        form = ExtendedUserCreationForm(
            {
                "name": existing_user.name,
                "email": existing_user.email,
                "groups": [group],
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "email" in form.errors

    def test_email_required(self):
        # A user with proto_user params does not exist yet.
        proto_user = NewUserFactory.build()
        group = GroupFactory.create()

        form = ExtendedUserCreationForm(
            {"name": proto_user.name, "email": "", "groups": [group]}
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "email" in form.errors

    def test_name_required(self):
        # A user with proto_user params does not exist yet.
        proto_user = NewUserFactory.build()
        group = GroupFactory.create()

        form = ExtendedUserCreationForm(
            {"name": "", "email": proto_user.email, "groups": [group]}
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "name" in form.errors

    def test_group_required(self):
        # A user with proto_user params does not exist yet.
        proto_user = NewUserFactory.build()

        form = ExtendedUserCreationForm(
            {"name": proto_user.name, "email": proto_user.email, "groups": []}
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "groups" in form.errors


class TestUserUpdateForm:
    def test_valid_form(self, rf: RequestFactory):
        new_group = GroupFactory.create()

        form = UserUpdateForm(
            {
                "name": "A new name",
                "email": "updatedemail@example.com",
                "groups": [new_group],
            }
        )

        assert form.is_valid()
