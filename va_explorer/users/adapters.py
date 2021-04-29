from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.http import HttpRequest
from django.urls import reverse
import os

# Choolwe EMAIL_URL=smtp://mail:25
EMAIL_URL = os.environ.get('EMAIL_URL', 'consolemail://')

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
        message = self.render_mail(email_template, user.email, ctx)
                
        # ensure credentials get written to stdout, regardless of email backend
        if not ("console" in settings.EMAIL_BACKEND and EMAIL_URL.startswith("consolemail")):
            print(message.message())
        
        try:
            message.send()
        except ConnectionRefusedError:
            print("WARNING: could not send email because connection was resfused. Ensure that EMAIL_URL environment variable and all django email settings are correct.")
            print(f"\t(see base or production files in config.settings). Current EMAIL_URL: {EMAIL_URL}")