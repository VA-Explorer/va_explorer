from django.core.management.base import BaseCommand

from va_explorer.users.utils.user_form_backend import get_form_fields


class Command(BaseCommand):
    help = "Utility to get information on all fields in the current user \
            creation form. If planning to bulk create users from CSV, use this \
            command to figure out which settings to define in the file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output_file", type=str, nargs="?", default="user_form_fields.csv"
        )

    def handle(self, *args, **options):
        output_file = options["output_file"]
        field_data = get_form_fields(orient="v")
        print(field_data.T)
        field_data.to_csv(output_file)
        self.stdout.write(f"DONE. Exported fields to {output_file}")
