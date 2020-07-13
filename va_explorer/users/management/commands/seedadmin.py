from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds an admin user"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Creating Admin user..."))

        # TODO: Add role
        find_or_create_admin(self)


def find_or_create_admin(self):
    try:
        admin = User.objects.get(email="admin@example.com")
    except User.DoesNotExist:
        admin = None

    if admin:
        self.stdout.write(self.style.SUCCESS("Successfully located admin user!"))

        return admin
    else:
        admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="Password1"
        )
        admin.is_active = True
        admin.save()

        # To avoid email verification, we add the below line to each user
        EmailAddress.objects.create(user=admin, email=admin.email, verified=True)

        self.stdout.write(self.style.SUCCESS("Successfully created an admin user!"))

    return admin
