from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds an admin user"

    def handle(self, *args, **options):
        print("Creating Admin user...")

        # TODO: Add role
        find_or_create_admin(self)


def find_or_create_admin(self):
    user = User.objects.get(email="admin@example.com")

    if user:
        self.stdout.write(self.style.SUCCESS("Successfully located admin user!"))

        return user
    else:
        user = user.objects.create_superuser(
            username="admin", email="admin@example.com", password="Password1"
        )
        user.is_active = True
        user.save()

        # To avoid email verifiaction, we add the below line to each user
        EmailAddress.objects.create(user=user, email=user.email, verified=True)

        self.stdout.write(self.style.SUCCESS("Successfully created an admin user!"))

    return user
