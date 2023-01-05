# from allauth.account.models import EmailAddress
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

User = get_user_model()

DEMO_USER_TYPES = ["Data Manager", "Data Viewer", "Field Worker"]


class Command(BaseCommand):
    help = "Seeds data manager, data viewer, and field worker users in the \
            local environment."

    def handle(self, *args, **options):
        if os.environ.get("DJANGO_SETTINGS_MODULE") != "config.settings.local":
            self.stdout.write(
                self.style.ERROR(
                    "This functionality is for demo purposes only in the "
                    "local environment. Exiting."
                )
            )
            exit()

        for user_type in DEMO_USER_TYPES:
            find_or_create_user(self, user_type)


def find_or_create_user(self, user_type):
    self.stdout.write(self.style.SUCCESS(f"Creating a {user_type}"))

    email_local_part = user_type.lower().replace(" ", "_")

    user, created = User.objects.get_or_create(
        email=f"{email_local_part}@example.com",
        defaults={"name": user_type, "is_active": True, "has_valid_password": True},
    )

    if created:
        user.set_password("Password1")
        user.save()

        user_group = Group.objects.get(name=f"{user_type}s")
        user_group.user_set.add(user)

        user_group.save()

        # If we do not require email confirmation, we no longer need the lines below
        # EmailAddress.objects.create(
        #     user=data_manager, email=data_manager.email, verified=True, primary=True
        # )

        self.stdout.write(self.style.SUCCESS(f"Successfully created a {user_type}!"))
