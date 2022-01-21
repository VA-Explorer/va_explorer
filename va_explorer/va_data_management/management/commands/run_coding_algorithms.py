import argparse
import pandas as pd
import time
from django.core.management.base import BaseCommand
from django.db.models import F
from va_explorer.va_data_management.utils.coding import run_coding_algorithms, ALGORITHM_SETTINGS, validate_algorithm_settings
from va_explorer.va_data_management.models import VerbalAutopsy, CauseOfDeath


class Command(BaseCommand):

    help = 'Run cause coding algorithms'

    def add_arguments(self, parser):
        # whether or not to overwrite existing CODs - if True, will clear all CODs before running
        parser.add_argument('--overwrite', type=bool, nargs='?', default=False)
        parser.add_argument('--cod_fname', type=str, nargs='?', default='old_cod_mapping.csv')

    def handle(self, **options):
        ti = time.time()
        # validate algorithm settings first. Only proceed if settings are valid. 
        settings_valid = validate_algorithm_settings(ALGORITHM_SETTINGS)
        if settings_valid:
            if options['overwrite']:
                self.clear_and_save_old_cods(options['cod_fname'])

            print('coding all eligible VAs... ')
            results = run_coding_algorithms()
            num_coded = len(results['causes'])
            num_total = len(results['verbal_autopsies'])
            num_issues = len(results['issues'])
            self.stdout.write(f'DONE. Total time: {time.time() - ti} secs')
            self.stdout.write(f'Coded {num_coded} verbal autopsies (out of {num_total}) [{num_issues} issues]')
        else:
            raise ValueError(f"At least one invalid algorithm setting in: \n {ALGORITHM_SETTINGS}. See va_data_management.utils.coding.py for valid setting values." )

    def clear_and_save_old_cods(self, cod_fname=None):
        
        print('clearing old CODs...')
        if not cod_fname:
            cod_fname = 'old_cod_mapping.csv'
        # export original CODs (and corersponding VA IDs) to flat file
        va_cod_df = pd.DataFrame(CauseOfDeath.objects.all().values())
        # only export if VAs have been coded
        if not va_cod_df.empty:
            va_cod_df.to_csv(cod_fname, index=False)
            print(f'exported {va_cod_df.shape[0]} old CODs to {cod_fname}')
        else:
            print('No CODs found, skipping export')

        # clear CODs to re-run coding algorithm
        CauseOfDeath.objects.all().delete()
