import time

import pandas as pd
from django.core.management.base import BaseCommand

from va_explorer.va_data_management.models import CauseOfDeath
from va_explorer.va_data_management.utils.coding import (
    ALGORITHM_SETTINGS,
    run_coding_algorithms,
    validate_algorithm_settings,
)


class Command(BaseCommand):
    help = "Run cause coding algorithms"

    def add_arguments(self, parser):
        # whether or not to overwrite existing CODs - if True, will
        # lear all CODs before running
        parser.add_argument("--overwrite", type=bool, nargs="?", default=False)
        parser.add_argument(
            "--cod_fname", type=str, nargs="?", default="old_cod_mapping.csv"
        )

    def handle(self, **options):
        ti = time.time()
        # validate algorithm settings first. Only proceed if settings are valid.
        if validate_algorithm_settings():
            if options["overwrite"]:
                self.clear_and_save_old_cods(options["cod_fname"])

            print("coding all eligible VAs... ")
            stats = run_coding_algorithms()
            num_coded = len(stats["causes"])
            num_total = len(stats["verbal_autopsies"])
            num_issues = len(stats["issues"])
            self.stdout.write(f"DONE. Total time: {time.time() - ti} secs")
            self.stdout.write(
                f"Coded {num_coded} verbal autopsies (out of {num_total}) [{num_issues} issues]"
            )
        else:
            print(
                f"At least one invalid algorithm setting in: \n {ALGORITHM_SETTINGS}. \
                  See va_data_management.utils.coding.py for valid settings.\n Exiting."
            )
            exit()

    def clear_and_save_old_cods(self, cod_fname):
        print("clearing old CODs...")
        # export original CODs (and corresponding VA IDs) to flat file
        va_cod_df = pd.DataFrame(CauseOfDeath.objects.all().values())
        # only export if VAs have been coded
        if not va_cod_df.empty:
            va_cod_df.to_csv(cod_fname, index=False)
            print(f"exported {va_cod_df.shape[0]} old CODs to {cod_fname}")
        else:
            print("No CODs found, skipping export")

        # clear CODs to re-run coding algorithm
        CauseOfDeath.objects.all().delete()
