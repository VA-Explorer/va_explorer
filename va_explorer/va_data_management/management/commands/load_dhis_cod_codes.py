import argparse

import pandas as pd
from django.core.management.base import BaseCommand

from va_explorer.va_data_management.models import CODCodesDHIS


class Command(BaseCommand):
    help = (
        "Loads COD codes necessary for dhis2 export into the database from a CSV file"
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=argparse.FileType("r"))

    def handle(self, *args, **options):
        dhis_df = pd.read_csv(options["csv_file"]).rename(columns=lambda c: c.lower())
        dhis_code_objs = [
            CODCodesDHIS(**cod_rec) for cod_rec in dhis_df.to_dict(orient="records")
        ]
        CODCodesDHIS.objects.bulk_create(dhis_code_objs)
        print(f"Loaded {len(dhis_code_objs)} DHIS COD Code Objects")
