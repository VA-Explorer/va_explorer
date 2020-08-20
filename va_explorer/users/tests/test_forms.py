import pytest
from django.test import RequestFactory

from va_explorer.users.forms import (
    ExtendedUserCreationForm,
    UserSetPasswordForm,
    UserUpdateForm,
)
from va_explorer.users.tests.factories import GroupFactory, LocationFactory, NewUserFactory

pytestmark = pytest.mark.django_db


class TestUserCreationForm:
    def test_valid_form(self, rf: RequestFactory):
        # A user with proto_user params does not exist yet.
        proto_user = NewUserFactory.build()
        group = GroupFactory.create()
        location = LocationFactory.create()

        form = ExtendedUserCreationForm(
            {
                "name": proto_user.name,
                "email": proto_user.email,
                "groups": [group],
                "locations": [location]}
        )

        # Note: The form expects a request object to be set in order to save it
        request = rf.get("/fake-url/")
        form.request = request

        assert form.is_valid()

    def test_email_uniqueness(self):
        # A user with existing_user params exists already.
        existing_user = NewUserFactory.create()
        group = GroupFactory.create()
        location = LocationFactory.create()

        form = ExtendedUserCreationForm(
            {
                "name": existing_user.name,
                "email": existing_user.email,
                "groups": [group],
                "locations": [location]
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "email" in form.errors

    def test_email_required(self):
        # A user with proto_user params does not exist yet.
        proto_user = NewUserFactory.build()
        group = GroupFactory.create()
        location = LocationFactory.create()

        form = ExtendedUserCreationForm(
            {
                "name": proto_user.name,
                "email": "",
                "groups": [group],
                "locations": [location]
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "email" in form.errors

    def test_name_required(self):
        # A user with proto_user params does not exist yet.
        proto_user = NewUserFactory.build()
        group = GroupFactory.create()
        location = LocationFactory.create()

        form = ExtendedUserCreationForm(
            {
                "name": "",
                "email": proto_user.email,
                "groups": [group],
                "locations": [location]
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "name" in form.errors

    def test_group_required(self):
        # A user with proto_user params does not exist yet.
        proto_user = NewUserFactory.build()
        location = LocationFactory.create()

        form = ExtendedUserCreationForm(
            {
                "name": proto_user.name,
                "email": proto_user.email,
                "groups": [],
                "locations": [location]
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "groups" in form.errors

    def test_location_required(self):
        # A user with proto_user params does not exist yet.
        proto_user = NewUserFactory.build()
        group = GroupFactory.create()

        form = ExtendedUserCreationForm(
            {
                "name": proto_user.name,
                "email": proto_user.email,
                "groups": [group],
                "locations": []
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "locations" in form.errors


class TestUserUpdateForm:
    def test_valid_form(self, rf: RequestFactory):
        new_group = GroupFactory.create()
        location = LocationFactory.create()

        form = UserUpdateForm(
            {
                "name": "A new name",
                "email": "updatedemail@example.com",
                "groups": [new_group],
                "is_active": False,
                "locations": [location]
            }
        )

        assert form.is_valid()

    def test_group_required(self):
        # A user with proto_user params does not exist yet.
        proto_user = NewUserFactory.build()
        location = LocationFactory.create()

        form = UserUpdateForm(
            {
                "name": proto_user.name,
                "email": proto_user.email,
                "groups": [],
                "locations": [location]
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "groups" in form.errors


class TestUserSetPasswordForm:
    def test_valid_form(self, rf: RequestFactory):
        form = UserSetPasswordForm(
            {
                "password1": "AReallyGreatPassword1!",
                "password2": "AReallyGreatPassword1!",
            }
        )

        assert form.is_valid()

    def test_invalid_form(self, rf: RequestFactory):
        form = UserSetPasswordForm(
            {
                "password1": "AReallyGreatPassword1!",
                "password2": "ACompletelyDifferentPassword1!",
            }
        )

        assert not form.is_valid()
        assert "You must type the same password each time." in form.errors["password2"]
        assert len(form.errors) == 1
