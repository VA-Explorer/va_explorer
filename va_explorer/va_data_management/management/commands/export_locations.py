from datetime import datetime

import pandas as pd
from django.core.management.base import BaseCommand

from va_explorer.va_data_management.models import Location


class Command(BaseCommand):
    help = "Exports current facility list as a CSV"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output_file",
            type=str,
            nargs="?",
            default="locations_"
            + datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
            + ".csv",
        )

    def handle(self, *args, **options):
        locations = list(Location.objects.filter(location_type="facility").all())

        keys = [location.path_string for location in locations]
        loc_df = pd.DataFrame({"path_string": keys})

        loc_df[["null", "country", "province", "district", "name"]] = loc_df[
            "path_string"
        ].str.split(r"\/", expand=True)

        loc_df["key"] = ""
        loc_df["status"] = ""

        for _, row in loc_df.iterrows():
            loc = Location.objects.filter(path_string=row["path_string"])
            row["key"] = [location.key for location in loc][0]

            status_b = [location.is_active for location in loc][0]
            row["status"] = "Active" if status_b else "Inactive"

        loc_df = loc_df.drop(columns=["path_string", "null", "country"])

        loc_df = loc_df.loc[
            (loc_df["name"].notnull())
            & (loc_df["province"].notnull())
            & (loc_df["district"].notnull())
        ]

        loc_df = loc_df[["province", "district", "name", "key", "status"]]

        fname = options["output_file"]

        try:
            loc_df.to_csv(fname, index=False)
            print(f"Exported current location file to {fname}")
        except Exception as err:
            print(
                f"Error {err} occurred while exporting location file. Check \
                  provided filename is a valid path."
            )
