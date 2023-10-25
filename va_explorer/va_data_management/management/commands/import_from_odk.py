import os

from django.core.management.base import BaseCommand

from va_explorer.va_data_management.utils.loading import load_records_from_dataframe
from va_explorer.va_data_management.utils.odk import download_responses


class Command(BaseCommand):
    help = "Loads a verbal autopsy data from ODK into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email", type=str, required=False, default=os.environ.get("ODK_EMAIL")
        )
        parser.add_argument(
            "--password",
            type=str,
            required=False,
            default=os.environ.get("ODK_PASSWORD"),
        )
        parser.add_argument("--project-name", type=str, required=False)
        parser.add_argument("--project-id", type=str, required=False)
        parser.add_argument("--form-id", type=str, required=False)
        parser.add_argument("--form-name", type=str, required=False)

    def handle(self, *args, **options):
        _ = args  # unused
        email = options["email"]
        password = options["password"]
        project_id = options["project_id"]
        project_name = options["project_name"]
        form_id = options["form_id"]
        form_name = options["form_name"]

        if not email or not password:
            self.stderr.write(
                "Must specify either --email and --password arguments or "
                "ODK_EMAIL and ODK_PASSWORD environment variables."
            )
            return

        # Should only specify project_id or project_name, not both.
        if (not project_id and not project_name) or (project_id and project_name):
            self.stderr.write(
                "Must specify either --project-id or --project-name arguments; not both"
            )
            return

        # Should only specify form_id or form_name, not both.
        if (not form_id and not form_name) or (form_id and form_name):
            self.stderr.write(
                "Must specify either --form-id or --form-name arguments; not both"
            )
            return

        forms = download_responses(
            email, password, project_name, project_id, form_name, form_id
        )

        results = load_records_from_dataframe(forms)

        num_created = len(results["created"])
        num_ignored = len(results["ignored"])
        num_outdated = len(results["outdated"])

        self.stdout.write(
            f"Loaded {num_created} verbal autopsies from ODK "
            f"({num_ignored} ignored, {num_outdated} removed as outdated)"
        )
