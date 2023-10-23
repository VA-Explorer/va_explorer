from django.core.management.base import BaseCommand

from va_explorer.users.utils.user_form_backend import get_anonymized_user_info


class Command(BaseCommand):
    help = "Export an (anonymized) list of all users in the system along with \
            their roles and permissions. No PII is exported during this process."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output_file", type=str, nargs="?", default="user_list.csv"
        )
        parser.add_argument("--user_file", type=str, nargs="?", default=None)

    def handle(self, *args, **options):
        fname = options["output_file"]
        user_file = options["user_file"]
        user_df = get_anonymized_user_info(user_list_file=user_file)
        try:
            user_df.to_csv(fname, index=False)
            print(f"Exported info for {user_df.shape[0]} users to {fname}")
        except Exception as err:
            print(
                f"Error {err} occurred while exporting user info. Check \
                  provided filename is a valid path."
            )
