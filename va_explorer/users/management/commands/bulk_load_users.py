import argparse

from django.core.management.base import BaseCommand

from va_explorer.users.utils.user_form_backend import create_users_from_file


class Command(BaseCommand):
    help = "Create user accounts, assigning a temporary password, given a csv \
            file that has at a minimum email, user group, and location \
            restriction information but can also add any permission information \
            that apears in the user creation form. \
            Run ./manage.py get_user_template to see all such options."

    def add_arguments(self, parser):
        parser.add_argument("user_list_file", type=argparse.FileType("r"))
        parser.add_argument("--email_confirmation", type=bool, nargs="?", default=False)

    def handle(self, *args, **options):
        user_file = options["user_list_file"]
        email_confirmation = options.get("email_confirmation", False)
        create_users_from_file(user_file, email_confirmation=email_confirmation)
        self.stdout.write(self.style.SUCCESS("Done!"))
