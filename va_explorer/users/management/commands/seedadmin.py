# from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds an admin user"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Creating Admin user..."))

        admin, created = User.objects.get_or_create(
            email="admin@example.com",
            defaults={
                "name": "Admin User",
                "is_active": True,
                "is_superuser": True,
                "has_valid_password": True,
            },
        )

        if created:
            admin.set_password("Password1")
            admin.save()

            # If we do not require email confirmation, we no longer need the lines below
            # EmailAddress.objects.create(
            #     user=admin, email=admin.email, verified=True, primary=True
            # )

            self.stdout.write(self.style.SUCCESS("Successfully created an admin!"))
