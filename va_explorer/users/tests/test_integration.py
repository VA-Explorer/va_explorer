import pytest
from django.core import mail
from django.test import RequestFactory
from django.urls import reverse

from va_explorer.users.forms import ExtendedUserCreationForm
from va_explorer.users.tests.factories import GroupFactory, NewUserFactory

pytestmark = pytest.mark.django_db


# A utility method to retrieve the temporary password contained in the plaintext email body.
# Update if using an html email template.
def retrieve_password_from_email_body(body):
    lines = body.split("\n")
    for line in lines:
        if "Temporary password" in line:
            password = line.split(" ")[2]

    return password


def test_user_creation(rf: RequestFactory):
    # A user with proto_user params does not exist yet.
    proto_user = NewUserFactory.build()
    group = GroupFactory.create()

    form = ExtendedUserCreationForm(
        {"name": proto_user.name, "email": proto_user.email, "groups": [group]}
    )

    # Note: The form expects a request object to be set in order to save it
    request = rf.get("/fake-url/")
    form.request = request

    assert len(mail.outbox) == 0

    user = form.save()
    assert user.name == proto_user.name
    assert user.email == proto_user.email
    assert user.groups.first() == group
    assert user.password != ""
    assert user.is_active is True
    assert user.has_valid_password is False

    assert len(mail.outbox) == 1

    email = mail.outbox[0]

    assert "Access Your VA Explorer Account" in email.subject
    assert user.email in email.to
    assert reverse("account_login") in email.body

    # Check the plaintext string we retrieved from the email body is the correct password for the user
    # See: https://docs.djangoproject.com/en/3.0/ref/contrib/auth/#django.contrib.auth.models.User.check_password
    password = retrieve_password_from_email_body(email.body)
    assert user.check_password(password) is True
