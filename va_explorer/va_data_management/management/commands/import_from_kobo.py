import os

from django.core.management.base import BaseCommand

from va_explorer.va_data_management.utils.kobo import download_responses
from va_explorer.va_data_management.utils.loading import load_records_from_dataframe

BATCH_SIZE = 5000


class Command(BaseCommand):
    help = "Loads verbal autopsy data from Kobo Toolbox into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--token",
            type=str,
            required=False,
            default=os.environ.get("KOBO_API_TOKEN"),
        )
        parser.add_argument(
            "--asset_id",
            type=str,
            required=False,
            default=os.environ.get("KOBO_ASSET_ID"),
        )

    def handle(self, *args, **options):
        _ = args  # unused
        token = options["token"]
        asset_id = options["asset_id"]

        if not token or not asset_id:
            self.stderr.write(
                "Must specify either --token and --asset_id arguments or "
                "KOBO_API_TOKEN and KOBO_ASSET_ID environment variables."
            )
            return

        # Make an initial call and loop if necessary
        forms, next_page = download_responses(token, asset_id, BATCH_SIZE, None)
        results = load_records_from_dataframe(forms)

        num_created = len(results["created"])
        num_ignored = len(results["ignored"])
        num_outdated = len(results["outdated"])
        num_corrected = len(results["corrected"])
        num_invalid = len(results["removed"])
        pages_processed = 1

        while next_page is not None:
            forms, next_page = download_responses(
                token, asset_id, BATCH_SIZE, next_page
            )
            results = load_records_from_dataframe(forms)
            num_created = num_created + len(results["created"])
            num_ignored = num_ignored + len(results["ignored"])
            num_outdated = num_outdated + len(results["outdated"])
            num_corrected = num_corrected + len(results["corrected"])
            num_invalid = num_invalid + len(results["removed"])
            pages_processed = pages_processed + 1
            self.stdout.write(
                "Processed Additional Page. " f"{pages_processed} processed total.."
            )

        self.stdout.write(
            f"Loaded {num_created} verbal autopsies from Kobo "
            f"{num_corrected} required correction in order to import "
            f"({num_ignored} ignored, {num_outdated} overwritten, "
            f"{num_invalid} removed as invalid)"
        )
