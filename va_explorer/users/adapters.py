from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.http import HttpRequest
from django.urls import reverse


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest):
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", False)

    # https://github.com/pennersr/django-allauth/blob/c19a212c6ee786af1bb8bc1b07eb2aa8e2bf531b/allauth/account/adapter.py#L97
    def send_new_user_mail(self, request, user, temporary_password):
        url = request.build_absolute_uri(reverse("account_login"))

        ctx = {
            "user": user,
            "url": url,
            "temporary_password": temporary_password,
        }
        email_template = "account/email/new_user"
        self.send_mail(email_template, user.email, ctx)
