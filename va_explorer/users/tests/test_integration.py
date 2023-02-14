import pytest
from django.core import mail
from django.test import Client, RequestFactory
from django.urls import reverse

from va_explorer.tests.factories import (
    GroupFactory,
    LocationFactory,
    NewUserFactory,
    UserFactory,
)
from va_explorer.users.forms import ExtendedUserCreationForm, UserUpdateForm

pytestmark = pytest.mark.django_db


# A utility method to retrieve the temporary password contained in the plaintext
# email body. Update if using an html email template.
def retrieve_password_from_email_body(body):
    lines = body.split("\n")
    for line in lines:
        if "Temporary password" in line:
            password = line.split(" ")[2]

    return password


# A utility method to create and return a new user via the ExtendedUserCreationForm
def create_and_return_a_new_user(rf, proto_user):
    group = GroupFactory.create()
    location = LocationFactory.create()

    form = ExtendedUserCreationForm(
        {
            "name": proto_user.name,
            "email": proto_user.email,
            "group": group,
            "geographic_access": "location-specific",
            "location_restrictions": [location],
        }
    )

    # Note: The form expects a request object to be set in order to save it
    request = rf.get("/fake-url/")
    form.request = request

    user = form.save()

    return user


def update_and_return_a_field_worker(rf, field_worker, group, facility):
    form = UserUpdateForm(
        {
            "name": field_worker.name,
            "email": field_worker.email,
            "group": group,
            "geographic_access": "location-specific",
            "location_restrictions": [facility],
        }
    )

    request = rf.get("/fake-url/")
    form.request = request
    form.instance = field_worker

    field_worker_updated = form.save()

    return field_worker_updated


def test_user_creation(rf: RequestFactory):
    # A user with proto_user params does not exist yet.
    proto_user = NewUserFactory.build()

    assert len(mail.outbox) == 0

    user = create_and_return_a_new_user(rf, proto_user)

    assert user.name == proto_user.name
    assert user.email == proto_user.email
    assert user.password != ""
    assert user.is_active is True
    assert user.has_valid_password is False

    assert len(mail.outbox) == 1

    email = mail.outbox[0]

    assert "Access Your VA Explorer Account" in email.subject
    assert user.email in email.to
    assert reverse("account_login") in email.body

    # Check the plaintext string we retrieved from the email body is the correct
    # password for the user
    # See: https://docs.djangoproject.com/en/3.0/ref/contrib/auth/#django.contrib.auth.models.User.check_password
    password = retrieve_password_from_email_body(email.body)
    assert user.check_password(password) is True


def test_user_set_password_after_create(rf: RequestFactory):
    # A user with proto_user params does not exist yet.
    proto_user = NewUserFactory.build()

    user = create_and_return_a_new_user(rf, proto_user)

    assert user.has_valid_password is False

    email = mail.outbox[0]
    password = retrieve_password_from_email_body(email.body)

    client = Client()

    response = client.post(
        reverse("account_login"),
        {"login": user.email, "password": password},
        follow=True,
    )

    # If the user does not have a valid password, they are redirected to
    # users:set_password
    assert b"Set Password" in response.content
    assert response.request["PATH_INFO"] == reverse("users:set_password")

    response = client.post(
        reverse("users:set_password"),
        {"password1": "AReallyGreatPassword1!", "password2": "AReallyGreatPassword1!"},
        follow=True,
    )

    assert response.status_code == 200

    user.refresh_from_db()
    assert user.has_valid_password is True
    assert user.check_password("AReallyGreatPassword1!") is True


def test_user_change_password():
    user = UserFactory.build()
    password = "AReallyGreatPassword1!"
    user.set_password(password)
    user.has_valid_password = True
    user.save()

    client = Client()

    client.force_login(user=user)

    response = client.post(
        reverse("users:change_password"),
        {
            "current_password": "AReallyGreatPassword1!",
            "password1": "MyNewPassword123!",
            "password2": "MyNewPassword123!",
        },
        follow=True,
    )

    assert response.status_code == 200

    user.refresh_from_db()
    assert user.check_password("MyNewPassword123!") is True
