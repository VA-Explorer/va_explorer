import pytest
from django.contrib.auth.models import AnonymousUser, Permission
from django.core.exceptions import PermissionDenied
from django.test import Client, RequestFactory
from django.urls import reverse

from va_explorer.tests.factories import GroupFactory, NewUserFactory, UserFactory
from va_explorer.users.models import User
from va_explorer.users.views import (
    UserRedirectView,
    UserUpdateView,
    user_create_view,
    user_detail_view,
)

pytestmark = pytest.mark.django_db


class TestUserRedirectView:
    """
    TODO:
        extracting view initialization code as class-scoped fixture
        would be great if only pytest-django supported non-function-scoped
        fixture db access -- this is a work-in-progress for now:
        https://github.com/pytest-dev/pytest-django/pull/258
    """

    def test_get_redirect_url(self, user: User, rf: RequestFactory):
        view = UserRedirectView()
        request = rf.get("/fake-url")
        request.user = user

        view.request = request

        assert view.get_redirect_url() == "/"


class TestUserDetailView:
    def test_with_view_permission(self, rf: RequestFactory):
        can_view_user = Permission.objects.filter(codename="view_user").first()
        can_view_user_group = GroupFactory.create(permissions=[can_view_user])
        user = UserFactory.create(groups=[can_view_user_group])

        another_user = UserFactory.create()

        request = rf.get("/users/")
        request.user = user

        response = user_detail_view(request, pk=another_user.id)

        assert response.status_code == 200

    # NOTE: All users can view their own profile (detail page), regardless of permission
    def test_can_view_own_profile_without_view_permission(
        self, user: User, rf: RequestFactory
    ):
        no_permissions_group = GroupFactory.create(permissions=[])
        user = UserFactory.create(groups=[no_permissions_group])

        request = rf.get("/users/")
        request.user = user

        response = user_detail_view(request, pk=user.id)

        assert response.status_code == 200

    def test_cannot_view_other_profile_without_view_permission(
        self, user: User, rf: RequestFactory
    ):
        no_permissions_group = GroupFactory.create(permissions=[])
        user = UserFactory.create(groups=[no_permissions_group])
        other_user = UserFactory.create()

        request = rf.get("/users/")
        request.user = user

        with pytest.raises(PermissionDenied):
            user_detail_view(request, pk=other_user.id)

    """
    TODO: The two tests below are more integration tests because we are testing the
    "real" URL and request/response cycle instead of only the view.
    The issue is that Django's RequestFactory doesn't have access to the Middleware:
    Session and authentication attributes must be supplied by the test itself if
    required for the view to function properly. So, for these tests we could add the
    middleware manually if that seems like a better approach.
    """

    def test_not_authenticated(self, user: User, rf: RequestFactory):
        client = Client()

        client.user = AnonymousUser()  # type: ignore
        url = "/users/" + str(user.id)
        response = client.get(url, follow=True)

        assert response.status_code == 200
        assert b"You must be signed in to view this page" in response.content

    def test_not_valid_password(self, user: User):
        client = Client()

        user = NewUserFactory.create()
        user.set_password("mygreatpassword")
        user.save()

        client.post(
            reverse("account_login"),
            {"login": user.email, "password": "mygreatpassword"},
        )

        url = "/users/" + str(user.id)
        response = client.get(url, follow=True)

        assert response.status_code == 200
        assert (
            b"You must set a new password before you can view this page"
            in response.content
        )


class TestUserCreateView:
    def test_with_valid_permission(self, user: User, rf: RequestFactory):
        can_add_user = Permission.objects.filter(codename="add_user").first()
        can_add_user_group = GroupFactory.create(permissions=[can_add_user])
        user = UserFactory.create(groups=[can_add_user_group])

        request = rf.get("/fake-url/")
        request.user = user

        response = user_create_view(request)

        assert response.status_code == 200

    def test_without_valid_permission(self, user: User, rf: RequestFactory):
        nothing_group = GroupFactory.create(permissions=[])
        user = UserFactory.create(groups=[nothing_group])

        request = rf.get("/users/")
        request.user = user

        with pytest.raises(PermissionDenied):
            user_create_view(request)

    def test_not_authenticated(self, user: User, rf: RequestFactory):
        client = Client()

        client.user = AnonymousUser()  # type: ignore
        url = "/users/"
        response = client.get(url, follow=True)

        assert response.status_code == 200
        assert b"You must be signed in to view this page" in response.content

    def test_not_valid_password(self, user: User):
        client = Client()

        user = NewUserFactory.create()
        user.set_password("mygreatpassword")
        user.save()

        client.post(
            reverse("account_login"),
            {"login": user.email, "password": "mygreatpassword"},
        )

        response = client.get("/users/", follow=True)

        assert response.status_code == 200
        assert (
            b"You must set a new password before you can view this page"
            in response.content
        )


class TestUserUpdateView:
    def test_get_success_url(self, user: User, rf: RequestFactory):
        view = UserUpdateView()
        request = rf.get("/fake-url/")
        request.user = user

        view.setup(request, pk=user.id)

        assert view.get_success_url() == f"/users/{user.id}/"

    def test_get_object(self, user: User, rf: RequestFactory):
        view = UserUpdateView()
        request = rf.get("/fake-url/")
        request.user = user

        view.setup(request, pk=user.id)

        assert view.get_object() == user


class TestUserSetPasswordView:
    """
    TODO: The two tests below are more integration tests because we are testing the
    "real" URL and request/response cycle instead of only the view.
    The issue is that Django's RequestFactory doesn't have access to the Middleware:
    Session and authentication attributes must be supplied by the test itself if
    required for the view to function properly. So, for these tests we could add the
    middleware manually if that seems like a better approach.
    """

    def test_set_password_without_valid_pw(self, user: User):
        client = Client()

        user = NewUserFactory.create()
        user.set_password("mygreatpassword")
        user.save()

        client.post(
            reverse("account_login"),
            {"login": user.email, "password": "mygreatpassword"},
        )

        url = "/users/set_password"
        response = client.get(url, follow=True)

        assert response.status_code == 200
        assert {
            b"Please type in a password of your choosing to replace your temporary password"
            in response.content
        }

    def test_set_password_with_valid_pw(self, user: User):
        client = Client()

        user = UserFactory.create()
        user.set_password("mygreatpassword")
        user.save()

        client.post(
            reverse("account_login"),
            {"login": user.email, "password": "mygreatpassword"},
        )

        url = "/users/set_password"
        response = client.get(url, follow=True)

        assert response.status_code == 200
        assert b"User has already set password" in response.content
