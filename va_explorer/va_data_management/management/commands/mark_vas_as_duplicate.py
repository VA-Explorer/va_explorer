# from allauth.account.models import EmailAddress


from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from va_explorer.va_data_management.models import VerbalAutopsy

User = get_user_model()


class Command(BaseCommand):
    help = "Marks existing VAs as duplicate"


    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Marks existing VAs as duplicate..."))

        if not hasattr(VerbalAutopsy, 'duplicate'):
            self.stdout.write(
                self.style.ERROR(
                    "Missing required database fields in Verbal Autopsy model."
                    "Please run latest migration to add fields."
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
