# from allauth.account.models import EmailAddress
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

User = get_user_model()


class Command(BaseCommand):
    help = "Creates an admin user"

    def add_arguments(self, parser):
        parser.add_argument("email")
        parser.add_argument("--password")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Creating Admin user..."))

        is_production_environment = (
            os.environ.get("DJANGO_SETTINGS_MODULE") == "config.settings.production"
        )

        if options["password"] is not None and is_production_environment:
            self.stdout.write(
                self.style.ERROR(
                    "Please do not supply your own password as an argument. The "
                    "system will assign you a random, temporary password and "
                    "print it to the console."
                )
            )
            exit()

        admin, created = User.objects.get_or_create(
            email=options["email"],
            defaults={"name": "Admin User", "is_active": True, "is_superuser": True},
        )

        if created:
            if options["password"] is None:
                password = get_random_string(length=32)
                admin.set_password(password)
                admin.has_valid_password = False

                self.stdout.write(
                    self.style.SUCCESS(f"Your temporary password is: {password}")
                )
            else:
                admin.set_password(options["password"])
                admin.has_valid_password = True

            admin.save()

            # If we do not require email confirmation, we no longer need the lines below
            # EmailAddress.objects.create(
            #     user=admin, email=admin.email, verified=True, primary=True
            # )

            self.stdout.write(self.style.SUCCESS("Successfully created an admin!"))
